import json
import os
import re
import time
import logging

log = logging.getLogger(__name__)


class ContentGenerator:
    """
    블로그 콘텐츠 생성기.

    ANTHROPIC_API_KEY가 설정되어 있으면 Claude를 사용하고,
    없으면 GROQ_API_KEY로 Groq(Llama)를 사용합니다.
    """

    def __init__(self, prompt_dir: str = "prompts"):
        self.prompt_dir = prompt_dir
        self._client = None
        self._api_type = None
        self._init_client()

    def _init_client(self):
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        groq_key = os.environ.get("GROQ_API_KEY")

        if groq_key:
            import openai
            self._client = openai.OpenAI(
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1",
            )
            self._api_type = "groq"
            log.info("Groq API 사용")
        elif anthropic_key:
            import anthropic
            self._client = anthropic.Anthropic(api_key=anthropic_key)
            self._api_type = "claude"
            log.info("Claude API 사용 (fallback)")
        else:
            raise ValueError("GROQ_API_KEY 또는 ANTHROPIC_API_KEY 환경 변수를 설정하세요.")

    def generate(
        self,
        product: dict,
        keyword: str,
        post_type: str,
        benchmark: dict | None = None,
        suggestions: list[str] | None = None,
    ) -> dict:
        """
        블로그 포스트를 생성합니다.

        Args:
            product: 상품 정보 딕셔너리
            keyword: 타겟 키워드
            post_type: 포스트 유형 (single_review, problem_solve)
            benchmark: SEO 벤치마크 기준 (seo_analyzer.get_benchmark() 결과)
            suggestions: 재생성 시 반영할 개선 사항 (quality_check() 결과)
        """
        prompt = self._load_prompt(post_type, product, keyword)
        if benchmark:
            prompt += self._format_benchmark_section(benchmark, keyword)
        if suggestions:
            prompt += self._format_suggestions_section(suggestions)

        raw = self._call_api(prompt)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # 응답에 JSON 블록이 섞여 있을 경우 추출 시도
            match = re.search(r'\{[^{}]*"title"[^{}]*"body"[^{}]*\}', raw, re.DOTALL)
            if not match:
                match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError as e:
                    raise ValueError(f"JSON 파싱 실패: {e}\n원본 응답: {raw[:300]}")
            else:
                raise ValueError(f"JSON을 찾을 수 없음\n원본 응답: {raw[:300]}")

        return {
            "title": data.get("title", ""),
            "body": data.get("body", ""),
            "tags": data.get("tags", [])[:10],
            "post_type": post_type,
        }

    def _load_prompt(self, post_type: str, product: dict, keyword: str) -> str:
        prompt_path = os.path.join(self.prompt_dir, f"{post_type}.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()

        result = template
        result = result.replace("{KEYWORD}", str(keyword))
        result = result.replace("{PRODUCT_NAME}", str(product.get("name", "")))
        result = result.replace("{PRICE}", str(product.get("price", "")))
        result = result.replace("{RATING}", str(product.get("rating", "")))
        result = result.replace("{REVIEW_COUNT}", str(product.get("review_count", "")))
        result = result.replace("{CATEGORY}", str(product.get("category", "")))
        return result

    def _format_benchmark_section(self, benchmark: dict, keyword: str) -> str:
        patterns = ", ".join(benchmark.get("title_patterns", [])) or "없음"
        top_titles = benchmark.get("top_titles", [])[:5]
        titles_str = "\n".join(f"  {i+1}. {t}" for i, t in enumerate(top_titles)) or "  없음"

        return f"""

[SEO 목표 수치 — 네이버 상위 블로그 분석 결과]
아래는 '{keyword}' 키워드로 네이버 상위 노출된 실제 블로그 글의 분석 결과입니다.
검색 상위 노출을 위해 반드시 이 기준을 충족해야 합니다.

- 본문 텍스트 최소 {benchmark['target_content_length']}자 이상 (HTML 태그 제외 순수 텍스트 기준)
- 키워드 '{keyword}' 최소 {benchmark['target_keyword_count']}회 자연스럽게 포함
- 제목은 {benchmark['target_title_length']}자 내외
- 상위 글 제목 패턴: {patterns}
- 참고할 상위 글 제목 예시:
{titles_str}"""

    def _format_suggestions_section(self, suggestions: list[str]) -> str:
        items = "\n".join(f"- {s}" for s in suggestions)
        return f"""

[이전 생성 결과의 개선 필요 사항 — 반드시 모두 반영하세요]
{items}"""

    def _call_api(self, prompt: str) -> str:
        if self._api_type == "claude":
            return self._call_claude(prompt)
        return self._call_groq(prompt)

    def _call_claude(self, prompt: str) -> str:
        max_retries = 3
        delay = 5

        for attempt in range(max_retries):
            try:
                response = self._client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=6000,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text
            except Exception as e:
                if attempt < max_retries - 1:
                    log.warning(f"Claude API 재시도 ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise

    def _call_groq(self, prompt: str) -> str:
        from openai import RateLimitError
        max_retries = 3
        delay = 1

        for attempt in range(max_retries):
            try:
                response = self._client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4500,
                    temperature=0.75,
                    response_format={"type": "json_object"},
                )
                return response.choices[0].message.content
            except RateLimitError:
                if attempt < max_retries - 1:
                    time.sleep(60)
                else:
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise
