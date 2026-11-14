"""Dobiera taśmy automatu 5 × 3 na podstawie teoretycznego RTP."""

import argparse
from collections import Counter
from fractions import Fraction
from functools import cache
from itertools import product
from math import lcm, prod


# W oznacza WILD, S oznacza symbol uruchamiający darmowe spiny.
SYMBOLS = "ABCDEFGHWS"
WILD = "W"
FREE_SPINS = "S"
FREE_SPIN_COUNT = 10
FS_REELS = (0, 2, 4)

# Wypłaty za 3, 4 i 5 symboli jako wielokrotność całej stawki.
PAYTABLE = {
    "A": (0.030, 0.05, 0.09),
    "B": (0.040, 0.06, 0.11),
    "C": (0.050, 0.08, 0.14),
    "D": (0.060, 0.10, 0.18),
    "E": (0.075, 0.13, 0.24),
    "F": (1.050, 1.50, 2.50),
    "G": (1.150, 1.80, 3.50),
    "H": (1.300, 2.20, 5.00),
}

PAYLINES = (
    (0, 0, 0, 0, 0), (1, 1, 1, 1, 1), (2, 2, 2, 2, 2),
    (0, 1, 2, 1, 0), (2, 1, 0, 1, 2),
    (0, 0, 1, 2, 2), (2, 2, 1, 0, 0),
    (0, 1, 1, 1, 0), (2, 1, 1, 1, 2),
    (1, 0, 0, 0, 1), (1, 2, 2, 2, 1),
    (0, 1, 0, 1, 0), (2, 1, 2, 1, 2),
    (1, 0, 1, 0, 1), (1, 2, 1, 2, 1),
    (0, 2, 0, 2, 0), (2, 0, 2, 0, 2),
    (0, 0, 2, 0, 0), (2, 2, 0, 2, 2),
    (1, 0, 2, 0, 1),
)

# Rdzenie obejmują dotychczasowe pozycje 1–10. Dalsze pozycje
# dopisujemy ze wzorca A–H, zaczynając w innym miejscu na każdym bębnie.
BASE_CORES = (
    "ABCDSHEFGA", "DGBAWEFCHB", "HEASWCBFDG", "FACDBHGWEA", "BCGHAEDFSB",
)
BONUS_CORES = (
    "ABCEDAFGHB", "DBGHWAEFCB", "FADCEBWHGA", "CWEABHDGFB", "GEHBDACFAB",
)


def build_tapes(cores, length, fill):
    tapes = []
    for reel, core in enumerate(cores):
        extra = "".join(fill[(reel + pos) % len(fill)] for pos in range(length - len(core)))
        tapes.append(core + extra)
    return tuple(tapes)


def make_line_evaluator():
    # Liczymy na liczbach całkowitych, np. 0,075× zapisujemy jako 15 jednostek
    # przy 200 jednostkach na stawkę. Wynik RTP pozostaje ułamkiem dokładnym.
    exact_table = {
        symbol: tuple(Fraction(str(pay)) for pay in payouts)
        for symbol, payouts in PAYTABLE.items()
    }
    units_per_stake = lcm(*(
        pay.denominator for payouts in exact_table.values() for pay in payouts
    ))
    pay_units = {
        symbol: tuple(int(pay * units_per_stake) for pay in payouts)
        for symbol, payouts in exact_table.items()
    }
    ordinary_symbols = tuple(pay_units)

    @cache
    def line_win(line):
        # Na linii 5-polowej każda seria 3–5 symboli obejmuje środkowe pole.
        middle = line[2]
        if middle == FREE_SPINS:
            return 0

        candidates = ordinary_symbols if middle == WILD else (middle,)
        best_payout = 0
        for symbol in candidates:
            matching = (symbol, WILD)
            start = end = 2
            while start > 0 and line[start - 1] in matching:
                start -= 1
            while end < 4 and line[end + 1] in matching:
                end += 1
            count = end - start + 1
            if count >= 3:
                best_payout = max(best_payout, pay_units[symbol][count - 3])
        return best_payout

    return line_win, units_per_stake


def reel_counts(tape):
    """Zlicza widoczne symbole po ekspansji oraz stopy z FS przed ekspansją."""
    rows = [Counter() for _ in range(3)]
    fs_stops = 0
    for stop in range(len(tape)):
        window = tuple(tape[(stop + row) % len(tape)] for row in range(3))
        fs_stops += FREE_SPINS in window
        if WILD in window:
            window = (WILD,) * 3
        for row, symbol in enumerate(window):
            rows[row][symbol] += 1
    return rows, fs_stops


def make_board_evaluator(line_win, units_per_stake):
    @cache
    def weighted_line(distributions):
        total = 0
        for combination in product(*distributions):
            symbols, counts = zip(*combination)
            total += line_win(symbols) * prod(counts)
        return total

    def board_value(reel_rows):
        # Po wybraniu stanu WILD każdy symbol linii pochodzi z innego bębna.
        # Liniowość wartości oczekiwanej pozwala zsumować wszystkie 20 linii.
        row_options = [[tuple(sorted(row.items())) for row in reel] for reel in reel_rows]
        stop_combinations = prod(sum(reel[0].values()) for reel in reel_rows)
        total = sum(
            weighted_line(tuple(row_options[reel][row] for reel, row in enumerate(line)))
            for line in PAYLINES
        )
        return Fraction(total, stop_combinations * units_per_stake)

    return board_value


def base_values(tapes, board_value):
    counts = [reel_counts(tape) for tape in tapes]
    bonus_frequency = prod(Fraction(counts[reel][1], len(tapes[reel])) for reel in FS_REELS)
    return board_value([rows for rows, _ in counts]), bonus_frequency


def bonus_value(tapes, board_value):
    """Średnia suma wypłat z 10 spinów, pod warunkiem uruchomienia bonusu."""
    rows = [reel_counts(tape)[0] for tape in tapes]
    no_wild = [Fraction(len(tape) - reel[0][WILD], len(tape)) for tape, reel in zip(tapes, rows)]
    ordinary_rows = [[{s: n for s, n in row.items() if s != WILD} for row in reel] for reel in rows]
    wild_rows = [{WILD: 1}] * 3

    # Tylko bębny 2–4 mogą zostać zablokowane. Dla każdego z 8 stanów
    # wartość planszy liczymy raz i ważymy szansą stanu w spinach 1–10.
    reel_states = [(False,) if p == 1 else (False, True) for p in no_wild]
    unlocked_at_spin = [[p ** spin for p in no_wild] for spin in range(1, FREE_SPIN_COUNT + 1)]
    total = Fraction(0)
    for locked in product(*reel_states):
        timing_weight = sum(
            prod(1 - p if is_locked else p for p, is_locked in zip(unlocked, locked))
            for unlocked in unlocked_at_spin
        )
        if timing_weight:
            board_rows = [wild_rows if is_locked else reel for reel, is_locked in zip(ordinary_rows, locked)]
            total += timing_weight * board_value(board_rows)
    return total


def search_tapes(lengths, fills, target, separate_lengths):
    line_win, units_per_stake = make_line_evaluator()
    board_value = make_board_evaluator(line_win, units_per_stake)
    base_options = {}
    bonus_options = {}

    # Każdą taśmę liczymy raz. Wkład bonusu zależy od dwóch liczb,
    # które możemy policzyć niezależnie: częstości startu i średniej wypłaty.
    for length, fill in product(lengths, fills):
        base = build_tapes(BASE_CORES, length, fill)
        bonus = build_tapes(BONUS_CORES, length, fill)
        base_options[length, fill] = (*base_values(base, board_value), base)
        bonus_options[length, fill] = (bonus_value(bonus, board_value), bonus)

    candidates = []
    for base_key, (base_rtp, frequency, base) in base_options.items():
        compatible_bonus_keys = bonus_options if separate_lengths else (base_key,)
        for bonus_key in compatible_bonus_keys:
            average_bonus, bonus = bonus_options[bonus_key]
            bonus_rtp = frequency * average_bonus
            total_rtp = base_rtp + bonus_rtp
            candidates.append({
                "base_key": base_key,
                "bonus_key": bonus_key,
                "base_tapes": base,
                "bonus_tapes": bonus,
                "base_rtp": base_rtp,
                "bonus_rtp": bonus_rtp,
                "total_rtp": total_rtp,
                "bonus_frequency": frequency,
                "average_bonus": average_bonus,
                "gap": total_rtp - target,
            })

    # Przy remisie pierwszeństwo ma konfiguracja z krótszymi taśmami.
    return sorted(candidates, key=lambda item: (
        abs(item["gap"]), item["base_key"][0] + item["bonus_key"][0],
    ))


def print_tape_composition(name, tapes):
    print(f"\n{name} = (")
    for tape in tapes:
        print(f'    "{tape}",')
    print(")")
    print(f"{'Bęben':>5} | " + " ".join(f"{s:>4}" for s in (*SYMBOLS[:8], "WILD", "FS")))
    for reel, tape in enumerate(tapes, start=1):
        counts = Counter(tape)
        print(f"{reel:>5} | " + " ".join(f"{counts[s]:>4}" for s in SYMBOLS))


def print_results(candidates, target, top):
    print(f"Cel: {float(target):.4%}. Liczba sprawdzonych konfiguracji: {len(candidates)}.")
    print("Długość/wzorzec bazy   Długość/wzorzec bonusu    RTP bazy    Wkład FS    RTP razem    Różnica [p.p.]")
    for item in candidates[:top]:
        base_length, base_fill = item["base_key"]
        bonus_length, bonus_fill = item["bonus_key"]
        print(
            f"{f'{base_length}/{base_fill}':<22} {f'{bonus_length}/{bonus_fill}':<23}"
            f"{float(item['base_rtp']):>9.4%} {100 * float(item['bonus_rtp']):>9.4f}"
            f" {float(item['total_rtp']):>11.6%} {100 * float(item['gap']):>+16.6f}"
        )

    best = candidates[0]
    print(f"\nNajbliżej celu: {float(best['total_rtp']):.6%} RTP.")
    print(f"Bonus średnio raz na {float(1 / best['bonus_frequency']):.2f} płatnych rund.")
    print(f"Średnia wypłata z całego bonusu: {float(best['average_bonus']):.4f}× stawki.")
    print_tape_composition("BASE_TAPES", best["base_tapes"])
    print_tape_composition("BONUS_TAPES", best["bonus_tapes"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-length", type=int, default=19, help="najkrótsza taśma")
    parser.add_argument("--max-length", type=int, default=23, help="najdłuższa taśma")
    parser.add_argument("--target", type=Fraction, default="94", help="docelowe RTP w procentach")
    parser.add_argument("--fill", action="append", help="wzorzec dopisywania A–H, można podać wielokrotnie")
    parser.add_argument("--separate-lengths", action="store_true", help="dobierz taśmy bazy i bonusu osobno")
    parser.add_argument("--top", type=int, default=10, help="liczba najlepszych wyników w tabeli")
    args = parser.parse_args()

    min_core_length = max(map(len, BASE_CORES + BONUS_CORES))
    if not min_core_length <= args.min_length <= args.max_length:
        parser.error(f"długości muszą spełniać {min_core_length} <= --min-length <= --max-length")
    if args.target <= 0 or args.top <= 0:
        parser.error("--target i --top muszą być dodatnie")
    fills = tuple(dict.fromkeys(fill.upper() for fill in (args.fill or ["ABCDE"])))
    if any(not fill or not set(fill) <= set(PAYTABLE) for fill in fills):
        parser.error("każdy --fill musi zawierać wyłącznie zwykłe symbole A–H")

    target = args.target / 100
    lengths = range(args.min_length, args.max_length + 1)
    candidates = search_tapes(lengths, fills, target, args.separate_lengths)
    print_results(candidates, target, args.top)


if __name__ == "__main__":
    main()
