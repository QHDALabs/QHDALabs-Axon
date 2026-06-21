# Dziennik weryfikacji — <NAZWA PROJEKTU>

> Nie changelog. Dziennik weryfikacji koncepcji — proces "zanim koncepcja
> stanie się teorią". Wzorzec wypracowany w XSIG.

## Jak używać

Dla każdej hipotezy/obserwabli, JEDEN wpis, w tej kolejności (nie zmieniaj kolejności
— zapisanie hipotezy PRZED testem chroni przed dopasowaniem testu do wyniku):

```
### [data] Hipoteza: <nazwa>

**Pytanie:** co dokładnie testujemy (jedno zdanie)
**Hipoteza:** czego się spodziewam i dlaczego
**Null / kontrola:** jak wygląda "brak efektu" (bootstrap? permutacja? constant?)
**Metryka:** co mierzę, jaki próg istotności
**Ryzyko artefaktu:** co mogłoby dać fałszywy sygnał (model gładki? za mało punktów?)

--- granica: poniżej dopisuję PO uruchomieniu ---

**Wynik:** liczby
**Interpretacja:** sygnał fizyczny / artefakt / null — i dlaczego
**Decyzja:** następny krok
```

## Zasady (twarde, z XSIG)

1. **Hipoteza przed testem.** Jeśli dopisujesz hipotezę po zobaczeniu wyniku — to nie jest weryfikacja.
2. **Null jawny.** "Brak efektu" musi mieć konkretną, liczbową postać.
3. **Surowe > gładkie.** Model parametryczny może dawać fałszywy sygnał z samej gładkości
   (lekcja King raw vs dipol α: z=1.29 → z=−0.66 po zamianie na surowe dane).
4. **Rozdzielczość.** Za mało permutacji = gruba p-value = fałszywe wnioski
   (lekcja: 30 permutacji dało z=+1.17, 500 dało z=−0.66 — znak się odwrócił).
5. **Null to wynik.** Negatywny rezultat uzyskany rygorystyczną metodą jest publikowalny.
6. **QC koduje, nie poświadcza.** "Przepuściłem przez procesor kwantowy" nie jest
   dowodem. Weryfikuje metoda (kontrola, null, statystyka), nie kwantowość obliczenia.

---

## Wpisy

### [RRRR-MM-DD] Hipoteza: <pierwsza>

**Pytanie:**
**Hipoteza:**
**Null / kontrola:**
**Metryka:**
**Ryzyko artefaktu:**

<!-- wynik dopisz po uruchomieniu -->
