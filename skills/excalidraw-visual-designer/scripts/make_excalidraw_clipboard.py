#!/usr/bin/env python3
"""Convert a generic scene spec into Excalidraw clipboard JSON."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import random
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote


def element_id(prefix: str = "e") -> str:
    suffix = f"{random.randrange(36**10):010x}{int(time.time() * 1000):x}"
    return f"{prefix}{suffix}"[:21]


class Builder:
    def __init__(self) -> None:
        self.index = 0

    def next_index(self) -> str:
        self.index += 1
        return f"a{self.index:03d}"

    def base(self, item: dict[str, Any]) -> dict[str, Any]:
        kind = item["type"]
        return {
            "id": item.get("id") or element_id(kind[0]),
            "type": kind,
            "x": item.get("x", 0),
            "y": item.get("y", 0),
            "width": item.get("width", 100),
            "height": item.get("height", 100),
            "angle": item.get("angle", 0),
            "strokeColor": item.get("strokeColor", "#1e1e1e"),
            "backgroundColor": item.get("backgroundColor", "transparent"),
            "fillStyle": item.get("fillStyle", "solid"),
            "strokeWidth": item.get("strokeWidth", 2),
            "strokeStyle": item.get("strokeStyle", "solid"),
            "roughness": item.get("roughness", 1),
            "opacity": item.get("opacity", 100),
            "groupIds": item.get("groupIds", []),
            "frameId": item.get("frameId"),
            "index": item.get("index") or self.next_index(),
            "roundness": item.get("roundness", {"type": 3} if kind == "rectangle" else None),
            "seed": item.get("seed", random.randrange(2**31)),
            "version": item.get("version", 1),
            "versionNonce": item.get("versionNonce", random.randrange(2**31)),
            "isDeleted": item.get("isDeleted", False),
            "boundElements": item.get("boundElements"),
            "updated": item.get("updated", int(time.time() * 1000)),
            "link": item.get("link"),
            "locked": item.get("locked", False),
        }

    def build(self, item: dict[str, Any], files: dict[str, Any]) -> dict[str, Any]:
        kind = item.get("type")
        if kind not in {"rectangle", "ellipse", "diamond", "text", "line", "arrow", "image"}:
            raise ValueError(f"Unsupported element type: {kind}")

        if kind == "text":
            return self.text(item)
        if kind in {"line", "arrow"}:
            return self.linear(item)
        if kind == "image":
            return self.image(item, files)

        return self.base(item)

    def text(self, item: dict[str, Any]) -> dict[str, Any]:
        text_value = item.get("text", "")
        element = self.base(
            {
                "width": max(120, item.get("width", 300)),
                "height": max(32, item.get("height", 40)),
                **item,
            }
        )
        element.update(
            {
                "text": text_value,
                "fontSize": item.get("fontSize", 24),
                "fontFamily": item.get("fontFamily", 2),
                "textAlign": item.get("textAlign", "left"),
                "verticalAlign": item.get("verticalAlign", "top"),
                "containerId": item.get("containerId"),
                "originalText": item.get("originalText", text_value),
                "autoResize": item.get("autoResize", False),
                "lineHeight": item.get("lineHeight", 1.25),
            }
        )
        return element

    def linear(self, item: dict[str, Any]) -> dict[str, Any]:
        points = item.get("points")
        if not isinstance(points, list) or len(points) < 2:
            raise ValueError("line and arrow elements require at least two points")

        element = self.base({"width": 1, "height": 1, **item})
        element.update(
            {
                "points": points,
                "lastCommittedPoint": item.get("lastCommittedPoint"),
                "startBinding": item.get("startBinding"),
                "endBinding": item.get("endBinding"),
                "startArrowhead": item.get("startArrowhead"),
                "endArrowhead": item.get("endArrowhead", "arrow" if item["type"] == "arrow" else None),
            }
        )
        return element

    def image(self, item: dict[str, Any], files: dict[str, Any]) -> dict[str, Any]:
        file_id = item.get("fileId") or element_id("file")
        if file_id not in files:
            files[file_id] = make_file(file_id, item)

        element = self.base(item)
        element.update(
            {
                "fileId": file_id,
                "scale": item.get("scale", [1, 1]),
                "status": item.get("status", "saved"),
            }
        )
        return element


def make_file(file_id: str, item: dict[str, Any]) -> dict[str, Any]:
    if item.get("dataURL"):
        data_url = item["dataURL"]
        mime_type = data_url.split(";", 1)[0].removeprefix("data:")
    elif item.get("svg"):
        mime_type = "image/svg+xml"
        data_url = "data:image/svg+xml;charset=utf-8," + quote(item["svg"])
    elif item.get("path"):
        path = Path(item["path"])
        mime_type = item.get("mimeType") or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        raw = path.read_bytes()
        if mime_type == "image/svg+xml":
            data_url = "data:image/svg+xml;charset=utf-8," + quote(raw.decode("utf-8"))
        else:
            data_url = f"data:{mime_type};base64,{base64.b64encode(raw).decode('ascii')}"
    else:
        raise ValueError("image elements require dataURL, svg, path, or an existing fileId")

    now = int(time.time() * 1000)
    return {
        "id": file_id,
        "mimeType": mime_type,
        "dataURL": data_url,
        "created": item.get("created", now),
        "lastRetrieved": item.get("lastRetrieved", now),
    }


def load_spec(path: str | None) -> dict[str, Any]:
    if not path:
        return {"elements": [], "files": {}}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_clipboard(spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("type") == "excalidraw/clipboard":
        spec.setdefault("elements", [])
        spec.setdefault("files", {})
        return spec

    files = dict(spec.get("files", {}))
    builder = Builder()
    elements = [builder.build(item, files) for item in spec.get("elements", [])]
    return {"type": "excalidraw/clipboard", "elements": elements, "files": files}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a generic scene spec into Excalidraw clipboard JSON."
    )
    parser.add_argument("--spec", help="Path to a generic scene spec JSON file.")
    parser.add_argument("--output", help="Write clipboard JSON to this path. Defaults to stdout.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_clipboard(load_spec(args.spec))
    text = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2 if args.pretty else None,
        separators=None if args.pretty else (",", ":"),
    )
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
