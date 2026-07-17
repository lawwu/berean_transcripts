"""Preserve legacy GitHub Pages URLs after the frontend migration."""

import argparse
import html
from pathlib import Path


def redirect_document(target: str, canonical_url: str) -> str:
    escaped_target = html.escape(target, quote=True)
    escaped_canonical = html.escape(canonical_url, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url={escaped_target}">
<link rel="canonical" href="{escaped_canonical}">
<title>Redirecting…</title>
</head>
<body><p><a href="{escaped_target}">Continue to the sermon transcript</a>.</p></body>
</html>
"""


def write_legacy_redirects(out_dir: Path, site_url: str) -> int:
    sermons_dir = out_dir / "sermons"
    site_url = site_url.rstrip("/")
    count = 0
    for sermon_path in sorted(sermons_dir.glob("*.html")):
        target = f"sermons/{sermon_path.name}"
        canonical = f"{site_url}/{target}" if site_url else target
        document = redirect_document(target, canonical)
        (out_dir / sermon_path.name).write_text(document, encoding="utf-8")
        (out_dir / f"transcript_{sermon_path.name}").write_text(
            document, encoding="utf-8"
        )
        count += 2

    archive_target = "index.html#archive"
    archive_canonical = f"{site_url}/#archive" if site_url else archive_target
    (out_dir / "legacy_index.html").write_text(
        redirect_document(archive_target, archive_canonical), encoding="utf-8"
    )
    return count + 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add redirects for the legacy Berean page layout."
    )
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--site-url", default="")
    args = parser.parse_args()
    count = write_legacy_redirects(args.out_dir, args.site_url)
    print(f"legacy redirects: {count}")


if __name__ == "__main__":
    main()
