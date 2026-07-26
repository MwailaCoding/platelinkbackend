"""Service layer for restaurant brand customization and theme management."""
from typing import List, Optional
from uuid import UUID
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.brand import BrandSettings, Theme
from app.models.restaurant import Restaurant
from app.schemas.brand import BrandSettingsUpdate, ThemeCreate
from app.services.cloudinary import CloudinaryService


class BrandService:
    @staticmethod
    async def get_brand_settings(db: AsyncSession, restaurant_id: UUID) -> BrandSettings:
        """
        Get existing brand settings for a restaurant or auto-create default settings.
        """
        stmt = select(BrandSettings).where(BrandSettings.restaurant_id == restaurant_id)
        result = await db.execute(stmt)
        settings = result.scalar_one_or_none()

        if not settings:
            settings = BrandSettings(
                restaurant_id=restaurant_id,
                primary_color="#F97316",
                secondary_color="#0A1628",
                background_color="#F8FAFC",
                text_color="#0A1628",
                accent_color="#10B981",
                heading_font="Inter",
                body_font="Inter",
                card_style="rounded",
                button_style="filled",
                category_display="tabs",
                cart_behavior="bottom_bar",
                is_active=True
            )
            db.add(settings)
            await db.commit()
            await db.refresh(settings)

            # Update restaurant foreign key
            restaurant = await db.get(Restaurant, restaurant_id)
            if restaurant:
                restaurant.brand_settings_id = settings.id
                await db.commit()

        return settings

    @staticmethod
    async def update_brand_settings(
        db: AsyncSession, restaurant_id: UUID, data: BrandSettingsUpdate
    ) -> BrandSettings:
        """
        Update brand settings for a restaurant.
        """
        settings = await BrandService.get_brand_settings(db, restaurant_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                # Handle Enum conversion if necessary
                if hasattr(value, "value"):
                    value = value.value
                setattr(settings, field, value)

        await db.commit()
        await db.refresh(settings)
        return settings

    @staticmethod
    async def upload_logo(db: AsyncSession, restaurant_id: UUID, file: UploadFile) -> str:
        """
        Upload logo image to CDN and update brand settings logo_url.
        """
        file_content = await file.read()
        url = await CloudinaryService.upload_image(file_content, folder=f"platelink/brand/{restaurant_id}/logo")
        
        settings = await BrandService.get_brand_settings(db, restaurant_id)
        settings.logo_url = url
        await db.commit()
        await db.refresh(settings)

        # Also update restaurant logo_url for backwards compatibility
        restaurant = await db.get(Restaurant, restaurant_id)
        if restaurant:
            restaurant.logo_url = url
            await db.commit()

        return url

    @staticmethod
    async def upload_hero(db: AsyncSession, restaurant_id: UUID, file: UploadFile) -> str:
        """
        Upload hero background image to CDN and update brand settings hero_image_url.
        """
        file_content = await file.read()
        url = await CloudinaryService.upload_image(file_content, folder=f"platelink/brand/{restaurant_id}/hero")

        settings = await BrandService.get_brand_settings(db, restaurant_id)
        settings.hero_image_url = url
        await db.commit()
        await db.refresh(settings)

        return url

    @staticmethod
    async def upload_favicon(db: AsyncSession, restaurant_id: UUID, file: UploadFile) -> str:
        """
        Upload favicon image to CDN and update brand settings favicon_url.
        """
        file_content = await file.read()
        url = await CloudinaryService.upload_image(file_content, folder=f"platelink/brand/{restaurant_id}/favicon")

        settings = await BrandService.get_brand_settings(db, restaurant_id)
        settings.favicon_url = url
        await db.commit()
        await db.refresh(settings)

        return url

    @staticmethod
    async def apply_theme(db: AsyncSession, restaurant_id: UUID, theme_id: UUID) -> BrandSettings:
        """
        Apply a theme template to restaurant's brand settings.
        """
        theme = await BrandService.get_theme(db, theme_id)
        if not theme:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme not found")

        template = theme.template_data or {}

        settings = await BrandService.get_brand_settings(db, restaurant_id)

        # Map template properties to BrandSettings attributes
        field_mapping = [
            "primary_color", "secondary_color", "background_color", "text_color", "accent_color",
            "heading_font", "body_font", "card_style", "button_style",
            "category_display", "cart_behavior"
        ]

        for key in field_mapping:
            if key in template and template[key] is not None:
                setattr(settings, key, template[key])

        await db.commit()
        await db.refresh(settings)

        # Record selected_theme_id on Restaurant
        restaurant = await db.get(Restaurant, restaurant_id)
        if restaurant:
            restaurant.selected_theme_id = theme.id
            await db.commit()

        return settings

    @staticmethod
    async def generate_brand_css(db: AsyncSession, restaurant_id: UUID) -> str:
        """
        Generate dynamic CSS root variables and custom styles from brand settings.
        """
        settings = await BrandService.get_brand_settings(db, restaurant_id)

        heading_font = settings.heading_font or "Inter"
        body_font = settings.body_font or "Inter"

        css = f"""/* PlateLink Dynamic Brand Theme CSS */
:root {{
  --primary-color: {settings.primary_color};
  --secondary-color: {settings.secondary_color};
  --background-color: {settings.background_color};
  --text-color: {settings.text_color};
  --accent-color: {settings.accent_color};
  --heading-font: '{heading_font}', sans-serif;
  --body-font: '{body_font}', sans-serif;
  --card-style: {settings.card_style};
  --button-style: {settings.button_style};
  --category-display: {settings.category_display};
  --cart-behavior: {settings.cart_behavior};
}}

body {{
  background-color: var(--background-color);
  color: var(--text-color);
  font-family: var(--body-font);
}}

h1, h2, h3, h4, h5, h6 {{
  font-family: var(--heading-font);
}}
"""
        if settings.custom_css:
            css += f"\n/* Custom Restaurant CSS */\n{settings.custom_css}\n"

        return css

    @staticmethod
    async def get_theme(db: AsyncSession, theme_id: UUID) -> Theme:
        """
        Get theme by ID.
        """
        theme = await db.get(Theme, theme_id)
        if not theme:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme not found")
        return theme

    @staticmethod
    async def list_themes(db: AsyncSession) -> List[Theme]:
        """
        List all available themes.
        """
        stmt = select(Theme).order_by(Theme.is_premium.asc(), Theme.name.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_theme(db: AsyncSession, data: ThemeCreate) -> Theme:
        """
        Create a new theme template.
        """
        theme = Theme(
            name=data.name,
            description=data.description,
            preview_image=data.preview_image,
            template_data=data.template_data,
            is_premium=data.is_premium,
            price=data.price
        )
        db.add(theme)
        await db.commit()
        await db.refresh(theme)
        return theme

    @staticmethod
    async def delete_theme(db: AsyncSession, theme_id: UUID) -> bool:
        """
        Delete a theme by ID.
        """
        theme = await db.get(Theme, theme_id)
        if not theme:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Theme not found")
        await db.delete(theme)
        await db.commit()
        return True


brand_service = BrandService()
