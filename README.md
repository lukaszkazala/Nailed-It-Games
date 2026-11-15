# Model matematyczny automatu 5 × 3

Przygotowałem ten model w ramach zadania rekrutacyjnego na stanowisko Junior Game Mathematician w Nailed It Games. Celem było uzyskanie RTP bliskiego 94% dla gry z Expanding Wild i bonusem 10 darmowych spinów.

## Jak działa gra

Gra ma 5 bębnów, 3 rzędy i 20 linii wypłat. Każdy bęben ma cykliczną taśmę z 21 pozycjami. Na planszy widać po trzy kolejne pozycje z każdej taśmy. W modelu jest 10 rodzajów symboli: A–H, WILD i FS.

- Na linii płacą serie co najmniej trzech kolejnych dopasowań. Seria może zaczynać się w środku linii. Na przykład `B A A A C` daje wypłatę za trzy A. Jeśli pasuje kilka kombinacji, wybieram tę z najwyższą wypłatą. Wypłaty ze wszystkich linii sumuję.
- W grze bazowej WILD rozszerza się na cały bęben i zastępuje symbole A–H.
- Bonus uruchamia się, gdy FS jest widoczny na każdym z bębnów 1, 3 i 5. Sprawdzam to przed rozszerzeniem WILD-a.
- W bonusie gracz dostaje 10 darmowych spinów. Gdy na bębnie pojawi się WILD, zajmuje cały bęben od tego spinu do końca bonusu.

## Wyniki teoretyczne

| Co mierzę | Wynik |
| --- | ---: |
| Docelowe RTP | 94% |
| RTP z gry bazowej | 69,708958% |
| Wkład darmowych spinów do całkowitego RTP | 24,292999 p.p. |
| **Całkowite RTP** | **94,001957%** |
| Częstotliwość bonusu | 0,291545%, średnio raz na 343 płatne rundy |
| Średnia łączna wypłata z uruchomionego bonusu | 83,3250× stawki |

## Co ile rund gracz wychodzi na plus

W symulacji miliona płatnych rund gracz wyszedł na plus **108 726 razy (10,8726%)**, czyli średnio **raz na 9,2 zagrania**. Liczyłem łączną wypłatę z płatnego spinu i ze wszystkich darmowych spinów, które ten spin uruchomił. Przy stawce 1 zł wypłata 0,60 zł daje stratę 0,40 zł.

| Wynik płatnej rundy | Odsetek rund |
| --- | ---: |
| Brak wypłaty | 21,5514% |
| Dodatnia wypłata poniżej stawki | 67,5547% |
| Zwrot całej stawki | 0,0213% |
| **Wypłata powyżej stawki** | **10,8726%** |

W tej próbie RTP wyniosło 94,7402% przy błędzie standardowym 0,6741 p.p. Odchylenie standardowe wypłaty na rundę wyniosło 6,7408× stawki.

## Jak policzyłem RTP

Każda z 21 pozycji na danym bębnie ma taką samą szansę wylosowania, a bębny losuję niezależnie. W grze bazowej liczę średnią wypłatę dla każdej linii i dodaję wyniki. Na każdym z bębnów 1, 3 i 5 symbol FS widać przy 3 z 21 możliwych zatrzymań, więc szansa na bonus wynosi `(3/21)^3 = 1/343`.

W bonusie uwzględniam, że WILD może zostać na bębnie z poprzednich spinów. Po `t` spinach szansa, że bęben z WILD-em na taśmie jest już zakryty, wynosi `1 − (18/21)^t`. Sumuję średnie wypłaty z 10 spinów i mnożę przez szansę uruchomienia bonusu. Tak otrzymuję wkład darmowych spinów w RTP jednej płatnej rundy.

## Jak dobrałem wypłaty i taśmy

Chciałem uzyskać częste małe wypłaty oraz rzadsze, wyższe trafienia. Pięć symboli A–E na jednej linii daje od 0,09× do 0,24× całkowitej stawki. Już trzy F, G lub H na jednej linii dają odpowiednio 1,05×, 1,15× albo 1,30× stawki.

Wydłużenie taśm z 10 do 21 pozycji zmniejszyło szansę na pojawienie się WILD-a na bębnie, który ma go na taśmie, z 30% do 14,29%. Dodatkowe miejsca przeznaczyłem na symbole A–E. Po tej zmianie RTP wynosiło 94,295090%. Następnie obniżyłem wypłatę za trzy E z 0,080× do 0,075× stawki i uzyskałem 94,001957%.

## Jak uruchomić

Wystarczy Python z biblioteką standardową.

```powershell
python -X utf8 main2.py --test-only
python -X utf8 main2.py --exact
python -X utf8 main2.py --rounds 1000000 --seed 2026
```

Pierwsze polecenie uruchamia testy reguł gry, drugie liczy wyniki teoretyczne, a trzecie odtwarza symulację. Stałe ziarno `2026` pozwala powtórzyć tę samą próbę. W `main2.py` są też taśmy, linie i tabela wypłat. Do sprawdzania różnych konfiguracji taśm służy `strojenie_tasm.py`.
