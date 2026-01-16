import re


def convert(text):
    """
    Simple Markdown to HTML converter for Toutiao.
    Handles headers, code blocks, lists, and basic formatting.
    """
    lines = text.split("\n")
    html = []
    in_code_block = False
    in_list = False

    for line in lines:
        stripped = line.strip()

        # Code blocks
        if stripped.startswith("```"):
            if in_code_block:
                html.append("</code></pre>")
                in_code_block = False
            else:
                html.append("<pre><code>")
                in_code_block = True
            continue

        if in_code_block:
            import html as html_lib

            # Escape code content
            safe_line = html_lib.escape(line)
            html.append(
                f"{safe_line}<br>"
            )  # Use br for newlines in code for some editors
            continue

        # List handling logic (exit list if empty line or header)
        if in_list and (not stripped or stripped.startswith("#")):
            html.append("</ul>")
            in_list = False

        # Headers
        if line.startswith("#"):
            # Close list if open
            if in_list:
                html.append("</ul>")
                in_list = False

            level = len(line.split()[0])
            # Max h6
            if level > 6:
                level = 6
            content = line[level:].strip()
            html.append(f"<h{level}>{content}</h{level}>")
            continue

        # Lists ( * or - or 1.)
        # Simplified: treat all as ul for now or simple lists
        is_list_item = stripped.startswith("* ") or stripped.startswith("- ")

        if is_list_item:
            if not in_list:
                html.append("<ul>")
                in_list = True
            content = stripped[2:]
            # Bold formatting inside list
            content = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", content)
            html.append(f"<li>{content}</li>")
            continue

        # Paragraphs
        if stripped:
            # If we're not in a list or code block, it's a paragraph
            if not in_list:
                # Bold formatting
                line_content = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", stripped)
                html.append(f"<p>{line_content}</p>")
            else:
                # Continuation of list? Or close it?
                # For simplicity, if we hit non-list text line, close list
                html.append("</ul>")
                in_list = False
                line_content = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", stripped)
                html.append(f"<p>{line_content}</p>")

    if in_list:
        html.append("</ul>")

    return "\n".join(html)


if __name__ == "__main__":
    # Test
    sample = """# Title
    
    Introduction **bold**.
    
    * Item 1
    * Item 2
    
    ```python
    print("Code")
    ```
    """
    print(convert(sample))
