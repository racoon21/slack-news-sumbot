"""link_extractor 모듈 단위 테스트."""

from bot.link_extractor import extract_links


def test_extract_slack_format_urls():
    """Slack 포맷 <url|label> 에서 URL을 추출한다."""
    messages = [
        {"text": "이 기사 참고하세요 <https://example.com/news1|뉴스1>"},
        {"text": "<https://example.com/news2>"},
    ]
    urls = extract_links(messages)
    assert urls == ["https://example.com/news1", "https://example.com/news2"]


def test_extract_plain_urls():
    """일반 URL도 추출한다."""
    messages = [{"text": "https://example.com/plain-url 참고"}]
    urls = extract_links(messages)
    assert urls == ["https://example.com/plain-url"]


def test_dedup_urls():
    """중복 URL은 제거한다."""
    messages = [
        {"text": "<https://example.com/dup>"},
        {"text": "<https://example.com/dup> 다시 공유"},
    ]
    urls = extract_links(messages)
    assert urls == ["https://example.com/dup"]


def test_empty_messages():
    """메시지가 없으면 빈 리스트를 반환한다."""
    assert extract_links([]) == []


def test_no_urls_in_message():
    """URL이 없는 메시지는 건너뛴다."""
    messages = [{"text": "오늘 날씨 좋네요"}]
    assert extract_links(messages) == []


def test_mixed_messages():
    """URL이 있는 메시지와 없는 메시지가 섞여있어도 정상 동작."""
    messages = [
        {"text": "안녕하세요"},
        {"text": "<https://example.com/a|기사A>"},
        {"text": "텍스트만"},
        {"text": "<https://example.com/b>"},
    ]
    urls = extract_links(messages)
    assert urls == ["https://example.com/a", "https://example.com/b"]
