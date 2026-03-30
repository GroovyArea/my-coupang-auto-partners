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
                "<p><small>⚠️ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, "
                "이에 따른 일정액의 수수료를 제공받습니다.</small></p><hr>"
            )
            # 쿠팡 구매 버튼 — 본문 하단
            buy_button = ""
            if coupang_url:
                buy_button = (
                    f'<br><br><p style="text-align:center;">'
                    f'<a href="{coupang_url}" target="_blank" '
                    f'style="background:#e4003b;color:#fff;padding:12px 24px;'
                    f'border-radius:6px;text-decoration:none;font-weight:bold;">'
                    f'쿠팡에서 최저가 확인하기 →</a></p>'
                )
            content = disclosure + body.replace("\n", "<br>") + buy_button

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
