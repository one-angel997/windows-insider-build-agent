# Windows Insider Build Agent

Questo progetto nasce per monitorare le build Windows 11 Insider e raccogliere automaticamente le note ufficiali associate a una build specifica.

Obiettivo:
- leggere la build corrente del sistema
- identificare eventuali note ufficiali Microsoft della build
- raccogliere riferimenti da fonti ufficiali come Windows Insider Blog e Microsoft Learn
- produrre un riepilogo leggibile in italiano o in inglese

## Struttura del progetto

- `scripts/Get-WindowsBuild.ps1` - rileva build, versione e channel
- `src/insider_agent.py` - agent Python che esegue lo script e cerca le note della build
- `src/insider_sources.py` - logica di ricerca per fonti ufficiali Microsoft
- `requirements.txt` - dipendenze Python

## Requisiti

- Windows 11
- Python 3.10+
- PowerShell 5.1+ o PowerShell 7+

## Esecuzione

```powershell
python .\src\insider_agent.py
```

Oppure:

```powershell
python .\src\insider_agent.py --output-md
```

## Output

Lo script genera un report JSON e, opzionalmente, un file Markdown con:
- build corrente
- channel Insider
- note trovate
- link alle fonti ufficiali
- eventuale segnalazione di "nessuna nota trovata"

## Fonti ufficiali considerate

- Windows Insider Blog (RSS ufficiale)
- Microsoft Learn Search API
- Microsoft Flight Hub (quando l’API o la pagina lo consente)

## Nota

Questo è un MVP iniziale: il sistema cerca e normalizza le informazioni disponibili in modo affidabile, ma alcune build possono avere note pubblicate in ritardo o con titoli non perfettamente standardizzati.
