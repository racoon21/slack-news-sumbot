"""Slack 뉴스 요약 봇 엔트리포인트.

Cloud Run Job에서 실행되거나, --now 플래그로 로컬에서 즉시 실행한다.
"""

import logging
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bot.formatter import format_summary
from bot.link_extractor import extract_links, fetch_metadata
from bot.slack_client import fetch_yesterday_messages, post_summary
from bot.summarizer import summarize_articles
from config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def run() -> None:
    """전체 파이프라인 실행.

    설정 로드 → 메시지 수집 → 링크 추출 → 메타데이터 수집 → AI 요약 → 포맷팅 → Slack 전송.
    """
    # 1. 설정 로드
    config = load_config()
    logger.info("설정 로드 완료")

    # 2. 전날 메시지 수집
    messages = fetch_yesterday_messages(
        token=config["slack_bot_token"],
        channel_id=config["slack_channel_id"],
        tz=config["timezone"],
    )
    logger.info("전날 메시지 %d건 수집", len(messages))

    # 3. 링크 추출
    urls = extract_links(messages)
    logger.info("URL %d건 추출", len(urls))

    # 4. 메타데이터 수집 (각 링크의 제목)
    articles = [fetch_metadata(url) for url in urls]
    logger.info("메타데이터 수집 완료")

    # 5. AI 요약
    articles = summarize_articles(
        api_key=config["anthropic_api_key"],
        articles=articles,
    )
    logger.info("AI 요약 완료")

    # 6. 포맷팅
    zone = ZoneInfo(config["timezone"])
    yesterday = datetime.now(zone) - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")
    text = format_summary(articles, date_str)

    # 7. Slack 전송
    post_summary(
        token=config["slack_bot_token"],
        channel_id=config["slack_channel_id"],
        text=text,
    )
    logger.info("Slack 전송 완료")


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logger.error("실행 중 오류 발생: %s", e)
        sys.exit(1)
