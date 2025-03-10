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

    # section 태그 찾기, 없으면 body나 루트 요소 사용
    main_element = soup.find("section")
    if not main_element:
        main_element = soup.find("body") or soup

    # 테이블 처리 함수
    def process_table(table):
        result = []

        # 테이블 헤더 처리
        headers = []
        header_aligns = []

        thead = table.find("thead")
        if thead:
            th_row = thead.find("tr")
            if th_row:
                for th in th_row.find_all(["th", "td"]):
                    # 헤더 텍스트 추출
                    header_text = "".join(
                        process_element(child) for child in th.children
                    ).strip()
                    headers.append(header_text)

                    # 정렬 속성 처리
                    align = th.get("align", "").lower()
                    if align == "center":
                        header_aligns.append(":---:")
                    elif align == "right":
                        header_aligns.append("---:")
                    elif align == "left":
                        header_aligns.append(":---")
                    else:
                        header_aligns.append("---")

        # 헤더가 없을 경우 첫 번째 행에서 추출
        if not headers:
            first_row = table.find("tr")
            if first_row:
                for cell in first_row.find_all(["th", "td"]):
                    # 헤더 텍스트 추출
                    header_text = "".join(
                        process_element(child) for child in cell.children
                    ).strip()
                    headers.append(header_text)

                    # 정렬 속성 처리
                    align = cell.get("align", "").lower()
                    if align == "center":
                        header_aligns.append(":---:")
                    elif align == "right":
                        header_aligns.append("---:")
                    elif align == "left":
                        header_aligns.append(":---")
                    else:
                        header_aligns.append("---")

        # 헤더 행 문자열 생성
        if headers:
            result.append("| " + " | ".join(headers) + " |")
            result.append("| " + " | ".join(header_aligns) + " |")

        # 테이블 본문 처리
        tbody = table.find("tbody") or table
        for tr in tbody.find_all("tr"):
            # thead의 tr은 이미 처리했으므로 건너뛰기
            if thead and tr.parent == thead:
                continue

            # 첫 번째 행을 헤더로 사용했을 경우 건너뛰기
            if not headers and tr == table.find("tr"):
                continue

            row_cells = []
            for cell in tr.find_all(["td", "th"]):
                cell_content = "".join(
                    process_element(child) for child in cell.children
                ).strip()
                # 파이프 문자가 있으면 이스케이프 처리
                cell_content = cell_content.replace("|", "\\|")
                row_cells.append(cell_content)

            result.append("| " + " | ".join(row_cells) + " |")

        return "\n".join(result) + "\n\n"

    # 재귀적으로 요소를 처리하는 함수
    def process_element(element):
        nonlocal markdown

        if element.name is None:  # 텍스트 노드인 경우
            if str(element).strip():
                return str(element).strip()
            return ""

        # 테이블 태그
        elif element.name == "table":
            return process_table(element)

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
        elif element.name == "strong" or element.name == "b":
            return (
                f"**{''.join(process_element(child) for child in element.children)}**"
            )

        # 기울임 태그
        elif element.name == "em" or element.name == "i":
            return f"*{''.join(process_element(child) for child in element.children)}*"

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

        # 순서 있는 리스트 태그
        elif element.name == "ol":
            list_items = []
            for idx, li in enumerate(element.find_all("li", recursive=False), 1):
                item_content = "".join(process_element(child) for child in li.children)
                list_items.append(f"{idx}. {item_content}")
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

        # 테이블 관련 태그들은 테이블 처리 시 함께 처리됨
        elif element.name in ["thead", "tbody", "tr", "th", "td"]:
            return "".join(process_element(child) for child in element.children)

        # 기타 태그는 재귀적으로 처리
        else:
            return "".join(process_element(child) for child in element.children)

    # 루트 요소 내부의 모든 요소 처리
    if main_element.name == "section" or main_element.name == "body":
        for child in main_element.children:
            markdown += process_element(child)
    else:  # 루트 요소가 테이블이나 다른 요소인 경우
        markdown += process_element(main_element)

    # 연속된 빈 줄 제거
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)

    return markdown.strip()


# 테스트 함수
def test_conversion():
    # 테이블 샘플 테스트
    table_html = """
    <table>
    <thead>
    <tr>
    <th align="left">타입</th>
    <th align="left">설명</th>
    </tr>
    </thead>
    <tbody>
    <tr>
    <td align="left">feat</td>
    <td align="left">새로운 기능 추가</td>
    </tr>
    <tr>
    <td align="left">fix</td>
    <td align="left">버그 수정</td>
    </tr>
    <tr>
    <td align="left">docs</td>
    <td align="left">문서 수정</td>
    </tr>
    <tr>
    <td align="left">style</td>
    <td align="left">공백, 세미콜론 등 스타일 수정</td>
    </tr>
    <tr>
    <td align="left">refactor</td>
    <td align="left">코드 리팩토링</td>
    </tr>
    <tr>
    <td align="left">perf</td>
    <td align="left">성능 개선</td>
    </tr>
    <tr>
    <td align="left">test</td>
    <td align="left">테스트 추가</td>
    </tr>
    <tr>
    <td align="left">chore</td>
    <td align="left">빌드 과정 또는 보조 기능(문서 생성기능 등) 수정</td>
    </tr>
    </tbody>
    </table>
    """

    print("테이블 테스트 결과:")
    print(html_to_obsidian_markdown(table_html))
    print("\n" + "-" * 50 + "\n")

    # 기존 샘플 테스트
    section_html = """
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

    print("Section 테스트 결과:")
    print(html_to_obsidian_markdown(section_html))


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
