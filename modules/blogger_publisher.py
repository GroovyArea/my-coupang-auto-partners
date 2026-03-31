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

    def _build_json_ld(self, product: dict, title: str, post_url: str = "") -> str:
        """Google 리치 스니펫용 JSON-LD 구조화 데이터 생성"""
        data = {
            "@context": "https://schema.org/",
            "@type": "Review",
            "name": title,
            "reviewBody": f"{product.get('name', '')} 실사용 리뷰",
            "author": {"@type": "Person", "name": "Groovy한 일지"},
            "itemReviewed": {
                "@type": "Product",
                "name": product.get("name", ""),
                "offers": {
                    "@type": "Offer",
                    "price": str(product.get("price", "")),
                    "priceCurrency": "KRW",
                    "availability": "https://schema.org/InStock",
                    "url": product.get("coupang_url", ""),
                },
            },
            "reviewRating": {
                "@type": "Rating",
                "ratingValue": str(product.get("rating", "4.5")),
                "bestRating": "5",
                "worstRating": "1",
            },
        }
        if product.get("review_count"):
            data["itemReviewed"]["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": str(product.get("rating", "4.5")),
                "reviewCount": str(product.get("review_count", "")),
                "bestRating": "5",
            }
        return (
            f'<script type="application/ld+json">'
            f'{json.dumps(data, ensure_ascii=False)}'
            f'</script>'
        )

    def write_post(
        self,
        title: str,
        body: str,
        image_path: Optional[str],
        tags: list[str],
        coupang_url: str = "",
        product: dict = None,
    ) -> Optional[str]:
        try:
            # JSON-LD 구조화 데이터 (리치 스니펫용)
            json_ld = self._build_json_ld(product or {}, title) if product else ""

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
            content = json_ld + disclosure + image_html + body + buy_button

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
