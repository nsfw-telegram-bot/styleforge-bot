import aiohttp
import asyncio
import random
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
    "elegant standing pose",
    "from below, legs spread"
]

async def generate_images(
    character_name: str,
    style_description: str = None,
    reference_image_path: str = None,
    num_images: int = 4,
    same_pose: bool = False
) -> List[str]:
    
    results = []
    
    if not style_description:
        style_description = "masterpiece, best quality, highly detailed, anime style, nsfw"
    
    async with aiohttp.ClientSession() as session:
        for i in range(num_images):
            if same_pose:
                pose = "same pose as reference, detailed"
            else:
                pose = random.choice(POSES)
            
            prompt = (
                f"masterpiece, best quality, ultra detailed, {style_description}, "
                f"1girl, {character_name}, {pose}, beautiful detailed face, detailed eyes, "
                f"perfect anatomy, sharp focus, high resolution, anime style, nsfw, explicit"
            )
            
            negative = "low quality, blurry, bad anatomy, deformed, extra limbs, watermark, text, censored, worst quality"
            
            workflow = {
                "3": {
                    "inputs": {
                        "seed": random.randint(1, 999999999),
                        "steps": 35,
                        "cfg": 7.5,
                        "sampler_name": "euler_ancestral",
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
                        "text": negative,
                        "clip": ["4", 1]
                    },
                    "class_type": "CLIPTextEncode"
                },
                "8": {
                    "inputs": {
                        "samples": ["3", 0],
                        "vae": ["4", 2]
                    },
                    "class_type": "VAEDecode"
                },
                "9": {
                    "inputs": {
                        "filename_prefix": "StyleForge",
                        "images": ["8", 0]
                    },
                    "class_type": "SaveImage"
                }
            }
            
            payload = {
                "prompt": workflow,
                "client_id": str(uuid.uuid4())
            }
            
            try:
                async with session.post(f"{COMFYUI_URL}/prompt", json=payload) as resp:
                    if resp.status != 200:
                        print(f"Error: {await resp.text()}")
                        continue
                    data = await resp.json()
                    prompt_id = data.get("prompt_id")
                
                image_url = await wait_for_image(session, prompt_id)
                if image_url:
                    results.append(image_url)
            except Exception as e:
                print(f"Generation error: {e}")
                continue
    
    return results

async def wait_for_image(session, prompt_id, timeout=120):
    for _ in range(timeout // 2):
        await asyncio.sleep(2)
        async with session.get(f"{COMFYUI_URL}/history/{prompt_id}") as resp:
            if resp.status == 200:
                history = await resp.json()
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    for node_id, node_output in outputs.items():
                        if "images" in node_output:
                            img = node_output["images"][0]
                            filename = img["filename"]
                            subfolder = img.get("subfolder", "")
                            return f"{COMFYUI_URL}/view?filename={filename}&subfolder={subfolder}&type=output"
    return None
