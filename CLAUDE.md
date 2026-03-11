# Slack News Summary Bot - 개발 계획

## 프로젝트 개요

`#02-관련동향` 채널에 전날 공유된 뉴스 링크를 수집하여, 매일 아침 8시에 **제목 - 한줄요약 - 링크** 형태의 표로 요약해서 슬랙에 자동 포스팅하는 봇.

## 아키텍처

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌────────────┐
│  Scheduler   │────▶│  Slack API   │────▶│  Summarizer │────▶│ Slack Post │
│ (cron 8:00) │     │ (메시지수집)  │     │ (Claude AI) │     │ (결과전송)  │
└─────────────┘     └──────────────┘     └─────────────┘     └────────────┘
```

## 기술 스택

- **언어**: Python 3.11+
- **Slack 연동**: `slack_sdk` (Slack Bolt for Python)
- **뉴스 요약**: Claude API (`anthropic` SDK)
- **링크 메타데이터 추출**: `requests` + `beautifulsoup4` (OG 태그 파싱)
- **스케줄링**: `APScheduler` (cron 트리거)
- **설정 관리**: `.env` 파일 (`python-dotenv`)
- **배포**: Docker (선택)

## 핵심 기능 흐름

1. **메시지 수집**: Slack `conversations.history` API로 전날 00:00~23:59 메시지 조회
2. **링크 추출**: 메시지 텍스트에서 URL 파싱 (`<http://...>` 형태의 Slack URL 포맷 처리)
3. **메타데이터 수집**: 각 링크에 접속하여 `<title>`, OG 태그 등에서 제목 추출
4. **AI 요약**: Claude API로 각 뉴스 기사를 한줄 요약
5. **결과 포스팅**: 정리된 표를 `#02-관련동향` 채널에 Slack 메시지로 전송

## 디렉토리 구조

```
slack-news-sumbot/
├── CLAUDE.md              # 개발 계획 (이 파일)
├── README.md              # 사용 가이드 (추후 작성)
├── requirements.txt       # Python 의존성
├── .env.example           # 환경 변수 템플릿
├── main.py                # 엔트리포인트 (스케줄러 실행)
├── bot/
│   ├── __init__.py
│   ├── slack_client.py    # Slack API 연동 (메시지 조회 + 전송)
│   ├── link_extractor.py  # 메시지에서 URL 추출 + 메타데이터 파싱
│   ├── summarizer.py      # Claude API로 뉴스 요약
│   └── formatter.py       # Slack 메시지 포맷 (표 형태)
├── config.py              # 설정 로드 (.env)
├── Dockerfile             # 컨테이너 배포용
└── tests/
    ├── __init__.py
    ├── test_link_extractor.py
    └── test_formatter.py
```

## 환경 변수

| 변수명 | 설명 |
|--------|------|
| `SLACK_BOT_TOKEN` | Slack Bot OAuth Token (`xoxb-...`) |
| `SLACK_CHANNEL_ID` | `#02-관련동향` 채널 ID |
| `ANTHROPIC_API_KEY` | Claude API 키 |
| `POST_HOUR` | 포스팅 시각 (기본값: 8) |
| `TIMEZONE` | 타임존 (기본값: Asia/Seoul) |

## Slack App 권한 (Bot Token Scopes)

- `channels:history` - 공개 채널 메시지 읽기
- `chat:write` - 메시지 전송
- `links:read` - 링크 미리보기 정보 (선택)

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

### Phase 5: 스케줄러 + 엔트리포인트
- [ ] `main.py` - APScheduler cron 트리거 (매일 08:00 KST)

### Phase 6: 테스트 및 배포
- [ ] 단위 테스트 작성
- [ ] Dockerfile 작성
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

# 환경 변수 설정
cp .env.example .env  # 값 채워넣기

# 즉시 실행 (테스트)
python main.py --now

# 스케줄러 실행
python main.py

# 테스트
pytest tests/
```
