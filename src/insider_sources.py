"""Poll official Microsoft sources for notes matching a Windows Insider build."""

from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class MicrosoftSources:
    """Search the Insider Blog RSS feed and Microsoft Learn search."""

    FEED_URL = "https://blogs.windows.com/windows-insider/feed/"
    LEARN_SEARCH_URL = "https://learn.microsoft.com/api/search?search={query}&locale=en-us&$top=10"
    USER_AGENT = "WindowsInsiderBuildAgent/0.1 (+https://github.com/one-angel997/windows-insider-build-agent)"

    def __init__(self, build_number: int | str, timeout: int = 20) -> None:
        self.build_number = str(build_number)
        self.timeout = timeout

    def _fetch_text(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": self.USER_AGENT, "Accept": "application/rss+xml, application/xml, application/json, text/html, */*"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except (URLError, TimeoutError, OSError):
            return ""

    def _matches_build(self, text: str) -> bool:
        return bool(re.search(rf"(?<!\d){re.escape(self.build_number)}(?!\d)", text))

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1].lower()

    @staticmethod
    def _plain_text(value: str) -> str:
        value = re.sub(r"<[^>]+>", " ", value)
        return " ".join(html.unescape(value).split())

    def search_windows_insider_blog(self) -> list[dict[str, Any]]:
        xml_text = self._fetch_text(self.FEED_URL)
        if not xml_text:
            return []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        notes: list[dict[str, Any]] = []
        for item in (element for element in root.iter() if self._local_name(element.tag) == "item"):
            values = {self._local_name(child.tag): (child.text or "") for child in item}
            title = self._plain_text(values.get("title", ""))
            description = self._plain_text(values.get("description", ""))
            link = values.get("link", "").strip()
            if link and self._matches_build(f"{title} {description}"):
                notes.append({"source": "Windows Insider Blog", "title": title, "url": link, "summary": description[:500]})
        return notes

    def search_learn(self) -> list[dict[str, Any]]:
        query = quote(f'Windows 11 Insider Preview build {self.build_number}')
        body = self._fetch_text(self.LEARN_SEARCH_URL.format(query=query))
        if not body:
            return []
        try:
            results = json.loads(body).get("results", [])
        except (json.JSONDecodeError, AttributeError):
            return []

        notes: list[dict[str, Any]] = []
        for item in results if isinstance(results, list) else []:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            url = str(item.get("url") or "").strip()
            summary = str(item.get("description") or item.get("descriptionText") or "").strip()
            if title and url and self._matches_build(f"{title} {summary}"):
                notes.append({"source": "Microsoft Learn", "title": title, "url": url, "summary": summary[:500]})
        return notes

    def search_all(self) -> list[dict[str, Any]]:
        results = self.search_windows_insider_blog() + self.search_learn()
        unique: list[dict[str, Any]] = []
        seen: set[str] = set()
        for note in results:
            key = note.get("url") or f"{note.get('source')}:{note.get('title')}"
            if key not in seen:
                seen.add(key)
                unique.append(note)
        return unique
