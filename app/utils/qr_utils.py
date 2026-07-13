# app/utils/qr_utils.py
import os
from datetime import datetime, timedelta
from jose import jwt
from PIL import Image, ImageDraw, ImageFont
import qrcode
from app.core.config import settings

def generate_qr_token(table_id: str, restaurant_id: str) -> str:
    """
    Generate a JWT token for the table QR code with a 1-year expiry.
    """
    payload = {
        "type": "table",
        "restaurant_id": str(restaurant_id),
        "table_id": str(table_id),
        "exp": datetime.utcnow() + timedelta(days=3650)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def generate_qr_image(token: str, logo: Image.Image = None) -> Image.Image:
    """
    Generate a styled QR code image with an optional centered logo.
    Uses High Error Correction (ERROR_CORRECT_H) to allow logo overlay.
    """
    qr = qrcode.QRCode(
        version=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2
    )
    qr.add_data(f"https://order.platelink.com/t/{token}")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    if logo:
        # Resize logo to 1/5 of the QR code size
        logo_size = img.width // 5
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        # Create mask for transparency if available
        mask = logo if logo.mode == 'RGBA' else None
        
        # Paste logo exactly in the center of the QR code
        position = ((img.width - logo_size) // 2, (img.height - logo_size) // 2)
        img.paste(logo, position, mask)
        
    return img
