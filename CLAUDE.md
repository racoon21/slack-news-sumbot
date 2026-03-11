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
- **Slack 연동**: `slack_sdk`
- **뉴스 요약**: Claude API (`anthropic` SDK)
- **링크 메타데이터 추출**: `requests` + `beautifulsoup4` (OG 태그 파싱)
- **웹 프레임워크**: `flask` (Cloud Run HTTP 트리거 수신용)
- **설정 관리**: 환경 변수 (GCP Secret Manager 연동)
- **배포**: Docker → Google Cloud Run Job + Cloud Scheduler

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
├── requirements.txt       # Python 의존성
├── .env.example           # 로컬 개발용 환경 변수 템플릿
├── main.py                # 엔트리포인트 (Flask 앱 + 즉시 실행 모드)
├── bot/
│   ├── __init__.py
│   ├── slack_client.py    # Slack API 연동 (메시지 조회 + 전송)
│   ├── link_extractor.py  # 메시지에서 URL 추출 + 메타데이터 파싱
│   ├── summarizer.py      # Claude API로 뉴스 요약
│   └── formatter.py       # Slack 메시지 포맷 (표 형태)
├── config.py              # 설정 로드 (환경 변수)
├── Dockerfile             # Cloud Run 배포용
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

## 구현 단계

### Phase 1: 기본 구조 세팅
- [ ] `requirements.txt` 작성
- [ ] `.env.example` 작성
- [ ] `config.py` - 환경 변수 로드

### Phase 2: Slack 메시지 수집
- [ ] `bot/slack_client.py` - 전날 메시지 조회 기능
- [ ] `bot/link_extractor.py` - URL 추출 및 OG 태그 파싱

### Phase 3: 뉴스 요약
- [ ] `bot/summarizer.py` - Claude API 호출로 뉴스 한줄 요약 생성

### Phase 4: 결과 포맷팅 및 전송
- [ ] `bot/formatter.py` - Slack mrkdwn 형식 표 생성
- [ ] `bot/slack_client.py` - 요약 결과 채널 전송

### Phase 5: 엔트리포인트
- [ ] `main.py` - Flask 앱 (HTTP 트리거) + `--now` 즉시 실행 모드

### Phase 6: 배포
- [ ] `Dockerfile` 작성
- [ ] `deploy/deploy.sh` - GCP 배포 자동화 스크립트
  - Artifact Registry에 이미지 푸시
  - Cloud Run Job 생성/업데이트
  - Cloud Scheduler 설정
  - Secret Manager 연동
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
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정 (로컬 개발)
cp .env.example .env  # 값 채워넣기

# 즉시 실행 (로컬 테스트)
python main.py --now

# Flask 서버 실행 (로컬에서 HTTP 트리거 테스트)
python main.py

# 테스트
pytest tests/

# Docker 빌드 & 로컬 테스트
docker build -t slack-news-sumbot .
docker run --env-file .env slack-news-sumbot

# GCP 배포
bash deploy/deploy.sh
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
