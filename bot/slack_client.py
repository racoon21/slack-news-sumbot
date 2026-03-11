"""Slack API 연동 모듈 — 메시지 조회 및 요약 결과 전송."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def fetch_yesterday_messages(token: str, channel_id: str, tz: str) -> list[dict]:
    """전날 00:00~23:59(KST) 메시지를 조회한다.

    페이지네이션을 처리하여 모든 메시지를 반환.
    Slack API 에러 시 예외를 발생시킨다.
    """
    client = WebClient(token=token)
    zone = ZoneInfo(tz)

    # 전날 00:00:00 ~ 23:59:59 범위 계산
    now = datetime.now(zone)
    yesterday = now - timedelta(days=1)
    start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Slack API는 Unix timestamp 사용
    oldest = str(start.timestamp())
    latest = str(end.timestamp())

    messages = []
    cursor = None

    while True:
        try:
            response = client.conversations_history(
                channel=channel_id,
                oldest=oldest,
                latest=latest,
                limit=200,
                cursor=cursor,
            )
        except SlackApiError as e:
            raise RuntimeError(f"Slack API 에러: {e.response['error']}") from e

        messages.extend(response.get("messages", []))

        # 페이지네이션: 다음 페이지가 있으면 계속
        cursor = response.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break

    return messages


def post_summary(token: str, channel_id: str, text: str) -> None:
    """채널에 요약 메시지를 전송한다.

    메시지가 비어있으면 전송하지 않는다.
    """
    if not text or not text.strip():
        return

    client = WebClient(token=token)

    try:
        client.chat_postMessage(channel=channel_id, text=text, mrkdwn=True)
    except SlackApiError as e:
        raise RuntimeError(f"Slack 메시지 전송 실패: {e.response['error']}") from e
