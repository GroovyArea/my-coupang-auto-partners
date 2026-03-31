import json
import os
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class BloggerPublisher:
    def __init__(self, token_json: str, blog_id: str):
        self.blog_id = blog_id
        token_data = json.loads(token_json)
        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=token_data.get("scopes"),
        )
        self.service = build("blogger", "v3", credentials=creds)

    def write_post(
        self,
        title: str,
        body: str,
        image_path: Optional[str],
        tags: list[str],
        coupang_url: str = "",
    ) -> Optional[str]:
        try:
            # 쿠팡 파트너스 고지 문구 (이용약관 필수) — 최상단
            disclosure = (
                '<p style="font-size:12px;color:#888;border:1px solid #ddd;'
                'padding:8px 12px;border-radius:4px;">'
                "⚠️ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, "
                "이에 따른 일정액의 수수료를 제공받습니다.</p>"
            )
            # 상품 이미지 — 고지 문구 바로 아래
            image_html = ""
            if image_path and os.path.exists(image_path):
                import base64
                with open(image_path, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode()
                ext = os.path.splitext(image_path)[1].lstrip(".") or "jpeg"
                image_html = (
                    f'<p style="text-align:center;">'
                    f'<img src="data:image/{ext};base64,{img_b64}" '
                    f'style="max-width:100%;border-radius:8px;" alt="상품 이미지"/></p>'
                )
            # 쿠팡 구매 버튼 — 본문 하단
            buy_button = ""
            if coupang_url:
                buy_button = (
                    '<div style="text-align:center;margin:24px 0;">'
                    f'<a href="{coupang_url}" target="_blank" rel="nofollow" '
                    'style="background:#e4003b;color:#fff;padding:14px 32px;'
                    'border-radius:8px;text-decoration:none;font-weight:bold;'
                    'font-size:16px;display:inline-block;">'
                    '🛒 쿠팡에서 최저가 확인하기</a></div>'
                )
            # body는 AI가 HTML로 생성하므로 그대로 사용
            content = disclosure + image_html + body + buy_button

            post_body = {
                "title": title,
                "content": content,
                "labels": tags,
            }

            result = self.service.posts().insert(
                blogId=self.blog_id,
                body=post_body,
                isDraft=False,
            ).execute()

            return result.get("url")

        except Exception as e:
            print(f"[BloggerPublisher] write_post error: {e}")
            return None

    def close(self) -> None:
        pass
