# Model matematyczny automatu 5 × 3

Przygotowałem model automatu z Expanding Wild w grze bazowej i 10 darmowymi spinami ze Sticky Expanding Wild. Celem było uzyskanie łącznego RTP jak najbliżej 94%. Dla opisanych niżej zasad model osiąga **93,999993% RTP**, a bonus uruchamia się średnio raz na **85,75 płatnej rundy**.

## 1. Matematyka gry

Plansza ma pięć bębnów i trzy wiersze. Używam trzech poziomych linii wypłat, po jednej na każdy wiersz. Konfiguracja w kodzie to `(0, 0, 0, 0, 0)`, `(1, 1, 1, 1, 1)` i `(2, 2, 2, 2, 2)`. Każda pozycja krotki odpowiada kolejnemu bębnowi od lewej, a wartość wskazuje wiersz.

Przyjąłem, że serię czytam od lewej do prawej i pozwalam jej zacząć się w dowolnym miejscu, w którym mieści się co najmniej trójka. Trójka może więc zająć bębny 1–3, 2–4 lub 3–5, czwórka 1–4 lub 2–5, a piątka 1–5. Na przykład `B A A A C` płaci 0,030× stawki. Na każdej linii wybieram najwyższą dostępną wypłatę, a wypłaty z trzech linii sumuję.

WILD występuje na bębnach 2, 3 i 4. Gdy pojawia się w widocznym oknie, od razu zajmuje całą kolumnę i zastępuje wyłącznie symbole A–H. Przykładowo linia `A WILD WILD WILD B` płaci 1,300× za trzy H na bębnach 2–4. W bazie ekspansja obowiązuje przez bieżący spin. W bonusie bęben pozostaje zakryty od chwili ekspansji do końca 10 darmowych spinów, a pozostałe uprawnione bębny mogą zostać zakryte w kolejnych spinach.

FS służy do uruchamiania bonusu. Sprawdzam, czy pojawił się na każdym z bębnów 1, 3 i 5, zanim rozszerzę WILD. Jeśli oba symbole wypadną na bębnie 3, wylosowany FS nadal liczy się do warunku startu. W bonusie taśmy nie zawierają FS i nie ma możliwości ponownego uruchomienia funkcji.

### Tabela wypłat

Każda wartość jest mnożnikiem **całkowitej stawki** za wygraną na jednej linii. WILD i FS nie mają osobnych wypłat w tabeli.

| Symbol | 3 kolejne | 4 kolejne | 5 kolejnych |
| --- | ---: | ---: | ---: |
| A | 0,030× | 0,050× | 0,090× |
| B | 0,040× | 0,060× | 0,110× |
| C | 0,050× | 0,080× | 0,140× |
| D | 0,060× | 0,100× | 0,180× |
| E | 0,075× | 0,130× | 0,240× |
| F | 1,050× | 1,500× | 2,500× |
| G | 1,150× | 1,800× | 3,500× |
| H | 1,300× | 2,200× | 5,000× |

### Taśmy bębnów

Każdy ciąg przedstawia 21 kolejnych pozycji na cyklicznej taśmie. Losuję po jednej pozycji na bęben, a na planszy pokazuję tę pozycję i dwie następne. Po końcu taśmy wracam na jej początek. `W` oznacza WILD, a `S` oznacza FS.

| Bęben | Gra bazowa | Darmowe spiny |
| --- | --- | --- |
| 1 | `DBCDSHDFGCABCDEABSDEA` | `ABCEDAFGHBABCDEABCDEA` |
| 2 | `DGWAWWFCHBAWDCAWEDEAB` | `DBGHWAEFWBBCDEABCDEAB` |
| 3 | `HABSWCAFDGCDEABWDEWBC` | `FADCEBWHGACDEABCDEABC` |
| 4 | `FWCDBHGAEADEABCDWABCD` | `WWEABHDGFBDEABCDEABCD` |
| 5 | `BCGHDEDFSBEABCDEASCDE` | `GEHBDACFABEABCDEABCDE` |

## 2. Analiza RTP

RTP odnosi się do sumy stawek z płatnych rund. Do wypłaty z rundy wliczam zarówno wygraną z bazowego spinu, jak i wypłaty ze wszystkich darmowych spinów, które ten spin uruchomił.

| Miernik | Wynik teoretyczny |
| --- | ---: |
| Cel RTP | 94% |
| RTP gry bazowej | 73,588768% |
| Wkład darmowych spinów do łącznego RTP | 20,411225 p.p. |
| **Łączne RTP** | **93,999993%** |
| Średnia suma wypłat z uruchomionego bonusu | 17,5026× stawki |

Średnia wypłata z uruchomionego bonusu jest wartością warunkową. Żeby otrzymać jego wkład przypadający na płatną rundę, mnożę tę średnią przez prawdopodobieństwo uruchomienia bonusu.

## 3. Częstotliwość Free Spins

FS jest widoczny przy 6 z 21 zatrzymań na bębnie 1, 3 z 21 na bębnie 3 oraz 6 z 21 na bębnie 5. Ponieważ zatrzymania bębnów są niezależne, prawdopodobieństwo jednoczesnego trafienia wynosi:

`P(bonus) = (6/21) × (3/21) × (6/21) = 4/343 ≈ 1,166181%`

Daje to średnio **jedno uruchomienie bonusu na 85,75 płatnej rundy**.

## 4. Metodyka obliczeń i symulacji

W grze bazowej dla każdego bębna zliczam symbole widoczne w danym wierszu po ekspansji WILD. Dla każdej linii łączę rozkłady z pięciu niezależnych bębnów, mnożę wypłatę za dany układ przez jego prawdopodobieństwo i sumuję wyniki. Wartość oczekiwana pozwala dodać średnie wypłaty z linii, nawet gdy wyniki poszczególnych linii są zależne.

W bonusie WILD jest widoczny przy 6, 3 i 4 zatrzymaniach z 21 odpowiednio na bębnach 2, 3 i 4. Jeżeli `w` to liczba takich zatrzymań na danym bębnie, prawdopodobieństwo, że bęben jest już zakryty w chwili oceny spinu numer `t`, wynosi `1 − (1 − w/21)^t`. Dla każdego z 10 spinów liczę średnią wypłatę z rozkładów uwzględniających te zakrycia. Sumuję średnie wypłaty, a następnie mnożę sumę przez prawdopodobieństwo startu bonusu. Do obliczeń teoretycznych używam dokładnych ułamków, a wyniki zaokrąglam do prezentacji.

Jako sprawdzenie uruchomiłem symulację Monte Carlo dla 1 000 000 płatnych rund z ziarnem `2026`. Otrzymałem RTP **93,9401%** przy błędzie standardowym **0,2633 p.p.** Bonus uruchomił się **11 701 razy** i wniósł **20,4231 p.p.** do RTP.

| Łączna wypłata z rundy | Odsetek rund w symulacji |
| --- | ---: |
| Brak wypłaty | 34,0277% |
| Dodatnia wypłata poniżej stawki | 36,1543% |
| Zwrot stawki | 0,0000% |
| Wypłata powyżej stawki | 29,8180% |

## 5. Uzasadnienie decyzji projektowych

**Liczba symboli i rozkład.** Wybrałem 10 symboli, aby rozdzielić zwykłe trafienia na pięć częstszych symboli A–E i trzy rzadsze F–H, a WILD i FS przypisać osobnym funkcjom. Każdy z F, G i H zajmuje po jednej pozycji na każdej taśmie. A–E wypełniają większość pozycji. Trzy proste linie pozwalają śledzić wypłaty bez rysowania dodatkowych ścieżek na planszy.

**Wypłaty i zmienność.** Chciałem, żeby baza regularnie dawała drobne wypłaty, a rzadsze trafienia dawały wyraźny zysk. Nawet pięć symboli A–E daje na linii od 0,090× do 0,240× stawki, a już trzy F, G lub H dają ponad 1×. W symulacji wypłatę otrzymało 65,9723% rund, ale zysk wystąpił w 29,8180% rund. Odchylenie standardowe łącznej wypłaty wyniosło 2,6330× stawki. W bonusie zakryte bębny przechodzą na kolejne spiny, więc wczesny WILD może wpływać na kilka wypłat w ramach tej samej rundy. Pozwala to skupić większe wypłaty w rzadszej funkcji.

**Podział RTP i strojenie.** Chciałem, żeby większość zwrotu pochodziła z gry bazowej, a bonus wnosił około 20 p.p., co nadaje znaczenie jego uruchomieniu. Żeby wyregulować częstość funkcji, dodałem po jednej pozycji FS na bębnach 1 i 5. W bonusie dodałem po jednej pozycji WILD na bębnach 2 i 4. W bazie zmniejszyłem liczbę pozycji WILD na bębnie 4 z trzech do dwóch, by dostroić łączne RTP. Porównałem długości taśm i wzorce uzupełniania ich zwykłymi symbolami. Konfiguracja z 21 pozycjami i wzorcem `ABCDE` pozwoliła osiągnąć założony podział oraz wynik bliski 94%. Liczy się też kolejność symboli na taśmie. Dwa sąsiednie WILD-y mogą wpaść w to samo widoczne okno i dać jedną ekspansję.

## 6. Pliki źródłowe i weryfikacja

- `main2.py` zawiera reguły gry, tabelę wypłat, taśmy, obliczenia teoretyczne, symulację i testy.
- `strojenie_tasm.py` porównuje konfiguracje taśm i sortuje je według odległości od celu RTP.

Wymagany jest Python 3.9 lub nowszy. Wystarczy biblioteka standardowa.

```powershell
python -X utf8 main2.py --test-only
python -X utf8 main2.py --exact
python -X utf8 main2.py --rounds 1000000 --seed 2026
python -X utf8 strojenie_tasm.py --min-length 21 --max-length 21 --top 1
```

Polecenia kolejno sprawdzają reguły gry, obliczają RTP teoretyczne, odtwarzają symulację i generują taśmy konfiguracji opisanej powyżej.
