from PIL import Image

async def analyze_style(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        width, height = img.size

        description = (
            f"masterpiece, best quality, highly detailed anime style, "
            f"clean lineart, soft shading, vibrant colors, "
            f"professional artist quality, detailed illustration"
        )
        return description
    except Exception:
        return "masterpiece, best quality, highly detailed anime style"
