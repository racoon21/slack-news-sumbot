#!/usr/bin/env bash
# GCP Cloud Run Job 배포 스크립트
# 사용법: bash deploy/deploy.sh
# 사전 조건: gcloud CLI 인증 완료, 환경 변수 설정 필요

set -euo pipefail

# ── 설정 (배포 전 수정 필요) ──────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:?GCP_PROJECT_ID 환경 변수를 설정하세요}"
REGION="asia-northeast3"
JOB_NAME="slack-news-sumbot"
REPO_NAME="slack-news-sumbot"
IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/bot"
SERVICE_ACCOUNT="${GCP_SERVICE_ACCOUNT:?GCP_SERVICE_ACCOUNT 환경 변수를 설정하세요}"
CHANNEL_ID="${SLACK_CHANNEL_ID:?SLACK_CHANNEL_ID 환경 변수를 설정하세요}"

echo "=== 1/4. Artifact Registry 저장소 생성 (이미 있으면 건너뜀) ==="
gcloud artifacts repositories create "$REPO_NAME" \
  --repository-format=docker \
  --location="$REGION" \
  --quiet 2>/dev/null || echo "  저장소가 이미 존재합니다."

echo "=== 2/4. Docker 이미지 빌드 & 푸시 ==="
gcloud builds submit --tag "$IMAGE"

echo "=== 3/4. Cloud Run Job 생성/업데이트 ==="
if gcloud run jobs describe "$JOB_NAME" --region="$REGION" &>/dev/null; then
  echo "  기존 Job 업데이트..."
  gcloud run jobs update "$JOB_NAME" \
    --image "$IMAGE" \
    --region "$REGION"
else
  echo "  새 Job 생성..."
  gcloud run jobs create "$JOB_NAME" \
    --image "$IMAGE" \
    --region "$REGION" \
    --memory 512Mi \
    --cpu 1 \
    --task-timeout 300s \
    --max-retries 1 \
    --set-secrets "SLACK_BOT_TOKEN=slack-bot-token:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest" \
    --set-env-vars "SLACK_CHANNEL_ID=$CHANNEL_ID,TIMEZONE=Asia/Seoul"
fi

echo "=== 4/4. Cloud Scheduler 설정 ==="
SCHEDULER_NAME="$JOB_NAME-trigger"
JOB_URI="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/$JOB_NAME:run"

if gcloud scheduler jobs describe "$SCHEDULER_NAME" --location="$REGION" &>/dev/null; then
  echo "  기존 스케줄러 업데이트..."
  gcloud scheduler jobs update http "$SCHEDULER_NAME" \
    --location "$REGION" \
    --schedule "0 8 * * *" \
    --time-zone "Asia/Seoul" \
    --uri "$JOB_URI" \
    --http-method POST \
    --oauth-service-account-email "$SERVICE_ACCOUNT"
else
  echo "  새 스케줄러 생성..."
  gcloud scheduler jobs create http "$SCHEDULER_NAME" \
    --location "$REGION" \
    --schedule "0 8 * * *" \
    --time-zone "Asia/Seoul" \
    --uri "$JOB_URI" \
    --http-method POST \
    --oauth-service-account-email "$SERVICE_ACCOUNT"
fi

echo ""
echo "=== 배포 완료 ==="
echo "  Cloud Run Job: $JOB_NAME"
echo "  스케줄: 매일 08:00 KST"
echo "  수동 실행: gcloud run jobs execute $JOB_NAME --region $REGION"
