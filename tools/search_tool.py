"""
Lightweight web search helper, used by agents when they need to look up
API references, error messages, or library documentation.

Uses DuckDuckGo's HTML endpoint (no API key required) as a default backend.
Swap in a different provider (Google/Bing/Tavily/Mistral web_search) by
replacing the implementation of `search()` — the return shape is what matters.
"""
import urllib.request
import urllib.parse
import re
from dataclasses import dataclass


@dataclass
class SearchHit:
    title: str
    url: str
    snippet: str


def search(query: str, max_results: int = 5) -> list[SearchHit]:
    """Perform a simple web search and return a list of SearchHit results."""
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (agent-search-tool)"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return [SearchHit(title="Search failed", url="", snippet=str(e))]

    # Very small, dependency-free scrape of DuckDuckGo's HTML results.
    pattern = re.compile(
        r'<a rel="nofollow" class="result__a" href="(?P<url>[^"]+)">(?P<title>.*?)</a>.*?'
        r'class="result__snippet">(?P<snippet>.*?)</a>',
        re.DOTALL,
    )
    hits = []
    for m in pattern.finditer(html):
        title = re.sub("<.*?>", "", m.group("title")).strip()
        snippet = re.sub("<.*?>", "", m.group("snippet")).strip()
        hits.append(SearchHit(title=title, url=m.group("url"), snippet=snippet))
        if len(hits) >= max_results:
            break
    return hits
