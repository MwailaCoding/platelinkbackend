# app/services/cloudinary.py
import cloudinary
import cloudinary.uploader
from app.core.config import settings

cloudinary.config(cloudinary_url=settings.CLOUDINARY_URL)

class CloudinaryService:
    @staticmethod
    async def upload_image(file_content, folder="platelink"):
        if not settings.CLOUDINARY_URL or "key" in settings.CLOUDINARY_URL:
            return f"https://res.cloudinary.com/demo/image/upload/v1/sample.png?folder={folder}"
        result = cloudinary.uploader.upload(file_content, folder=folder)
        return result.get("secure_url")
