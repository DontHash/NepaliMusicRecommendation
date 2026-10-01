"""Central configuration for the audio <-> lyrics pipeline.

Everything tunable lives here so scripts stay declarative and artifacts can
record the config/schema version that produced them.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIO_DATA_DIR = PROJECT_ROOT / "R_data" / "audio"

# External audio collection (change per machine / per library).
COLLECTION_ROOT = Path(
    os.environ.get("PROJECTR_AUDIO_COLLECTION", r"C:\Users\praka\Downloads\Nepali Music Collection")
)

AUDIO_EXTS = {".mp3", ".m4a", ".ogg", ".wav", ".flac", ".opus", ".aac", ".3gpp", ".webm"}

# --- artifact contract -------------------------------------------------------
SCHEMA_VERSION = "1"

# --- metadata matching thresholds (0-100 fuzzy scores) -----------------------
TITLE_STRONG = 90.0
ARTIST_STRONG = 85.0
TITLE_PROBABLE = 78.0
ARTIST_PROBABLE = 75.0
TITLE_WEAK = 65.0
ARTIST_WEAK = 90.0
TITLE_CANDIDATE = 60.0

# --- lyrics verification thresholds -----------------------------------------
CONFIRM_SIM = 68.0            # lyrics clearly the same song
CONFIRM_SIM_METADATA = 55.0   # lower bar when metadata already points at the song
AMBIGUOUS_SIM = 45.0
NEPALI_MIN_RATIO = 0.40      # reject foreign-language matches (set 0.0 for other languages)
MIN_NEW_TOKENS = 10
MIN_NEW_LINES = 3

# --- audio embedding ---------------------------------------------------------
EMBEDDING_MODEL = "laion/clap-htsat-unfused"
SAMPLE_RATE = 48000
CLIP_SECONDS = 10.0
CLIPS_PER_TRACK = 3
DECODE_MIN_SECONDS = 1.0

# --- ids ---------------------------------------------------------------------
# Provisional ids for songs found via audio are content-addressed from the
# stable track key, so they never shift between runs; the corpus merge assigns
# final integer song_ids.
NEW_ID_PREFIX = "A-"
