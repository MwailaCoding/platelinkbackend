# app/services/cloudinary.py
import re
import cloudinary
import cloudinary.uploader
from app.core.config import settings

if settings.CLOUDINARY_URL and "key" not in settings.CLOUDINARY_URL:
    match = re.match(r"cloudinary://([^:]+):([^@]+)@(.+)", settings.CLOUDINARY_URL)
    if match:
        cloudinary.config(
            api_key=match.group(1),
            api_secret=match.group(2),
            cloud_name=match.group(3)
        )

class CloudinaryService:
    @staticmethod
    async def upload_image(file_content, folder="platelink"):
        if not settings.CLOUDINARY_URL or "key" in settings.CLOUDINARY_URL:
            return f"https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder={folder}"
        result = cloudinary.uploader.upload(file_content, folder=folder)
        return result.get("secure_url")
