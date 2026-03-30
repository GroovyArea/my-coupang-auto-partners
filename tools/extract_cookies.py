"""
네이버 쿠키 추출 도구
실행: python3 tools/extract_cookies.py

브라우저가 열리면 직접 네이버 로그인 완료 후 터미널에서 Enter 입력
추출된 쿠키는 GitHub Secrets에 자동 등록됩니다.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def main():
    print("브라우저를 열고 있습니다...")

    options = Options()
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    driver.get("https://nid.naver.com/nidlogin.login")

    print("\n" + "="*50)
    print("브라우저에서 네이버 로그인을 완료해주세요.")
    print("(캡차가 있으면 직접 해결 후 로그인)")
    print("로그인 완료 후 여기서 Enter를 눌러주세요.")
    print("="*50)
    input()

    cookies = {
        c["name"]: c["value"]
        for c in driver.get_cookies()
        if c["name"] in ["NID_AUT", "NID_SES"]
    }
    driver.quit()

    if not cookies.get("NID_AUT") or not cookies.get("NID_SES"):
        print("❌ 쿠키 추출 실패. 로그인이 완료됐는지 확인해주세요.")
        sys.exit(1)

    print(f"\n✅ 쿠키 추출 완료!")
    print(f"  NID_AUT: {cookies['NID_AUT'][:20]}...")
    print(f"  NID_SES: {cookies['NID_SES'][:20]}...")

    # GitHub Secrets 등록
    print("\nGitHub Secrets에 등록 중...")
    cookie_json = json.dumps(cookies)

    result = subprocess.run(
        ["gh", "secret", "set", "NAVER_COOKIES", "--body", cookie_json],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        print("✅ NAVER_COOKIES Secret 등록 완료!")
        print("\n이제 GitHub Actions에서 쿠키 기반 로그인이 사용됩니다.")
    else:
        print(f"❌ Secret 등록 실패: {result.stderr}")
        print(f"수동 등록: gh secret set NAVER_COOKIES --body '{cookie_json}'")


if __name__ == "__main__":
    main()
