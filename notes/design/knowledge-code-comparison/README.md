# Code Coupling vs Knowledge Coupling

## Fonti dati

| File | Contenuto |
|------|-----------|
| `code-dependencies-stefano/deps.json` | Dipendenze statiche: per ogni file, la lista di file che importa |
| `knowledge-dependecies-stefano/coupling.csv` | Coupling storico: coppie di file con `degree` (% di commit in cui compaiono insieme) e `average-revs` |

---

## Code Coupling

Cattura le **relazioni di import statiche** tra file sorgente — cosa il codice dichiara esplicitamente.

Il punteggio usato nell'analisi:

| Edge di import tra la coppia | Score |
|------------------------------|-------|
| 0 (nessun import in nessuna direzione) | 0 |
| 1 (A → B oppure B → A) | 50 |
| 2 (A → B **e** B → A, bidirezionale) | 100 |

È una proprietà **strutturale**: determinata dallo snapshot del codice, indipendente dalla storia dei commit.

---

## Knowledge Coupling

Cattura la **frequenza di co-modifica** — quante volte due file vengono toccati nello stesso commit.

La colonna `degree` (0–100 %) è la percentuale di commit in cui *entrambi* i file appaiono insieme, sul totale dei commit che toccano almeno uno dei due. `average-revs` è il numero medio di revisioni di ciascun file nella coppia.

È una proprietà **comportamentale / storica**: riflette le abitudini del team, indipendente dagli import dichiarati nel codice.

---

## I quattro quadranti

```
knowledge
   100 │ Hidden dep.  │  Aligned
       │  (smell)     │  (atteso)
    50 ├──────────────┼──────────────
       │  Indipendent │  Stale import
     0 │  (atteso)    │  (stale?)
       └──────────────┴──────────────
         0           25            code
```

| Quadrante | Code | Knowledge | Interpretazione |
|-----------|------|-----------|-----------------|
| **Aligned** | alto | alto | Accoppiamento coerente — atteso |
| **Hidden dependency** | basso | alto | File sempre committati insieme ma senza import — possibile smell architetturale, candidati a estrarre un'astrazione comune |
| **Stale import** | alto | basso | Import dichiarato ma file raramente modificati insieme — import stabile, vestigiale, o wrapper che isola i cambiamenti |
| **Independent** | basso | basso | File indipendenti — atteso |

---

## Script

### `scatter.py` → `scatter_quadrants.png`

Panoramica generale su **tutte** le coppie di file (nessun filtraggio).  
Ogni punto è una coppia, colorato per quadrante. Jitter su X (per i 3 valori discreti di code) e su Y per i punti a `knowledge=0` (per evitare sovrapposizione).  
Stampa anche il conteggio totale di coppie e la distribuzione per quadrante.

```bash
python3 scatter.py
```

### `focused.py` → `focused_hidden_dep.png` + `focused_stale_import.png`

Dettaglio sulle **top 15 coppie più significative** nei due quadranti interessanti, con nomi file leggibili (lollipop chart).

- `focused_hidden_dep.png` — ordinato per `degree` decrescente, poi `average-revs` decrescente
- `focused_stale_import.png` — doppio lollipop: score code (viola) + score knowledge (blu) affiancati

```bash
python3 focused.py
```

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install pandas matplotlib numpy
```
