from bs4 import BeautifulSoup
import re


def html_to_obsidian_markdown(html_content):
    """
    HTML 내용을 Obsidian Markdown 형식으로 변환합니다.

    Args:
        html_content (str): 변환할 HTML 문자열

    Returns:
        str: 변환된 Obsidian Markdown 문자열
    """
    # BeautifulSoup 객체 생성
    soup = BeautifulSoup(html_content, "html.parser")

    # 최종 마크다운 결과물
    markdown = ""

    # section 태그 찾기
    section = soup.find("section")
    if not section:
        return "변환할 section 태그를 찾을 수 없습니다."

    # 재귀적으로 요소를 처리하는 함수
    def process_element(element):
        nonlocal markdown

        if element.name is None:  # 텍스트 노드인 경우
            if element.strip():
                return element.strip()
            return ""

        # 헤더 태그 (h1~h6)
        elif re.match(r"h[1-6]", element.name):
            level = int(element.name[1])
            header_text = "".join(process_element(child) for child in element.children)
            return f"{'#' * level} {header_text}\n\n"

        # 문단 태그
        elif element.name == "p":
            paragraph_text = "".join(
                process_element(child) for child in element.children
            )
            return f"{paragraph_text}\n\n"

        # 강조 태그
        elif element.name == "strong":
            return (
                f"**{''.join(process_element(child) for child in element.children)}**"
            )

        # 인라인 코드 태그
        elif element.name == "code":
            return f"`{''.join(process_element(child) for child in element.children)}`"

        # 링크 태그
        elif element.name == "a":
            text = "".join(process_element(child) for child in element.children)
            href = element.get("href", "")
            return f"[{text}]({href})"

        # 리스트 태그
        elif element.name == "ul":
            list_items = []
            for li in element.find_all("li", recursive=False):
                item_content = "".join(process_element(child) for child in li.children)
                list_items.append(f"- {item_content}")
            return "\n".join(list_items) + "\n\n"

        # 코드 블록 태그 (deckgo-highlight-code)
        elif element.name == "deckgo-highlight-code":
            code_slot = element.find("code", {"slot": "code"})
            if code_slot:
                code_content = code_slot.get_text()
                language = element.get("language", "")
                return f"```{language}\n{code_content}\n```\n\n"
            return ""

        # 수평선 태그
        elif element.name == "hr":
            return "---\n\n"

        # 줄바꿈 태그
        elif element.name == "br":
            return "\n"

        # 기타 태그는 재귀적으로 처리
        else:
            return "".join(process_element(child) for child in element.children)

    # section 내부의 모든 요소 처리
    for child in section.children:
        markdown += process_element(child)

    # 연속된 빈 줄 제거
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)

    return markdown.strip()


# 테스트 함수
def test_conversion():
    sample_html = """
    <section><h2>git <strong>help</strong></h2>
    <p>Git 사용 중 모르는 부분이 있을 때 도움을 받을 수 있는 기능</p>
    <deckgo-highlight-code language="bash" terminal="carbon" theme="material" class="deckgo-highlight-code-carbon deckgo-highlight-code-theme-material hydrated">
              <code slot="code">git help</code>
            </deckgo-highlight-code>
    <ul>
    <li>기본적인 명령어들과 설명</li>
    </ul>
    <br>
    <deckgo-highlight-code language="bash" terminal="carbon" theme="material" class="deckgo-highlight-code-carbon deckgo-highlight-code-theme-material hydrated">
              <code slot="code">git help -a</code>
            </deckgo-highlight-code>
    <ul>
    <li>Git의 모든 명령어들</li>
    <li><code>j</code>로 내리기, <code>k</code>로 올리기, <code>:q</code>로 닫기</li>
    </ul>
    <br>
    <deckgo-highlight-code language="bash" terminal="carbon" theme="material" class="deckgo-highlight-code-carbon deckgo-highlight-code-theme-material hydrated">
              <code slot="code">git (명령어) -h</code>
            </deckgo-highlight-code>
    <ul>
    <li>해당 명령어의 설명과 옵션 보기</li>
    </ul>
    <br>
    <deckgo-highlight-code language="bash" terminal="carbon" theme="material" class="deckgo-highlight-code-carbon deckgo-highlight-code-theme-material hydrated">
              <code slot="code">git help (명령어)</code>
            </deckgo-highlight-code>
    <deckgo-highlight-code language="bash" terminal="carbon" theme="material" class="deckgo-highlight-code-carbon deckgo-highlight-code-theme-material hydrated">
              <code slot="code">git (명령어) --help</code>
            </deckgo-highlight-code>
    <ul>
    <li>해당 명령어의 설명과 옵션 웹사이트에서 보기</li>
    <li>⭐️ 웹에서 열리지 않을 시 끝에 <code>-w</code>를 붙여 명시</li>
    </ul>
    <br>
    <hr>
    <br>
    <h2>Git 문서</h2>
    <ul>
    <li><a href="https://git-scm.com/docs" target="_blank">Git 문서 보기</a></li>
    <li><a href="https://git-scm.com/book/ko/v2" target="_blank">Pro Git 책 보기</a></li>
    </ul></section>
    """

    result = html_to_obsidian_markdown(sample_html)
    print(result)


# 변환 기능 실행 코드 추가
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # 파일에서 HTML 읽기
        with open(sys.argv[1], "r", encoding="utf-8") as file:
            html_content = file.read()

        markdown_content = html_to_obsidian_markdown(html_content)

        # 결과를 파일에 저장할 경우
        if len(sys.argv) > 2:
            with open(sys.argv[2], "w", encoding="utf-8") as file:
                file.write(markdown_content)
        else:
            # 콘솔에 출력
            print(markdown_content)
    else:
        # 테스트 실행
        test_conversion()
