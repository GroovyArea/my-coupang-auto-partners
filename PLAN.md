# 쿠팡 파트너스 블로그 자동화 구현 계획

## 프로젝트 개요

쿠팡 파트너스 제휴 링크를 포함한 블로그 포스트를 AI로 생성하고 자동 발행하는 시스템.

- **블로그 플랫폼**: Google Blogger (blogspot.com)
- **인프라**: GitHub Actions (무료, 공개 레포)
- **AI**: Groq API — Llama 3.1 8B (무료 티어)
- **DB**: SQLite + GitHub Artifact (90일 보존)
- **총 비용**: 0원

---

## 아키텍처

```
GitHub Actions (cron)
    │
    ├─ db/seed.py          → SQLite에 키워드/상품 데이터 투입
    ├─ modules/keyword_manager.py  → 다음 발행할 키워드 선택
    ├─ modules/content_generator.py → Groq API로 한국어 포스트 생성
    └─ modules/blogger_publisher.py → Blogger REST API로 발행
```

---

## 운영 준비 단계 (완료)

| 단계 | 내용 | 상태 |
|---|---|---|
| 1 | 쿠팡 파트너스 가입 (AF5006969) | ✅ |
| 2 | Groq API 키 발급 | ✅ |
| 3 | GitHub 레포 생성 (공개) | ✅ |
| 4 | Google Blogger 블로그 생성 | ✅ |
| 5 | Google Cloud — Blogger API 활성화 | ✅ |
| 6 | OAuth 2.0 토큰 발급 | ✅ |
| 7 | GitHub Secrets 등록 | ✅ |
| 8 | 상품 seed 데이터 입력 | ✅ |

---

## GitHub Secrets

| Secret명 | 설명 |
|---|---|
| `GROQ_API_KEY` | Groq API 인증키 |
| `BLOGGER_TOKEN` | Google OAuth 2.0 토큰 JSON |
| `BLOGGER_BLOG_ID` | Blogger 블로그 ID (`1529431367190128336`) |
| `COUPANG_AFFILIATE_ID` | 쿠팡 파트너스 ID (`AF5006969`) |

---

## 자동 발행 스케줄

- **KST 10:00** (UTC 01:00) — 1일 1회차
- **KST 15:00** (UTC 06:00) — 1일 2회차
- 하루 최대 2건, DB에 기록하여 중복 발행 방지

---

## 파일 구조

```
my-coupang-auto-partners/
├── main.py                         # 파이프라인 오케스트레이터
├── requirements.txt
├── PLAN.md                         # 이 문서
├── .github/workflows/post.yml      # GitHub Actions 워크플로우
├── db/
│   ├── database.py                 # SQLite 관리
│   └── seed.py                     # 초기 키워드/상품 데이터
├── modules/
│   ├── keyword_manager.py          # 키워드 선택 로직
│   ├── content_generator.py        # Groq API 포스트 생성
│   ├── image_processor.py          # 이미지 다운로드/리사이즈
│   └── blogger_publisher.py        # Blogger REST API 발행
├── prompts/
│   ├── single_review.txt           # 단일 상품 리뷰 프롬프트
│   └── problem_solve.txt           # 문제 해결형 프롬프트
└── tools/
    └── get_blogger_token.py        # OAuth 토큰 발급 도구 (로컬 1회 실행)
```

---

## 현재 seed 키워드 목록 (7개)

| 키워드 | 상품 | 카테고리 |
|---|---|---|
| 유산균 추천 장건강 | 락토핏 생유산균 골드 60포 | 건강 |
| 유아 물티슈 추천 순한 | 하기스 천연물 물티슈 100매 10팩 | 유아 |
| 고양이 모래 추천 | 스웨덴케어 두부모래 6L | 반려동물 |
| 강아지 간식 추천 | 퍼피아 닭가슴살 져키 500g | 반려동물 |
| 공기청정기 추천 소형 | 삼성 블루스카이 3000 | 가전 |
| 에어프라이어 추천 1인가구 | 필립스 에어프라이어 HD9252 | 가전 |
| 무선청소기 추천 가성비 | 다이슨 V8 무선청소기 | 가전 |

---

## 주기적 유지보수

| 주기 | 작업 |
|---|---|
| 월 1회 | `python3 tools/get_blogger_token.py` — OAuth 토큰 갱신 |
| 분기 1회 | `db/seed.py` — 신규 키워드/상품 추가 |
| 수시 | GitHub Actions 로그 확인, 실패 시 원인 파악 |

---

## 향후 개선 방향

- [ ] 쿠팡 파트너스 API 승인(15만원 달성) 후 상품 자동 수집으로 교체
- [ ] 구글 애드센스 블로그 승인 신청 (트래픽 쌓인 후)
- [ ] Google Search Console 등록으로 구글 색인 가속
- [ ] 포스트 수 30개 이상 → 애드센스 심사 적합 수준 확보

---

## 포스팅 주의사항 (쿠팡 파트너스 이용약관)

- 모든 포스트 상단에 **"이 포스팅은 쿠팡 파트너스 활동의 일환으로..."** 고지 문구 자동 삽입됨
- 자동 클릭 유도 금지 (계정 영구 정지)
- 허위/과장 정보 기재 금지
