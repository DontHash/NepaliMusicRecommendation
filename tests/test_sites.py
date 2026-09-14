"""Unit tests for lyric-site adapters and the pages queue."""

from __future__ import annotations

from data_collection import state
from data_collection.crawl_sites import crawl_site
from data_collection.http import HttpResult
from data_collection.sites import blogger_atom, nepalilyrics, paankopat, songsdiary, wordpress_api
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


def test_paankopat_pipeline_title_without_pipes_and_category_artist():
    html = """
    <html><head>
      <meta property="og:title" content="5:55 : Maya (High Sessions) Lyrics and Chords - Paan Ko Pat" />
    </head><body>
      <article class="spnc-post">
        <a href="https://paankopat.com/topi-studios/">Topi Studios</a>
        <a href="https://paankopat.com/pop-song/">POP SONG</a>
        <a href="https://paankopat.com/the-uglyz/">The Uglyz</a>
        <a href="https://paankopat.com/author/paankopat-com/">पागल प्रेमी</a>
        <div class="spnc-entry-content"><p>maya ko dori le bhandhai</p></div>
      </article>
    </body></html>
    """
    page = paankopat.parse(html, "https://paankopat.com/2024/02/15/555-maya-high-sessions-lyrics/")
    assert page is not None
    assert page.title == "5:55 : Maya (High Sessions)"
    assert page.artist == "The Uglyz"


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


class _StubClient:
    def __init__(self, text=None, json_data=None):
        self.text = text
        self.json_data = json_data
        self.text_calls: list[str] = []
        self.json_calls: list[dict | None] = []

    def get_text(self, source, url, params=None, refresh=False, timeout=None):
        self.text_calls.append(url)
        return self.text

    def get_json(self, source, url, params=None, refresh=False, timeout=None):
        self.json_calls.append(params)
        data = self.json_data(params) if callable(self.json_data) else self.json_data
        return HttpResult(ok=True, status=200, data=data)


def test_nepalilyrics_parse_strips_chords():
    html = """
    <html><head>
      <meta property="og:title" content="Babu Ko Jungo - Pushpan Pradhan Lyrics &amp; Chords" />
    </head><body>
      <div class="font-mono text-[var(--chord-color,#f97316)] whitespace-pre select-none">
        <span>Am</span>   <span>F</span>
      </div>
      <p class="whitespace-pre-wrap">Bara choro, tera naati
Budaa ko dhokro, kadhai maathi</p>
      <div class="font-mono whitespace-pre select-none"><span>Am</span></div>
      <p class="whitespace-pre-wrap">Aankha ma aansu, chheu chhaina
<span class="font-mono">G</span>Timro maya le</p>
    </body></html>
    """
    page = nepalilyrics.parse(html, "https://nepalilyrics.net/en/songs/babu-ko-jungo")
    assert page is not None
    assert page.title == "Babu Ko Jungo"
    assert page.artist == "Pushpan Pradhan"
    assert "Bara choro, tera naati" in page.lyrics
    assert "Aankha ma aansu, chheu chhaina" in page.lyrics
    assert "Am" not in page.lyrics
    assert "G\n" not in page.lyrics


def test_nepalilyrics_policy_and_discovery():
    assert nepalilyrics.allowed_url("https://nepalilyrics.net/en/songs/x")
    assert not nepalilyrics.allowed_url("https://nepalilyrics.net/api/lyrics")
    assert not nepalilyrics.allowed_url("https://nepalilyrics.net/en/search?q=x")
    assert not nepalilyrics.allowed_url("https://nepalilyrics.net/admin")
    assert not nepalilyrics.allowed_url("https://nepalilyrics.net/en/artists/x")
    assert not nepalilyrics.allowed_url("https://other.net/en/songs/x")
    assert nepalilyrics.parse("<html></html>", "https://nepalilyrics.net/api/songs") is None
    xml = """<urlset>
      <loc>https://nepalilyrics.net/en/songs/a</loc>
      <loc>https://nepalilyrics.net/api/songs</loc>
      <loc>https://nepalilyrics.net/en/artists/x</loc>
      <loc>https://nepalilyrics.net/en/songs/b</loc>
    </urlset>"""
    urls = nepalilyrics.discover(_StubClient(text=xml))
    assert urls == ["https://nepalilyrics.net/en/songs/a", "https://nepalilyrics.net/en/songs/b"]


def test_wordpress_api_parse_fragment():
    adapter = wordpress_api.make_adapter(domain="nepaligeetlyrics.com", base="https://nepaligeetlyrics.com")
    html = """
    <div data-role="song-title">Gayo Ta Gayo Lyrics | Sushant KC</div>
    <p>Sushant KC is a name that resonates deeply within the hearts of music lovers around the world.</p>
    <h2>Gayo Ta Gayo Lyrics – (Released Year 2026)</h2>
    <p>Intro:</p>
    <p>Sora Barsey Umerai Ma Mai Pani Jhilke Hudo Ho</p>
    <p>Verse 1:</p>
    <p>Gayo ta Gayo Samaya Aaba K Bhanu</p>
    <p>Explore More Lyrics: Bela Bela Lyrics | Sushant KC</p>
    <p>You Can Watch Video Gayo Ta Gayo By Sushant KC</p>
    """
    page = adapter.parse(html, "https://nepaligeetlyrics.com/artist/gayo-ta-gayo-lyrics/")
    assert page is not None
    assert page.title == "Gayo Ta Gayo"
    assert page.artist == "Sushant KC"
    assert "Sora Barsey Umerai Ma" in page.lyrics
    assert "Gayo ta Gayo Samaya" in page.lyrics
    assert "Intro:" not in page.lyrics
    assert "resonates" not in page.lyrics
    assert "Explore More" not in page.lyrics


def test_wordpress_api_iter_pages_pagination():
    adapter = wordpress_api.make_adapter(domain="nepaligeetlyrics.com", base="https://nepaligeetlyrics.com")

    def post(index, page):
        return {
            "link": f"https://nepaligeetlyrics.com/artist/song-{page}-{index}/",
            "title": {"rendered": f"Song {index} Lyrics | Artist"},
            "content": {"rendered": f"<p>line {index}</p>"},
        }

    posts = {1: [post(index, 1) for index in range(100)], 2: [post(100, 2)]}
    client = _StubClient(json_data=lambda params: posts.get((params or {}).get("page"), []))
    items = list(adapter.iter_pages(client, max_pages=5))
    assert len(items) == 101
    assert items[0][0].endswith("/song-1-0/")
    assert items[0][1].startswith('<div data-role="song-title">Song 0 Lyrics | Artist</div>')
    assert [(params or {}).get("page") for params in client.json_calls] == [1, 2]


def test_blogger_atom_parse_devanagari_marker():
    adapter = blogger_atom.make_adapter(domain="geetishabda.blogspot.com", base="https://geetishabda.blogspot.com")
    html = """
    <h3>Jhim Jhimaune Aankha Lyrics in Nepali By Ekdev Limbu</h3>
    <div>
      <p>"Jhim Jhimaune Aankha" is a captivating new song by the talented Nepali singer Ekdev Limbu.</p>
      <p>♫ Title:</p><p>Jhim Jhimaune Aankha | झिम-झिमाउने आँखा</p>
      <p>♫ Genre:</p><p>Love Confession, Romantic</p>
      <p>नेपाली</p>
      <p>झिम-झिमाउने आँखा, गाउँदै छु म भाका</p>
      <p>सुनिदेऊ सुनिदेऊ सुनिदेउन</p>
      <p>♫ Thank You ♫</p>
    </div>
    """
    page = adapter.parse(html, "https://geetishabda.blogspot.com/2025/01/x.html")
    assert page is not None
    assert page.title == "Jhim Jhimaune Aankha"
    assert page.artist == "Ekdev Limbu"
    assert page.lyrics == "झिम-झिमाउने आँखा, गाउँदै छु म भाका\nसुनिदेऊ सुनिदेऊ सुनिदेउन"


def test_blogger_atom_parse_credit_block():
    adapter = blogger_atom.make_adapter(
        domain="nepali-songslyrics.com",
        base="https://www.nepali-songslyrics.com",
        style="credit_block",
    )
    html = """
    <p>Baimani - Alkaa Subedi, Kushal Singh Lyrics</p>
    <p>Singer</p><p>Alkaa Subedi, Kushal Singh</p>
    <p>Music</p><p>Alkaa Subedi</p>
    <p>Song Writer</p><p>Alkaa Subedi</p>
    <p>Arrenger</p><p>Alkaa Subedi</p>
    <p>Sath timro ye maya</p>
    <p>Pauchhu ki paudina van ana</p>
    <p>♫ Thank You ♫</p>
    """
    page = adapter.parse(html, "https://www.nepali-songslyrics.com/2025/06/baimani-lyrics.html")
    assert page is not None
    assert page.title == "Baimani"
    assert page.artist == "Alkaa Subedi, Kushal Singh"
    assert page.lyrics == "Sath timro ye maya\nPauchhu ki paudina van ana"


def test_blogger_atom_iter_pages_pagination():
    adapter = blogger_atom.make_adapter(domain="geetishabda.blogspot.com", base="https://geetishabda.blogspot.com")

    def feed(params):
        if (params or {}).get("start-index") == 1:
            return {
                "feed": {
                    "entry": [
                        {
                            "title": {"$t": "T1"},
                            "content": {"$t": "<p>a</p>"},
                            "link": [{"rel": "alternate", "type": "text/html", "href": "https://g.example/1.html"}],
                        },
                        {
                            "title": {"$t": "T2"},
                            "content": {"$t": "<p>b</p>"},
                            "link": [{"rel": "alternate", "type": "text/html", "href": "https://g.example/2.html"}],
                        },
                    ],
                    "openSearch$totalResults": {"$t": "2"},
                }
            }
        return {"feed": {"entry": []}}

    client = _StubClient(json_data=feed)
    items = list(adapter.iter_pages(client, max_pages=5))
    assert items == [("https://g.example/1.html", "<p>a</p>"), ("https://g.example/2.html", "<p>b</p>")]
    assert len(client.json_calls) == 1


def test_crawl_site_consumes_prefetched_pages(tmp_path):
    conn = state.open_db(tmp_path / "db.sqlite")
    state.init_db(conn)
    lyrics_line = "जुन तारा तिम्रो लागी सजाइ दिउँला"
    content = f"<h3>Test Song Lyrics in Nepali By Artist Name</h3><p>नेपाली</p>" + "".join(
        f"<p>{lyrics_line}</p>" for _ in range(8)
    )
    module = blogger_atom.make_adapter(domain="test.blogspot.com", base="https://test.blogspot.com")

    def feed(params):
        return {
            "feed": {
                "entry": [
                    {
                        "title": {"$t": "Test Song Lyrics in Nepali By Artist Name"},
                        "content": {"$t": content},
                        "link": [{"rel": "alternate", "type": "text/html", "href": "https://test.blogspot.com/1.html"}],
                    }
                ],
                "openSearch$totalResults": {"$t": "1"},
            }
        }

    class _NoFetchClient(_StubClient):
        def get_text(self, source, url, params=None, refresh=False, timeout=None):
            raise AssertionError(f"prefetched page must not be fetched: {url}")

    stats = crawl_site(conn, _NoFetchClient(json_data=feed), module, delay=0)
    assert stats["hits"] == 1
    assert stats["fetch_failed"] == 0
    assert stats["parse_failed"] == 0
    assert state.stats(conn)["lyrics_total"] == 1

