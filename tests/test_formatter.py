"""formatter 모듈 단위 테스트."""

from bot.formatter import format_summary


def test_format_with_articles():
    """기사가 있으면 번호, 제목(링크), 요약을 포함한다."""
    articles = [
        {"title": "테스트 뉴스", "url": "https://example.com/1", "summary": "테스트 요약"},
    ]
    result = format_summary(articles, "2026-03-10")
    assert ":newspaper:" in result
    assert "2026-03-10" in result
    assert "<https://example.com/1|테스트 뉴스>" in result
    assert "테스트 요약" in result
    assert "총 1건" in result


def test_format_empty_articles():
    """기사 0건이면 '공유된 뉴스가 없습니다'를 반환한다."""
    result = format_summary([], "2026-03-10")
    assert "공유된 뉴스가 없습니다" in result
    assert "2026-03-10" in result


def test_format_multiple_articles():
    """여러 기사가 순서대로 번호 매겨진다."""
    articles = [
        {"title": "뉴스A", "url": "https://a.com", "summary": "요약A"},
        {"title": "뉴스B", "url": "https://b.com", "summary": "요약B"},
        {"title": "뉴스C", "url": "https://c.com", "summary": "요약C"},
    ]
    result = format_summary(articles, "2026-03-10")
    assert "*1.*" in result
    assert "*2.*" in result
    assert "*3.*" in result
    assert "총 3건" in result
