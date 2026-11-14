# Model matematyczny automatu 5 × 3

Docelowe RTP wynosi 94%. Wypłaty w `PAYTABLE` są wielokrotnością całkowitej stawki za spin. Konfiguracja 20 linii oraz cykliczne taśmy obu trybów są w `main.py`. Model ma 10 rodzajów symboli. Każda z pięciu taśm w każdym trybie zawiera 21 pozycji.

| Wynik teoretyczny | Wartość |
| --- | ---: |
| RTP gry bazowej | 69,708958% |
| Wkład darmowych spinów do RTP | 24,292999 p.p. |
| Całkowite RTP | **94,001957%** |
| Różnica względem celu | +0,001957 p.p. |
| Częstotliwość bonusu | 0,291545% (1 na 343 płatne rundy) |
| Średnia łączna wypłata z 10 darmowych spinów | 83,3250× stawki |

## Uruchomienie

```powershell
python -X utf8 main.py --test-only
python -X utf8 main.py --exact
python -X utf8 main.py --rounds 1000000 --seed 2026
```

Kod korzysta z biblioteki standardowej Pythona. Tryb `--exact` oblicza wartości oczekiwane na ułamkach. Tryb symulacji podaje również odchylenie standardowe wypłaty na płatną rundę i błąd standardowy estymacji RTP.

## Weryfikacja integralności kodu

`sprawdz_integralnosc.py` oblicza SHA-256 pliku `main.py`, który zawiera taśmy, tabelę wypłat, linie i reguły gry. Po zakończeniu testów danej wersji zapisz jej hash referencyjny w raporcie. Weryfikujący pobiera go z zaufanej kopii raportu i porównuje z hashem otrzymanego pliku. Zmiana treści pliku, w tym końców linii, wpływa na skrót.

```powershell
python -X utf8 sprawdz_integralnosc.py main.py
python -X utf8 sprawdz_integralnosc.py main.py --verify HASH_Z_RAPORTU
```

Zastąp `HASH_Z_RAPORTU` 64-znakowym hashem referencyjnym. Kod wyjścia `0` oznacza zgodność, `1` rozbieżność, a `2` błąd argumentu lub odczytu pliku.

To demonstracja kontroli integralności jednego pliku modelu. Ocena RNG i certyfikacja całego systemu wymagają odrębnych badań. Generator `random.Random(seed)` służy do odtwarzalnej symulacji. [GLI-19 v4.0, § 2.3 i rozdział 5](https://gaminglabs.com/wp-content/uploads/2026/11/GLI-19-v4.0-Standards-for-Interactive-Gaming-Systems.pdf)

## Obliczenia i parametry

1. Każdy stop na taśmie jest jednakowo prawdopodobny. Z wybranego stopu odczytujemy trzy kolejne pozycje. Przed oceną linii WILD rozszerza się na całą kolumnę. Rozkłady symboli w wybranych rzędach są niezależne między bębnami. Wartości oczekiwane 20 wypłat liniowych można sumować także wtedy, gdy linie współdzielą pola.
2. Każdy z bębnów 1, 3 i 5 pokazuje FS w trzech stopach z 21. Stąd prawdopodobieństwo bonusu wynosi `(3/21)^3 = 1/343`. Symbol FS liczymy przed rozszerzeniem WILD. Na linii model wypłaca najwyżej wycenioną serię złożoną z co najmniej trzech kolejnych dopasowań. Może się ona zacząć w środku linii, np. `B A A A C` daje wypłatę za `3×A`.
3. W darmowym spinie `t` prawdopodobieństwo, że dany dozwolony bęben jest już w całości WILD, wynosi `1 − (18/21)^t`. Oczekiwane wypłaty kolejnych spinów sumujemy, a wynik mnożymy przez `1/343`, aby otrzymać wkład bonusu do RTP na płatną rundę.
4. Wydłużenie taśm z 10 do 21 pozycji obniżyło prawdopodobieństwo widocznego WILD-a na uprawnionym bębnie z 30% do ok. 14,29%. Dodane pozycje służą częstszym, niskim wypłatom za A–E. Pięć takich symboli na jednej linii płaci od 0,09× do 0,24× stawki. Już trzy F, G lub H na jednej linii płacą odpowiednio 1,05×, 1,15× oraz 1,30×. Po wydłużeniu taśm RTP wynosiło 94,295090%. Zmiana wypłaty za `3×E` z 0,080× na 0,075× obniżyła je o ok. 0,293133 p.p.

W symulacji miliona płatnych rund RTP wyniosło 94,7402%, przy błędzie standardowym 0,6741 p.p. W 21,5514% rund wypłata wyniosła zero, w 67,5547% była dodatnia i poniżej stawki, w 0,0213% była równa stawce, a w 10,8726% przekroczyła stawkę. Kategoria rundy obejmuje wypłatę bazową i ewentualną całą sesję bonusową.
