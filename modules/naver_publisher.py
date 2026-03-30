import os
import random
import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class NaverPublisher:
    def __init__(self, naver_id: str, naver_pw: str, blog_id: str, cookies: dict = None):
        self.naver_id = naver_id
        self.naver_pw = naver_pw
        self.blog_id = blog_id
        self.cookies = cookies or {}
        self.driver = self._init_driver()

    def _init_driver(self) -> webdriver.Chrome:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def _sleep(self, min: float = 0.5, max: float = 1.5) -> None:
        time.sleep(random.uniform(min, max))

    def _wait_for(self, css_selector: str, timeout: int = 15) -> webdriver.remote.webelement.WebElement:
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        )

    def login(self) -> bool:
        try:
            # 쿠키 기반 인증 (NAVER_COOKIES 환경변수 우선)
            if self.cookies.get("NID_AUT") and self.cookies.get("NID_SES"):
                # 쿠키는 도메인 접속 후에만 주입 가능
                self.driver.get("https://www.naver.com")
                self._sleep(1.0, 2.0)

                self.driver.add_cookie({"name": "NID_AUT", "value": self.cookies["NID_AUT"], "domain": ".naver.com"})
                self.driver.add_cookie({"name": "NID_SES", "value": self.cookies["NID_SES"], "domain": ".naver.com"})

                # 로그인 상태 확인
                self.driver.get("https://www.naver.com")
                self._sleep(1.5, 2.5)

                # 로그인 여부: 로그인 버튼이 없으면 성공
                login_btns = self.driver.find_elements(By.CSS_SELECTOR, "#gnb_login_button, .gnb_login_button")
                if not login_btns:
                    return True

                self.driver.save_screenshot("/tmp/debug_login_fail.png")
                return False

            # 폴백: ID/PW 직접 로그인 (로컬 환경용)
            self.driver.get("https://nid.naver.com/nidlogin.login")
            self._sleep(1.0, 2.0)
            self.driver.execute_script("document.getElementById('id').value = arguments[0]", self.naver_id)
            self._sleep()
            self.driver.execute_script("document.getElementById('pw').value = arguments[0]", self.naver_pw)
            self._sleep()
            self.driver.find_element(By.ID, "log.login").click()
            self._sleep(2.0, 3.0)

            if "nid.naver.com" not in self.driver.current_url:
                return True

            self.driver.save_screenshot("/tmp/debug_login_fail.png")
            return False

        except Exception as e:
            print(f"[NaverPublisher] login error: {e}")
            self.driver.save_screenshot("/tmp/debug_login_fail.png")
            return False

    def write_post(
        self,
        title: str,
        body: str,
        image_path: Optional[str],
        tags: list[str],
    ) -> Optional[str]:
        try:
            self.driver.get(f"https://blog.naver.com/{self.blog_id}/postwrite")
            self._sleep(5.0, 6.0)
        except Exception as e:
            print(f"[NaverPublisher] navigate error: {e}")
            self.driver.save_screenshot("/tmp/debug_navigate.png")
            return None

        # 제목 입력
        try:
            title_el = None
            for selector in [".se-title-input", '[placeholder*="제목"]']:
                try:
                    title_el = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except Exception:
                    continue

            if title_el is None:
                raise RuntimeError("title element not found")

            title_el.click()
            self._sleep()
            self.driver.execute_script(
                "arguments[0].textContent = arguments[1]", title_el, title
            )
            self._sleep()
        except Exception as e:
            print(f"[NaverPublisher] title input error: {e}")
            self.driver.save_screenshot("/tmp/debug_title.png")
            return None

        # 본문 입력
        try:
            body_el = None
            for selector in [".se-content", ".se-component-content"]:
                try:
                    body_el = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except Exception:
                    continue

            if body_el is None:
                raise RuntimeError("body element not found")

            body_el.click()
            self._sleep()
            html_body = body.replace("\n", "<br>")
            self.driver.execute_script(
                "arguments[0].innerHTML = arguments[1]", body_el, html_body
            )
            self._sleep()
        except Exception as e:
            print(f"[NaverPublisher] body input error: {e}")
            self.driver.save_screenshot("/tmp/debug_body.png")
            return None

        # 이미지 업로드
        if image_path is not None:
            try:
                abs_image_path = os.path.abspath(image_path)

                photo_btn = None
                for selector in [
                    '[data-se-type="photo"]',
                    ".se-toolbar-item-photo",
                    '[title*="사진"]',
                    '[aria-label*="사진"]',
                ]:
                    try:
                        photo_btn = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except Exception:
                        continue

                if photo_btn:
                    photo_btn.click()
                    self._sleep(1.0, 2.0)

                file_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
                )
                file_input.send_keys(abs_image_path)

                WebDriverWait(self.driver, 10).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, ".se-image-resource")) > 0
                )
                self._sleep(1.0, 2.0)
            except Exception as e:
                print(f"[NaverPublisher] image upload error: {e}")
                self.driver.save_screenshot("/tmp/debug_image.png")

        # 태그 입력
        try:
            tag_el = None
            for selector in [".se-tag-input", '[placeholder*="태그"]']:
                try:
                    tag_el = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except Exception:
                    continue

            if tag_el:
                for tag in tags:
                    tag_el.click()
                    self._sleep()
                    self.driver.execute_script(
                        "arguments[0].textContent = arguments[1]", tag_el, tag
                    )
                    self._sleep()
                    tag_el.send_keys(Keys.RETURN)
                    self._sleep()
        except Exception as e:
            print(f"[NaverPublisher] tag input error: {e}")
            self.driver.save_screenshot("/tmp/debug_tags.png")

        # 발행 버튼 클릭
        try:
            publish_btn = None
            for selector in [".publish_btn", '[data-action="publish"]']:
                try:
                    publish_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except Exception:
                    continue

            if publish_btn is None:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if "발행" in btn.text:
                        publish_btn = btn
                        break

            if publish_btn is None:
                raise RuntimeError("publish button not found")

            publish_btn.click()
            self._sleep(3.0, 5.0)
        except Exception as e:
            print(f"[NaverPublisher] publish button error: {e}")
            self.driver.save_screenshot("/tmp/debug_publish.png")
            return None

        # 최종 발행 확인 버튼 (모달 등)
        try:
            confirm_btn = None
            for selector in [".confirm_btn", ".btn_confirm", '[data-action="confirm"]']:
                try:
                    confirm_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except Exception:
                    continue

            if confirm_btn is None:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if btn.text.strip() == "발행":
                        confirm_btn = btn
                        break

            if confirm_btn:
                confirm_btn.click()
                self._sleep(3.0, 5.0)
        except Exception as e:
            print(f"[NaverPublisher] confirm publish error: {e}")
            self.driver.save_screenshot("/tmp/debug_confirm.png")

        # 발행된 URL 반환
        try:
            current_url = self.driver.current_url
            if self.blog_id in current_url and "postwrite" not in current_url:
                return current_url

            WebDriverWait(self.driver, 10).until(
                lambda d: self.blog_id in d.current_url and "postwrite" not in d.current_url
            )
            return self.driver.current_url
        except Exception as e:
            print(f"[NaverPublisher] get post url error: {e}")
            self.driver.save_screenshot("/tmp/debug_final_url.png")
            return None

    def close(self) -> None:
        try:
            self.driver.quit()
        except Exception as e:
            print(f"[NaverPublisher] close error: {e}")
