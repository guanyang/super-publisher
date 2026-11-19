#!/usr/bin/env python3
"""Package the exact static assets from a cover preview directory."""

import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
from tempfile import TemporaryDirectory
import unicodedata
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import ImageCms

from build_cover import CHARMS, validate_upload


class ReviewImages(HTMLParser):
    def __init__(self, page):
        super().__init__()
        self.sources = set()
        self.feed(page)
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            self.sources.add(dict(attrs).get("src"))


def package_review(page, filenames):
    if "data:image/" in page or ReviewImages(page).sources != set(filenames):
        raise ValueError("Review must reference exactly the local preview JPG and selected PNGs")
    page = re.sub(r'''(\bsrc\s*=\s*)(["'])([^"']+)\2''',
                  lambda match: match[1] + match[2] + filenames.get(match[3], match[3]) + match[2],
                  page, flags=re.IGNORECASE)
    if ReviewImages(page).sources != set(filenames.values()):
        raise ValueError("Could not resolve the packaged review image references")
    return page


def pack_cover(preview, output, sources=()):
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Choose a new output directory instead of {output}")

    filenames = {"preview.jpg": "cover.jpg"}
    cover = (preview / "preview.jpg").read_bytes()
    validate_upload(cover)
    uploads = {"cover.jpg": cover}
    for kind in CHARMS:
        filename = f"{kind}-charm-preview.png"
        source = preview / filename
        if source.exists():
            target = f"{kind}-charm.png"
            data = source.read_bytes()
            try:
                validate_upload(data, charm=kind)
            except (OSError, ValueError, ImageCms.PyCMSError) as error:
                raise ValueError(f"{filename} — {error}") from error
            filenames[filename] = target
            uploads[target] = data
    page = package_review((preview / "review.html").read_text(encoding="utf-8"), filenames)

    output.parent.mkdir(parents=True, exist_ok=True)
    src_names = set()
    with TemporaryDirectory(prefix=".cover-pack-", dir=output.parent) as temporary:
        stage = Path(temporary) / "pack"
        stage.mkdir()
        for name, data in uploads.items():
            (stage / name).write_bytes(data)
        (stage / "review.html").write_text(page, encoding="utf-8")
        members = [*uploads, "review.html"]
        if sources:
            (stage / "sources").mkdir()
        for source in sources:
            name = source.name
            key = unicodedata.normalize("NFC", name).casefold()
            if not name or "\\" in name or key in src_names:
                raise ValueError(f"Choose distinct source filenames. Invalid or duplicate name {name}")
            src_names.add(key)
            member = f"sources/{name}"
            shutil.copyfile(source, stage / member)
            members.append(member)

        with ZipFile(stage / "cover-pack.zip", "x", compression=ZIP_DEFLATED) as archive:
            for member in members:
                archive.write(stage / member, arcname=member)
        with ZipFile(stage / "cover-pack.zip") as archive:
            if archive.namelist() != members or archive.testzip() is not None:
                raise ValueError("ZIP verification failed")
            if any(archive.read(name) != data for name, data in uploads.items()):
                raise ValueError("Packaged upload files differ from the preview")
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Choose a new output directory instead of {output}")
        stage.rename(output)

    return {"zip": str(output / "cover-pack.zip"), "review": str(output / "review.html"),
            "uploads": [str(output / name) for name in uploads]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preview", type=Path, help="Directory produced by --preview-only")
    parser.add_argument("--output", type=Path, required=True, help="New package directory")
    parser.add_argument("--source", type=Path, action="append", default=[], help="Source file to include; repeat as needed")
    args = parser.parse_args()
    try:
        result = pack_cover(args.preview, args.output.absolute(), args.source)
    except (OSError, ValueError, ImageCms.PyCMSError) as error:
        parser.exit(2, f"{error}\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
