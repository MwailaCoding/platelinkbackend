# app/services/qr_pdf_generator.py
import os
import io
import math
from datetime import datetime
from typing import List, Dict, Any
from PIL import Image, ImageDraw, ImageFont
import qrcode

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Constants
PLATELINK_GREEN = "#059669"
PLATELINK_DARK_GREEN = "#047857"
PLATELINK_ORANGE = "#EA580C"
WHITE = "#FFFFFF"
LIGHT_GREY = "#F8FAFC"
SHADOW_COLOR = "rgba(0,0,0,0.08)"

# Try to register Poppins fonts if available in current directory
def _register_fonts():
    fonts = [
        ("Poppins-Regular", "Poppins-Regular.ttf"),
        ("Poppins-Bold", "Poppins-Bold.ttf"),
        ("Poppins-SemiBold", "Poppins-SemiBold.ttf")
    ]
    for font_name, filename in fonts:
        if font_name not in pdfmetrics.getRegisteredFontNames():
            try:
                if os.path.exists(filename):
                    pdfmetrics.registerFont(TTFont(font_name, filename))
            except Exception:
                pass

_register_fonts()

class TableCard(Flowable):
    """Custom ReportLab Flowable representing a styled table QR card."""
    def __init__(self, generator: "QRPDFGenerator", qr_img: Image.Image, table_number: int):
        Flowable.__init__(self)
        self.generator = generator
        self.qr_img = qr_img
        self.table_number = table_number
        self.width = 220
        self.height = 220

    def draw(self):
        canvas = self.canv
        
        # 1. Subtle drop shadow
        canvas.setFillColor(Color(0, 0, 0, alpha=0.08))
        canvas.roundRect(4, -4, 220, 220, 12, fill=1, stroke=0)
        
        # 2. Rounded card background
        canvas.setFillColor(HexColor(LIGHT_GREY))
        canvas.setStrokeColor(HexColor(PLATELINK_GREEN))
        canvas.setLineWidth(1.5)
        canvas.roundRect(0, 0, 220, 220, 12, fill=1, stroke=1)
        
        # 3. Center QR Code image
        qr_buf = io.BytesIO()
        self.qr_img.save(qr_buf, format="PNG")
        qr_buf.seek(0)
        reader = ImageReader(qr_buf)
        canvas.drawImage(reader, 35, 50, width=150, height=150)
        
        # 4. Table label text
        font_name = self.generator.get_font_name("bold")
        canvas.setFont(font_name, 16)
        canvas.setFillColor(HexColor(PLATELINK_GREEN))
        canvas.drawCentredString(110, 20, f"TABLE {self.table_number}")

class QRPDFGenerator:
    def __init__(self, restaurant_name: str, restaurant_logo: bytes = None):
        self.restaurant_name = restaurant_name
        
        # Load or generate logo image
        if restaurant_logo:
            try:
                self.logo = Image.open(io.BytesIO(restaurant_logo))
            except Exception:
                self.logo = self._get_default_logo()
        else:
            if os.path.exists("platelink_icon.png"):
                try:
                    self.logo = Image.open("platelink_icon.png")
                except Exception:
                    self.logo = self._get_default_logo()
            else:
                self.logo = self._get_default_logo()

    def _get_default_logo(self) -> Image.Image:
        """Generates a default emerald green circle logo with white letter P."""
        img = Image.new("RGBA", (200, 200), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        # Draw emerald circle
        draw.ellipse([0, 0, 200, 200], fill=(5, 150, 105, 255))
        
        # Center "P"
        text = "P"
        try:
            font = ImageFont.truetype("arial.ttf", 120)
        except Exception:
            font = ImageFont.load_default()
            
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            x = (200 - w) / 2 - bbox[0]
            y = (200 - h) / 2 - bbox[1]
            draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        except AttributeError:
            # Pillow version fallback
            draw.text((65, 30), text, fill=(255, 255, 255, 255), font=font)
            
        return img

    def get_font_name(self, style: str) -> str:
        """Returns Poppins if registered, otherwise Helvetica fallback."""
        if style == "bold":
            return "Poppins-Bold" if "Poppins-Bold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
        elif style == "semibold":
            return "Poppins-SemiBold" if "Poppins-SemiBold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
        else:
            return "Poppins-Regular" if "Poppins-Regular" in pdfmetrics.getRegisteredFontNames() else "Helvetica"

    def generate_qr_code(self, table_number: int, token: str) -> Image.Image:
        """Generate QR code with URL and embed centered logo."""
        from app.utils.qr_utils import generate_qr_image
        return generate_qr_image(token, self.logo)

    def create_table_card(self, qr_img: Image.Image, table_number: int) -> Flowable:
        """Returns a custom Flowable representing the card."""
        return TableCard(self, qr_img, table_number)

    def create_header(self) -> Flowable:
        """Returns a Flowable wrapper for the page header."""
        class Header(Flowable):
            def __init__(self, generator: "QRPDFGenerator"):
                Flowable.__init__(self)
                self.generator = generator
            def draw(self):
                # Draw directly on the canvas
                canvas = self.canv
                
                # Restaurant Name (28px Bold)
                font_bold = self.generator.get_font_name("bold")
                canvas.setFont(font_bold, 28)
                canvas.setFillColor(HexColor(PLATELINK_GREEN))
                canvas.drawCentredString(297.5, 770, self.generator.restaurant_name)
                
                # Date (16px Regular)
                font_regular = self.generator.get_font_name("regular")
                canvas.setFont(font_regular, 14)
                canvas.setFillColor(HexColor("#64748B"))
                today_str = datetime.now().strftime("%B %d, %Y")
                canvas.drawCentredString(297.5, 745, today_str)
                
                # Instructions line
                font_semibold = self.generator.get_font_name("semibold")
                canvas.setFont(font_semibold, 11)
                canvas.setFillColor(HexColor(PLATELINK_GREEN))
                canvas.drawCentredString(297.5, 715, "Scan to view menu & order  |  PlateLink Africa")
                
                # Underline separator
                canvas.setStrokeColor(HexColor(PLATELINK_GREEN))
                canvas.setLineWidth(1)
                canvas.line(70, 695, 525, 695)
        return Header(self)

    def create_footer(self) -> Flowable:
        """Returns a Flowable wrapper for the page footer."""
        class Footer(Flowable):
            def __init__(self, generator: "QRPDFGenerator"):
                Flowable.__init__(self)
                self.generator = generator
            def draw(self):
                canvas = self.canv
                font_regular = self.generator.get_font_name("regular")
                canvas.setFont(font_regular, 10)
                canvas.setFillColor(HexColor("#64748B"))
                canvas.drawCentredString(297.5, 50, "PlateLink Africa  |  Digital Ordering. Smarter Restaurants.")
        return Footer(self)

    def add_cut_lines(self, canvas: canvas.Canvas, page_width: float, page_height: float):
        """Draw dotted lines at horizontal and vertical midpoints."""
        canvas.setStrokeColor(HexColor("#CCCCCC"))
        canvas.setLineWidth(0.5)
        try:
            canvas.setDash([4, 4], 0)
        except Exception:
            try:
                canvas.setDash(4, 4)
            except Exception:
                pass
        
        # Vertical cut line
        canvas.line(page_width / 2.0, 100, page_width / 2.0, 680)
        
        # Horizontal cut line
        canvas.line(40, 410, page_width - 40, 410)
        
        # Reset dash
        try:
            canvas.setDash()
        except Exception:
            pass


    def generate_pdf(self, tables: List[Dict[str, Any]]) -> bytes:
        """
        Generate A4 PDF in memory.
        Lays out cards in 2x2 grid based on card positions.
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        page_width, page_height = A4
        
        # Exact position configurations
        positions = [
            (70, 430),   # Table 1
            (320, 430),  # Table 2
            (70, 170),   # Table 3
            (320, 170)   # Table 4
        ]
        
        pages_count = math.ceil(len(tables) / 4.0)
        
        for p in range(pages_count):
            # 1. Header
            header = self.create_header()
            header.drawOn(c, 0, 0)
            
            # 2. Cards
            page_tables = tables[p*4 : (p+1)*4]
            for idx, table in enumerate(page_tables):
                x, y = positions[idx]
                
                # Fetch token and build QR
                token = table.get("token", "")
                qr_img = self.generate_qr_code(table.get("number"), token)
                
                card = self.create_table_card(qr_img, table.get("number"))
                card.drawOn(c, x, y)
                
            # 3. Footer
            footer = self.create_footer()
            footer.drawOn(c, 0, 0)
            
            # 4. Cut Lines
            self.add_cut_lines(c, page_width, page_height)
            
            # Commit page
            c.showPage()
            
        c.save()
        buffer.seek(0)
        return buffer.getvalue()
