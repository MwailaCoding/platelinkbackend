"""Migration 006: Brand customization tables (brand_settings, themes) and restaurant brand attributes.

Revision ID: 006
Revises: 005
Create Date: 2026-07-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import json

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create brand_settings table
    op.create_table(
        'brand_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('primary_color', sa.String(length=7), server_default='#F97316', nullable=False),
        sa.Column('secondary_color', sa.String(length=7), server_default='#0A1628', nullable=False),
        sa.Column('background_color', sa.String(length=7), server_default='#F8FAFC', nullable=False),
        sa.Column('text_color', sa.String(length=7), server_default='#0A1628', nullable=False),
        sa.Column('accent_color', sa.String(length=7), server_default='#10B981', nullable=False),
        sa.Column('logo_url', sa.String(length=255), nullable=True),
        sa.Column('hero_image_url', sa.String(length=255), nullable=True),
        sa.Column('favicon_url', sa.String(length=255), nullable=True),
        sa.Column('heading_font', sa.String(length=100), server_default='Inter', nullable=False),
        sa.Column('body_font', sa.String(length=100), server_default='Inter', nullable=False),
        sa.Column('welcome_message', sa.Text(), nullable=True),
        sa.Column('tagline', sa.String(length=255), nullable=True),
        sa.Column('footer_text', sa.Text(), nullable=True),
        sa.Column('instagram_url', sa.String(length=255), nullable=True),
        sa.Column('facebook_url', sa.String(length=255), nullable=True),
        sa.Column('twitter_url', sa.String(length=255), nullable=True),
        sa.Column('youtube_url', sa.String(length=255), nullable=True),
        sa.Column('card_style', sa.String(length=20), server_default='rounded', nullable=False),
        sa.Column('button_style', sa.String(length=20), server_default='filled', nullable=False),
        sa.Column('category_display', sa.String(length=20), server_default='tabs', nullable=False),
        sa.Column('cart_behavior', sa.String(length=20), server_default='bottom_bar', nullable=False),
        sa.Column('custom_css', sa.Text(), nullable=True),
        sa.Column('custom_js', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('restaurant_id')
    )
    op.create_index('ix_brand_settings_restaurant_id', 'brand_settings', ['restaurant_id'])

    # 2. Create themes table
    op.create_table(
        'themes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('preview_image', sa.String(length=255), nullable=True),
        sa.Column('template_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_premium', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), server_default='0.00', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_themes_is_premium', 'themes', ['is_premium'])

    # 3. Add brand columns to restaurants table
    op.add_column('restaurants', sa.Column('brand_settings_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('restaurants', sa.Column('selected_theme_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_restaurants_brand_settings_id', 'restaurants', 'brand_settings', ['brand_settings_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_restaurants_selected_theme_id', 'restaurants', 'themes', ['selected_theme_id'], ['id'], ondelete='SET NULL')

    # 4. Seed default themes
    themes_table = sa.table(
        'themes',
        sa.column('name', sa.String),
        sa.column('description', sa.Text),
        sa.column('preview_image', sa.String),
        sa.column('template_data', postgresql.JSONB),
        sa.column('is_premium', sa.Boolean),
        sa.column('price', sa.Numeric)
    )

    default_themes = [
        {
            "name": "Minimal Light",
            "description": "Clean, modern, and accessible design suited for contemporary cafes and diners.",
            "preview_image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600",
            "template_data": {
                "primary_color": "#F97316",
                "secondary_color": "#0A1628",
                "background_color": "#F8FAFC",
                "text_color": "#0A1628",
                "accent_color": "#10B981",
                "heading_font": "Inter",
                "body_font": "Inter",
                "card_style": "rounded",
                "button_style": "filled",
                "category_display": "tabs",
                "cart_behavior": "bottom_bar"
            },
            "is_premium": False,
            "price": 0.00
        },
        {
            "name": "Dark Luxury",
            "description": "Sophisticated dark theme tailored for high-end dining and cocktail lounges.",
            "preview_image": "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?w=600",
            "template_data": {
                "primary_color": "#E11D48",
                "secondary_color": "#18181B",
                "background_color": "#09090B",
                "text_color": "#FAFAFA",
                "accent_color": "#F59E0B",
                "heading_font": "Playfair Display",
                "body_font": "Lora",
                "card_style": "sharp",
                "button_style": "outline",
                "category_display": "sidebar",
                "cart_behavior": "side_drawer"
            },
            "is_premium": True,
            "price": 19.99
        },
        {
            "name": "Vibrant Sunset",
            "description": "Warm and energetic aesthetic perfect for street food, food trucks, and fast casual.",
            "preview_image": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600",
            "template_data": {
                "primary_color": "#FF6B00",
                "secondary_color": "#1E293B",
                "background_color": "#FFFBEB",
                "text_color": "#1E293B",
                "accent_color": "#06B6D4",
                "heading_font": "Outfit",
                "body_font": "Plus Jakarta Sans",
                "card_style": "floating",
                "button_style": "filled",
                "category_display": "dropdown",
                "cart_behavior": "bottom_bar"
            },
            "is_premium": False,
            "price": 0.00
        },
        {
            "name": "Emerald Bistro",
            "description": "Organic and fresh look ideal for farm-to-table restaurants and vegan spots.",
            "preview_image": "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=600",
            "template_data": {
                "primary_color": "#059669",
                "secondary_color": "#064E3B",
                "background_color": "#F0FDF4",
                "text_color": "#064E3B",
                "accent_color": "#D97706",
                "heading_font": "Merriweather",
                "body_font": "Open Sans",
                "card_style": "rounded",
                "button_style": "filled",
                "category_display": "tabs",
                "cart_behavior": "side_drawer"
            },
            "is_premium": True,
            "price": 14.99
        }
    ]

    op.bulk_insert(themes_table, default_themes)


def downgrade() -> None:
    # 1. Drop foreign keys and columns on restaurants
    op.drop_constraint('fk_restaurants_selected_theme_id', 'restaurants', type_='foreignkey')
    op.drop_constraint('fk_restaurants_brand_settings_id', 'restaurants', type_='foreignkey')
    op.drop_column('restaurants', 'selected_theme_id')
    op.drop_column('restaurants', 'brand_settings_id')

    # 2. Drop themes table
    op.drop_index('ix_themes_is_premium', table_name='themes')
    op.drop_table('themes')

    # 3. Drop brand_settings table
    op.drop_index('ix_brand_settings_restaurant_id', table_name='brand_settings')
    op.drop_table('brand_settings')
