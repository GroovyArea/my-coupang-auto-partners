"""
초기 데이터 투입 스크립트
실행: python db/seed.py

상품 URL은 쿠팡 파트너스(partners.coupang.com)에서 직접 생성한 링크로 교체 필요
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import DatabaseManager

# ──────────────────────────────────────────
# 키워드 + 상품 데이터 (URL은 파트너스 링크로 교체)
# ──────────────────────────────────────────
SEED_DATA = [
    {
        "keyword": "유산균 추천 장건강",
        "category": "건강",
        "post_type": "problem_solve",
        "products": [
            {
                "name": "종근당건강 락토핏 생유산균 골드 60포",
                "price": 29900,
                "rating": 4.9,
                "review_count": 187000,
                "image_url": "https://img.danawa.com/prod_img/500000/567/160/img/6160567_1.jpg",
                "coupang_url": "https://link.coupang.com/a/eeto2F",
            },
        ],
    },
    {
        "keyword": "유아 물티슈 추천 순한",
        "category": "유아",
        "post_type": "single_review",
        "products": [
            {
                "name": "하기스 천연물 물티슈 100매 10팩",
                "price": 22900,
                "rating": 4.9,
                "review_count": 95400,
                "image_url": "https://img.danawa.com/prod_img/500000/083/652/img/17652083_1.jpg",
                "coupang_url": "https://link.coupang.com/a/eetp2M",
            },
        ],
    },
    {
        "keyword": "고양이 모래 추천",
        "category": "반려동물",
        "post_type": "single_review",
        "products": [
            {
                "name": "스웨덴케어 고양이 두부모래 6L",
                "price": 13900,
                "rating": 4.8,
                "review_count": 41200,
                "image_url": "https://www.fitpetmall.com/wp-content/uploads/2022/11/image-28.png",
                "coupang_url": "https://link.coupang.com/a/eetqCa",
            },
        ],
    },
    {
        "keyword": "강아지 간식 추천",
        "category": "반려동물",
        "post_type": "single_review",
        "products": [
            {
                "name": "퍼피아 닭가슴살 져키 500g",
                "price": 12900,
                "rating": 4.9,
                "review_count": 62800,
                "image_url": "https://img.danawa.com/prod_img/500000/567/160/img/6160567_1.jpg",
                "coupang_url": "https://link.coupang.com/a/eetrag",
            },
        ],
    },
    {
        "keyword": "공기청정기 추천 소형",
        "category": "가전",
        "post_type": "single_review",
        "products": [
            {
                "name": "삼성 블루스카이 3000 공기청정기",
                "price": 159000,
                "rating": 4.8,
                "review_count": 12400,
                "image_url": "https://img.danawa.com/prod_img/500000/083/149/img/13149083_1.jpg",
                "coupang_url": "https://link.coupang.com/a/eetrTq",
            },
        ],
    },
    {
        "keyword": "에어프라이어 추천 1인가구",
        "category": "가전",
        "post_type": "single_review",
        "products": [
            {
                "name": "필립스 에어프라이어 HD9252 3.2L",
                "price": 129000,
                "rating": 4.8,
                "review_count": 44300,
                "image_url": "https://img.danawa.com/prod_img/500000/093/845/img/12845093_1.jpg",
                "coupang_url": "https://link.coupang.com/a/eetsov",
            },
        ],
    },
    {
        "keyword": "무선청소기 추천 가성비",
        "category": "가전",
        "post_type": "single_review",
        "products": [
            {
                "name": "다이슨 V8 무선청소기",
                "price": 449000,
                "rating": 4.9,
                "review_count": 31500,
                "image_url": "https://img.danawa.com/prod_img/500000/133/760/img/21760133_1.jpg",
                "coupang_url": "https://link.coupang.com/a/eetsRX",
            },
        ],
    },
]


def main():
    db = DatabaseManager()
    db.init_db()

    keyword_count = 0
    product_count = 0
    skipped = 0

    for item in SEED_DATA:
        # URL 미입력 상품 체크
        all_replaced = all(
            p["coupang_url"] != "REPLACE_ME" for p in item["products"]
        )
        if not all_replaced:
            print(f"⏭️  스킵 (URL 미입력): {item['keyword']}")
            skipped += 1
            continue

        kid = db.add_keyword(item["keyword"], item["category"], item["post_type"])
        keyword_count += 1

        for p in item["products"]:
            p["keyword"] = item["keyword"]
            p["category"] = item["category"]
            db.add_product(p)
            product_count += 1

    print(f"\n✅ 키워드 {keyword_count}개, 상품 {product_count}개 투입 완료")
    if skipped:
        print(f"⏭️  {skipped}개 항목 스킵 (URL을 'REPLACE_ME'에서 파트너스 링크로 교체 후 재실행)")


if __name__ == "__main__":
    main()
