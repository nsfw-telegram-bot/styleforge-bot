import aiohttp
import asyncio
import random
import json
import uuid
from typing import List
from config import COMFYUI_URL

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
    reference_image_path: str = None,
    num_images: int = 4
) -> List[str]:
    """
    Generate images using RunPod ComfyUI.
    Currently basic text-to-image (we will improve IP-Adapter later).
    """
    results = []
    
    async with aiohttp.ClientSession() as session:
        for i in range(num_images):
            pose = random.choice(POSES)
            
            prompt = (
                f"masterpiece, best quality, highly detailed, {style_description}, "
                f"1girl, {character_name}, {pose}, beautiful face, detailed eyes, "
                f"soft lighting, perfect anatomy, anime style"
            )
            
            # Simple workflow for now (text-to-image)
            workflow = {
                "3": {
                    "inputs": {
                        "seed": random.randint(1, 999999999),
                        "steps": 25,
                        "cfg": 7.5,
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "denoise": 1.0,
                        "model": ["4", 0],
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "latent_image": ["5", 0]
                    },
                    "class_type": "KSampler"
                },
                "4": {
                    "inputs": {
                        "ckpt_name": "ponyDiffusionV6XL.safetensors"
                    },
                    "class_type": "CheckpointLoaderSimple"
                },
                "5": {
                    "inputs": {
                        "width": 768,
                        "height": 1024,
                        "batch_size": 1
                    },
                    "class_type": "EmptyLatentImage"
                },
                "6": {
                    "inputs": {
                        "text": prompt,
                        "clip": ["4", 1]
                    },
                    "class_type": "CLIPTextEncode"
                },
                "7": {
                    "inputs": {
