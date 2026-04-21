"""
Cloudinary upload helper. configure() must be called before use.
"""
import asyncio
import os
import cloudinary
import cloudinary.uploader


def configure():
    cloudinary.config(
        cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
        api_key=os.environ.get("CLOUDINARY_API_KEY", ""),
        api_secret=os.environ.get("CLOUDINARY_API_SECRET", ""),
    )


async def upload_cover_image(file_bytes: bytes, filename: str) -> dict:
    """
    Uploads image bytes to Cloudinary under the blog/ folder.
    Returns {"public_id": "blog/xyz", "secure_url": "https://..."}
    """
    loop = asyncio.get_event_loop()

    def _upload():
        return cloudinary.uploader.upload(
            file_bytes,
            folder="blog",
            use_filename=True,
            unique_filename=True,
            resource_type="image",
        )

    result = await loop.run_in_executor(None, _upload)
    return {
        "public_id": result["public_id"],
        "secure_url": result["secure_url"],
    }
