import aiohttp
from typing import Optional

async def analyze_image_style(image_path: str) -> str:
    """
    يحلل الصورة ويعطي وصف دقيق للاستايل والجودة والوضعية
    """
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        HF_TOKEN = "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"
        
        headers = {
            "Authorization": f"Bearer {HF_TOKEN}"
        }
        
        API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, data=image_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if isinstance(result, list) and len(result) > 0:
                        caption = result[0].get("generated_text", "")
                        style_prompt = (
                            f"{caption}, masterpiece, best quality, highly detailed, "
                            f"anime style, detailed skin, soft lighting, intricate details, nsfw"
                        )
                        return style_prompt
                else:
                    error = await resp.text()
                    print(f"HF Error: {error}")
                    return "masterpiece, best quality, highly detailed, anime style, beautiful detailed face, nsfw"
    except Exception as e:
        print(f"Analysis error: {e}")
        return "masterpiece, best quality, highly detailed, anime style, beautiful detailed face, nsfw"
