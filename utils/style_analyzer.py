from PIL import Image

async def analyze_style(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        description = (
            "masterpiece, best quality, highly detailed anime style, "
            "clean lineart, soft shading, vibrant colors, "
            "professional artist quality, detailed illustration"
        )
        return description
    except Exception:
        return "masterpiece, best quality, highly detailed anime style"
