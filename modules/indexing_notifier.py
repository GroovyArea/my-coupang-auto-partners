import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build


class IndexingNotifier:
    SCOPES = ["https://www.googleapis.com/auth/indexing"]

    def __init__(self, sa_json: str):
        sa_info = json.loads(sa_json)
        creds = service_account.Credentials.from_service_account_info(
            sa_info, scopes=self.SCOPES
        )
        self.service = build("indexing", "v3", credentials=creds)

    def notify(self, url: str) -> bool:
        try:
            body = {"url": url, "type": "URL_UPDATED"}
            self.service.urlNotifications().publish(body=body).execute()
            return True
        except Exception as e:
            print(f"[IndexingNotifier] 실패: {e}")
            return False
