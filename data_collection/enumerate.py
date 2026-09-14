"""CLI: enumerate candidate tracks from Deezer/iTunes for seed artists."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from rapidfuzz import fuzz

from . import config as cfg
from . import state
from .http import CachedHttp
from .sources import deezer, itunes

EXCLUDED_ARTISTS = {
    "",
    "genius romanizations",
    "genius translations",
    "genius nepali translations",
    "various artists",
    "unknown",
    "unknown artist",
}
DEFAULT_SEEDS = Path(__file__).resolve().parent / "seeds" / "nepali_artists.txt"


def load_seed_artists(conn, seeds_path: Path) -> list[str]:
    artists = {str(row["artist"]).strip() for row in conn.execute("SELECT DISTINCT artist FROM candidates")}
    if seeds_path.exists():
        for line in seeds_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                artists.add(line)
    return sorted(a for a in artists if a and a.casefold() not in EXCLUDED_ARTISTS)


def enumerate_artist(
    client: CachedHttp,
    artist: str,
    *,
    max_albums: int = 20,
    max_tracks: int = 300,
    with_itunes: bool = True,
) -> tuple[list, dict]:
    stats = {"deezer_artist": None, "deezer_tracks": 0, "itunes_tracks": 0}
    candidates = []
    match = deezer.best_artist_match(deezer.search_artists(client, artist), artist)
    if match:
        stats["deezer_artist"] = str(match.get("name"))
        albums = deezer.artist_albums(client, match["id"], limit=max_albums)[:max_albums]
        for album in albums:
            for track in deezer.album_tracks(client, album.get("id")):
                cand = deezer.track_to_candidate(track, album=album.get("title"))
                if cand is not None:
                    candidates.append(cand)
                    stats["deezer_tracks"] += 1
                if stats["deezer_tracks"] >= max_tracks:
                    break
            if stats["deezer_tracks"] >= max_tracks:
                break
    if with_itunes:
        seed_folded = artist.casefold()
        for track in itunes.search_songs(client, artist):
            cand = itunes.track_to_candidate(track)
            if cand is None:
                continue
            if fuzz.token_set_ratio(seed_folded, cand.artist.casefold()) < 75:
                continue
            candidates.append(cand)
            stats["itunes_tracks"] += 1
    return candidates, stats


def write_report(report: dict, paths=None) -> Path:
    paths = (paths or cfg.DEFAULT_PATHS).ensure()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = paths.reports / f"enumerate_{stamp}.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enumerate candidate tracks for seed artists.")
    parser.add_argument("--db", type=Path, default=cfg.DEFAULT_PATHS.db)
    parser.add_argument("--seeds", type=Path, default=DEFAULT_SEEDS)
    parser.add_argument("--artist", type=str, default=None, help="Enumerate a single artist only")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of artists (0 = all)")
    parser.add_argument("--max-albums", type=int, default=20)
    parser.add_argument("--max-tracks", type=int, default=300)
    parser.add_argument("--skip-itunes", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = state.open_db(args.db)
    state.init_db(conn)
    client = CachedHttp()
    if args.artist:
        seeds = [args.artist]
    else:
        seeds = load_seed_artists(conn, args.seeds)
        if args.limit:
            seeds = seeds[: args.limit]
    print(f"artists to enumerate: {len(seeds)}")
    totals = {"added": 0, "dupes": 0, "deezer_tracks": 0, "itunes_tracks": 0}
    per_artist = []
    for index, artist in enumerate(seeds, start=1):
        try:
            candidates, stats = enumerate_artist(
                client,
                artist,
                max_albums=args.max_albums,
                max_tracks=args.max_tracks,
                with_itunes=not args.skip_itunes,
            )
        except Exception as exc:
            stats = {"error": f"{type(exc).__name__}: {exc}", "deezer_tracks": 0, "itunes_tracks": 0}
            candidates = []
        added, dupes = state.enqueue(conn, candidates)
        state.set_meta(conn, "enumerate:last_artist", artist)
        totals["added"] += added
        totals["dupes"] += dupes
        totals["deezer_tracks"] += stats.get("deezer_tracks", 0)
        totals["itunes_tracks"] += stats.get("itunes_tracks", 0)
        per_artist.append({"artist": artist, "added": added, "dupes": dupes, **stats})
        print(
            f"[{index}/{len(seeds)}] {artist}: +{added} new, {dupes} dupes "
            f"(deezer={stats.get('deezer_tracks', 0)}, itunes={stats.get('itunes_tracks', 0)})"
        )
    report = {"totals": totals, "artists": len(seeds), "per_artist": per_artist}
    path = write_report(report)
    print(json.dumps(totals, ensure_ascii=False, indent=2))
    print(f"report -> {path}")
    print(json.dumps(state.stats(conn), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
