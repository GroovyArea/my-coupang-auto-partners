"""
키워드 잔여량 확인 및 부족 시 GitHub Issue 생성
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import DatabaseManager


def main():
    db = DatabaseManager()
    db.init_db()

    remaining = db.get_remaining_keyword_count()
    print(f"[check_keywords] 남은 키워드: {remaining}개")

    threshold = int(os.environ.get("KEYWORD_THRESHOLD", "4"))

    if remaining <= threshold:
        title = f"⚠️ 키워드 소진 임박 — 잔여 {remaining}개 ({remaining // 2}일치)"
        body = (
            f"## 키워드 보충이 필요합니다\n\n"
            f"현재 발행 가능한 키워드가 **{remaining}개** 남았습니다.\n"
            f"하루 2회 포스팅 기준으로 약 **{remaining // 2}일** 후 소진됩니다.\n\n"
            f"### 조치 방법\n"
            f"1. 쿠팡 파트너스(partners.coupang.com)에서 새 상품 링크 생성\n"
            f"2. `db/seed.py`에 키워드 + 상품 + 링크 추가\n"
            f"3. push 하면 자동 반영됩니다\n\n"
            f"_이 이슈는 자동 생성되었습니다._"
        )

        result = subprocess.run(
            ["gh", "issue", "create",
             "--title", title,
             "--body", body,
             "--label", "keywords"],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            print(f"[check_keywords] GitHub Issue 생성 완료: {result.stdout.strip()}")
        else:
            # label이 없으면 label 없이 재시도
            result2 = subprocess.run(
                ["gh", "issue", "create", "--title", title, "--body", body],
                capture_output=True, text=True
            )
            if result2.returncode == 0:
                print(f"[check_keywords] GitHub Issue 생성 완료: {result2.stdout.strip()}")
            else:
                print(f"[check_keywords] Issue 생성 실패: {result2.stderr}")
    else:
        print(f"[check_keywords] 키워드 충분함 ({remaining}개). 알림 불필요.")


if __name__ == "__main__":
    main()
