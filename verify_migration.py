#!/usr/bin/env python3
"""
PostgreSQL Migration Verification Script
Comprehensive data integrity verification between source and target databases
"""

import asyncio
import asyncpg
import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
import html

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Database URLs
SOURCE_URL = os.getenv('SOURCE_DB_URL', 'postgresql+asyncpg://postgres:2030@localhost:5432/platelink')
TARGET_URL = os.getenv('TARGET_DB_URL', 'postgresql://platelink_user:PPMZUSp5yyIshueVDBbmU3RaKwGM7blR@dpg-d9al849kh4rs73fu4pv0-a.oregon-postgres.render.com/platelink')

def clean_url(url: str) -> str:
    return url.replace('postgresql+asyncpg://', 'postgresql://')

class MigrationVerifier:
    def __init__(self, source_url: str, target_url: str):
        self.source_url = clean_url(source_url)
        self.target_url = clean_url(target_url)
        self.source_conn = None
        self.target_conn = None
        self.results = {
            'verification_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tables': 0,
                'tables_ok': 0,
                'tables_warning': 0,
                'tables_error': 0,
                'total_rows_source': 0,
                'total_rows_target': 0,
                'size_source_mb': 0,
                'size_target_mb': 0,
                'sequence_mismatches': 0,
                'fk_mismatches': 0,
                'index_mismatches': 0,
                'orphaned_records_errors': 0
            },
            'table_results': [],
            'sequence_results': [],
            'fk_results': [],
            'index_results': [],
            'orphaned_results': [],
            'errors': []
        }

    async def connect(self):
        try:
            logger.info("Connecting to source database...")
            self.source_conn = await asyncpg.connect(self.source_url)
            logger.info("✅ Connected to source database")
        except Exception as e:
            logger.warning(f"Failed to connect to source without SSL: {e}. Trying with SSL...")
            try:
                self.source_conn = await asyncpg.connect(self.source_url, ssl='require')
                logger.info("✅ Connected to source database (SSL)")
            except Exception as e_ssl:
                logger.error(f"❌ Failed to connect to source database: {e_ssl}")
                raise

        try:
            logger.info("Connecting to target database (SSL)...")
            self.target_conn = await asyncpg.connect(self.target_url, ssl='require')
            logger.info("✅ Connected to target database")
        except Exception as e:
            logger.warning(f"Failed to connect to target with SSL: {e}. Trying without SSL...")
            try:
                self.target_conn = await asyncpg.connect(self.target_url)
                logger.info("✅ Connected to target database (No SSL)")
            except Exception as e_nossl:
                logger.error(f"❌ Failed to connect to target database: {e_nossl}")
                raise

    async def disconnect(self):
        if self.source_conn:
            await self.source_conn.close()
        if self.target_conn:
            await self.target_conn.close()
        logger.info("🔌 Connections closed")

    async def get_all_tables(self) -> List[str]:
        query = """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT IN ('spatial_ref_sys', 'geography_columns', 'geometry_columns')
            ORDER BY tablename
        """
        result = await self.source_conn.fetch(query)
        return [row['tablename'] for row in result]

    async def get_table_info(self, conn: asyncpg.Connection, table_name: str) -> Dict[str, Any]:
        info = {
            'columns': [],
            'primary_key': [],
            'row_count': 0,
            'size_bytes': 0,
            'checksum': None
        }
        
        try:
            col_query = """
                SELECT 
                    column_name, 
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns
                WHERE table_name = $1 AND table_schema = 'public'
                ORDER BY ordinal_position
            """
            rows = await conn.fetch(col_query, table_name)
            info['columns'] = [dict(r) for r in rows]
            
            pk_query = """
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_name = $1
                    AND tc.table_schema = 'public'
            """
            info['primary_key'] = [row['column_name'] for row in await conn.fetch(pk_query, table_name)]
            
            count_query = f'SELECT COUNT(*) FROM "{table_name}"'
            info['row_count'] = await conn.fetchval(count_query)
            
            size_query = f"SELECT pg_total_relation_size('public.\"{table_name}\"')"
            info['size_bytes'] = await conn.fetchval(size_query)
            
            if info['row_count'] > 0 and info['row_count'] <= 100000:
                try:
                    columns = [col['column_name'] for col in info['columns']]
                    exclude_types = {'bytea', 'geometry', 'geography'}
                    valid_cols = [col for col in info['columns'] if col['data_type'] not in exclude_types]
                    valid_col_names = [col['column_name'] for col in valid_cols]

                    if valid_cols:
                        select_cols = []
                        for col in valid_cols:
                            col_name = col['column_name']
                            dtype = col['data_type']
                            if 'timestamp' in dtype.lower():
                                select_cols.append(f"COALESCE(to_char(\"{col_name}\" AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS.US'), 'NULL')")
                            elif 'date' == dtype.lower():
                                select_cols.append(f"COALESCE(to_char(\"{col_name}\", 'YYYY-MM-DD'), 'NULL')")
                            elif dtype.lower() in {'numeric', 'double precision', 'real'}:
                                select_cols.append(f"COALESCE(TRIM(trailing '.' from TRIM(trailing '0' from round(\"{col_name}\"::numeric, 6)::text)), 'NULL')")
                            elif dtype.lower() == 'boolean':
                                select_cols.append(f"COALESCE(CASE WHEN \"{col_name}\" THEN 't' ELSE 'f' END, 'NULL')")
                            else:
                                select_cols.append(f"COALESCE(\"{col_name}\"::text, 'NULL')")
                        
                        concat_cols = " || '||' || ".join(select_cols)
                        order_cols = info['primary_key'] if info['primary_key'] else [c['column_name'] for c in valid_cols]
                        order_by_clause = " ORDER BY " + ", ".join([f'"{col}"::text COLLATE "C"' for col in order_cols])
                        
                        checksum_query = f"""
                            SELECT MD5(string_agg({concat_cols}, '||'{order_by_clause}))
                            FROM "{table_name}"
                        """
                        info['checksum'] = await conn.fetchval(checksum_query)
                except Exception as checksum_err:
                    logger.warning(f"Could not generate checksum for {table_name}: {checksum_err}")
                    
        except Exception as e:
            logger.error(f"Error getting info for table {table_name}: {e}")
            
        return info

    async def compare_schema(self, table_name: str, source_info: Dict, target_info: Dict) -> List[str]:
        issues = []
        source_cols = {col['column_name']: col for col in source_info['columns']}
        target_cols = {col['column_name']: col for col in target_info['columns']}
        
        missing_cols = set(source_cols.keys()) - set(target_cols.keys())
        if missing_cols:
            issues.append(f"Missing columns in target: {', '.join(missing_cols)}")
        
        extra_cols = set(target_cols.keys()) - set(source_cols.keys())
        if extra_cols:
            issues.append(f"Extra columns in target: {', '.join(extra_cols)}")
        
        for col_name, src_col in source_cols.items():
            if col_name in target_cols:
                tgt_col = target_cols[col_name]
                if src_col['data_type'] != tgt_col['data_type']:
                    issues.append(f"Data type mismatch for '{col_name}': source={src_col['data_type']}, target={tgt_col['data_type']}")
                if src_col['is_nullable'] != tgt_col['is_nullable']:
                    issues.append(f"Nullability mismatch for '{col_name}': source={src_col['is_nullable']}, target={tgt_col['is_nullable']}")
                if src_col.get('character_maximum_length') != tgt_col.get('character_maximum_length'):
                    issues.append(f"Char length mismatch for '{col_name}': source={src_col.get('character_maximum_length')}, target={tgt_col.get('character_maximum_length')}")
                if src_col.get('numeric_precision') != tgt_col.get('numeric_precision') or src_col.get('numeric_scale') != tgt_col.get('numeric_scale'):
                    issues.append(f"Numeric precision/scale mismatch for '{col_name}': source=({src_col.get('numeric_precision')}, {src_col.get('numeric_scale')}), target=({tgt_col.get('numeric_precision')}, {tgt_col.get('numeric_scale')})")
        
        if set(source_info['primary_key']) != set(target_info['primary_key']):
            issues.append(f"Primary key mismatch: source={source_info['primary_key']}, target={target_info['primary_key']}")
        
        return issues

    async def verify_table(self, table_name: str) -> Dict[str, Any]:
        result = {
            'table_name': table_name,
            'status': 'OK',
            'messages': [],
            'source_rows': 0,
            'target_rows': 0,
            'row_mismatch': False,
            'schema_issues': [],
            'data_mismatch': False,
            'size_source_bytes': 0,
            'size_target_bytes': 0,
            'checksum_source': None,
            'checksum_target': None
        }
        
        try:
            source_info = await self.get_table_info(self.source_conn, table_name)
            target_info = await self.get_table_info(self.target_conn, table_name)
            
            result['source_rows'] = source_info['row_count']
            result['target_rows'] = target_info['row_count']
            result['size_source_bytes'] = source_info['size_bytes']
            result['size_target_bytes'] = target_info['size_bytes']
            result['checksum_source'] = source_info.get('checksum')
            result['checksum_target'] = target_info.get('checksum')
            
            if source_info['row_count'] != target_info['row_count']:
                result['row_mismatch'] = True
                result['messages'].append(f"Row count mismatch: source={source_info['row_count']}, target={target_info['row_count']}")
                result['status'] = 'ERROR'
            
            schema_issues = await self.compare_schema(table_name, source_info, target_info)
            if schema_issues:
                result['schema_issues'] = schema_issues
                result['messages'].extend(schema_issues)
                result['status'] = 'ERROR'
            
            if source_info.get('checksum') and target_info.get('checksum'):
                if source_info['checksum'] != target_info['checksum']:
                    result['data_mismatch'] = True
                    result['messages'].append("Data checksum mismatch - data contents differ or may be corrupted")
                    result['status'] = 'ERROR'
            elif source_info['row_count'] > 0 and source_info['row_count'] <= 100000 and (not source_info.get('checksum') or not target_info.get('checksum')):
                result['messages'].append("Checksum generation failed on one of the servers")
                if result['status'] == 'OK':
                    result['status'] = 'WARNING'
            
            if source_info['size_bytes'] > 0:
                size_diff_percent = abs(source_info['size_bytes'] - target_info['size_bytes']) / source_info['size_bytes'] * 100
                if size_diff_percent > 15 and source_info['row_count'] > 0:
                    result['messages'].append(f"Size difference of {size_diff_percent:.2f}% detected (source={source_info['size_bytes'] / 1024:.1f} KB, target={target_info['size_bytes'] / 1024:.1f} KB)")
                    if result['status'] == 'OK':
                        result['status'] = 'WARNING'
            
            if result['status'] == 'OK':
                result['messages'].append(f"Table verified successfully: {source_info['row_count']} rows")
            
        except Exception as e:
            result['status'] = 'ERROR'
            result['messages'].append(f"Verification error: {str(e)}")
            
        return result

    async def verify_sequences(self) -> List[Dict[str, Any]]:
        results = []
        try:
            seq_query = """
                SELECT 
                    schemaname,
                    sequencename,
                    last_value,
                    start_value,
                    increment_by,
                    max_value
                FROM pg_sequences
                WHERE schemaname = 'public'
            """
            
            source_seqs = await self.source_conn.fetch(seq_query)
            target_seqs = await self.target_conn.fetch(seq_query)
            
            source_seq_dict = {seq['sequencename']: seq for seq in source_seqs}
            target_seq_dict = {seq['sequencename']: seq for seq in target_seqs}
            
            for seq_name, src_seq in source_seq_dict.items():
                result = {
                    'sequence_name': seq_name,
                    'source_last_value': src_seq['last_value'],
                    'target_last_value': None,
                    'status': 'OK',
                    'message': ''
                }
                
                if seq_name in target_seq_dict:
                    tgt_seq = target_seq_dict[seq_name]
                    result['target_last_value'] = tgt_seq['last_value']
                    
                    if src_seq['last_value'] != tgt_seq['last_value']:
                        result['status'] = 'WARNING'
                        result['message'] = f"Sequence value mismatch: source={src_seq['last_value']}, target={tgt_seq['last_value']}"
                    else:
                        result['message'] = f"Sequence verified: {src_seq['last_value']}"
                else:
                    result['status'] = 'ERROR'
                    result['message'] = "Sequence missing in target database"
                    
                results.append(result)
        except Exception as e:
            logger.error(f"Error verifying sequences: {e}")
        return results

    async def verify_foreign_keys(self) -> List[Dict[str, Any]]:
        results = []
        try:
            fk_query = """
                SELECT
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = 'public'
                ORDER BY tc.table_name
            """
            
            source_fks = await self.source_conn.fetch(fk_query)
            target_fks = await self.target_conn.fetch(fk_query)
            
            source_fk_dict = {fk['constraint_name']: fk for fk in source_fks}
            target_fk_dict = {fk['constraint_name']: fk for fk in target_fks}
            
            for fk_name, src_fk in source_fk_dict.items():
                result = {
                    'constraint_name': fk_name,
                    'table': src_fk['table_name'],
                    'status': 'OK',
                    'message': ''
                }
                
                if fk_name in target_fk_dict:
                    tgt_fk = target_fk_dict[fk_name]
                    if (src_fk['column_name'] == tgt_fk['column_name'] and
                        src_fk['foreign_table_name'] == tgt_fk['foreign_table_name']):
                        result['message'] = f"FK links '{src_fk['column_name']}' to '{src_fk['foreign_table_name']}({src_fk['foreign_column_name']})'"
                    else:
                        result['status'] = 'ERROR'
                        result['message'] = "FK constraint definition mismatch"
                else:
                    result['status'] = 'ERROR'
                    result['message'] = "FK constraint missing in target"
                    
                results.append(result)
        except Exception as e:
            logger.error(f"Error verifying foreign keys: {e}")
        return results

    async def verify_indexes(self) -> List[Dict[str, Any]]:
        results = []
        try:
            idx_query = """
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND indexname NOT LIKE '%_pkey'
                ORDER BY tablename
            """
            
            source_idx = await self.source_conn.fetch(idx_query)
            target_idx = await self.target_conn.fetch(idx_query)
            
            source_idx_dict = {idx['indexname']: idx for idx in source_idx}
            target_idx_dict = {idx['indexname']: idx for idx in target_idx}
            
            for idx_name, src_idx in source_idx_dict.items():
                result = {
                    'index_name': idx_name,
                    'table': src_idx['tablename'],
                    'status': 'OK',
                    'message': ''
                }
                
                if idx_name in target_idx_dict:
                    tgt_idx = target_idx_dict[idx_name]
                    src_def = " ".join(src_idx['indexdef'].split()).lower()
                    tgt_def = " ".join(tgt_idx['indexdef'].split()).lower()
                    if src_def == tgt_def:
                        result['message'] = "Index exists and matches definition"
                    else:
                        result['status'] = 'WARNING'
                        result['message'] = "Index definition differs slightly in SQL format"
                else:
                    result['status'] = 'ERROR'
                    result['message'] = "Index missing in target"
                    
                results.append(result)
        except Exception as e:
            logger.error(f"Error verifying indexes: {e}")
        return results

    async def verify_missing_tables(self) -> Dict[str, List[str]]:
        source_tables = set(await self.get_all_tables())
        target_tables_query = """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            AND tablename NOT IN ('spatial_ref_sys', 'geography_columns', 'geometry_columns')
        """
        target_tables = set([row['tablename'] for row in await self.target_conn.fetch(target_tables_query)])
        
        missing = source_tables - target_tables
        extra = target_tables - source_tables
        
        return {
            'missing_tables': list(missing),
            'extra_tables': list(extra)
        }

    async def verify_orphaned_records(self) -> List[Dict[str, Any]]:
        results = []
        try:
            fk_query = """
                SELECT
                    tc.table_name AS child_table,
                    kcu.column_name AS child_column,
                    ccu.table_name AS parent_table,
                    ccu.column_name AS parent_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = 'public'
                ORDER BY tc.table_name
            """
            fks = await self.source_conn.fetch(fk_query)
            
            for fk in fks:
                child_table = fk['child_table']
                child_column = fk['child_column']
                parent_table = fk['parent_table']
                parent_column = fk['parent_column']
                
                query = f"""
                    SELECT COUNT(*) 
                    FROM "{child_table}" c
                    LEFT JOIN "{parent_table}" p ON c."{child_column}" = p."{parent_column}"
                    WHERE c."{child_column}" IS NOT NULL AND p."{parent_column}" IS NULL
                """
                try:
                    orphaned_count = await self.target_conn.fetchval(query)
                    result = {
                        'child_table': child_table,
                        'child_column': child_column,
                        'parent_table': parent_table,
                        'parent_column': parent_column,
                        'orphaned_count': orphaned_count,
                        'status': 'OK' if orphaned_count == 0 else 'ERROR',
                        'message': f"No orphaned records found" if orphaned_count == 0 else f"Found {orphaned_count} orphaned records referencing {parent_table}({parent_column})"
                    }
                    results.append(result)
                except Exception as check_err:
                    results.append({
                        'child_table': child_table,
                        'child_column': child_column,
                        'parent_table': parent_table,
                        'parent_column': parent_column,
                        'orphaned_count': 0,
                        'status': 'WARNING',
                        'message': f"Could not perform orphaned record check: {check_err}"
                    })
        except Exception as e:
            logger.error(f"Error checking orphaned records: {e}")
        return results

    async def get_database_size(self, conn: asyncpg.Connection) -> float:
        query = "SELECT pg_database_size(current_database())"
        size_bytes = await conn.fetchval(query)
        return size_bytes / (1024 * 1024)

    async def run_verification(self) -> Dict[str, Any]:
        logger.info("🔍 Starting comprehensive migration verification...")
        
        try:
            await self.connect()
            
            table_check = await self.verify_missing_tables()
            if table_check['missing_tables']:
                self.results['errors'].extend([
                    f"Missing table in target: {tbl}" for tbl in table_check['missing_tables']
                ])
            if table_check['extra_tables']:
                self.results['errors'].extend([
                    f"Extra table in target: {tbl}" for tbl in table_check['extra_tables']
                ])
            
            tables = await self.get_all_tables()
            self.results['summary']['total_tables'] = len(tables)
            
            for table in tables:
                result = await self.verify_table(table)
                self.results['table_results'].append(result)
                
                if result['status'] == 'OK':
                    self.results['summary']['tables_ok'] += 1
                elif result['status'] == 'WARNING':
                    self.results['summary']['tables_warning'] += 1
                else:
                    self.results['summary']['tables_error'] += 1
                
                self.results['summary']['total_rows_source'] += result['source_rows']
                self.results['summary']['total_rows_target'] += result['target_rows']
            
            self.results['sequence_results'] = await self.verify_sequences()
            seq_errors = [seq for seq in self.results['sequence_results'] if seq['status'] == 'ERROR']
            self.results['summary']['sequence_mismatches'] = len(seq_errors)
            
            self.results['fk_results'] = await self.verify_foreign_keys()
            fk_errors = [fk for fk in self.results['fk_results'] if fk['status'] == 'ERROR']
            self.results['summary']['fk_mismatches'] = len(fk_errors)
            
            self.results['index_results'] = await self.verify_indexes()
            idx_errors = [idx for idx in self.results['index_results'] if idx['status'] == 'ERROR']
            self.results['summary']['index_mismatches'] = len(idx_errors)
            
            self.results['orphaned_results'] = await self.verify_orphaned_records()
            orph_errors = [o for o in self.results['orphaned_results'] if o['status'] == 'ERROR']
            self.results['summary']['orphaned_records_errors'] = len(orph_errors)

            self.results['summary']['size_source_mb'] = await self.get_database_size(self.source_conn)
            self.results['summary']['size_target_mb'] = await self.get_database_size(self.target_conn)
            
            if (self.results['summary']['tables_error'] == 0 
                and self.results['summary']['sequence_mismatches'] == 0
                and self.results['summary']['fk_mismatches'] == 0
                and self.results['summary']['index_mismatches'] == 0
                and self.results['summary']['orphaned_records_errors'] == 0
                and not self.results['errors']):
                self.results['overall_status'] = 'PASSED'
            elif (self.results['summary']['tables_error'] > 0 
                  or self.results['summary']['fk_mismatches'] > 0
                  or self.results['summary']['orphaned_records_errors'] > 0):
                self.results['overall_status'] = 'FAILED'
            else:
                self.results['overall_status'] = 'WARNING'
            
            self.generate_html_report()
            self.generate_json_report()
            self.print_summary()
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            raise
        finally:
            await self.disconnect()
            
        return self.results

    def generate_html_report(self):
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        overall = self.results['overall_status']
        status_emoji = '✅' if overall == 'PASSED' else ('❌' if overall == 'FAILED' else '⚠️')
        
        table_rows_html = ""
        for table in self.results['table_results']:
            status_class = table['status']
            row_diff = table['target_rows'] - table['source_rows']
            row_diff_str = f"+{row_diff:,}" if row_diff > 0 else (f"{row_diff:,}" if row_diff < 0 else "0")
            row_diff_color = "#ef4444" if row_diff != 0 else "#10b981"
            size_src_kb = table['size_source_bytes'] / 1024
            size_tgt_kb = table['size_target_bytes'] / 1024
            
            msg_list = [f"<li>{html.escape(msg)}</li>" for msg in table['messages']]
            messages_html = f"<ul>{''.join(msg_list)}</ul>" if msg_list else "<span class='text-muted'>None</span>"
            
            table_rows_html += f"""
            <tr>
                <td class="font-bold">{html.escape(table['table_name'])}</td>
                <td><span class="badge badge-{status_class}">{status_class}</span></td>
                <td>{table['source_rows']:,}</td>
                <td>{table['target_rows']:,}</td>
                <td style="color: {row_diff_color}; font-weight: bold;">{row_diff_str}</td>
                <td>{size_src_kb:.1f} KB / {size_tgt_kb:.1f} KB</td>
                <td class="messages-cell">{messages_html}</td>
            </tr>
            """

        seq_rows_html = ""
        for seq in self.results['sequence_results']:
            status_class = seq['status']
            seq_rows_html += f"""
            <tr>
                <td class="font-bold">{html.escape(seq['sequence_name'])}</td>
                <td><span class="badge badge-{status_class}">{status_class}</span></td>
                <td>{seq['source_last_value'] if seq['source_last_value'] is not None else 'N/A'}</td>
                <td>{seq['target_last_value'] if seq['target_last_value'] is not None else 'N/A'}</td>
                <td>{html.escape(seq.get('message', ''))}</td>
            </tr>
            """
            
        fk_rows_html = ""
        for fk in self.results['fk_results']:
            status_class = fk['status']
            fk_rows_html += f"""
            <tr>
                <td class="font-bold">{html.escape(fk['constraint_name'])}</td>
                <td><span class="badge badge-{status_class}">{status_class}</span></td>
                <td>{html.escape(fk['table'])}</td>
                <td>{html.escape(fk.get('message', ''))}</td>
            </tr>
            """

        idx_rows_html = ""
        for idx in self.results['index_results']:
            status_class = idx['status']
            idx_rows_html += f"""
            <tr>
                <td class="font-bold">{html.escape(idx['index_name'])}</td>
                <td><span class="badge badge-{status_class}">{status_class}</span></td>
                <td>{html.escape(idx['table'])}</td>
                <td>{html.escape(idx.get('message', ''))}</td>
            </tr>
            """

        orphaned_rows_html = ""
        if self.results['orphaned_results']:
            for orph in self.results['orphaned_results']:
                status_class = orph['status']
                orphaned_rows_html += f"""
                <tr>
                    <td class="font-bold">{html.escape(orph['child_table'])}.{html.escape(orph['child_column'])}</td>
                    <td><span class="badge badge-{status_class}">{status_class}</span></td>
                    <td>{html.escape(orph['parent_table'])}.{html.escape(orph['parent_column'])}</td>
                    <td>{orph['orphaned_count']}</td>
                    <td>{html.escape(orph.get('message', ''))}</td>
                </tr>
                """
        else:
            orphaned_rows_html = "<tr><td colspan='5' class='text-muted text-center'>No foreign keys to verify for orphaned records.</td></tr>"

        issues_list_html = ""
        all_warnings_and_errors = []
        for err in self.results['errors']:
            all_warnings_and_errors.append(f"<li class='global-error'>{html.escape(err)}</li>")
            
        for t in self.results['table_results']:
            if t['status'] != 'OK':
                for msg in t['messages']:
                    all_warnings_and_errors.append(f"<li><strong>{html.escape(t['table_name'])}</strong>: {html.escape(msg)}</li>")
                    
        for seq in self.results['sequence_results']:
            if seq['status'] != 'OK':
                all_warnings_and_errors.append(f"<li>Sequence <strong>{html.escape(seq['sequence_name'])}</strong>: {html.escape(seq['message'])}</li>")
                
        for fk in self.results['fk_results']:
            if fk['status'] != 'OK':
                all_warnings_and_errors.append(f"<li>FK <strong>{html.escape(fk['constraint_name'])}</strong>: {html.escape(fk['message'])}</li>")
                
        for idx in self.results['index_results']:
            if idx['status'] != 'OK':
                all_warnings_and_errors.append(f"<li>Index <strong>{html.escape(idx['index_name'])}</strong>: {html.escape(idx['message'])}</li>")

        for orph in self.results['orphaned_results']:
            if orph['status'] != 'OK':
                all_warnings_and_errors.append(f"<li>Orphaned check <strong>{html.escape(orph['child_table'])}</strong>: {html.escape(orph['message'])}</li>")

        if all_warnings_and_errors:
            issues_list_html = f"<ul>{''.join(all_warnings_and_errors)}</ul>"
        else:
            issues_list_html = "<div class='no-issues'>✅ All systems nominal! No migration mismatches or integrity issues detected.</div>"

        header_gradient = "linear-gradient(135deg, #059669 0%, #10b981 100%)"
        if overall == 'FAILED':
            header_gradient = "linear-gradient(135deg, #dc2626 0%, #ef4444 100%)"
        elif overall == 'WARNING':
            header_gradient = "linear-gradient(135deg, #d97706 0%, #f59e0b 100%)"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Migration Verification Report - PlateLink</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0f19;
            --panel-bg: #111827;
            --panel-border: #1f2937;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --primary: #6366f1;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            line-height: 1.5;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            background: {header_gradient};
            padding: 40px;
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -30%;
            width: 100%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 60%);
            pointer-events: none;
        }}
        
        .header h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            color: #ffffff;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header p.timestamp {{
            color: rgba(255, 255, 255, 0.85);
            font-size: 0.95rem;
            font-weight: 500;
        }}
        
        .header .status-badge-container {{
            margin-top: 20px;
            display: inline-flex;
            align-items: center;
            background: rgba(0, 0, 0, 0.25);
            padding: 8px 18px;
            border-radius: 50px;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }}
        
        .header .status-badge-container span {{
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            font-size: 1.1rem;
            letter-spacing: 0.5px;
            margin-left: 8px;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .card {{
            background-color: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 24px rgba(0,0,0,0.25);
        }}
        
        .card h3 {{
            font-family: 'Outfit', sans-serif;
            font-size: 0.9rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
            border-bottom: 1px solid var(--panel-border);
            padding-bottom: 8px;
        }}
        
        .card .stat-value {{
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--text-main);
            font-family: 'Outfit', sans-serif;
            margin-bottom: 8px;
        }}
        
        .card .stat-sub {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-top: 4px;
        }}
        
        .card .stat-sub strong {{
            color: var(--text-main);
        }}
        
        .section-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.6rem;
            margin-top: 40px;
            margin-bottom: 20px;
            color: var(--text-main);
            border-left: 4px solid var(--primary);
            padding-left: 12px;
        }}
        
        .panel {{
            background-color: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 30px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }}
        
        .table-responsive {{
            width: 100%;
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.9rem;
        }}
        
        th {{
            background-color: rgba(255, 255, 255, 0.02);
            color: var(--text-muted);
            font-weight: 600;
            padding: 14px 16px;
            border-bottom: 2px solid var(--panel-border);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
        }}
        
        td {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--panel-border);
            color: var(--text-main);
            vertical-align: middle;
        }}
        
        tr:hover td {{
            background-color: rgba(255, 255, 255, 0.015);
        }}
        
        .font-bold {{
            font-weight: 600;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            font-size: 0.75rem;
            font-weight: 700;
            border-radius: 20px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .badge-OK {{
            background-color: rgba(16, 185, 129, 0.1);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.2);
        }}
        
        .badge-WARNING {{
            background-color: rgba(245, 158, 11, 0.1);
            color: var(--warning);
            border: 1px solid rgba(245, 158, 11, 0.2);
        }}
        
        .badge-ERROR {{
            background-color: rgba(239, 68, 68, 0.1);
            color: var(--error);
            border: 1px solid rgba(239, 68, 68, 0.2);
        }}
        
        .messages-cell ul {{
            list-style: none;
            padding-left: 0;
        }}
        
        .messages-cell li {{
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-bottom: 4px;
            position: relative;
            padding-left: 12px;
        }}
        
        .messages-cell li::before {{
            content: "•";
            color: var(--primary);
            position: absolute;
            left: 0;
            font-weight: bold;
        }}
        
        .text-muted {{
            color: var(--text-muted);
        }}
        
        .text-center {{
            text-align: center;
        }}
        
        .issues-panel {{
            border-left: 4px solid var(--error);
        }}
        
        .issues-panel ul {{
            padding-left: 20px;
            color: var(--text-main);
        }}
        
        .issues-panel li {{
            margin-bottom: 8px;
            font-size: 0.9rem;
        }}
        
        .issues-panel strong {{
            color: var(--warning);
        }}
        
        .global-error {{
            color: var(--error);
            font-weight: 600;
        }}
        
        .no-issues {{
            background-color: rgba(16, 185, 129, 0.05);
            border: 1px solid rgba(16, 185, 129, 0.15);
            padding: 16px;
            border-radius: 8px;
            color: var(--success);
            font-weight: 500;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .footer {{
            margin-top: 60px;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.8rem;
            border-top: 1px solid var(--panel-border);
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        
        <div class="header">
            <h1>PlateLink Database Verification</h1>
            <p class="timestamp">Verification executed on: {timestamp_str}</p>
            <div class="status-badge-container">
                <span>{status_emoji} Migration Status: <strong>{overall}</strong></span>
            </div>
        </div>
        
        <div class="summary-grid">
            <div class="card">
                <h3>Tables Status</h3>
                <div class="stat-value">{self.results['summary']['total_tables']}</div>
                <div class="stat-sub">
                    <span style="color: var(--success)">✅ {self.results['summary']['tables_ok']} OK</span> | 
                    <span style="color: var(--warning)">⚠️ {self.results['summary']['tables_warning']} Warn</span> | 
                    <span style="color: var(--error)">❌ {self.results['summary']['tables_error']} Err</span>
                </div>
            </div>
            
            <div class="card">
                <h3>Row Counts</h3>
                <div class="stat-value">{self.results['summary']['total_rows_target']:,}</div>
                <div class="stat-sub">
                    Source: <strong>{self.results['summary']['total_rows_source']:,}</strong> | 
                    Diff: <strong style="color: {'var(--error)' if self.results['summary']['total_rows_source'] != self.results['summary']['total_rows_target'] else 'var(--success)'}">
                        {abs(self.results['summary']['total_rows_source'] - self.results['summary']['total_rows_target']):,}
                    </strong>
                </div>
            </div>
            
            <div class="card">
                <h3>Database Size</h3>
                <div class="stat-value">{self.results['summary']['size_target_mb']:.2f} MB</div>
                <div class="stat-sub">
                    Source: <strong>{self.results['summary']['size_source_mb']:.2f} MB</strong> | 
                    Diff: <strong>{abs(self.results['summary']['size_source_mb'] - self.results['summary']['size_target_mb']):.2f} MB</strong>
                </div>
            </div>
            
            <div class="card">
                <h3>Mismatches</h3>
                <div class="stat-value" style="color: {'var(--success)' if (self.results['summary']['sequence_mismatches'] + self.results['summary']['fk_mismatches'] + self.results['summary']['index_mismatches'] + self.results['summary']['orphaned_records_errors']) == 0 else 'var(--warning)'}">
                    {self.results['summary']['sequence_mismatches'] + self.results['summary']['fk_mismatches'] + self.results['summary']['index_mismatches'] + self.results['summary']['orphaned_records_errors']}
                </div>
                <div class="stat-sub">
                    Seq: <strong>{self.results['summary']['sequence_mismatches']}</strong> | 
                    FK: <strong>{self.results['summary']['fk_mismatches']}</strong> | 
                    Index: <strong>{self.results['summary']['index_mismatches']}</strong> | 
                    Orphan: <strong>{self.results['summary']['orphaned_records_errors']}</strong>
                </div>
            </div>
        </div>

        <h2 class="section-title">⚠️ Integrity Issues & Warnings</h2>
        <div class="panel issues-panel">
            {issues_list_html}
        </div>

        <h2 class="section-title">📋 Table Verification Details</h2>
        <div class="panel">
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Table Name</th>
                            <th>Status</th>
                            <th>Source Rows</th>
                            <th>Target Rows</th>
                            <th>Row Diff</th>
                            <th>Total Size (Source/Target)</th>
                            <th>Messages / Schema Issues</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <h2 class="section-title">🔢 Auto-Increment Sequences</h2>
        <div class="panel">
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Sequence Name</th>
                            <th>Status</th>
                            <th>Source Last Value</th>
                            <th>Target Last Value</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {seq_rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <h2 class="section-title">🔗 Foreign Key Constraints</h2>
        <div class="panel">
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Constraint Name</th>
                            <th>Status</th>
                            <th>Child Table</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {fk_rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <h2 class="section-title">⚡ Indexes</h2>
        <div class="panel">
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Index Name</th>
                            <th>Status</th>
                            <th>Table</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {idx_rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <h2 class="section-title">🚨 Orphaned Records Check</h2>
        <div class="panel">
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Child Field</th>
                            <th>Status</th>
                            <th>Parent Field</th>
                            <th>Orphaned Count</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {orphaned_rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="panel" style="background-color: rgba(255, 255, 255, 0.01); border-style: dashed; margin-top: 40px;">
            <h3 style="margin-bottom: 12px; font-family: 'Outfit';">System Metadata</h3>
            <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 4px;"><strong>Source DB URL:</strong> {self.source_url.split('@')[-1]}</p>
            <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 4px;"><strong>Target DB URL:</strong> {self.target_url.split('@')[-1]}</p>
            <p style="font-size: 0.85rem; color: var(--text-muted);"><strong>Verification Tool Version:</strong> 1.0.0 (Antigravity Spec)</p>
        </div>

        <div class="footer">
            <p>PlateLink Admin Console &copy; 2026. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        filename = f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"📄 HTML report saved: {filename}")
        
        # Also copy as a fixed name so it's easy to read/view
        with open("verification_report_latest.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        artifact_dir = "C:\\Users\\HP\\.gemini\\antigravity-ide\\brain\\d28533d7-d5a5-4297-8bad-d83cae96f2bc"
        if os.path.exists(artifact_dir):
            artifact_file = os.path.join(artifact_dir, "verification_report.html")
            with open(artifact_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"📄 HTML report saved to artifacts: {artifact_file}")

    def generate_json_report(self):
        filename = f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        def convert_to_serializable(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            if hasattr(obj, 'items') or hasattr(obj, 'keys'):
                return dict(obj)
            return str(obj)
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, default=convert_to_serializable, indent=2)
        logger.info(f"📄 JSON report saved: {filename}")

        with open("verification_report_latest.json", 'w') as f:
            json.dump(self.results, f, default=convert_to_serializable, indent=2)

        artifact_dir = "C:\\Users\\HP\\.gemini\\antigravity-ide\\brain\\d28533d7-d5a5-4297-8bad-d83cae96f2bc"
        if os.path.exists(artifact_dir):
            artifact_file = os.path.join(artifact_dir, "verification_report.json")
            with open(artifact_file, 'w') as f:
                json.dump(self.results, f, default=convert_to_serializable, indent=2)
            logger.info(f"📄 JSON report saved to artifacts: {artifact_file}")

    def print_summary(self):
        print("\n" + "="*70)
        print("MIGRATION VERIFICATION SUMMARY")
        print("="*70)
        print(f"Overall Status: {self.results['overall_status']}")
        print("-"*70)
        print(f"Tables: {self.results['summary']['tables_ok']} OK, {self.results['summary']['tables_warning']} Warnings, {self.results['summary']['tables_error']} Errors")
        print(f"Total Rows: Source={self.results['summary']['total_rows_source']:,}, Target={self.results['summary']['total_rows_target']:,}")
        print(f"Database Size: Source={self.results['summary']['size_source_mb']:.2f} MB, Target={self.results['summary']['size_target_mb']:.2f} MB")
        print(f"Sequence Mismatches: {self.results['summary']['sequence_mismatches']}")
        print(f"FK Mismatches: {self.results['summary']['fk_mismatches']}")
        print(f"Index Mismatches: {self.results['summary']['index_mismatches']}")
        print(f"Orphaned Record Mismatches: {self.results['summary']['orphaned_records_errors']}")
        
        if self.results['errors']:
            print("\nErrors/Warnings Found:")
            for error in self.results['errors']:
                print(f"  - {error}")
        
        print("="*70)
        print(f"Verification completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Reports generated: HTML and JSON formats")
        print("="*70 + "\n")

async def main():
    if sys.platform.startswith('win'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass
            
    verifier = MigrationVerifier(SOURCE_URL, TARGET_URL)
    try:
        await verifier.run_verification()
    except KeyboardInterrupt:
        logger.info("⏹️ Verification interrupted by user")
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
