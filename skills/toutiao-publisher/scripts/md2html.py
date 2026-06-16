import re
from dataclasses import dataclass
from pathlib import Path


IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


@dataclass
class ConvertedMarkdown:
    html: str
    images: list[dict[str, str]]


def _resolve_image_path(raw_path, base_dir):
    cleaned = raw_path.strip().strip("<>").strip("\"'")
    if cleaned.startswith(("http://", "https://", "data:")):
        return cleaned
    base = Path(base_dir or ".")
    image_path = Path(cleaned)
    if not image_path.is_absolute():
        image_path = base / image_path
    return str(image_path.resolve())


def _replace_markdown_images(line, images, base_dir):
    def replace(match):
        placeholder = f"TTIMGPH_{len(images)}"
        images.append(
            {
                "placeholder": placeholder,
                "path": _resolve_image_path(match.group(2), base_dir),
                "alt": match.group(1).strip(),
            }
        )
        return placeholder

    return IMAGE_PATTERN.sub(replace, line)


def convert_with_images(text, base_dir=None):
    """
    Simple Markdown to HTML converter for Toutiao.
    Handles headers, code blocks, lists, and basic formatting.
    """
    lines = text.split("\n")
    html = []
    images = []
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

        line = _replace_markdown_images(line, images, base_dir)
        stripped = line.strip()

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

    return ConvertedMarkdown(html="\n".join(html), images=images)


def convert(text):
    return convert_with_images(text).html


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
