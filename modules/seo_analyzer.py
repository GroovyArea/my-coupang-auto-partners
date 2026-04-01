"""
SEO 분석 모듈
blog_bot/post_evaluator.py 기반, my-coupang-auto-partners용으로 재작성.

기능:
- 네이버 상위 블로그 글 수집 및 분석 (NAVER_CLIENT_ID/SECRET 필요)
- 키워드별 벤치마크 기준 생성
- 발행 전 품질 검사 (70점 이상 pass)
"""

import os
import re
import logging
import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


def search_blog_posts(keyword: str, count: int = 10) -> list[dict]:
    """네이버 블로그 검색 API로 관련도순 상위 글을 수집합니다."""
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        log.warning("NAVER_CLIENT_ID/SECRET 미설정 — 벤치마크 스킵")
        return []

    try:
        resp = requests.get(
            "https://openapi.naver.com/v1/search/blog.json",
            headers={
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret,
            },
            params={"query": keyword, "display": count, "start": 1, "sort": "sim"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("items", [])
    except Exception as e:
        log.warning(f"블로그 검색 실패: {e}")
        return []


def fetch_blog_content(blog_url: str) -> dict | None:
    """네이버 블로그 본문을 크롤링합니다. 실패 시 None 반환."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
    }
    try:
        resp = requests.get(blog_url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # iframe 구조 처리
        iframe = soup.find("iframe", {"id": "mainFrame"})
        if iframe and iframe.get("src"):
            content_url = "https://blog.naver.com" + iframe["src"]
            resp = requests.get(content_url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

        content_area = (
            soup.find("div", class_="se-main-container")
            or soup.find("div", id="postViewArea")
            or soup.find("div", class_="post-view")
        )

        if content_area:
            text = content_area.get_text(separator="\n", strip=True)
            return {"text": text}
        return None
    except Exception as e:
        log.debug(f"콘텐츠 수집 실패 ({blog_url[:50]}): {e}")
        return None


def analyze_post(title: str, content: str, keyword: str) -> dict:
    """제목과 본문을 분석하여 SEO 수치를 반환합니다."""
    title_clean = re.sub(r"<[^>]+>", "", title)
    content_clean = re.sub(r"<[^>]+>", "", content)

    keyword_count = content_clean.count(keyword)
    keyword_density = (keyword_count / max(len(content_clean), 1)) * 100
    external_links = len(re.findall(r"https?://[^\s<>\"]+", content))

    return {
        "title": title_clean,
        "title_length": len(title_clean),
        "keyword_in_title": keyword in title_clean,
        "content_length": len(content_clean),
        "paragraph_count": len([p for p in content_clean.split("\n") if p.strip()]),
        "keyword_count": keyword_count,
        "keyword_density": round(keyword_density, 2),
        "external_links": external_links,
    }


def _analyze_title_patterns(titles: list[str]) -> list[str]:
    """상위 글 제목에서 공통 패턴을 추출합니다."""
    patterns = []

    if sum(1 for t in titles if re.search(r"\d+", t)) > len(titles) * 0.4:
        patterns.append("숫자 포함이 많음")

    for word in ["후기", "추천", "비교", "리뷰", "순위", "정리", "모음"]:
        if sum(1 for t in titles if word in t) >= 3:
            patterns.append(f"'{word}' 다수 사용")

    avg_len = sum(len(t) for t in titles) / max(len(titles), 1)
    patterns.append(f"평균 {avg_len:.0f}자")
    return patterns


def get_benchmark(keyword: str, fetch_full: bool = True) -> dict:
    """
    네이버 상위 블로그 글을 분석하여 벤치마크 기준을 반환합니다.
    NAVER_CLIENT_ID/SECRET 미설정 시 기본값을 반환합니다.
    """
    default = {
        "target_content_length": 2000,
        "target_keyword_count": 6,
        "target_keyword_density": 0.3,
        "target_title_length": 28,
        "title_patterns": [],
        "top_titles": [],
    }

    top_posts = search_blog_posts(keyword, count=10)
    if not top_posts:
        log.info(f"[벤치마크] '{keyword}' — API 미설정, 기본값 사용")
        return default

    log.info(f"[벤치마크] '{keyword}' 상위 {len(top_posts)}개 글 분석 중...")

    top_analyses = []
    for post in top_posts:
        title = re.sub(r"<[^>]+>", "", post.get("title", ""))
        link = post.get("link", "")
        analysis = {"title": title, "title_length": len(title), "keyword_in_title": keyword in title}

        if fetch_full and "blog.naver.com" in link:
            content_data = fetch_blog_content(link)
            if content_data:
                analysis.update(analyze_post(title, content_data["text"], keyword))

        top_analyses.append(analysis)

    top_with_content = [a for a in top_analyses if "content_length" in a]

    if top_with_content:
        avg_content = round(sum(a["content_length"] for a in top_with_content) / len(top_with_content))
        avg_kw_count = round(sum(a["keyword_count"] for a in top_with_content) / len(top_with_content), 1)
        avg_kw_density = round(sum(a["keyword_density"] for a in top_with_content) / len(top_with_content), 2)
        avg_title = round(sum(a["title_length"] for a in top_with_content) / len(top_with_content))
    else:
        avg_content = default["target_content_length"]
        avg_kw_count = default["target_keyword_count"]
        avg_kw_density = default["target_keyword_density"]
        avg_title = round(sum(a["title_length"] for a in top_analyses) / max(len(top_analyses), 1))

    title_patterns = _analyze_title_patterns([a["title"] for a in top_analyses])
    benchmark = {
        "target_content_length": max(avg_content, 1500),
        "target_keyword_count": max(round(avg_kw_count), 4),
        "target_keyword_density": avg_kw_density,
        "target_title_length": avg_title,
        "title_patterns": title_patterns,
        "top_titles": [a["title"] for a in top_analyses],
    }

    log.info(
        f"[벤치마크] 목표 — 본문 {benchmark['target_content_length']}자, "
        f"키워드 {benchmark['target_keyword_count']}회, "
        f"제목 {benchmark['target_title_length']}자 내외 | 패턴: {', '.join(title_patterns)}"
    )
    return benchmark


def quality_check(title: str, content: str, keyword: str, benchmark: dict) -> dict:
    """
    발행 전 품질 검증. 70점 이상 pass.

    Returns:
        {"passed": bool, "score": int, "issues": list, "suggestions": list, "analysis": dict}
    """
    analysis = analyze_post(title, content, keyword)
    score = 100
    issues = []
    suggestions = []

    # 본문 길이 (30점)
    target_len = benchmark["target_content_length"]
    ratio = analysis["content_length"] / max(target_len, 1)
    if ratio < 0.6:
        score -= 30
        gap = target_len - analysis["content_length"]
        issues.append(f"본문 너무 짧음 ({analysis['content_length']}자 / 목표 {target_len}자)")
        suggestions.append(f"본문을 {gap}자 이상 추가하세요. 상품 상세 리뷰, 사용 팁, 주의사항 섹션을 보강하세요.")
    elif ratio < 0.8:
        score -= 15
        gap = target_len - analysis["content_length"]
        issues.append(f"본문 약간 짧음 ({analysis['content_length']}자 / 목표 {target_len}자)")
        suggestions.append(f"본문을 {gap}자 정도 더 추가하세요.")

    # 제목에 키워드 포함 (20점)
    if not analysis["keyword_in_title"]:
        score -= 20
        issues.append("제목에 키워드 없음")
        suggestions.append(f"제목에 '{keyword}'를 포함하세요.")

    # 키워드 사용 횟수 (15점)
    target_kw = benchmark["target_keyword_count"]
    if analysis["keyword_count"] < max(target_kw * 0.5, 3):
        score -= 15
        issues.append(f"키워드 사용 부족 ({analysis['keyword_count']}회 / 목표 {target_kw}회)")
        suggestions.append(f"본문에 '{keyword}'를 자연스럽게 {target_kw}회 이상 사용하세요.")
    elif analysis["keyword_count"] < target_kw * 0.7:
        score -= 7

    # 키워드 밀도 과다 (15점)
    target_density = benchmark["target_keyword_density"]
    if target_density > 0 and analysis["keyword_density"] > target_density * 3:
        score -= 15
        issues.append(f"키워드 밀도 과다 ({analysis['keyword_density']}% / 평균 {target_density}%)")
        suggestions.append("키워드가 과도하게 반복됩니다. 본문을 늘리거나 유사 표현으로 대체하세요.")

    # 제목 길이 (10점)
    if analysis["title_length"] < 10:
        score -= 10
        issues.append(f"제목이 너무 짧음 ({analysis['title_length']}자)")
        suggestions.append(f"제목을 {benchmark['target_title_length']}자 내외로 작성하세요.")
    elif analysis["title_length"] > 45:
        score -= 5
        issues.append(f"제목이 너무 김 ({analysis['title_length']}자)")

    # 외부 링크 과다 (10점)
    if analysis["external_links"] > 2:
        score -= 10
        issues.append(f"외부 링크 과다 ({analysis['external_links']}개)")
        suggestions.append("외부 링크는 쿠팡 파트너스 링크 1개만 유지하세요.")

    passed = score >= 70
    status = "PASS" if passed else "FAIL"
    log.info(f"[품질검사] {status} (점수: {score}/100)")
    for issue in issues:
        log.info(f"  - {issue}")

    return {
        "passed": passed,
        "score": score,
        "issues": issues,
        "suggestions": suggestions,
        "analysis": analysis,
    }
