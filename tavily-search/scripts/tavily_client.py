"""
Tavily API Client — Lightweight wrapper for Search & Extract endpoints.
Docs: https://docs.tavily.com
"""

import os
import json
import urllib.request
import urllib.error
from typing import Optional
from pathlib import Path


def _load_dotenv():
    """Load .env file from the same directory as this script."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


class TavilyClient:
    """Minimal Tavily API client using only stdlib (no pip dependencies)."""

    BASE_URL = "https://api.tavily.com"

    def __init__(self, api_key: Optional[str] = None):
        _load_dotenv()
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Tavily API key required. Set TAVILY_API_KEY env var or pass api_key."
            )

    def _post(self, endpoint: str, payload: dict, timeout: int = 60) -> dict:
        """POST JSON to Tavily API and return parsed response."""
        url = f"{self.BASE_URL}/{endpoint}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Tavily API error {e.code}: {body}") from e

    def search(
        self,
        query: str,
        *,
        search_depth: str = "basic",       # "basic" | "advanced" (deep search)
        topic: str = "general",             # "general" | "news" | "finance"
        max_results: int = 5,
        include_answer: bool = True,
        include_raw_content: bool = False,
        include_images: bool = False,
        include_domains: Optional[list] = None,
        exclude_domains: Optional[list] = None,
        days: Optional[int] = None,         # Recency filter (last N days)
        timeout: int = 60,
    ) -> dict:
        """
        Web search via Tavily.
        
        search_depth="basic"    → Fast search (~1s)
        search_depth="advanced" → Deep search (~5-10s, higher quality)
        
        Returns: {query, answer, results: [{title, url, content, score, ...}], ...}
        """
        payload = {
            "query": query,
            "search_depth": search_depth,
            "topic": topic,
            "max_results": max_results,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "include_images": include_images,
        }
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        if days is not None:
            payload["days"] = days

        return self._post("search", payload, timeout=timeout)

    def extract(
        self,
        urls: list,
        *,
        timeout: int = 60,
    ) -> dict:
        """
        Extract clean content from URLs via Tavily Extract.
        
        Args:
            urls: List of URLs to extract content from (max 20).
        
        Returns: {results: [{url, raw_content, ...}], failed_results: [...]}
        """
        payload = {"urls": urls[:20]}
        return self._post("extract", payload, timeout=timeout)
