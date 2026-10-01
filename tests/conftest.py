"""Test-suite defaults.

The suite exercises the staging layout: a local publish (music_rec_artifacts/
current.json) must never change what the tests read. Tests for published-set
resolution opt out explicitly via monkeypatch.
"""

import os

os.environ["PROJECTR_ARTIFACTS_DISABLE"] = "1"
