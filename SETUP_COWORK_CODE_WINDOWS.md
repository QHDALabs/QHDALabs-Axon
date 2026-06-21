# QHDALabs — konfiguracja Cowork + Code na Windows

*Krzysztof Banasiewicz | QHDALabs*

Przewodnik konfiguracji środowiska pracy Claude (Cowork + Code) na Windows
dla projektów QHDALabs, oraz szkielet repo do kopiowania przy każdym nowym projekcie.

> **Stan na czerwiec 2026.** Nazwy produktów i wymagania mogą się zmienić —
> zawsze potwierdź na `claude.com/download` i `support.claude.com`.

---

## 1. Co jest czym (żeby nie mylić)

Wszystko mieszka w **jednej aplikacji desktop** (Claude Desktop), w trzech zakładkach:

| Zakładka | Do czego | Twój use case w QHDALabs |
|---|---|---|
| **Chat** | rozmowa, szybkie pytania | iteracja nad koncepcją, diagnoza |
| **Cowork** | autonomiczne zadania na plikach | analiza danych, raporty, README, pipeline'y na folderach |
| **Code** | środowisko Claude Code (jak terminal) | pisanie i refaktor kodu repo, testy, git |

Cowork i Code wymagają **planu płatnego** (Pro $20/mc lub wyżej). Chat jest darmowy.

---

## 2. Wymagania Windows

**Twardy wymóg dla Cowork:**

- Windows 10/11 — **edycja Pro / Enterprise / Education** (nie Home — Cowork wymaga Hyper-V / Virtual Machine Platform)
- Uprawnienia **administratora** przy instalacji (instalator stawia usługę `CoworkVMService`)
- Architektura **x64** (ARM64 dla Cowork wciąż w rozwoju; Chat i Code działają na ARM64)
- Aktywne połączenie z internetem (brak trybu offline — całość liczy się w chmurze Anthropic)

Sprawdź edycję: `Ustawienia → System → Informacje → Specyfikacje Windows`.
Sprawdź architekturę: `Ustawienia → System → Informacje → Typ systemu`.

> Jeśli masz Windows **Home**: Chat i Code zadziałają, Cowork nie. Upgrade do Pro
> przez `Ustawienia → System → Aktywacja` albo używaj Cowork na innej maszynie.

---

## 3. Instalacja krok po kroku

1. Wejdź na **`claude.com/download`** → pobierz instalator Windows (x64).
2. Uruchom instalator. Zatwierdź **UAC** (prompt administratora) — bez tego Cowork się nie skonfiguruje.
3. Otwórz Claude Desktop z menu Start, zaloguj się kontem Anthropic (plan płatny).
4. Przełącz na zakładkę **Cowork**. Przy pierwszym uruchomieniu pobiera obraz VM (~2 GB) — poczekaj.
5. Nadaj Cowork dostęp do folderu roboczego (patrz niżej — wskazuj folder projektu, nie cały dysk).

> **Ważne:** Claude Desktop musi pozostać **otwarty** podczas zadań Cowork.
> Minimalizacja OK, zamknięcie ubija aktywne zadania.

---

## 4. Konfiguracja pod QHDALabs

### Struktura katalogu roboczego

Trzymaj wszystkie projekty w jednym drzewie, np.:

```
C:\Users\krzys\QHDALABS-WORK\
├── QHDALabs-XSIG\
├── QHDALabs-Wildfire\
├── qhda-core\              ← biblioteka wspólna (pip install -e)
└── <NOWY-PROJEKT>\         ← kopiujesz tu szkielet
```

Cowork dawaj dostęp do **konkretnego folderu projektu**, nie do `QHDALABS-WORK`
w całości — mniejszy zasięg = mniej przypadkowych zmian w innych repo.

### MCP / konektory (opcjonalnie)

Connectory (Google Drive, GitHub, Slack) instalujesz jednym kliknięciem
z `claude.ai/directory`. Dla QHDALabs przydatne:

- **GitHub** — Cowork/Code czyta i pisze do repo bez ręcznego git push
- **Filesystem** — jeśli chcesz dać dostęp do danych poza folderem projektu (np. katalog z FITS Plancka)

> Connectory działające na danych (GitHub, Drive) wymagają autoryzacji per-konektor.
> Nie wpisuj tokenów ani haseł w prompt — autoryzuj przez oficjalny flow OAuth.

---

## 5. Wzorzec pracy: Chat → Code → Cowork

Sprawdzony przepływ z XSIG/wildfire:

1. **Chat** — iterujesz nad koncepcją, diagnozujesz problem, ustalasz architekturę.
   (To, co robiliśmy przy XSIG: "most chyba naprawialiśmy, sprawdź").
2. **Code** — implementacja: pisanie modułów, testy, refaktor, git. Tu mieszka kod.
3. **Cowork** — uruchamianie pipeline'ów na danych, generowanie raportów/README,
   analiza wyników. Tu Claude działa autonomicznie na Twoich plikach.

Dla projektu fizycznego/kwantowego QHDALabs typowo: koncepcja w Chat → pipeline
w Code → przebieg + weryfikacja obserwabli w Cowork.

---

## 6. Szkielet nowego projektu

Pliki szkieletu są w tym samym archiwum (`qhdalabs_template/`). Kopiujesz cały
folder do nowego repo i zmieniasz nazwy. Zawartość opisana w `PROJECT_SKELETON.md`.

```
<NOWY-PROJEKT>/
├── .claude/
│   └── instructions.md      ← kontekst projektu dla Claude (Code/Cowork czyta)
├── src/
│   └── __init__.py
├── tests/
│   └── test_smoke.py
├── data/                    ← dane (gitignore'owane)
│   └── .gitkeep
├── notebooks/               ← eksploracja
├── README.md
├── pyproject.toml
├── .gitignore
├── requirements.txt
└── VERIFICATION_LOG.md      ← dziennik weryfikacji obserwabli (lekcja z XSIG)
```

---

## 7. Lekcja z XSIG wbudowana w szkielet

Szkielet zawiera `VERIFICATION_LOG.md` — to nie jest zwykły changelog. To miejsce
na **dziennik weryfikacji koncepcji**, wzorowany na tym, czego nauczył Cię XSIG:

- każda hipoteza zapisana zanim ją testujesz (żeby nie dopasować testu do wyniku)
- null hypothesis / kontrola jawnie zdefiniowana
- rozróżnienie "sygnał fizyczny" vs "artefakt metody" (jak King raw vs model dipola)
- wynik negatywny traktowany jako wynik, nie porażka

To jest Twój proces "zanim koncepcja stanie się teorią" — sformalizowany w pliku,
który kopiujesz do każdego projektu.

---

## 8. Uwagi praktyczne

- **Aktualizacje Cowork** czasem psują działanie. Jeśli przestanie startować VM:
  odinstaluj, pobierz starszą stabilną wersję, zainstaluj ręcznie. Sprawdź Help Center.
- **Model:** domyślnie Opus 4.8 na trybie heavy, Sonnet 4.6 na codziennym.
  Do ciężkiej weryfikacji (jak XSIG) trzymaj się Opus.
- **Limity:** zależne od planu — patrz `support.claude.com` po aktualne wartości.
- Trzymaj `qhda-core` zainstalowane editable (`pip install -e`) w środowisku
  projektu, żeby importować wspólne mechanizmy bez kopiowania kodu.

---

*Plik wygenerowany jako część frameworku QHDALabs. Kopiuj, dostosowuj, wersjonuj.*
