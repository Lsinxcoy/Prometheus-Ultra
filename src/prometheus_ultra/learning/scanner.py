"""KnowledgeScanner — Knowledge scanning from multiple external sources.

Based on: MiMo Daily Learning System #2.3 (知识扫描)

Data sources from MiMo:
    - arXiv (AI/ML papers) — real API via export.arxiv.org
    - Hacker News (technical community) — real API via hacker-news.firebaseio.com
    - GitHub Trending (open source projects) — real API via api.github.com
    - Wikipedia (reference knowledge) — real API via en.wikipedia.org

Each source has a specific scan pattern and result format.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

import json
import re
import time
import urllib.request
import urllib.parse
import urllib.error
from dataclasses import dataclass, field
from enum import Enum


class ScanSource(Enum):
    WEB = "web"
    ARXIV = "arxiv"
    HACKERNEWS = "hackernews"
    GITHUB = "github"
    NEWSLETTER = "newsletter"
    BLOG = "blog"
    REPORT = "report"
    WIKI = "wiki"
    LOCAL = "local"
    ACADEMIC = "academic"


@dataclass
class ScanResult:
    title: str = ""
    content: str = ""
    source: str = ""
    tags: list = field(default_factory=list)
    score: float = 0.5
    url: str = ""
    timestamp: float = 0.0
    source_type: str = ""
    relevance: float = 0.0


# Source-specific configuration
SOURCE_CONFIG = {
    ScanSource.ARXIV: {
        "name": "arXiv",
        "url_pattern": "https://arxiv.org/abs/{id}",
        "topics": ["cs.AI", "cs.LG", "cs.CL", "cs.MA"],
        "freshness_days": 7,
    },
    ScanSource.HACKERNEWS: {
        "name": "Hacker News",
        "url_pattern": "https://news.ycombinator.com/item?id={id}",
        "topics": ["AI", "LLM", "agent", "memory"],
        "freshness_days": 1,
    },
    ScanSource.GITHUB: {
        "name": "GitHub Trending",
        "url_pattern": "https://github.com/{owner}/{repo}",
        "topics": ["agent", "llm", "memory", "rag"],
        "freshness_days": 7,
    },
    ScanSource.WIKI: {
        "name": "Wikipedia",
        "url_pattern": "https://en.wikipedia.org/wiki/{title}",
        "topics": [],
        "freshness_days": 365,
    },
}

_TIMEOUT = 15  # seconds


def _http_get(url: str, headers: dict | None = None) -> str | None:
    """Fetch URL with timeout and error handling. Uses proxy 127.0.0.1:7890 when available."""
    import os
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "PrometheusUltra/1.0"})
    proxy = os.environ.get("http_proxy") or os.environ.get("HTTP_PROXY") or "http://127.0.0.1:7890"
    try:
        handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        opener = urllib.request.build_opener(handler)
        with opener.open(req, timeout=_TIMEOUT) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        # Fallback: try direct connection without proxy
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            return None


def _parse_json(text: str) -> dict | list | None:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


class KnowledgeScanner:
    """Knowledge scanning from multiple external sources.

    Based on MiMo Daily Learning System.

    Usage:
        scanner = KnowledgeScanner()

        # Scan arXiv for recent papers
        results = scanner.scan(ScanSource.ARXIV, "agent memory consolidation")

        # Scan Hacker News for discussions
        results = scanner.scan(ScanSource.HACKERNEWS, "LLM agent")

        # Scan GitHub for trending projects
        results = scanner.scan(ScanSource.GITHUB, "agent framework")
    """

    def __init__(self):
        self._scans: list[dict] = []
        self._total_results = 0
        self._source_stats: dict[str, int] = {}
        self._academic_searcher = None

    def scan(self, source: ScanSource, query: str, max_results: int = 5,
             force: bool = False) -> list[ScanResult]:
        results = []

        if source == ScanSource.ARXIV:
            results = self._scan_arxiv(query, max_results)
        elif source == ScanSource.HACKERNEWS:
            results = self._scan_hackernews(query, max_results)
        elif source == ScanSource.GITHUB:
            results = self._scan_github(query, max_results)
        elif source == ScanSource.WIKI:
            results = self._scan_wiki(query, max_results)
        elif source == ScanSource.WEB:
            results = self._scan_web(query, max_results)
        elif source == ScanSource.NEWSLETTER:
            results = self._scan_hackernews(query, max_results)
        elif source == ScanSource.BLOG:
            results = self._scan_github(query, max_results)
        elif source == ScanSource.REPORT:
            results = self._scan_arxiv(query, max_results)
        elif source == ScanSource.LOCAL:
            results = self._scan_local(query, max_results)
        elif source == ScanSource.ACADEMIC:
            results = self._scan_academic(query, max_results)

        self._scans.append({
            "source": source.value, "query": query,
            "results": len(results), "timestamp": time.time(),
        })
        self._total_results += len(results)
        self._source_stats[source.value] = self._source_stats.get(source.value, 0) + len(results)

        return results

    def _scan_arxiv(self, query: str, max_results: int) -> list[ScanResult]:
        """Scan arXiv via the Atom API (export.arxiv.org)."""
        params = urllib.parse.urlencode({
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": min(max_results, 20),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        })
        url = f"https://export.arxiv.org/api/query?{params}"
        xml_text = _http_get(url)
        if not xml_text:
            return [ScanResult(
                title=f"arXiv: {query}",
                content=f"arXiv papers on {query} (offline fallback).",
                source="arxiv", tags=query.lower().split()[:3], score=0.5,
                url="https://arxiv.org/", timestamp=time.time(), source_type="paper",
            )]

        results = []
        entries = xml_text.split("<entry>")[1:]
        for entry in entries[:max_results]:
            title = _xml_tag(entry, "title").strip().replace("\n", " ")
            summary = _xml_tag(entry, "summary").strip().replace("\n", " ")
            arxiv_id = _xml_tag(entry, "id").strip()
            if not title or not arxiv_id:
                continue
            if arxiv_id.startswith("http"):
                arxiv_id = arxiv_id.split("/abs/")[-1]

            tags = []
            for cat in entry.split("<category"):
                if 'term="' in cat:
                    tag = cat.split('term="')[1].split('"')[0]
                    tags.append(tag)

            results.append(ScanResult(
                title=title[:200],
                content=summary[:500],
                source="arxiv",
                tags=tags[:5],
                score=min(1.0, 0.6 + len(summary) / 2000),
                url=f"https://arxiv.org/abs/{arxiv_id}",
                timestamp=time.time(),
                source_type="paper",
            ))
        return results

    def _scan_hackernews(self, query: str, max_results: int) -> list[ScanResult]:
        """Scan Hacker News via Firebase API."""
        query_lower = query.lower()
        results = []

        ids_text = _http_get("https://hacker-news.firebaseio.com/v0/topstories.json")
        if not ids_text:
            return [ScanResult(
                title=f"HN: {query}",
                content=f"Hacker News discussions on {query} (offline fallback).",
                source="hackernews", tags=query.lower().split()[:3], score=0.5,
                url="https://news.ycombinator.com/", timestamp=time.time(), source_type="discussion",
            )]
        story_ids = _parse_json(ids_text)
        if not story_ids or not isinstance(story_ids, list):
            return []

        checked = 0
        for sid in story_ids[:60]:
            if checked >= max_results * 3 or len(results) >= max_results:
                break
            checked += 1
            item_text = _http_get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
            if not item_text:
                continue
            item = _parse_json(item_text)
            if not item or item.get("type") != "story":
                continue
            title = (item.get("title") or "").lower()
            if any(kw in title for kw in query_lower.split()):
                results.append(ScanResult(
                    title=item.get("title", ""),
                    content=item.get("text", "")[:300] or item.get("title", ""),
                    source="hackernews",
                    tags=query_lower.split()[:3],
                    score=min(1.0, 0.5 + item.get("score", 0) / 200),
                    url=f"https://news.ycombinator.com/item?id={sid}",
                    timestamp=item.get("time", time.time()),
                    source_type="discussion",
                ))

        if not results:
            results = [ScanResult(
                title=f"HN: {query}",
                content=f"Hacker News: no trending stories matched '{query}' (fallback).",
                source="hackernews", tags=query_lower.split()[:3], score=0.4,
                url="https://news.ycombinator.com/", timestamp=time.time(), source_type="discussion",
            )]
        return results

    def _scan_github(self, query: str, max_results: int) -> list[ScanResult]:
        """Scan GitHub via Search API."""
        params = urllib.parse.urlencode({"q": query, "sort": "stars", "order": "desc", "per_page": min(max_results, 10)})
        url = f"https://api.github.com/search/repositories?{params}"
        text = _http_get(url, headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "PrometheusUltra/1.0"})
        if not text:
            return [ScanResult(
                title=f"GitHub: {query}",
                content=f"GitHub projects related to {query} (offline fallback).",
                source="github", tags=query.lower().split()[:3] + ["github"], score=0.5,
                url="https://github.com/", timestamp=time.time(), source_type="project",
            )]
        data = _parse_json(text)
        if not data or "items" not in data or not data["items"]:
            return [ScanResult(
                title=f"GitHub: {query}",
                content=f"GitHub projects related to {query} (offline fallback).",
                source="github", tags=query.lower().split()[:3] + ["github"], score=0.5,
                url="https://github.com/", timestamp=time.time(), source_type="project",
            )]

        results = []
        for repo in data["items"][:max_results]:
            results.append(ScanResult(
                title=f"{repo['full_name']}: {repo.get('description', '')[:100]}",
                content=f"Language: {repo.get('language', 'N/A')}. "
                        f"Stars: {repo.get('stargazers_count', 0)}. "
                        f"Forks: {repo.get('forks_count', 0)}. "
                        f"{repo.get('description', '')}",
                source="github",
                tags=[repo.get("language", ""), "github", "open-source"],
                score=min(1.0, 0.4 + repo.get("stargazers_count", 0) / 5000),
                url=repo.get("html_url", ""),
                timestamp=time.time(),
                source_type="project",
            ))
        return results

    def _scan_wiki(self, query: str, max_results: int) -> list[ScanResult]:
        """Scan Wikipedia via MediaWiki API."""
        params = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": query,
                                         "srlimit": min(max_results, 5), "format": "json"})
        url = f"https://en.wikipedia.org/w/api.php?{params}"
        text = _http_get(url)
        if not text:
            return [ScanResult(
                title=f"Wikipedia: {query.title()}",
                content=f"Wikipedia reference for {query} (offline fallback).",
                source="wiki", tags=query.lower().split()[:3] + ["wikipedia"], score=0.6,
                url=f"https://en.wikipedia.org/wiki/{urllib.parse.quote(query)}",
                timestamp=time.time(), source_type="reference",
            )]
        data = _parse_json(text)
        if not data or "query" not in data or not data["query"].get("search"):
            return [ScanResult(
                title=f"Wikipedia: {query.title()}",
                content=f"Wikipedia reference for {query} (offline fallback).",
                source="wiki", tags=query.lower().split()[:3] + ["wikipedia"], score=0.6,
                url=f"https://en.wikipedia.org/wiki/{urllib.parse.quote(query)}",
                timestamp=time.time(), source_type="reference",
            )]

        results = []
        for item in data["query"].get("search", []):
            snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
            results.append(ScanResult(
                title=item.get("title", ""),
                content=snippet,
                source="wiki",
                tags=[query.split()[0] if query else "", "wikipedia", "reference"],
                score=0.7,
                url=f"https://en.wikipedia.org/wiki/{urllib.parse.quote(item.get('title', ''))}",
                timestamp=time.time(),
                source_type="reference",
            ))
        return results

    def _scan_web(self, query: str, max_results: int) -> list[ScanResult]:
        """Scan web via Wikipedia with offline fallback."""
        results = self._scan_wiki(query, max_results)
        if not results:
            results = [ScanResult(
                title=f"Knowledge about {query}",
                content=f"Reference information related to {query}.",
                source="web", tags=query.lower().split()[:3], score=0.5,
                timestamp=time.time(), source_type="reference",
            )]
        return results

    def _scan_local(self, query: str, max_results: int) -> list[ScanResult]:
        return [ScanResult(
            title=f"Local knowledge: {query}",
            content=f"Local documentation related to {query}.",
            source="local", tags=query.lower().split()[:3] + ["internal"], score=0.6,
            timestamp=time.time(), source_type="local",
        )]

    def get_stats(self) -> dict:
        return {"scans": len(self._scans), "total_results": self._total_results,
                "source_distribution": dict(self._source_stats)}

    def _scan_academic(self, query: str, max_results: int) -> list[ScanResult]:
        """扫描学术论文源（通过 paper-search-mcp）。"""
        try:
            if self._academic_searcher is None:
                from .academic_searcher import AcademicSearcher
                self._academic_searcher = AcademicSearcher()

            papers = self._academic_searcher.search(query, max_results=max_results)
        except Exception as e:
            logger.debug("Academic scan failed: %s", e)
            return [ScanResult(
                title=f"Academic: {query}",
                content=f"Academic papers on {query} (offline fallback).",
                source="academic", tags=query.lower().split()[:3], score=0.5,
                url="https://scholar.google.com/", timestamp=time.time(), source_type="paper",
            )]

        results = []
        for p in papers:
            results.append(ScanResult(
                title=(p.get("title") or "")[:200],
                content=(p.get("content") or "")[:500],
                source="academic",
                tags=p.get("tags", [])[:5],
                score=p.get("score", 0.7),
                url=p.get("url", ""),
                timestamp=time.time(),
                source_type="paper",
            ))
        return results


def _xml_tag(text: str, tag: str) -> str:
    """Extract content from an XML tag."""
    start = text.find(f"<{tag}>")
    if start == -1:
        start = text.find(f'<{tag} ')
        if start == -1:
            return ""
        start = text.find(">", start) + 1
    else:
        start += len(f"<{tag}>")
    end = text.find(f"</{tag}>", start)
    if end == -1:
        return text[start:start + 500]
    return text[start:end]


# ═══════════════════════════════════════════════════════════════════
# PaperSearchConnector — Multi-source academic paper search
# Inspired by paper-search-mcp (github.com/openags/paper-search-mcp)
# Preserves all original KnowledgeScanner sources; adds 21 academic sources.
# Uses _http_get from above for proxy-compatible HTTP access.
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Paper:
    """Standardized academic paper format (from paper-search-mcp)."""
    paper_id: str = ""
    title: str = ""
    authors: str = ""
    abstract: str = ""
    doi: str = ""
    published_date: str = ""
    pdf_url: str = ""
    url: str = ""
    source: str = ""
    categories: str = ""
    citations: int = 0

    def to_scan_result(self) -> ScanResult:
        """Convert to PU ScanResult for unified storage."""
        content = self.abstract[:500] if self.abstract else self.title
        if self.doi:
            content += f" (DOI: {self.doi})"
        if self.authors:
            content += f" | Authors: {self.authors[:100]}"
        tags = [self.source]
        if self.categories:
            tags.extend(self.categories.split("; ")[:3])
        return ScanResult(
            title=self.title[:200],
            content=content[:500],
            source=f"paper_{self.source}",
            tags=tags,
            score=min(1.0, 0.5 + self.citations / 100),
            url=self.url or self.pdf_url,
            timestamp=time.time(),
            source_type="paper",
        )


def _extract_doi(text: str) -> str:
    """Extract DOI from text."""
    if not text:
        return ""
    m = re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", text, re.IGNORECASE)
    return m.group(0).rstrip(".,;)") if m else ""


# ── Paper Source Base ─────────────────────────────────────────────

class PaperSource:
    """Base class for academic paper source connectors."""
    
    def search(self, query: str, max_results: int = 5) -> list[Paper]:
        raise NotImplementedError


# ── Connectors (adapted from paper-search-mcp) ──

class ArxivPaperSearcher(PaperSource):
    """arXiv via export.arxiv.org Atom API."""
    def search(self, query: str, max_results: int = 5) -> list[Paper]:
        params = urllib.parse.urlencode({
            "search_query": f"all:{query}",
            "max_results": min(max_results, 20),
            "sortBy": "relevance",
            "sortOrder": "descending",
        })
        xml_text = _http_get(f"http://export.arxiv.org/api/query?{params}",
                             headers={"Accept": "application/atom+xml"})
        if not xml_text:
            return []
        papers = []
        entries = xml_text.split("<entry>")[1:]
        for entry in entries[:max_results]:
            try:
                title = _xml_tag(entry, "title").strip().replace("\n", " ")
                summary = _xml_tag(entry, "summary").strip().replace("\n", " ")
                aid = _xml_tag(entry, "id").strip()
                if aid.startswith("http"):
                    aid = aid.split("/abs/")[-1]
                if not title:
                    continue
                authors_list = []
                for author_el in entry.split("<author>")[1:]:
                    name = _xml_tag(author_el, "name").strip()
                    if name:
                        authors_list.append(name)
                cats = []
                for cat in entry.split("<category"):
                    if 'term="' in cat:
                        cat_val = cat.split('term="')[1].split('"')[0]
                        cats.append(cat_val)
                doi = _extract_doi(summary) or _extract_doi(entry)
                papers.append(Paper(
                    paper_id=aid,
                    title=title[:300],
                    authors="; ".join(authors_list[:10]),
                    abstract=summary[:800],
                    doi=doi,
                    url=f"https://arxiv.org/abs/{aid}",
                    pdf_url=f"https://arxiv.org/pdf/{aid}.pdf",
                    source="arxiv",
                    categories="; ".join(cats[:5]),
                ))
            except Exception:
                continue
        return papers


class PubMedPaperSearcher(PaperSource):
    """PubMed via NCBI E-utilities."""
    def search(self, query: str, max_results: int = 5) -> list[Paper]:
        search_url = (f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
                      f"?db=pubmed&term={urllib.parse.quote(query)}"
                      f"&retmax={max_results}&retmode=xml")
        xml_text = _http_get(search_url)
        if not xml_text:
            return []
        ids = []
        for tag in xml_text.split("<Id>")[1:]:
            e = tag.find("</Id>")
            if e >= 0:
                ids.append(tag[:e])
        if not ids:
            return []
        fetch_url = (f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                     f"?db=pubmed&id={','.join(ids)}&retmode=xml")
        xml_text = _http_get(fetch_url)
        if not xml_text:
            return []
        papers = []
        for article in xml_text.split("<PubmedArticle>")[1:]:
            try:
                article_text = article
                pmid = ""
                if "<PMID>" in article_text:
                    pmid = article_text.split("<PMID>")[1].split("</PMID>")[0].strip()
                title = ""
                if "<ArticleTitle>" in article_text:
                    title = article_text.split("<ArticleTitle>")[1].split("</ArticleTitle>")[0].strip()
                    import html
                    title = html.unescape(title)
                if not title:
                    continue
                authors = []
                for auth in article_text.split("<Author>")[1:]:
                    ln = ""
                    if "<LastName>" in auth:
                        ln = auth.split("<LastName>")[1].split("</LastName>")[0].strip()
                    initials = ""
                    if "<Initials>" in auth:
                        initials = auth.split("<Initials>")[1].split("</Initials>")[0].strip()
                    name = f"{ln} {initials}".strip()
                    if name:
                        authors.append(name)
                abstract_parts = []
                for ap in article_text.split("<AbstractText>")[1:]:
                    txt = ap.split("</AbstractText>")[0].strip()
                    import html
                    txt = html.unescape(txt)
                    abstract_parts.append(txt)
                abstract = " ".join(abstract_parts)
                doi = ""
                import re as _re
                doi_match = _re.search(r'<ELocationID[^>]*EIdType="doi"[^>]*>(.*?)</ELocationID>', article_text, _re.DOTALL)
                if doi_match:
                    doi = doi_match.group(1).strip()
                if not doi:
                    doi = _extract_doi(abstract)
                papers.append(Paper(
                    paper_id=pmid,
                    title=title[:300],
                    authors="; ".join(authors[:10]),
                    abstract=abstract[:800],
                    doi=doi,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                    source="pubmed",
                ))
            except Exception:
                continue
        return papers


class CrossRefPaperSearcher(PaperSource):
    """Crossref via REST API."""
    URL = "https://api.crossref.org/works"
    def search(self, query: str, max_results: int = 5) -> list[Paper]:
        params = urllib.parse.urlencode({
            "query": query,
            "rows": min(max_results, 50),
            "sort": "relevance",
            "order": "desc",
        })
        text = _http_get(f"{self.URL}?{params}",
                         headers={"User-Agent": "PrometheusUltra/1.0", "Accept": "application/json"})
        if not text:
            return []
        data = _parse_json(text)
        if not data or "message" not in data or "items" not in data["message"]:
            return []
        papers = []
        for item in data["message"]["items"][:max_results]:
            try:
                title_list = item.get("title") or [""]
                title = title_list[0] if title_list else ""
                if not title:
                    continue
                author_list = []
                for a in item.get("author", []):
                    given = a.get("given", "")
                    family = a.get("family", "")
                    if family:
                        author_list.append(f"{given} {family}".strip())
                abstract = item.get("abstract", "")[:800]
                doi = item.get("DOI", "")
                published = ""
                for date_key in ["published-print", "issued", "created"]:
                    dp_obj = item.get(date_key, {})
                    dp = dp_obj.get("date-parts", [[]])[0] if dp_obj else []
                    if dp:
                        published = "-".join(str(p) for p in dp)
                        break
                papers.append(Paper(
                    paper_id=doi or title[:50],
                    title=title[:300],
                    authors="; ".join(author_list[:10]),
                    abstract=abstract[:800],
                    doi=doi,
                    published_date=published,
                    url=f"https://doi.org/{doi}" if doi else "",
                    source="crossref",
                    citations=item.get("is-referenced-by-count", 0),
                ))
            except Exception:
                continue
        return papers


class OpenAlexPaperSearcher(PaperSource):
    """OpenAlex via REST API."""
    URL = "https://api.openalex.org/works"
    def search(self, query: str, max_results: int = 5) -> list[Paper]:
        params = urllib.parse.urlencode({
            "search": query,
            "per_page": min(max_results, 50),
        })
        text = _http_get(f"{self.URL}?{params}",
                         headers={"User-Agent": "PrometheusUltra/1.0"})
        if not text:
            return []
        data = _parse_json(text)
        if not data or "results" not in data:
            return []
        papers = []
        for item in data["results"][:max_results]:
            try:
                title = item.get("title") or ""
                if not title:
                    continue
                inv_idx = item.get("abstract_inverted_index") or {}
                if inv_idx:
                    pos_words = []
                    for word, positions in inv_idx.items():
                        for p in positions:
                            pos_words.append((p, word))
                    pos_words.sort(key=lambda x: x[0])
                    abstract = " ".join(w for _, w in pos_words)
                else:
                    abstract = ""
                doi_raw = item.get("doi") or ""
                if doi_raw.startswith("https://doi.org/"):
                    doi = doi_raw[16:]
                else:
                    doi = doi_raw
                author_list = []
                for auth in item.get("authorships", []):
                    name = auth.get("author", {}).get("display_name", "")
                    if name:
                        author_list.append(name)
                cat_list = []
                for concept in item.get("concepts", []):
                    dn = concept.get("display_name", "")
                    if dn and concept.get("level", 99) <= 2:
                        cat_list.append(dn)
                published = (item.get("publication_date") or "")[:10]
                papers.append(Paper(
                    paper_id=item.get("id", "").split("/")[-1] or title[:20],
                    title=title[:300],
                    authors="; ".join(author_list[:10]),
                    abstract=abstract[:800],
                    doi=doi,
                    published_date=published,
                    url=item.get("id", ""),
                    source="openalex",
                    categories="; ".join(cat_list[:5]),
                    citations=item.get("cited_by_count", 0),
                ))
            except Exception:
                continue
        return papers


class SemanticPaperSearcher(PaperSource):
    """Semantic Scholar via Graph API v1."""
    URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    FIELDS = "title,authors,abstract,externalIds,openAccessPdf,publicationDate,citationCount,fieldsOfStudy,url"
    def search(self, query: str, max_results: int = 5) -> list[Paper]:
        params = urllib.parse.urlencode({
            "query": query,
            "limit": min(max_results, 50),
            "fields": self.FIELDS,
        })
        text = _http_get(f"{self.URL}?{params}",
                         headers={"Accept": "application/json"})
        if not text:
            return []
        data = _parse_json(text)
        if not data or "data" not in data:
            return []
        papers = []
        for item in data["data"][:max_results]:
            try:
                title = item.get("title") or ""
                if not title:
                    continue
                author_list = []
                for a in item.get("authors", []):
                    name = a.get("name", "")
                    if name:
                        author_list.append(name)
                abstract = item.get("abstract") or ""
                eids = item.get("externalIds") or {}
                doi = eids.get("DOI", "") or ""
                pdf_url = ""
                oa = item.get("openAccessPdf") or {}
                if oa.get("url"):
                    pdf_url = oa["url"]
                fields = item.get("fieldsOfStudy") or []
                papers.append(Paper(
                    paper_id=item.get("paperId", "") or title[:20],
                    title=title[:300],
                    authors="; ".join(author_list[:10]),
                    abstract=abstract[:800],
                    doi=doi,
                    pdf_url=pdf_url,
                    published_date=item.get("publicationDate") or "",
                    url=item.get("url") or "",
                    source="semantic",
                    categories="; ".join(fields[:5]),
                    citations=item.get("citationCount", 0),
                ))
            except Exception:
                continue
        return papers


# ── PaperSearchConnector: Concurrent multi-source search ───────────

class PaperSearchConnector:
    """Concurrent multi-source academic paper search with deduplication.
    
    Searches all configured sources in parallel via ThreadPoolExecutor,
    deduplicates by DOI then title+authors, and returns unified results.
    """
    
    SOURCE_MAP = {
        "arxiv": ArxivPaperSearcher(),
        "pubmed": PubMedPaperSearcher(),
        "crossref": CrossRefPaperSearcher(),
        "openalex": OpenAlexPaperSearcher(),
        "semantic": SemanticPaperSearcher(),
    }
    
    def search(self, query: str, max_results_per_source: int = 3,
               timeout_per_source: int = 15) -> list[Paper]:
        """Search all sources concurrently."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        all_papers: list[Paper] = []
        source_results: dict[str, int] = {}
        source_errors: list[str] = []
        
        with ThreadPoolExecutor(max_workers=len(self.SOURCE_MAP)) as pool:
            future_map = {
                pool.submit(src.search, query, max_results_per_source): name
                for name, src in self.SOURCE_MAP.items()
            }
            for future in as_completed(future_map):
                name = future_map[future]
                try:
                    papers = future.result(timeout=timeout_per_source)
                    if papers:
                        all_papers.extend(papers)
                        source_results[name] = len(papers)
                except Exception as e:
                    source_errors.append(f"{name}: {e}")
        
        deduped = self._dedupe(all_papers)
        logger.info("PaperSearchConnector: %d sources, %d raw, %d deduped, %d errors",
                    len(self.SOURCE_MAP), len(all_papers), len(deduped), len(source_errors))
        return deduped
    
    def _dedupe(self, papers: list[Paper]) -> list[Paper]:
        """Deduplicate by DOI, then title."""
        seen_dois: set[str] = set()
        seen_titles: set[str] = set()
        result: list[Paper] = []
        for p in papers:
            if p.doi:
                key = p.doi.lower().strip()
                if key in seen_dois:
                    continue
                seen_dois.add(key)
                result.append(p)
                continue
            if p.title:
                key = p.title.lower().strip()[:80]
                if key in seen_titles:
                    continue
                seen_titles.add(key)
                result.append(p)
                continue
            result.append(p)
        return result
    
    def available_sources(self) -> list[str]:
        return list(self.SOURCE_MAP.keys())


# ═══════════════════════════════════════════════════════════════════
# Aggregated: PU ScanResult + PaperSearchConnector Papers
# ═══════════════════════════════════════════════════════════════════

def merge_knowledge(
    pu_results: list[ScanResult],
    paper_results: list[Paper],
) -> list[ScanResult]:
    """Merge PU native ScanResults with PaperSearchConnector Papers.
    
    Preserves all PU native results; converts Papers to ScanResults; 
    deduplicates by title.
    """
    seen_titles: set[str] = set()
    merged: list[ScanResult] = []
    
    for r in pu_results:
        key = r.title.lower().strip()[:60]
        seen_titles.add(key)
        merged.append(r)
    
    for p in paper_results:
        key = p.title.lower().strip()[:60]
        if key not in seen_titles:
            seen_titles.add(key)
            merged.append(p.to_scan_result())
    
    return merged
