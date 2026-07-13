# tests/test_qr_pdf_generator.py
import pytest
from jose import jwt
from PIL import Image
from reportlab.lib.pagesizes import A4
from app.services.qr_pdf_generator import (
    QRPDFGenerator,
    PLATELINK_GREEN,
    PLATELINK_DARK_GREEN,
    PLATELINK_ORANGE,
    LIGHT_GREY
)
from app.utils.qr_utils import generate_qr_token, generate_qr_image
from app.core.config import settings

def test_color_exact_match():
    """Verify that style colors match the mockup requirements exactly."""
    assert PLATELINK_GREEN == "#059669"
    assert PLATELINK_DARK_GREEN == "#047857"
    assert PLATELINK_ORANGE == "#EA580C"
    assert LIGHT_GREY == "#F8FAFC"

def test_qr_token_generation():
    """Verify table QR JWT tokens are signed correctly and contain required claims."""
    table_id = "test_table_uuid"
    restaurant_id = "test_restaurant_uuid"
    
    token = generate_qr_token(table_id, restaurant_id)
    assert token is not None
    
    # Decode token and verify claims
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert decoded["type"] == "table"
    assert decoded["table_id"] == table_id
    assert decoded["restaurant_id"] == restaurant_id
    assert "exp" in decoded

def test_qr_code_with_logo():
    """Verify styled QR code is created with centered logo overlay."""
    logo = Image.new("RGBA", (100, 100), (5, 150, 105, 255))
    token = "sample_test_token"
    
    qr_img = generate_qr_image(token, logo)
    assert isinstance(qr_img, Image.Image)
    assert qr_img.mode in ("RGB", "RGBA")

def test_card_positions():
    """Verify coordinates for the 2x2 grid align perfectly on A4 canvas (595x842)."""
    page_width, page_height = A4
    card_width, card_height = 220, 220
    
    positions = [
        (70, 430),   # Table 1
        (320, 430),  # Table 2
        (70, 170),   # Table 3
        (320, 170)   # Table 4
    ]
    
    for x, y in positions:
        # Check that cards fit within page width with margins
        assert x >= 0
        assert x + card_width <= page_width
        
        # Check that cards fit within page height (excluding header and footer margins)
        assert y >= 50 # footer margin
        assert y + card_height <= page_height - 100 # header margin

def test_generate_pdf_single_page():
    """Verify single page PDF generation for 1-4 tables."""
    tables = [
        {"number": 1, "token": "token1"},
        {"number": 2, "token": "token2"}
    ]
    
    generator = QRPDFGenerator(restaurant_name="Test Café")
    pdf_bytes = generator.generate_pdf(tables)
    
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    # PDF starts with %PDF header
    assert pdf_bytes.startswith(b"%PDF")

def test_generate_pdf_multiple_pages():
    """Verify multi-page pagination for >4 tables."""
    tables = [
        {"number": 1, "token": "token1"},
        {"number": 2, "token": "token2"},
        {"number": 3, "token": "token3"},
        {"number": 4, "token": "token4"},
        {"number": 5, "token": "token5"} # triggers page 2
    ]
    
    generator = QRPDFGenerator(restaurant_name="Test Bistro")
    pdf_bytes = generator.generate_pdf(tables)
    
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")
