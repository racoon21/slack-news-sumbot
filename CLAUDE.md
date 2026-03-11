# Slack News Summary Bot - 개발 계획

## 프로젝트 개요

`#02-관련동향` 채널에 전날 공유된 뉴스 링크를 수집하여, 매일 아침 8시(KST)에 **제목 - 한줄요약 - 링크** 형태의 표로 요약해서 슬랙에 자동 포스팅하는 봇.

## 아키텍처

```
┌──────────────────┐     ┌──────────────┐     ┌─────────────┐     ┌────────────┐
│ Cloud Scheduler  │────▶│  Slack API   │────▶│  Summarizer │────▶│ Slack Post │
│ (매일 08:00 KST) │     │ (메시지수집)  │     │ (Claude AI) │     │ (결과전송)  │
└──────────────────┘     └──────────────┘     └─────────────┘     └────────────┘
        │                        │                    │                   │
        ▼                        ▼                    ▼                   ▼
  GCP Cloud Scheduler      Cloud Run Job         Anthropic API      Slack Webhook
  → HTTP 트리거             (컨테이너 실행)        (뉴스 요약)        (메시지 전송)
```

### 배포 구조

```
Google Cloud Platform
├── Cloud Run Job          # 뉴스 요약 봇 (Docker 컨테이너)
├── Cloud Scheduler        # 매일 08:00 KST cron 트리거
├── Secret Manager         # API 키 안전 보관
└── Artifact Registry      # Docker 이미지 저장소
```

## 기술 스택

- **언어**: Python 3.11+
- **패키지 관리**: `uv` (pyproject.toml + uv.lock)
- **Slack 연동**: `slack_sdk`
- **뉴스 요약**: Claude API (`anthropic` SDK)
- **링크 메타데이터 추출**: `requests` + `beautifulsoup4` (OG 태그 파싱)
- **설정 관리**: 환경 변수 (GCP Secret Manager 연동)
- **배포**: Docker (uv 기반 빌드) → Google Cloud Run Job + Cloud Scheduler
- **참고**: Cloud Run Job은 단순 스크립트 실행형이므로 Flask 등 웹 프레임워크 불필요

## 핵심 기능 흐름

1. **트리거**: Cloud Scheduler가 매일 08:00 KST에 Cloud Run Job 실행
2. **메시지 수집**: Slack `conversations.history` API로 전날 00:00~23:59(KST) 메시지 조회
3. **링크 추출**: 메시지 텍스트에서 URL 파싱 (`<http://...>` 형태의 Slack URL 포맷 처리)
4. **메타데이터 수집**: 각 링크에 접속하여 `<title>`, OG 태그 등에서 제목 추출
5. **AI 요약**: Claude API로 각 뉴스 기사를 한줄 요약
6. **결과 포스팅**: 정리된 표를 `#02-관련동향` 채널에 Slack 메시지로 전송

## 디렉토리 구조

```
slack-news-sumbot/
├── CLAUDE.md              # 개발 계획 (이 파일)
├── README.md              # 사용 가이드
├── pyproject.toml         # 프로젝트 메타데이터 + 의존성 정의 (uv)
├── uv.lock                # 의존성 락파일 (uv, 커밋 필수)
├── .python-version        # Python 버전 고정 (uv 자동 생성)
├── .env.example           # 로컬 개발용 환경 변수 템플릿
├── main.py                # 엔트리포인트 (Cloud Run Job 실행 스크립트)
├── bot/
│   ├── __init__.py
│   ├── slack_client.py    # Slack API 연동 (메시지 조회 + 전송)
│   ├── link_extractor.py  # 메시지에서 URL 추출 + 메타데이터 파싱
│   ├── summarizer.py      # Claude API로 뉴스 요약
│   └── formatter.py       # Slack 메시지 포맷 (표 형태)
├── config.py              # 설정 로드 (환경 변수)
├── Dockerfile             # Cloud Run 배포용 (uv 기반 멀티스테이지 빌드)
├── deploy/
│   └── deploy.sh          # GCP 배포 스크립트
└── tests/
    ├── __init__.py
    ├── test_link_extractor.py
    └── test_formatter.py
```

## 환경 변수

| 변수명 | 설명 | 보관 위치 |
|--------|------|-----------|
| `SLACK_BOT_TOKEN` | Slack Bot OAuth Token (`xoxb-...`) | Secret Manager |
| `SLACK_CHANNEL_ID` | `#02-관련동향` 채널 ID | 환경 변수 |
| `ANTHROPIC_API_KEY` | Claude API 키 | Secret Manager |
| `TIMEZONE` | 타임존 (기본값: `Asia/Seoul`) | 환경 변수 |
| `GCP_PROJECT_ID` | GCP 프로젝트 ID | 배포 스크립트 |

## Slack App 권한 (Bot Token Scopes)

- `channels:history` - 공개 채널 메시지 읽기
- `chat:write` - 메시지 전송
- `links:read` - 링크 미리보기 정보 (선택)

## GCP 배포 설정

### Cloud Run Job 설정
- **리전**: `asia-northeast3` (서울)
- **메모리**: 512Mi
- **CPU**: 1
- **타임아웃**: 300초 (5분)
- **최대 재시도**: 1

### Cloud Scheduler 설정
- **스케줄**: `0 8 * * *` (매일 08:00)
- **타임존**: `Asia/Seoul`
- **대상**: Cloud Run Job 실행

### 무료 티어 범위
- Cloud Run: 월 180,000 vCPU-초, 360,000 GiB-초 무료
- Cloud Scheduler: 월 3개 잡 무료
- Secret Manager: 월 6개 시크릿 버전 무료
- Artifact Registry: 500MB 스토리지 무료
- **하루 1회 실행 기준 무료 범위 내 충분**

## 모듈별 핵심 함수 시그니처

```python
# config.py — 환경 변수를 읽어 설정 객체 반환
def load_config() -> dict:
    """SLACK_BOT_TOKEN, SLACK_CHANNEL_ID, ANTHROPIC_API_KEY, TIMEZONE 로드.
    필수 변수 누락 시 명확한 에러 메시지와 함께 종료."""

# bot/slack_client.py — Slack API 래퍼
def fetch_yesterday_messages(token: str, channel_id: str, tz: str) -> list[dict]:
    """전날 00:00~23:59(KST) 메시지 조회. 페이지네이션 처리 포함.
    Slack API 에러 시 예외 발생."""

def post_summary(token: str, channel_id: str, text: str) -> None:
    """채널에 요약 메시지 전송. 메시지가 비어있으면 전송하지 않음."""

# bot/link_extractor.py — URL 추출 + 메타데이터
def extract_links(messages: list[dict]) -> list[str]:
    """메시지에서 URL 추출. Slack 포맷 <http://...|label> 처리.
    중복 URL 제거."""

def fetch_metadata(url: str) -> dict:
    """URL에 접속하여 제목(title, og:title) 추출.
    타임아웃 5초, 접속 실패 시 URL 자체를 제목으로 사용 (에러 무시)."""

# bot/summarizer.py — Claude API 요약
def summarize_articles(api_key: str, articles: list[dict]) -> list[dict]:
    """여러 기사를 한번의 Claude API 호출로 일괄 요약 (비용 절감).
    각 기사에 title + one_line_summary 필드 추가.
    API 호출 실패 시 요약 없이 제목만 반환."""

# bot/formatter.py — Slack 메시지 포맷
def format_summary(articles: list[dict], date_str: str) -> str:
    """Slack mrkdwn 표 형식으로 변환. 기사 0건이면 '공유된 뉴스가 없습니다' 반환."""

# main.py — 엔트리포인트
def run() -> None:
    """전체 파이프라인 실행: 설정 로드 → 메시지 수집 → 링크 추출 →
    메타데이터 수집 → AI 요약 → 포맷팅 → Slack 전송.
    --now 플래그 또는 Cloud Run Job에서 직접 실행."""
```

## 에지 케이스 처리

| 상황 | 처리 방식 |
|------|-----------|
| 전날 뉴스 0건 | "공유된 뉴스가 없습니다" 메시지 전송 (빈 표 방지) |
| 링크 접속 실패/타임아웃 | URL 자체를 제목으로 사용, 요약은 "-"로 표시 |
| Claude API 호출 실패 | 제목만 표시, 요약 컬럼은 "요약 실패"로 표시 |
| Slack API 토큰 만료 | 명확한 에러 로그 출력 후 exit(1) |
| 메시지에 URL 없음 (텍스트만) | 해당 메시지 건너뜀 |
| 동일 URL 중복 공유 | 중복 제거 후 1건만 처리 |

## 구현 단계

### Phase 1: 기본 구조 세팅
- [ ] `uv init` 프로젝트 초기화 + `pyproject.toml` 의존성 정의
- [ ] `uv add slack_sdk anthropic requests beautifulsoup4 python-dotenv`
- [ ] `.env.example` 작성
- [ ] `config.py` - 환경 변수 로드 (`load_config()`)

### Phase 2: Slack 메시지 수집 + 링크 추출
- [ ] `bot/slack_client.py` - `fetch_yesterday_messages()`, `post_summary()`
- [ ] `bot/link_extractor.py` - `extract_links()`, `fetch_metadata()`

### Phase 3: 뉴스 요약 + 포맷팅
- [ ] `bot/summarizer.py` - `summarize_articles()` (일괄 요약으로 API 호출 최소화)
- [ ] `bot/formatter.py` - `format_summary()` (Slack mrkdwn 표)

### Phase 4: 엔트리포인트 + 배포
- [ ] `main.py` - `run()` 파이프라인 (단순 스크립트, Flask 없음)
- [ ] `Dockerfile` 작성
- [ ] `deploy/deploy.sh` - GCP 배포 자동화 스크립트
- [ ] 단위 테스트 작성
- [ ] README.md 작성

## 출력 메시지 예시

```
:newspaper: *전날 관련동향 뉴스 요약* (2026-03-10)

| # | 제목 | 요약 | 링크 |
|---|------|------|------|
| 1 | OpenAI, GPT-5 발표 | OpenAI가 차세대 모델 GPT-5를 공개하며 멀티모달 성능 대폭 향상 | <https://example.com/1> |
| 2 | 구글 Gemini 업데이트 | 구글이 Gemini 2.0을 출시하며 코딩 능력 강화 | <https://example.com/2> |

_총 2건의 뉴스가 공유되었습니다._
```

## 개발 명령어

```bash
# 프로젝트 초기화 (최초 1회)
uv init
uv add slack_sdk anthropic requests beautifulsoup4 python-dotenv

# 개발 의존성 추가
uv add --dev pytest

# 의존성 동기화 (clone 후)
uv sync

# 환경 변수 설정 (로컬 개발)
cp .env.example .env  # 값 채워넣기

# 즉시 실행 (로컬 테스트)
uv run python main.py --now

# 테스트
uv run pytest tests/

# Docker 빌드 & 로컬 테스트
docker build -t slack-news-sumbot .
docker run --env-file .env slack-news-sumbot

# GCP 배포
bash deploy/deploy.sh
```

## Dockerfile 예시 (uv 기반 멀티스테이지 빌드)

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# 의존성 파일 복사 및 설치 (캐시 레이어 활용)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 소스 코드 복사
COPY . .
RUN uv sync --frozen --no-dev

CMD ["uv", "run", "python", "main.py", "--now"]
```

## GCP 배포 절차 (deploy.sh 내용)

```bash
# 1. Docker 이미지 빌드 & 푸시
gcloud builds submit --tag asia-northeast3-docker.pkg.dev/$PROJECT_ID/slack-news-sumbot/bot

# 2. Cloud Run Job 생성
gcloud run jobs create slack-news-sumbot \
  --image asia-northeast3-docker.pkg.dev/$PROJECT_ID/slack-news-sumbot/bot \
  --region asia-northeast3 \
  --memory 512Mi \
  --cpu 1 \
  --task-timeout 300s \
  --max-retries 1 \
  --set-secrets "SLACK_BOT_TOKEN=slack-bot-token:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest" \
  --set-env-vars "SLACK_CHANNEL_ID=$CHANNEL_ID,TIMEZONE=Asia/Seoul"

# 3. Cloud Scheduler 설정
gcloud scheduler jobs create http slack-news-sumbot-trigger \
  --schedule "0 8 * * *" \
  --time-zone "Asia/Seoul" \
  --uri "https://asia-northeast3-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/slack-news-sumbot:run" \
  --http-method POST \
  --oauth-service-account-email $SERVICE_ACCOUNT
```
