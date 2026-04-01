import os
import sys
import logging
from dotenv import load_dotenv

from db.database import DatabaseManager
from modules.keyword_manager import KeywordManager
from modules.content_generator import ContentGenerator
from modules.image_processor import ImageProcessor
from modules.blogger_publisher import BloggerPublisher
from modules.indexing_notifier import IndexingNotifier
from modules.seo_analyzer import get_benchmark, quality_check

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/run.log"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)


def main() -> None:
    log.info("===== 자동 포스팅 시작 =====")

    db = DatabaseManager()
    db.init_db()

    today_count = db.get_today_post_count()
    if today_count >= 2:
        log.info(f"오늘 이미 {today_count}건 발행 완료. 종료.")
        return

    keyword_manager = KeywordManager(db)
    next_item = keyword_manager.get_next()
    if not next_item:
        log.warning("발행할 키워드 또는 상품 없음. 종료.")
        sys.exit(0)

    keyword = next_item["keyword"]
    keyword_id = next_item["keyword_id"]
    post_type = next_item["post_type"]
    products = next_item["products"]
    product = products[0]

    log.info(f"키워드: {keyword} | 타입: {post_type} | 상품: {product['name']}")

    # ── 이미지 처리 ─────────────────────────────────────────────
    image_processor = ImageProcessor()
    image_path = None
    if product.get("image_url"):
        image_path = image_processor.download_and_resize(product["image_url"])
        if image_path:
            log.info(f"이미지 다운로드 완료: {image_path}")
        else:
            log.warning("이미지 다운로드 실패, 이미지 없이 진행")

    # ── SEO 벤치마크 수집 ────────────────────────────────────────
    benchmark = None
    try:
        benchmark = get_benchmark(keyword)
    except Exception as e:
        log.warning(f"벤치마크 수집 실패 (건너뜀): {e}")

    # ── 콘텐츠 생성 ──────────────────────────────────────────────
    generator = ContentGenerator()
    try:
        post = generator.generate(product, keyword, post_type, benchmark=benchmark)
    except Exception as e:
        log.error(f"콘텐츠 생성 실패: {e}")
        sys.exit(1)

    log.info(f"생성된 제목: {post['title']}")

    # ── 품질 검사 + 재생성 ───────────────────────────────────────
    if benchmark:
        try:
            qc = quality_check(post["title"], post["body"], keyword, benchmark)
            if not qc["passed"] and qc["suggestions"]:
                log.info(f"품질 FAIL (점수: {qc['score']}/100) — 피드백 반영 후 재생성")
                post = generator.generate(
                    product, keyword, post_type,
                    benchmark=benchmark,
                    suggestions=qc["suggestions"],
                )
                log.info(f"재생성 완료: {post['title']}")
            else:
                log.info(f"품질 PASS (점수: {qc['score']}/100)")
        except Exception as e:
            log.warning(f"품질 검사 실패 (건너뜀): {e}")

    # ── DB에 pending 상태로 기록 ─────────────────────────────────
    post_id = db.create_post({
        "product_id": product["id"],
        "keyword_id": keyword_id,
        "post_type": post_type,
        "title": post["title"],
        "content_preview": post["body"][:200],
        "status": "pending",
    })

    # ── 발행 ─────────────────────────────────────────────────────
    publisher = BloggerPublisher(
        token_json=os.environ["BLOGGER_TOKEN"],
        blog_id=os.environ["BLOGGER_BLOG_ID"],
    )

    try:
        post_url = publisher.write_post(
            title=post["title"],
            body=post["body"],
            image_path=image_path,
            tags=post["tags"],
            coupang_url=product.get("coupang_url", ""),
            product=product,
        )

        if post_url:
            db.update_post_status(post_id, "success", url=post_url)
            keyword_manager.mark_used(keyword_id)
            log.info(f"발행 완료: {post_url}")

            sa_json = os.environ.get("GOOGLE_INDEXING_SA")
            if sa_json:
                notifier = IndexingNotifier(sa_json)
                if notifier.notify(post_url):
                    log.info(f"Google 색인 요청 완료: {post_url}")
                else:
                    log.warning("Google 색인 요청 실패 (무시)")
        else:
            db.update_post_status(post_id, "failed", error="발행 URL 없음")
            log.error("발행 실패: URL 반환 없음")
            sys.exit(1)

    except Exception as e:
        log.error(f"발행 중 예외 발생: {e}")
        db.update_post_status(post_id, "failed", error=str(e))
        sys.exit(1)

    finally:
        image_processor.cleanup()

    log.info("===== 자동 포스팅 완료 =====")


if __name__ == "__main__":
    main()
