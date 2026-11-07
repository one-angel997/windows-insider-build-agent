# Changelog

## v1.1.0

### Nuove funzionalità
- Monitoraggio continuativo della build Windows Insider.
- Controllo singolo con `--once` e nuova ricerca forzata con `--force`.
- Intervallo di controllo configurabile con `--interval-minutes`.
- Stato locale persistente in `data/state.json`.
- Report JSON e Markdown per ciascuna build.
- Nuovi tentativi automatici quando le note ufficiali non sono ancora disponibili.

### Miglioramenti
- Rilevamento di PowerShell 7 (`pwsh`) o Windows PowerShell.
- Parsing del feed RSS con parser XML.
- Verifica della build con limiti numerici per ridurre i falsi positivi.
- Rimozione dei risultati duplicati.
- Gestione più robusta di errori, timeout e file di stato.
- Aggiornamento delle istruzioni nel README.

### Fonti
- Windows Insider Blog
- Microsoft Learn