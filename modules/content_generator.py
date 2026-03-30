import json
import time
import os
import openai
from openai import RateLimitError


class ContentGenerator:
    def __init__(self, api_key: str, prompt_dir: str = "prompts"):
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self.prompt_dir = prompt_dir

    def generate(self, product: dict, keyword: str, post_type: str) -> dict:
        prompt = self._load_prompt(post_type, product, keyword)
        raw = self._call_api(prompt)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 실패: {e}\n원본 응답: {raw}")

        return {
            "title": data.get("title", ""),
            "body": data.get("body", ""),
            "tags": data.get("tags", [])[:10],
            "post_type": post_type,
        }

    def _load_prompt(self, post_type: str, product: dict, keyword: str) -> str:
        prompt_path = os.path.join(self.prompt_dir, f"{post_type}.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()

        result = template
        result = result.replace("{KEYWORD}", str(keyword))
        result = result.replace("{PRODUCT_NAME}", str(product.get("name", "")))
        result = result.replace("{PRICE}", str(product.get("price", "")))
        result = result.replace("{URL}", str(product.get("url", "")))
        result = result.replace("{RATING}", str(product.get("rating", "")))
        result = result.replace("{CATEGORY}", str(product.get("category", "")))
        return result

    def _call_api(self, prompt: str) -> str:
        max_retries = 3
        delay = 1

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    temperature=0.75,
                    response_format={"type": "json_object"},
                )
                return response.choices[0].message.content

            except RateLimitError:
                if attempt < max_retries - 1:
                    time.sleep(60)
                else:
                    raise

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise
