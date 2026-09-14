"""Central configuration for Phase A data collection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

USER_AGENT = "ProjectR-research/0.2 (Nepali lyrics corpus; local research project)"

CONNECT_TIMEOUT = 10.0
READ_TIMEOUT = 30.0
MAX_RETRIES = 4
BACKOFF_BASE = 1.0
BACKOFF_MAX = 20.0
CIRCUIT_FAIL_THRESHOLD = 10
CIRCUIT_COOLDOWN_SECONDS = 300.0
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})

RATE_LIMITS: dict[str, float] = {
    "lrclib.net": 1.0,
    "api.deezer.com": 4.0,
    "itunes.apple.com": 0.33,
    "api.genius.com": 1.0,
    "ws.audioscrobbler.com": 4.0,
    "musicbrainz.org": 1.0,
    "default": 0.5,
}


@dataclass(frozen=True)
class Paths:
    root: Path = PROJECT_ROOT
    raw: Path = PROJECT_ROOT / "R_data" / "raw"
    state: Path = PROJECT_ROOT / "R_data" / "state"
    corpus: Path = PROJECT_ROOT / "R_data" / "corpus"
    db: Path = PROJECT_ROOT / "R_data" / "state" / "work.sqlite"
    cache_index: Path = PROJECT_ROOT / "R_data" / "raw" / "cache_index.jsonl"

    @property
    def reports(self) -> Path:
        return self.corpus / "reports"

    def raw_dir(self, source: str, kind: str = "api") -> Path:
        return self.raw / source / kind

    def ensure(self) -> "Paths":
        for path in (self.raw, self.state, self.corpus, self.reports):
            path.mkdir(parents=True, exist_ok=True)
        return self


DEFAULT_PATHS = Paths()
