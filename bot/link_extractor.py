"""메시지에서 URL을 추출하고, 각 URL의 메타데이터(제목)를 파싱하는 모듈."""

import re

import requests
from bs4 import BeautifulSoup

# Slack 메시지 내 URL 패턴: <https://example.com> 또는 <https://example.com|표시텍스트>
_SLACK_URL_PATTERN = re.compile(r"<(https?://[^|>]+)(?:\|[^>]*)?>")

# 일반 URL 패턴 (Slack 포맷이 아닌 경우 대비)
_PLAIN_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")


def extract_links(messages: list[dict]) -> list[str]:
    """메시지 목록에서 URL을 추출한다.

    Slack 포맷 <http://...|label>을 우선 처리하고,
    일반 URL도 추출한다. 중복 URL은 제거하며 순서를 유지한다.
    """
    seen = set()
    urls = []

    for msg in messages:
        text = msg.get("text", "")

        # Slack 포맷 URL 추출 (우선)
        slack_spans = []
        for match in _SLACK_URL_PATTERN.finditer(text):
            url = match.group(1)
            slack_spans.append((match.start(), match.end()))
            if url not in seen:
                seen.add(url)
                urls.append(url)

        # 일반 URL 추출 (Slack <...> 포맷 범위 밖에서만)
        for match in _PLAIN_URL_PATTERN.finditer(text):
            # Slack 포맷 범위 내 URL은 건너뛴다
            if any(s <= match.start() < e for s, e in slack_spans):
                continue
            url = match.group(0)
            if url not in seen:
                seen.add(url)
                urls.append(url)

    return urls


def fetch_metadata(url: str) -> dict:
    """URL에 접속하여 제목을 추출한다.

    og:title → <title> 태그 순으로 시도.
    타임아웃 5초, 접속 실패 시 URL 자체를 제목으로 사용한다.
    """
    title = url  # 기본값: URL 자체

    try:
        resp = requests.get(url, timeout=5, headers={"User-Agent": "SlackNewsSumBot/1.0"})
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # og:title 우선 시도
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
        elif soup.title and soup.title.string:
            title = soup.title.string.strip()

    except (requests.RequestException, Exception):
        # 접속 실패 시 URL을 제목으로 사용 (에러 무시)
        pass

    return {"url": url, "title": title}
