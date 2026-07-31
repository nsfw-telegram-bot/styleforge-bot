import random
from typing import List

POSES = [
    "sitting on bed",
    "lying on bed looking at viewer",
    "standing gracefully",
    "leaning forward",
    "from side view",
    "close-up portrait",
    "full body",
    "dynamic pose",
    "sitting with legs crossed",
    "looking over shoulder",
    "lying on side",
    "kneeling",
    "from above",
    "elegant standing pose"
]

async def generate_images(
    character_name: str,
    style_description: str,
    reference_image_path: str,
    num_images: int = 4
) -> List[str]:
    
    results = []
    for i in range(num_images):
        pose = random.choice(POSES)
        
        prompt = (
            f"masterpiece, best quality, highly detailed, {style_description}, "
            f"1girl, {character_name}, {pose}, beautiful face, detailed eyes, "
            f"soft lighting, perfect anatomy"
        )
        
        results.append(
            f"Generated image {i+1} for {character_name}\n"
            f"Pose: {pose}\n"
            f"Prompt: {prompt[:120]}..."
        )
    
    return results
