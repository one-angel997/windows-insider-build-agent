"""Windows Insider build monitoring agent."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from insider_sources import MicrosoftSources

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
REPORTS_DIR = ROOT / "reports"
STATE_PATH = ROOT / "data" / "state.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_powershell_build_query() -> dict[str, Any]:
    script = SCRIPTS_DIR / "Get-WindowsBuild.ps1"
    if not script.is_file():
        raise FileNotFoundError(f"PowerShell script not found: {script}")

    executable = shutil.which("pwsh") or shutil.which("powershell")
    if not executable:
        raise RuntimeError("PowerShell non trovato. Installa PowerShell 7 o esegui l'agente su Windows.")

    result = subprocess.run(
        [executable, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"PowerShell ha restituito {result.returncode}: {(result.stderr or result.stdout).strip()}")
    try:
        data = json.loads(result.stdout.strip())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Output PowerShell non valido: {result.stdout.strip()!r}") from exc
    if not isinstance(data, dict) or not data.get("CurrentBuild"):
        raise RuntimeError("PowerShell non ha restituito CurrentBuild.")
    return data


def load_state() -> dict[str, Any]:
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(STATE_PATH)


def write_report(report: dict[str, Any], build_key: str) -> tuple[Path, Path]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_key = "".join(char if char.isalnum() or char in ".-_" else "_" for char in build_key)
    json_path = REPORTS_DIR / f"build-report-{safe_key}.json"
    md_path = REPORTS_DIR / f"build-report-{safe_key}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_markdown_report(report), encoding="utf-8")
    return json_path, md_path


def build_markdown_report(report: dict[str, Any]) -> str:
    build = report["build"]
    notes = report["notes"]
    lines = [
        "# Rapporto Windows Insider",
        "",
        f"- Prodotto: {build.get('ProductName', 'Windows')}",
        f"- Versione: {build.get('DisplayVersion', 'sconosciuta')}",
        f"- Build: {build.get('FullBuild', 'sconosciuta')}",
        f"- Canale/branch rilevato: {build.get('Channel', 'sconosciuto')}",
        f"- Controllato (UTC): {report['checked_at_utc']}",
        f"- Stato: {report['status']}",
        "",
        "## Note ufficiali",
    ]
    if not notes:
        lines.extend(["", "Non sono state trovate note ufficiali per questa build. La ricerca verrà ripetuta al prossimo controllo."])
    else:
        lines.append("")
        for note in notes:
            lines.extend([f"### {note['title']}", "", f"- Fonte: {note['source']}", f"- Link: {note['url']}"])
            if note.get("summary"):
                lines.extend(["", note["summary"]])
            lines.append("")
    lines.extend(["", "> Il riepilogo riporta i risultati delle fonti ufficiali consultate; l'assenza di risultati non dimostra l'assenza di modifiche.", ""])
    return "\n".join(lines)


def check_once(force: bool = False) -> dict[str, Any]:
    build = run_powershell_build_query()
    build_key = str(build.get("FullBuild") or f"{build['CurrentBuild']}.{build.get('UBR', 0)}")
    state = load_state()
    previous_build = state.get("current_build")
    changed = previous_build != build_key

    if not force and not changed and state.get("status") == "notes_found":
        print(f"Build {build_key}: invariata; note già raccolte. Nessuna nuova ricerca.")
        return {"skipped": True, "build": build, "notes": []}

    notes = MicrosoftSources(build["CurrentBuild"]).search_all()
    status = "notes_found" if notes else "notes_pending"
    report = {
        "build": build,
        "previous_build": previous_build,
        "build_changed": changed,
        "status": status,
        "notes": notes,
        "checked_at_utc": utc_now(),
    }
    json_path, md_path = write_report(report, build_key)
    save_state({
        "current_build": build_key,
        "status": status,
        "last_checked_at_utc": report["checked_at_utc"],
        "report_json": str(json_path.relative_to(ROOT)),
        "report_markdown": str(md_path.relative_to(ROOT)),
    })

    print(f"Build rilevata: {build_key} ({build.get('Channel', 'channel sconosciuto')})")
    if notes:
        print(f"Trovate {len(notes)} nota/e ufficiale/i.")
    else:
        print("Note non ancora trovate: verranno cercate di nuovo al prossimo controllo.")
    print(f"Report: {md_path}")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitora la build Windows Insider e le relative note ufficiali.")
    parser.add_argument("--once", action="store_true", help="Esegue un controllo e termina.")
    parser.add_argument("--force", action="store_true", help="Ripete la ricerca anche se la build ha già le note.")
    parser.add_argument("--interval-minutes", type=int, default=60, help="Intervallo di polling; minimo 5 minuti (default: 60).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.interval_minutes < 5:
        print("L'intervallo minimo consentito è 5 minuti.", file=sys.stderr)
        return 2

    while True:
        try:
            check_once(force=args.force)
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            print(f"Errore durante il controllo: {exc}", file=sys.stderr)
        if args.once:
            return 0
        print(f"Prossimo controllo tra {args.interval_minutes} minuti. Interrompi con Ctrl+C.")
        try:
            time.sleep(args.interval_minutes * 60)
        except KeyboardInterrupt:
            print("Monitoraggio interrotto.")
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
