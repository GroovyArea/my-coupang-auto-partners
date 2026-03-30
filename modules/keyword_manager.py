from typing import Optional
from db.database import DatabaseManager


class KeywordManager:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_next(self) -> Optional[dict]:
        keyword = self.db.get_pending_keyword()
        if not keyword:
            return None

        products = self.db.get_products_by_keyword(keyword["keyword"])
        if not products:
            return None

        return {
            "keyword_id": keyword["id"],
            "keyword": keyword["keyword"],
            "category": keyword["category"],
            "post_type": keyword["post_type"],
            "products": products,
        }

    def mark_used(self, keyword_id: int):
        self.db.mark_keyword_used(keyword_id)
