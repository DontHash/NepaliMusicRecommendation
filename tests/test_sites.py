"""Unit tests for lyric-site adapters and the pages queue."""

from __future__ import annotations

from data_collection import state
from data_collection.sites import paankopat, songsdiary
from data_collection.sites.base import strip_chord_lines


def test_songsdiary_parse():
    html = """
    <html><body>
      <h1>Aajai Ra Rati K Dekhe Sapana Lyrics! and more..</h1>
      <div class="lyrics" id="lyrics" tabindex="0">
        ⚠ Unverified
        📖 Read in Devanagari
        Aajai Ra Rati
        Ke Dekhe Sapana?
        Mai Mari Gayeko
        Batasa Bicha Hangako Fula
      </div>
    </body></html>
    """
    page = songsdiary.parse(html, "https://songsdiary.com/47/aajai-ra-rati-k-dekhe-sapana-lyrics-narayan-gopal")
    assert page is not None
    assert page.title == "aajai ra rati k dekhe sapana"
    assert page.artist == "narayan gopal"
    assert "Mai Mari Gayeko" in page.lyrics
    assert "Devanagari" not in page.lyrics


def test_songsdiary_parse_missing_container():
    assert songsdiary.parse("<html><body>no lyrics here</body></html>", "https://songsdiary.com/1/x") is None


def test_paankopat_parse_strips_chords():
    html = """
    <html><head>
      <meta property="og:title" content="Timro Nyano | तिम्रो न्यानो | Uglyz Lyrics and Chords - Paan Ko Pat" />
    </head><body>
      <article class="spnc-post">
        <div class="spnc-entry-content">
          <p>Scale : G Major</p>
          <p>G D. C
timro nyano angalo ko maya
G D
sadhai rahirahos
Em
Jaba samma sansar rahanchha</p>
        </div>
      </article>
    </body></html>
    """
    page = paankopat.parse(html, "https://paankopat.com/2016/03/17/timro-nyano-ugliz-lyrics/")
    assert page is not None
    assert page.title == "Timro Nyano"
    assert page.artist == "Uglyz"
    assert "timro nyano angalo ko maya" in page.lyrics
    assert "G D. C" not in page.lyrics
    assert "Scale" not in page.lyrics


def test_strip_chord_lines_keeps_lyrics():
    text = "G D. C\ntimro nyano angalo ko maya\nEm G\nsadhai rahirahos\nC  Am  F  G\n"
    out = strip_chord_lines(text)
    assert out == "timro nyano angalo ko maya\nsadhai rahirahos"


def test_pages_queue_roundtrip(tmp_path):
    conn = state.open_db(tmp_path / "db.sqlite")
    state.init_db(conn)
    added = state.register_pages(conn, ["https://a.com/1", "https://a.com/2", "https://a.com/1"], domain="a.com")
    assert added == 2
    rows = state.next_pages(conn, domain="a.com")
    assert len(rows) == 2
    state.mark_page(conn, "https://a.com/1", "done", candidate_id=5, title="t", artist="a")
    stats = state.page_stats(conn)
    assert stats["a.com"]["new"] == 1
    assert stats["a.com"]["done"] == 1
    second = state.register_pages(conn, ["https://a.com/1"], domain="a.com")
    assert second == 0
