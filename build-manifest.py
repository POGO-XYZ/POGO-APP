#!/usr/bin/env python3
"""
POGO-APP — manifest builder

Reads the local archive and media repositories and writes manifest.json:
a single flat file describing every archived work.

The app loads that one file instead of querying the GitHub API repeatedly,
which removes the rate limit, loads faster, and works even if the API is
unavailable. Run this after archiving new works, then commit manifest.json
alongside them.

Usage
-----
    python3 build-manifest.py

Assumes the three repositories sit side by side:

    POGO/
    ├── POGO-ARCHIVE/
    ├── POGO-ARCHIVE-MEDIA/
    └── POGO-APP/            <- run from here

If they live elsewhere, pass the paths:

    python3 build-manifest.py --archive ../POGO-ARCHIVE --media ../POGO-ARCHIVE-MEDIA
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

RAW = "https://raw.githubusercontent.com/POGO-XYZ/{repo}/main/{path}"
YEAR_DIR = re.compile(r"^\d{4}$")
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def raw_url(repo, path):
    return RAW.format(repo=repo, path=str(path).replace("\\", "/"))


def event_date(record, kind):
    for event in record.get("events") or []:
        if event.get("type") == kind:
            return event.get("date", "")
    return ""


def file_entry(record, role):
    for entry in record.get("files") or []:
        if entry.get("role") == role:
            return entry
    return {}


THUMB_DIR = Path("thumbs")
THUMB_PX = 480
THUMB_QUALITY = 72


def build_thumb(source_path, work_id):
    """Small WebP copy for grid views. Full images stay untouched."""
    if Image is None:
        return None
    THUMB_DIR.mkdir(exist_ok=True)
    out = THUMB_DIR / (work_id + ".webp")
    if out.exists() and out.stat().st_mtime >= source_path.stat().st_mtime:
        return out.as_posix()
    try:
        with Image.open(source_path) as im:
            im = im.convert("RGB")
            im.thumbnail((THUMB_PX, THUMB_PX), Image.LANCZOS)
            im.save(out, "WEBP", quality=THUMB_QUALITY, method=6)
        return out.as_posix()
    except Exception:
        return None


def collect_media(media_root):
    """Map uppercase POGO ID -> raw media URL."""
    index = {}
    if not media_root.is_dir():
        return index
    for year_dir in sorted(media_root.iterdir()):
        if not (year_dir.is_dir() and YEAR_DIR.match(year_dir.name)):
            continue
        for path in sorted(year_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in IMAGE_EXT:
                key = path.stem.upper()
                index[key] = {
                    "url": raw_url("POGO-ARCHIVE-MEDIA", f"{year_dir.name}/{path.name}"),
                    "path": path,
                }
    return index


def collect_works(archive_root, media_index):
    works = []
    problems = []

    for year_dir in sorted(archive_root.iterdir(), reverse=True):
        if not (year_dir.is_dir() and YEAR_DIR.match(year_dir.name)):
            continue
        year = year_dir.name
        records_dir = year_dir / f"records-{year}"
        if not records_dir.is_dir():
            continue

        for path in sorted(records_dir.iterdir()):
            if not (path.is_file() and path.suffix.lower() == ".json"):
                continue
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                problems.append(f"{path.name}: invalid JSON ({exc})")
                continue

            work_id = path.stem.upper()
            source = file_entry(record, "reference_image_source")
            web = file_entry(record, "reference_image_web")
            media = media_index.get(work_id)
            media_url = media["url"] if media else None
            thumb_url = build_thumb(media["path"], work_id) if media else None

            if not media_url:
                problems.append(f"{work_id}: no media file found")

            works.append(
                {
                    "id": work_id,
                    "year": record.get("year", year),
                    "title": record.get("title", ""),
                    "medium": record.get("medium", ""),
                    "dimensions": record.get("dimensions", ""),
                    "focus": record.get("focus", ""),
                    "series": record.get("series", ""),
                    "type_code": record.get("type_code", ""),
                    "sequence": record.get("sequence", ""),
                    "schema_version": record.get("schema_version", ""),
                    "created": event_date(record, "creation"),
                    "archived": event_date(record, "archival"),
                    "source_sha256": (source.get("sha256") or "").lower(),
                    "web_sha256": (web.get("sha256") or "").lower(),
                    "record_url": raw_url(
                        "POGO-ARCHIVE", f"{year}/records-{year}/{path.name}"
                    ),
                    "media_url": media_url,
                    "thumb_url": thumb_url,
                }
            )

    return works, problems


def main():
    parser = argparse.ArgumentParser(description="Build the POGO-APP manifest.")
    parser.add_argument("--archive", default="../POGO-ARCHIVE")
    parser.add_argument("--media", default="../POGO-ARCHIVE-MEDIA")
    parser.add_argument("--out", default="manifest.json")
    args = parser.parse_args()

    archive_root = Path(args.archive).resolve()
    media_root = Path(args.media).resolve()

    if not archive_root.is_dir():
        sys.exit(f"Archive not found: {archive_root}")

    media_index = collect_media(media_root)
    works, problems = collect_works(archive_root, media_index)

    if not works:
        sys.exit("No records found — check the archive path.")

    manifest = {
        "generated": date.today().isoformat(),
        "count": len(works),
        "years": sorted({w["year"] for w in works}, reverse=True),
        "works": works,
    }

    out_path = Path(args.out)
    out_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"Wrote {out_path} — {len(works)} works across {len(manifest['years'])} years")
    if Image is None:
        print("\nPillow not installed — thumbnails were skipped and grids will")
        print("load full-size images. Install it with:  pip3 install pillow")
    else:
        made = sum(1 for w in works if w.get("thumb_url"))
        print(f"Thumbnails: {made} in ./thumbs/")
    orphans = set(media_index) - {w["id"] for w in works}
    if orphans:
        problems.extend(f"{i}: media file with no matching record" for i in sorted(orphans))
    if problems:
        print(f"\n{len(problems)} issue(s) to review:")
        for line in problems:
            print(f"  - {line}")


if __name__ == "__main__":
    main()
