import hashlib
import os
import requests
from PIL import Image
import io


class ImageProcessor:
    def __init__(self, save_dir: str = "/tmp/images"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

    def download_and_resize(self, image_url: str, max_width: int = 1200) -> str | None:
        try:
            filename = hashlib.md5(image_url.encode()).hexdigest() + ".jpg"
            save_path = os.path.join(self.save_dir, filename)

            resp = requests.get(
                image_url,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
            )
            resp.raise_for_status()

            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            if img.width > max_width:
                ratio = max_width / img.width
                img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)

            img.save(save_path, "JPEG", quality=85, optimize=True)
            return os.path.abspath(save_path)

        except Exception as e:
            print(f"[ImageProcessor] 이미지 다운로드 실패: {e}")
            return None

    def cleanup(self) -> None:
        try:
            for f in os.listdir(self.save_dir):
                os.remove(os.path.join(self.save_dir, f))
        except Exception as e:
            print(f"[ImageProcessor] 정리 실패: {e}")
