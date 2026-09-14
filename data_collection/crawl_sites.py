"""CLI: crawl configured lyric sites into the work queue (sitemap/pagination)."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from . import config as cfg
from . import state
from .fetch import acceptable
from .http import CachedHttp
from .models import Candidate, LyricsHit
from .normalize import detect_script, lyrics_sha
from .sites import paankopat, songsdiary

SITES = {
    "songsdiary": songsdiary,
    "paankopat": paankopat,
}


def crawl_site(
    conn,
    client: CachedHttp,
    module,
    *,
    limit: int = 0,
    max_pages: int = 20,
    delay: float = 2.0,
) -> dict:
    domain = module.DOMAIN
    stats = {
        "site": domain,
        "discovered": 0,
        "new_pages": 0,
        "processed": 0,
        "hits": 0,
        "duplicates": 0,
        "rejected": 0,
        "parse_failed": 0,
        "fetch_failed": 0,
    }
    urls = module.discover(client, max_pages=max_pages)
    stats["discovered"] = len(urls)
    stats["new_pages"] = state.register_pages(conn, urls, domain=domain)
    rows = state.next_pages(conn, domain=domain, limit=limit or None, status="new")
    print(f"[{domain}] discovered={len(urls)} new_pages={stats['new_pages']} to_process={len(rows)}")
    for index, row in enumerate(rows, start=1):
        url = row["url"]
        html = client.get_text(f"site_{domain}", url)
        if not html:
            state.mark_page(conn, url, "fetch_failed")
            stats["fetch_failed"] += 1
            continue
        page = module.parse(html, url)
        if page is None or not page.lyrics:
            state.mark_page(conn, url, "parse_failed")
            stats["parse_failed"] += 1
            continue
        hit = LyricsHit(
            stage=f"site_{domain}",
            lyrics=page.lyrics,
            source_url=url,
            script=detect_script(page.lyrics),
            sha256=lyrics_sha(page.lyrics),
        )
        ok, reason = acceptable(hit)
        if not ok:
            state.mark_page(conn, url, f"rejected:{reason}")
            stats["rejected"] += 1
            continue
        existing = state.find_by_lyrics_sha(conn, hit.sha256)
        candidate = Candidate(
            source=f"site_{domain}",
            source_id=url,
            artist=page.artist,
            title=page.title,
            extra={"url": url},
        )
        added, _dupes = state.enqueue(conn, [candidate])
        db_row = state.get_by_dedupe_key(conn, candidate.dedupe_key)
        candidate_id = db_row["id"]
        if existing is not None and existing != candidate_id:
            state.mark_page(conn, url, "duplicate", candidate_id=existing, title=page.title, artist=page.artist)
            stats["duplicates"] += 1
        else:
            if added or not state.candidate_has_lyrics(conn, candidate_id):
                state.save_lyrics(conn, candidate_id, hit)
            state.mark_page(conn, url, "done", candidate_id=candidate_id, title=page.title, artist=page.artist)
            stats["hits"] += 1
        stats["processed"] += 1
        if index % 25 == 0 or index == len(rows):
            print(
                f"[{domain} {index}/{len(rows)}] hits={stats['hits']} dupes={stats['duplicates']} "
                f"rejected={stats['rejected']} failed={stats['fetch_failed'] + stats['parse_failed']}"
            )
        if delay:
            time.sleep(delay)
    return stats


def write_report(report: dict, paths=None) -> Path:
    paths = (paths or cfg.DEFAULT_PATHS).ensure()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = paths.reports / f"crawl_{stamp}.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl lyric sites into the work queue.")
    parser.add_argument("--db", type=Path, default=cfg.DEFAULT_PATHS.db)
    parser.add_argument("--sites", nargs="+", choices=list(SITES), default=list(SITES))
    parser.add_argument("--limit", type=int, default=0, help="Max pages to process per site")
    parser.add_argument("--max-pages", type=int, default=40, help="Listing pages to scan for links")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between page fetches")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = state.open_db(args.db)
    state.init_db(conn)
    client = CachedHttp()
    report = {"sites": {}}
    for name in args.sites:
        stats = crawl_site(
            conn,
            client,
            SITES[name],
            limit=args.limit,
            max_pages=args.max_pages,
            delay=args.delay,
        )
        report["sites"][name] = stats
    path = write_report(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"report -> {path}")
    print(json.dumps({"pages": state.page_stats(conn), **state.stats(conn)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
