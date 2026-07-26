"""LinkService for handling link generation, staff access links, domain verification, and analytics."""
import logging
from datetime import date, datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.link import Link
from app.models.qr import QRCode
from app.models.analytics import LinkAnalytics
from app.models.restaurant import Restaurant
from app.schemas.link import LinkCreate, LinkUpdate, StaffAccessLinks, LinkType
from app.schemas.analytics import AnalyticsSummary, AnalyticsSource
from app.services.domain_service import domain_service
from app.services.qr_service import qr_service

logger = logging.getLogger(__name__)

class LinkService:
    async def get_links(self, db: AsyncSession, restaurant_id: UUID) -> List[Link]:
        """List all links for a restaurant."""
        stmt = select(Link).where(Link.restaurant_id == restaurant_id).order_by(Link.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_link(self, db: AsyncSession, link_id: UUID, restaurant_id: UUID) -> Optional[Link]:
        """Get link by ID."""
        stmt = select(Link).where(Link.id == link_id, Link.restaurant_id == restaurant_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_link(self, db: AsyncSession, restaurant_id: UUID, data: LinkCreate) -> Link:
        """Create a new link."""
        domain = data.custom_domain
        url = f"https://{domain}/{data.slug}" if domain else f"https://{data.slug}.platelink.africa"

        link_obj = Link(
            restaurant_id=restaurant_id,
            branch_id=data.branch_id,
            type=data.type.value if isinstance(data.type, LinkType) else data.type,
            slug=data.slug,
            url=url,
            custom_domain=domain,
            is_active=data.is_active
        )
        db.add(link_obj)
        await db.commit()
        await db.refresh(link_obj)
        return link_obj

    async def update_link(self, db: AsyncSession, link_id: UUID, restaurant_id: UUID, data: LinkUpdate) -> Link:
        """Update an existing link."""
        link_obj = await self.get_link(db, link_id, restaurant_id)
        if not link_obj:
            raise ValueError("Link not found")

        if data.slug is not None:
            link_obj.slug = data.slug
            base_domain = link_obj.custom_domain if link_obj.custom_domain else f"{link_obj.slug}.platelink.africa"
            link_obj.url = f"https://{base_domain}"

        if data.custom_domain is not None:
            link_obj.custom_domain = data.custom_domain
            link_obj.url = f"https://{data.custom_domain}/{link_obj.slug}"

        if data.domain_verified is not None:
            link_obj.domain_verified = data.domain_verified

        if data.is_active is not None:
            link_obj.is_active = data.is_active

        link_obj.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(link_obj)
        return link_obj

    async def delete_link(self, db: AsyncSession, link_id: UUID, restaurant_id: UUID) -> bool:
        """Delete link by ID."""
        link_obj = await self.get_link(db, link_id, restaurant_id)
        if not link_obj:
            return False
        await db.delete(link_obj)
        await db.commit()
        return True

    async def get_staff_access_links(self, db: AsyncSession, restaurant_id: UUID) -> StaffAccessLinks:
        """Get staff access URLs for waiter, kitchen, and cashier."""
        restaurant = await db.get(Restaurant, restaurant_id)
        sub = restaurant.subdomain if restaurant else "app"

        return StaffAccessLinks(
            waiter=f"https://{sub}.platelink.africa/waiter",
            kitchen=f"https://{sub}.platelink.africa/kitchen",
            cashier=f"https://{sub}.platelink.africa/cashier"
        )

    async def get_primary_link(self, db: AsyncSession, restaurant_id: UUID) -> Optional[Link]:
        """Get primary menu link."""
        stmt = select(Link).where(Link.restaurant_id == restaurant_id, Link.type == "primary")
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_custom_domain(self, db: AsyncSession, restaurant_id: UUID) -> Optional[Dict[str, Any]]:
        """Get custom domain configuration."""
        stmt = select(Link).where(Link.restaurant_id == restaurant_id, Link.custom_domain.isnot(None))
        result = await db.execute(stmt)
        link_obj = result.scalars().first()
        if not link_obj or not link_obj.custom_domain:
            return None

        return {
            "domain": link_obj.custom_domain,
            "verified": link_obj.domain_verified,
            "dns_record": domain_service.generate_dns_record(link_obj.custom_domain),
            "status": "verified" if link_obj.domain_verified else "pending"
        }

    async def verify_custom_domain(self, db: AsyncSession, restaurant_id: UUID, domain: str) -> Dict[str, Any]:
        """Verify custom domain CNAME record."""
        is_valid = await domain_service.verify_domain(restaurant_id, domain)
        
        stmt = select(Link).where(Link.restaurant_id == restaurant_id, Link.custom_domain == domain)
        result = await db.execute(stmt)
        link_obj = result.scalar_one_or_none()

        if link_obj:
            link_obj.domain_verified = is_valid
            await db.commit()

        return {
            "domain": domain,
            "verified": is_valid,
            "dns_record": domain_service.generate_dns_record(domain),
            "status": "verified" if is_valid else "pending"
        }

    async def update_custom_domain(self, db: AsyncSession, restaurant_id: UUID, domain: str) -> Dict[str, Any]:
        """Update or register custom domain."""
        primary = await self.get_primary_link(db, restaurant_id)
        if primary:
            primary.custom_domain = domain
            primary.domain_verified = False
            await db.commit()

        return await self.verify_custom_domain(db, restaurant_id, domain)

    async def generate_qr_code(
        self,
        db: AsyncSession,
        table_number: str,
        restaurant_id: UUID,
        branch_id: Optional[UUID] = None
    ) -> QRCode:
        """Helper delegation to QRService."""
        return await qr_service.generate_table_qr(db, table_number, restaurant_id, branch_id)

    async def download_all_qr_codes(self, db: AsyncSession, restaurant_id: UUID) -> bytes:
        """Helper delegation to QRService."""
        return await qr_service.download_all_qr_codes(db, restaurant_id)

    async def get_link_analytics(self, db: AsyncSession, link_id: UUID, start_date: date, end_date: date) -> AnalyticsSummary:
        """Aggregate performance analytics for a link."""
        stmt = select(LinkAnalytics).where(
            LinkAnalytics.link_id == link_id,
            LinkAnalytics.date >= start_date,
            LinkAnalytics.date <= end_date
        )
        result = await db.execute(stmt)
        records = result.scalars().all()

        total_views = sum(r.views for r in records)
        total_clicks = sum(r.clicks for r in records)
        total_conversions = sum(r.conversions for r in records)

        ctr = round((total_clicks / total_views * 100) if total_views > 0 else 0.0, 2)
        conversion_rate = round((total_conversions / total_clicks * 100) if total_clicks > 0 else 0.0, 2)

        source_map: Dict[str, int] = {}
        daily_list: List[Dict[str, Any]] = []

        for r in records:
            source_map[r.source] = source_map.get(r.source, 0) + r.views
            daily_list.append({
                "date": str(r.date),
                "views": r.views,
                "clicks": r.clicks,
                "conversions": r.conversions,
                "source": r.source
            })

        return AnalyticsSummary(
            total_views=total_views,
            total_clicks=total_clicks,
            total_conversions=total_conversions,
            ctr=ctr,
            conversion_rate=conversion_rate,
            source_breakdown=source_map,
            daily=daily_list
        )

link_service = LinkService()
