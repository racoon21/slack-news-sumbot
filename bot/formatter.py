"""Slack mrkdwn 형식으로 뉴스 요약 표를 생성하는 모듈."""


def format_summary(articles: list[dict], date_str: str) -> str:
    """기사 목록을 Slack mrkdwn 표 형식으로 변환한다.

    기사 0건이면 '공유된 뉴스가 없습니다' 메시지를 반환.
    각 article dict에는 title, url, summary 필드가 필요하다.
    """
    if not articles:
        return f":newspaper: *전날 관련동향 뉴스 요약* ({date_str})\n\n_공유된 뉴스가 없습니다._"

    lines = [
        f":newspaper: *전날 관련동향 뉴스 요약* ({date_str})",
        "",
    ]

    for i, article in enumerate(articles, 1):
        title = article.get("title", "-")
        summary = article.get("summary", "-")
        url = article.get("url", "")
        lines.append(f"*{i}.* <{url}|{title}>")
        lines.append(f"    _{summary}_")
        lines.append("")

    lines.append(f"_총 {len(articles)}건의 뉴스가 공유되었습니다._")

    return "\n".join(lines)
