import requests
import base64
from django.conf import settings
from decouple import config


def generate_image(prompt, width=1024, height=1024):
    ACCOUNT_ID = config('ACCOUNT_ID', default="")
    API_URL = (f"https://api.cloudflare.com/client/v4/accounts/"
               f"{ACCOUNT_ID}/ai/run/@cf/stabilityai/stable-diffusion-xl-base-1.0")

    headers = {
        "Authorization": f"Bearer {settings.CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "height": min(height, 1024),
        "width": min(width, 1024),
        "num_steps": 20,
        "guidance_scale": 7.5
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        content_type = response.headers.get('Content-Type', '')
        # Если это сразу картинка – возвращаем её
        if 'image/png' in content_type or 'image/jpeg' in content_type:
            return response.content
        # Если JSON – извлекаем base64
        try:
            data = response.json()
            if data.get("success") and "result" in data and "image" in data["result"]:
                return base64.b64decode(data["result"]["image"])
            else:
                raise Exception(f"JSON ответ без изображения: {data}")
        except ValueError:
            raise Exception(f"Ответ не JSON и не изображение: {response.text[:200]}")
    else:
        response.raise_for_status()