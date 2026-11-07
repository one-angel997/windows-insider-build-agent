# Windows Insider Build Agent

Agente di monitoraggio per Windows 11 Insider. Rileva la build installata, cerca le note nelle fonti Microsoft e genera report JSON e Markdown. Se le note non sono ancora pubblicate, riprova al controllo successivo.

## Requisiti

- Windows 11 Insider
- Python 3.10 o successivo
- Windows PowerShell 5.1 oppure PowerShell 7 (`pwsh`)
- Connessione Internet per consultare le fonti

## Installazione

Da PowerShell, nella cartella del repository:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Un controllo singolo

```powershell
python .\src\insider_agent.py --once
```

Per forzare una nuova ricerca anche se la build è già stata analizzata:

```powershell
python .\src\insider_agent.py --once --force
```

## Monitoraggio continuo

Il processo controlla la build ogni 60 minuti per impostazione predefinita:

```powershell
python .\src\insider_agent.py
```

Intervallo personalizzato (minimo 5 minuti):

```powershell
python .\src\insider_agent.py --interval-minutes 30
```

Lascia aperta la finestra PowerShell mentre il monitor è in esecuzione. Per l'avvio automatico dopo l'accesso a Windows, si può configurare in seguito l'Utilità di pianificazione.

## Cosa fa il monitor

- Esegue `scripts/Get-WindowsBuild.ps1` per ricavare versione, build, UBR e branch/channel dal registro di Windows.
- Rileva il cambio di build e avvia una ricerca delle relative note.
- Consulta il feed RSS del Windows Insider Blog e la ricerca Microsoft Learn.
- Se le note non sono disponibili, registra lo stato come in attesa e riprova all'intervallo successivo.
- Quando trova note, salva un rapporto e non ripete la ricerca a ogni ciclo, a meno che non si usi `--force`.

I report sono salvati in `reports/`; lo stato del monitor in `data/state.json`. Entrambi sono locali e ignorati da Git.

## Fonti e limiti

Fonti consultate: [Windows Insider Blog](https://blogs.windows.com/windows-insider/) e [Microsoft Learn](https://learn.microsoft.com/). Le note possono essere pubblicate in ritardo, indicizzare la build con formati diversi o descrivere rollout graduali. L'assenza di risultati non significa che una build non contenga modifiche: il report distingue esplicitamente le note non ancora trovate.

Il progetto usa solo le fonti originali e non genera affermazioni con un modello AI.
