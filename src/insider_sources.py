import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib import parse, request, error

from insider_sources import MicrosoftSources

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / 'scripts'
REPORTS_DIR = ROOT / 'reports'


def run_powershell_build_query() -> Dict[str, Any]:
    powershell_script = SCRIPTS_DIR / 'Get-WindowsBuild.ps1'
    if not powershell_script.exists():
        raise FileNotFoundError(f'PowerShell script not found: {powershell_script}')

    command = [
        'powershell',
        '-NoProfile',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        str(powershell_script),
    ]

    result = subprocess.run(command, capture_output=True, text=True, shell=False)

    if result.returncode != 0:
        raise RuntimeError(f"PowerShell failed: {result.stderr.strip() or result.stdout.strip()}")

    output = result.stdout.strip()
    if not output:
        raise RuntimeError('PowerShell returned no output.')

    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f'PowerShell output is not valid JSON: {output}') from exc

    return data


def save_report(report: Dict[str, Any], output_path: str | None = None) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    if output_path:
        path = REPORTS_DIR / output_path
    else:
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        path = REPORTS_DIR / f'build-report-{timestamp}.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return path


def build_markdown_report(report: Dict[str, Any]) -> str:
    build = report.get('build', {})
    notes = report.get('notes', [])

    lines = [
        '# Windows Insider Build Report',
        '',
        f'- Build: {build.get("CurrentBuild") or "Unknown"}',
        f'- UBR: {build.get("UBR") or "Unknown"}',
        f'- Full Build: {build.get("FullBuild") or "Unknown"}',
        f'- Channel: {build.get("Channel") or "Unknown"}',
        f'- Product: {build.get("ProductName") or "Unknown"}',
        f'- Timestamp: {build.get("TimestampUtc") or "Unknown"}',
        '',
        '## Note ufficiali trovate',
    ]

    if not notes:
        lines.append('Nessuna nota ufficiale trovata per questa build. Potrebbe essere ancora in fase di pubblicazione.')
    else:
        for index, note in enumerate(notes, 1):
            lines.append(f'{index}. **{note.get("title", "Titolo non disponibile")}**')
            lines.append(f'   - Source: {note.get("source", "Unknown")}')
            lines.append(f'   - URL: {note.get("url", "") }')
            summary = note.get('summary', '').strip()
            if summary:
                lines.append(f'   - Summary: {summary}')
            lines.append('')

    return '\n'.join(lines) + '\n'


def analyze() -> Dict[str, Any]:
    build_info = run_powershell_build_query()
    build_number = build_info.get('CurrentBuild')
    if not build_number:
        raise ValueError('CurrentBuild not found in Windows registry.')

    sources = MicrosoftSources(build_number)
    notes = sources.search_all()

    report = {
        'build': build_info,
        'build_number': build_number,
        'notes': notes,
        'generated_at_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Windows Insider Build Agent')
    parser.add_argument('--output-md', action='store_true', help='Generate Markdown report as well.')
    return parser.parse_args()


def main() -> int:
    try:
        report = analyze()
        json_path = save_report(report)

        print(f'Build rilevata: {report["build"].get("FullBuild", "Unknown")}')
        print(f'Report JSON salvato in: {json_path}')

        if len(report['notes']) > 0:
            print(f'Note trovate: {len(report["notes"])}')
        else:
            print('Nessuna nota ufficiale trovata per la build corrente.')

        args = parse_args()
        if args.output_md:
            md_content = build_markdown_report(report)
            md_path = REPORTS_DIR / f'build-report-{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}.md'
            md_path.write_text(md_content, encoding='utf-8')
            print(f'Report Markdown salvato in: {md_path}')

    except Exception as exc:  # pragma: no cover
        print(f'Errore: {exc}', file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
