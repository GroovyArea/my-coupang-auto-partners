import sqlite3
import os
from datetime import datetime, date
from typing import Optional


class DatabaseManager:
    def __init__(self, db_path: str = "db/coupang_blog.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS products (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    name         TEXT NOT NULL,
                    coupang_url  TEXT NOT NULL,
                    image_url    TEXT,
                    price        INTEGER,
                    category     TEXT,
                    keyword      TEXT,
                    rating       REAL,
                    review_count INTEGER,
                    is_active    INTEGER DEFAULT 1,
                    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS keywords (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword      TEXT NOT NULL UNIQUE,
                    category     TEXT,
                    post_type    TEXT DEFAULT 'single_review',
                    used_count   INTEGER DEFAULT 0,
                    last_used_at DATETIME,
                    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS posts (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id      INTEGER REFERENCES products(id),
                    keyword_id      INTEGER REFERENCES keywords(id),
                    post_type       TEXT,
                    title           TEXT,
                    content_preview TEXT,
                    naver_post_url  TEXT,
                    status          TEXT DEFAULT 'pending',
                    error_message   TEXT,
                    published_at    DATETIME,
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def add_product(self, product: dict) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO products (name, coupang_url, image_url, price, category, keyword, rating, review_count)
                   VALUES (:name, :coupang_url, :image_url, :price, :category, :keyword, :rating, :review_count)""",
                product,
            )
            return cursor.lastrowid

    def get_products_by_keyword(self, keyword: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM products WHERE keyword = ? AND is_active = 1", (keyword,)
            ).fetchall()
            return [dict(r) for r in rows]

    def add_keyword(self, keyword: str, category: str, post_type: str) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO keywords (keyword, category, post_type) VALUES (?, ?, ?)",
                (keyword, category, post_type),
            )
            if cursor.lastrowid:
                return cursor.lastrowid
            row = conn.execute(
                "SELECT id FROM keywords WHERE keyword = ?", (keyword,)
            ).fetchone()
            return row["id"]

    def get_pending_keyword(self) -> Optional[dict]:
        today = date.today().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                """SELECT * FROM keywords
                   WHERE id NOT IN (
                       SELECT DISTINCT keyword_id FROM posts
                       WHERE DATE(created_at) = ? AND keyword_id IS NOT NULL
                   )
                   AND (last_used_at IS NULL OR DATE(last_used_at) <= DATE('now', '-7 days'))
                   ORDER BY used_count ASC, last_used_at ASC
                   LIMIT 1""",
                (today,),
            ).fetchone()
            return dict(row) if row else None

    def get_today_post_count(self) -> int:
        today = date.today().isoformat()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM posts WHERE DATE(created_at) = ?", (today,)
            ).fetchone()
            return row["cnt"]

    def create_post(self, post: dict) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO posts (product_id, keyword_id, post_type, title, content_preview, status)
                   VALUES (:product_id, :keyword_id, :post_type, :title, :content_preview, :status)""",
                post,
            )
            return cursor.lastrowid

    def update_post_status(
        self,
        post_id: int,
        status: str,
        url: Optional[str] = None,
        error: Optional[str] = None,
    ):
        published_at = datetime.now().isoformat() if status == "published" else None
        with self._connect() as conn:
            conn.execute(
                """UPDATE posts
                   SET status = ?, naver_post_url = ?, error_message = ?, published_at = ?
                   WHERE id = ?""",
                (status, url, error, published_at, post_id),
            )

    def get_remaining_keyword_count(self) -> int:
        """7일 이내 사용되지 않은 발행 가능한 키워드 수 반환"""
        with self._connect() as conn:
            row = conn.execute(
                """SELECT COUNT(*) AS cnt FROM keywords
                   WHERE last_used_at IS NULL
                      OR DATE(last_used_at) <= DATE('now', '-7 days')"""
            ).fetchone()
            return row["cnt"]

    def mark_keyword_used(self, keyword_id: int):
        with self._connect() as conn:
            conn.execute(
                """UPDATE keywords
                   SET used_count = used_count + 1, last_used_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (keyword_id,),
            )

    def seed_initial_data(self):
        keywords = [
            ("반려동물 사료 추천", "반려동물", "single_review"),
            ("고양이 화장실 추천", "반려동물", "comparison"),
            ("강아지 간식 추천", "반려동물", "single_review"),
            ("공기청정기 추천 소형", "가전", "comparison"),
            ("에어프라이어 1인용", "가전", "single_review"),
            ("목 베개 추천 직장인", "건강", "problem_solve"),
            ("무선 청소기 추천", "가전", "comparison"),
            ("유아 물티슈 추천", "유아", "single_review"),
            ("강아지 하네스 추천", "반려동물", "single_review"),
            ("노트북 거치대 추천", "IT", "problem_solve"),
        ]
        for keyword, category, post_type in keywords:
            self.add_keyword(keyword, category, post_type)
