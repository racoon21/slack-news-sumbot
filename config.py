"""환경 변수를 읽어 설정 딕셔너리를 반환하는 모듈."""

import os
import sys

from dotenv import load_dotenv


def load_config() -> dict:
    """SLACK_BOT_TOKEN, SLACK_CHANNEL_ID, ANTHROPIC_API_KEY, TIMEZONE 로드.

    필수 변수 누락 시 명확한 에러 메시지와 함께 종료.
    """
    # 로컬 개발 시 .env 파일 로드 (Cloud Run에서는 환경 변수가 직접 주입됨)
    load_dotenv()

    required = ["SLACK_BOT_TOKEN", "SLACK_CHANNEL_ID", "ANTHROPIC_API_KEY"]
    missing = [key for key in required if not os.environ.get(key)]

    if missing:
        print(f"[ERROR] 필수 환경 변수 누락: {', '.join(missing)}", file=sys.stderr)
        print("  .env.example을 참고하여 .env 파일을 작성하세요.", file=sys.stderr)
        sys.exit(1)

    return {
        "slack_bot_token": os.environ["SLACK_BOT_TOKEN"],
        "slack_channel_id": os.environ["SLACK_CHANNEL_ID"],
        "anthropic_api_key": os.environ["ANTHROPIC_API_KEY"],
        "timezone": os.environ.get("TIMEZONE", "Asia/Seoul"),
    }
