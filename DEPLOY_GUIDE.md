# Google Cloud Run 배포 가이드

Slack 뉴스 요약 봇을 Google Cloud Run Job + Cloud Scheduler로 배포하는 단계별 가이드.

---

## 사전 준비

### 1. 필요한 계정 및 도구

| 항목 | 설명 |
|------|------|
| GCP 계정 | [console.cloud.google.com](https://console.cloud.google.com) |
| gcloud CLI | [설치 가이드](https://cloud.google.com/sdk/docs/install) |
| Slack App | [api.slack.com/apps](https://api.slack.com/apps) |
| Anthropic API Key | [console.anthropic.com](https://console.anthropic.com) |

### 2. gcloud CLI 초기 설정

```bash
# 로그인
gcloud auth login

# 프로젝트 생성 (또는 기존 프로젝트 사용)
gcloud projects create my-slack-bot --name="Slack News Bot"

# 프로젝트 선택
gcloud config set project my-slack-bot

# 결제 계정 연결 (무료 티어라도 결제 계정 필요)
# GCP 콘솔 → 결제 → 결제 계정 연결
```

### 3. 필요한 API 활성화

```bash
gcloud services enable \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

---

## Step 1: Slack App 생성

### 1-1. App 생성

1. [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. App Name: `뉴스요약봇` (원하는 이름)
3. Workspace: 봇을 설치할 워크스페이스 선택

### 1-2. Bot Token Scopes 설정

**OAuth & Permissions** 메뉴에서 아래 권한 추가:

| Scope | 용도 |
|-------|------|
| `channels:history` | 공개 채널 메시지 읽기 |
| `chat:write` | 메시지 전송 |

### 1-3. 워크스페이스에 설치

1. **OAuth & Permissions** → **Install to Workspace** → 권한 허용
2. **Bot User OAuth Token** (`xoxb-...`) 복사 → 나중에 Secret Manager에 저장

### 1-4. 채널에 봇 초대

```
/invite @뉴스요약봇
```

`#02-관련동향` 채널에서 위 명령어로 봇을 초대.

### 1-5. 채널 ID 확인

- 채널 이름 우클릭 → **링크 복사**
- URL의 마지막 경로가 채널 ID (예: `C0XXXXXXXXX`)
- 또는: 채널 상세정보 하단에서 확인 가능

---

## Step 2: Secret Manager에 API 키 저장

민감한 정보(API 키)를 Secret Manager에 안전하게 보관한다.

```bash
# Slack Bot Token 저장
echo -n "xoxb-your-actual-token" | \
  gcloud secrets create slack-bot-token --data-file=-

# Anthropic API Key 저장
echo -n "sk-ant-your-actual-key" | \
  gcloud secrets create anthropic-api-key --data-file=-
```

### 확인

```bash
# 저장된 시크릿 목록 확인
gcloud secrets list

# 값 확인 (필요 시)
gcloud secrets versions access latest --secret=slack-bot-token
```

---

## Step 3: 서비스 계정 설정

Cloud Run Job과 Cloud Scheduler가 사용할 서비스 계정을 생성한다.

```bash
PROJECT_ID=$(gcloud config get-value project)

# 서비스 계정 생성
gcloud iam service-accounts create slack-news-bot \
  --display-name="Slack News Bot"

SA_EMAIL="slack-news-bot@$PROJECT_ID.iam.gserviceaccount.com"

# Secret Manager 접근 권한 부여
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"

# Cloud Run Job 실행 권한 부여 (Scheduler가 Job을 트리거하기 위해)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/run.invoker"
```

---

## Step 4: 배포

### 방법 A: 배포 스크립트 사용 (권장)

```bash
# 환경 변수 설정
export GCP_PROJECT_ID=$(gcloud config get-value project)
export GCP_SERVICE_ACCOUNT="slack-news-bot@$GCP_PROJECT_ID.iam.gserviceaccount.com"
export SLACK_CHANNEL_ID="C0XXXXXXXXX"  # 실제 채널 ID로 변경

# 배포 실행
bash deploy/deploy.sh
```

### 방법 B: 수동 배포

#### 4-1. Artifact Registry 저장소 생성

```bash
gcloud artifacts repositories create slack-news-sumbot \
  --repository-format=docker \
  --location=asia-northeast3
```

#### 4-2. Docker 이미지 빌드 & 푸시

```bash
IMAGE="asia-northeast3-docker.pkg.dev/$PROJECT_ID/slack-news-sumbot/bot"

gcloud builds submit --tag $IMAGE
```

#### 4-3. Cloud Run Job 생성

```bash
gcloud run jobs create slack-news-sumbot \
  --image $IMAGE \
  --region asia-northeast3 \
  --memory 512Mi \
  --cpu 1 \
  --task-timeout 300s \
  --max-retries 1 \
  --service-account $SA_EMAIL \
  --set-secrets "SLACK_BOT_TOKEN=slack-bot-token:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest" \
  --set-env-vars "SLACK_CHANNEL_ID=$SLACK_CHANNEL_ID,TIMEZONE=Asia/Seoul"
```

#### 4-4. Cloud Scheduler 설정

```bash
JOB_URI="https://asia-northeast3-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/slack-news-sumbot:run"

gcloud scheduler jobs create http slack-news-sumbot-trigger \
  --location asia-northeast3 \
  --schedule "0 8 * * *" \
  --time-zone "Asia/Seoul" \
  --uri "$JOB_URI" \
  --http-method POST \
  --oauth-service-account-email $SA_EMAIL
```

---

## Step 5: 동작 확인

### 수동 실행 테스트

```bash
# Cloud Run Job 즉시 실행
gcloud run jobs execute slack-news-sumbot --region asia-northeast3

# 실행 로그 확인
gcloud run jobs executions list --job slack-news-sumbot --region asia-northeast3

# 상세 로그 확인
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=slack-news-sumbot" \
  --limit 50 \
  --format "table(timestamp, textPayload)"
```

### 스케줄러 테스트

```bash
# 스케줄러 즉시 실행 (다음 정시를 기다리지 않고 테스트)
gcloud scheduler jobs run slack-news-sumbot-trigger --location asia-northeast3
```

### 확인 사항

- [ ] `#02-관련동향` 채널에 요약 메시지가 올라오는지 확인
- [ ] 뉴스가 없는 경우 "공유된 뉴스가 없습니다" 메시지 확인
- [ ] 로그에 에러가 없는지 확인

---

## 업데이트 배포

코드 수정 후 재배포:

```bash
# 이미지 다시 빌드 & 푸시
gcloud builds submit --tag asia-northeast3-docker.pkg.dev/$PROJECT_ID/slack-news-sumbot/bot

# Cloud Run Job 이미지 업데이트
gcloud run jobs update slack-news-sumbot \
  --image asia-northeast3-docker.pkg.dev/$PROJECT_ID/slack-news-sumbot/bot \
  --region asia-northeast3
```

---

## 비용 안내 (무료 티어)

| 서비스 | 무료 범위 | 이 봇의 예상 사용량 |
|--------|-----------|---------------------|
| Cloud Run | 180,000 vCPU-초/월 | ~150 vCPU-초/월 (하루 5초 × 30일) |
| Cloud Scheduler | 3개 잡/월 | 1개 |
| Secret Manager | 6개 시크릿 버전/월 | 2개 |
| Artifact Registry | 500MB | ~100MB |
| Cloud Build | 120분/일 | ~1분/배포 |

> 하루 1회 실행 기준 **무료 범위 내** 충분합니다.

---

## 트러블슈팅

### "Permission denied" 에러

```bash
# 서비스 계정 권한 확인
gcloud projects get-iam-policy $PROJECT_ID \
  --filter="bindings.members:$SA_EMAIL" \
  --format="table(bindings.role)"

# Secret Manager 접근 권한이 없는 경우
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

### Slack API "channel_not_found" 에러

- 채널 ID가 올바른지 확인 (채널 이름이 아닌 ID)
- 봇이 채널에 초대되어 있는지 확인 (`/invite @봇이름`)

### Slack API "not_in_channel" 에러

```
/invite @뉴스요약봇
```

채널에서 위 명령어로 봇을 다시 초대.

### Cloud Run Job 타임아웃

기사 수가 많아 5분을 초과하는 경우:

```bash
gcloud run jobs update slack-news-sumbot \
  --task-timeout 600s \
  --region asia-northeast3
```

### 리소스 정리 (삭제)

```bash
# 스케줄러 삭제
gcloud scheduler jobs delete slack-news-sumbot-trigger --location asia-northeast3

# Cloud Run Job 삭제
gcloud run jobs delete slack-news-sumbot --region asia-northeast3

# Secret 삭제
gcloud secrets delete slack-bot-token
gcloud secrets delete anthropic-api-key

# Artifact Registry 삭제
gcloud artifacts repositories delete slack-news-sumbot --location asia-northeast3

# 서비스 계정 삭제
gcloud iam service-accounts delete $SA_EMAIL
```
