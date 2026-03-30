"""
Google Blogger OAuth 토큰 발급 스크립트
실행: python3 tools/get_blogger_token.py

브라우저에서 Google 계정 인증 완료 후 token.json이 생성됩니다.
생성된 token.json 내용을 GitHub Secret(BLOGGER_TOKEN)에 등록합니다.
"""
import json
import subprocess
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/blogger"]

CLIENT_SECRET_FILE = os.path.expanduser(
    "~/Downloads/client_secret_675606100012-7gp0jin7pqtbkshm7hauoqoqncfdjliu.apps.googleusercontent.com.json"
)


def main():
    print("브라우저에서 Google 계정 인증을 진행합니다...")

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    token_data = json.loads(creds.to_json())
    token_json = json.dumps(token_data)

    # 블로그 목록 확인
    service = build("blogger", "v3", credentials=creds)
    blogs = service.blogs().listByUser(userId="self").execute()

    print("\n✅ 인증 완료!")
    print("\n=== 내 블로그 목록 ===")
    for blog in blogs.get("items", []):
        print(f"  이름: {blog['name']}")
        print(f"  ID:   {blog['id']}")
        print(f"  URL:  {blog['url']}")
        print()

    # GitHub Secret 등록
    print("GitHub Secret에 등록 중...")
    result = subprocess.run(
        ["gh", "secret", "set", "BLOGGER_TOKEN", "--body", token_json],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("✅ BLOGGER_TOKEN Secret 등록 완료!")
    else:
        print(f"❌ Secret 등록 실패: {result.stderr}")
        print(f"\n수동 등록:\ngh secret set BLOGGER_TOKEN --body '{token_json}'")

    print("\n위 블로그 ID를 복사해서 GitHub Secret BLOGGER_BLOG_ID에 등록하세요:")
    print("gh secret set BLOGGER_BLOG_ID --body '여기에_블로그_ID'")


if __name__ == "__main__":
    main()
