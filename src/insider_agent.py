import json
import re
from typing import Any, Dict, List
from urllib import parse, request, error


class MicrosoftSources:
    def __init__(self, build_number: int | str):
        self.build_number = str(build_number)

    def fetch_text(self, url: str) -> str:
        req = request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, application/json, text/html, */*',
        })
        try:
            with request.urlopen(req, timeout=20) as response:
                return response.read().decode('utf-8', errors='replace')
        except error.URLError:
            return ''

    def search_windows_insider_blog(self) -> List[Dict[str, Any]]:
        feed_url = 'https://blogs.windows.com/windows-insider/feed/'
        xml = self.fetch_text(feed_url)
        if not xml:
            return []

        notes: List[Dict[str, Any]] = []

        for match in re.finditer(r'<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?<description>(.*?)</description>', xml, re.DOTALL | re.IGNORECASE):
            title = self._clean_html(match.group(1))
            link = self._clean_html(match.group(2))
            description = self._clean_html(match.group(3))
            if self.build_number in title or self.build_number in description:
                notes.append({
                    'source': 'Windows Insider Blog',
                    'title': title,
                    'url': link,
                    'summary': description[:300],
                })
        return notes

    def search_learn_api(self) -> List[Dict[str, Any]]:
        query = f'Windows 11 Insider build {self.build_number}'
        encoded = parse.quote(query)
        url = f'https://learn.microsoft.com/api/search?search={encoded}&locale=en-us&$top=5'
        body = self.fetch_text(url)
        if not body:
            return []

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return []

        results = payload.get('results', [])
        notes: List[Dict[str, Any]] = []
        for item in results[:5]:
            title = item.get('title')
            url = item.get('url')
            description = item.get('description') or item.get('descriptionText') or ''
            if not title or not url:
                continue
            if self.build_number in title or self.build_number in description:
                notes.append({
                    'source': 'Microsoft Learn',
                    'title': title,
                    'url': url,
                    'summary': description[:300],
                })
        return notes

    def search_all(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        results.extend(self.search_windows_insider_blog())
        results.extend(self.search_learn_api())

        unique: List[Dict[str, Any]] = []
        seen = set()
        for note in results:
            key = (note.get('source'), note.get('title'), note.get('url'))
            if key in seen:
                continue
            seen.add(key)
            unique.append(note)
        return unique

    @staticmethod
    def _clean_html(raw: str) -> str:
        cleaned = re.sub(r'<.*?>', ' ', raw)
        cleaned = cleaned.replace('&amp;', '&')
        cleaned = cleaned.replace('&nbsp;', ' ')
        cleaned = cleaned.replace('&#39;', "'")
        return ' '.join(cleaned.split())


if __name__ == '__main__':
    results = MicrosoftSources('26100').search_all()
    print(json.dumps(results[:5], ensure_ascii=False, indent=2))
