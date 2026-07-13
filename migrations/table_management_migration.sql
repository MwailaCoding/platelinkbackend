-- migrations/table_management_migration.sql

-- Add columns to tables
ALTER TABLE tables ADD COLUMN IF NOT EXISTS occupied_since TIMESTAMPTZ;
ALTER TABLE tables ADD COLUMN IF NOT EXISTS last_status_change TIMESTAMPTZ;
ALTER TABLE tables ADD COLUMN IF NOT EXISTS status_history JSONB DEFAULT '[]'::jsonb;

-- Add columns to customer_sessions
ALTER TABLE customer_sessions ADD COLUMN IF NOT EXISTS order_number VARCHAR(50);
ALTER TABLE customer_sessions ADD COLUMN IF NOT EXISTS device_fingerprint TEXT;

-- Create table transfers log
CREATE TABLE IF NOT EXISTS table_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE SET NULL,
    original_table_id UUID REFERENCES tables(id) ON DELETE SET NULL,
    new_table_id UUID REFERENCES tables(id) ON DELETE SET NULL,
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    transferred_by UUID REFERENCES staff(id) ON DELETE SET NULL,
    transferred_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create order item transfers log
CREATE TABLE IF NOT EXISTS item_transfers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    restaurant_id UUID REFERENCES restaurants(id) ON DELETE SET NULL,
    order_item_id UUID REFERENCES order_items(id) ON DELETE SET NULL,
    from_session_id UUID REFERENCES customer_sessions(id) ON DELETE SET NULL,
    to_session_id UUID REFERENCES customer_sessions(id) ON DELETE SET NULL,
    transferred_by UUID REFERENCES staff(id) ON DELETE SET NULL,
    transferred_at TIMESTAMPTZ DEFAULT NOW()
);
