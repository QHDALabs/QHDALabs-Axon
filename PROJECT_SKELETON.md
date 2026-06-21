# Szkielet projektu QHDALabs — jak użyć

Kopiujesz cały folder `qhdalabs_template/` do nowego repo i robisz find/replace.

## Kroki przy nowym projekcie

1. Skopiuj folder, zmień nazwę na `QHDALabs-<NAZWA>`.
2. Find/replace `<NAZWA PROJEKTU>` → faktyczna nazwa (README, .claude, VERIFICATION_LOG).
3. W `pyproject.toml`: zmień `name`, `description`.
4. Wypełnij `.claude/instructions.md` — to czyta Claude Code/Cowork.
5. Jeśli projekt kwantowy: odkomentuj qiskit w `requirements.txt` i `pyproject.toml`.
6. `pip install -e ../qhda-core` — podłącz wspólne mechanizmy.
7. `git init`, pierwszy commit.

## Co jest w szkielecie

| Plik | Rola |
|---|---|
| `.claude/instructions.md` | kontekst projektu — Claude czyta automatycznie |
| `VERIFICATION_LOG.md` | dziennik weryfikacji (lekcja z XSIG) — NAJWAŻNIEJSZY |
| `pyproject.toml` | pakowanie, zależności, extras |
| `tests/test_smoke.py` | sprawdza środowisko + dostępność qhda-core |
| `requirements.txt` | zależności runtime |
| `.gitignore` | dane, cache, outputy poza gitem |
| `README.md` | opis projektu |
| `SETUP_COWORK_CODE_WINDOWS.md` | konfiguracja środowiska Claude (raz, nie per-projekt) |

## Filozofia

Szkielet wymusza dwie rzeczy, które XSIG udowodnił że działają:
- **kontekst dla Claude** (`.claude/`) — mniej tłumaczenia za każdym razem
- **dziennik weryfikacji** — proces "zanim koncepcja stanie się teorią"
