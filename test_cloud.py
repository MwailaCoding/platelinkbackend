import asyncio
from app.services.cloudinary import CloudinaryService

async def main():
    try:
        url = await CloudinaryService.upload_image(b'fake data')
        print(url)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    asyncio.run(main())
