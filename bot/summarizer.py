"""Claude API를 사용하여 뉴스 기사를 한줄 요약하는 모듈."""

import json

import anthropic


def summarize_articles(api_key: str, articles: list[dict]) -> list[dict]:
    """여러 기사를 한번의 Claude API 호출로 일괄 요약한다.

    비용 절감을 위해 단일 프롬프트로 모든 기사를 처리.
    각 기사의 dict에 'summary' 필드를 추가하여 반환.
    API 호출 실패 시 요약 없이 제목만 반환한다.
    """
    if not articles:
        return articles

    # 기사 목록을 번호 매긴 텍스트로 구성
    article_list = "\n".join(
        f"{i + 1}. 제목: {a['title']}\n   URL: {a['url']}"
        for i, a in enumerate(articles)
    )

    prompt = f"""다음 뉴스 기사들을 각각 한 줄(30자 이내)로 요약해주세요.
반드시 아래 JSON 배열 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.

기사 목록:
{article_list}

응답 형식 (JSON 배열만):
[
  {{"index": 1, "summary": "요약 내용"}},
  {{"index": 2, "summary": "요약 내용"}}
]"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        # 응답에서 JSON 파싱
        response_text = message.content[0].text.strip()
        summaries = json.loads(response_text)

        # index 기반으로 매핑
        summary_map = {s["index"]: s["summary"] for s in summaries}
        for i, article in enumerate(articles):
            article["summary"] = summary_map.get(i + 1, "요약 실패")

    except (anthropic.APIError, json.JSONDecodeError, KeyError, Exception):
        # API 호출 실패 시 요약 없이 반환
        for article in articles:
            article.setdefault("summary", "요약 실패")

    return articles
