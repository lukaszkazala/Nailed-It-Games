import argparse
import math
import random
from collections import Counter
from fractions import Fraction
from functools import cache
from itertools import product
from unittest.mock import patch


WILD = "WILD"
FS = "FS"
STAKE = 1.0
TARGET_RTP = Fraction(94, 100)
FREE_SPIN_COUNT = 10
FS_REELS = (0, 2, 4)

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

# Mnożniki całkowitej stawki za 3, 4 i 5 kolejnych dopasowań.
PAYTABLE = {
    "A": (0.03, 0.05, 0.09),
    "B": (0.04, 0.06, 0.11),
    "C": (0.05, 0.08, 0.14),
    "D": (0.06, 0.10, 0.18),
    "E": (0.075, 0.13, 0.24),
    "F": (1.05, 1.50, 2.50),
    "G": (1.15, 1.80, 3.50),
    "H": (1.30, 2.20, 5.00),
}

# Każdy napis to 21 kolejnych pozycji jednej cyklicznej taśmy.
# Taśmy są w kolejności bębnów 1–5. W = WILD, S = FS.
BASE_TAPES = (
    "ABCDSHEFGAABCDEABCDEA",
    "DGBAWEFCHBBCDEABCDEAB",
    "HEASWCBFDGCDEABCDEABC",
    "FACDBHGWEADEABCDEABCD",
    "BCGHAEDFSBEABCDEABCDE",
)

BONUS_TAPES = (
    "ABCEDAFGHBABCDEABCDEA",
    "DBGHWAEFCBBCDEABCDEAB",
    "FADCEBWHGACDEABCDEABC",
    "CWEABHDGFBDEABCDEABCD",
    "GEHBDACFABEABCDEABCDE",
)


def decode_strips(tapes):
    special_symbols = {"W": WILD, "S": FS}
    return tuple(
        tuple(special_symbols.get(code, code) for code in tape)
        for tape in tapes
    )


BASE_STRIPS = decode_strips(BASE_TAPES)
BONUS_STRIPS = decode_strips(BONUS_TAPES)


def reel_window(strip, stop):
    return tuple(strip[(stop + row) % len(strip)] for row in range(3))


def spin_board(reel_strips, rng):
    """Zwraca planszę w układzie board[bęben][rząd]."""
    board = []
    for strip in reel_strips:
        stop = rng.randrange(len(strip))
        board.append(reel_window(strip, stop))
    return tuple(board)


def evaluate_payline(line, paytable):
    """Zwraca (symbol, indeks początku, długość, mnożnik) lub None."""
    # Na linii z 5 pól każda seria długości co najmniej 3 obejmuje środek.
    middle = line[2]
    if middle == FS:
        return None

    candidates = sorted(paytable) if middle == WILD else (middle,)
    best_win = None
    best_rank = None

    for symbol in candidates:
        matching_symbols = (symbol, WILD)
        start = end = 2

        while start > 0 and line[start - 1] in matching_symbols:
            start -= 1
        while end < 4 and line[end + 1] in matching_symbols:
            end += 1

        count = end - start + 1
        if count < 3:
            continue

        # Krótsza podseria tego samego symbolu płaci mniej.
        payout = paytable[symbol][count - 3]
        rank = (payout, -start, count)

        # Przy pełnym remisie zachowujemy pierwszy symbol alfabetycznie.
        if best_rank is None or rank > best_rank:
            best_rank = rank
            best_win = (symbol, start, count, payout)

    return best_win


def evaluate_board(board, paylines, paytable):
    """Sumuje mnożniki ze wszystkich aktywnych linii."""
    total = 0.0
    for r0, r1, r2, r3, r4 in paylines:
        line = (
            board[0][r0], board[1][r1], board[2][r2],
            board[3][r3], board[4][r4],
        )
        win = evaluate_payline(line, paytable)
        if win is not None:
            total += win[3]
    return total


def reels_with_wild(board):
    return {reel for reel, column in enumerate(board) if WILD in column}


def expand_wilds(board, wild_reels):
    return tuple(
        (WILD, WILD, WILD) if reel in wild_reels else column
        for reel, column in enumerate(board)
    )


def triggers_free_spins(board):
    return all(FS in board[reel] for reel in FS_REELS)


def play_free_spins(rng, stake=STAKE):
    sticky_reels = set()
    free_spins_win = 0.0

    for _ in range(FREE_SPIN_COUNT):
        board = spin_board(BONUS_STRIPS, rng)
        sticky_reels.update(reels_with_wild(board))
        payout_board = expand_wilds(board, sticky_reels)
        free_spins_win += stake * evaluate_board(payout_board, PAYLINES, PAYTABLE)

    return free_spins_win


def play_round(rng, stake=STAKE):
    original_board = spin_board(BASE_STRIPS, rng)
    bonus_triggered = triggers_free_spins(original_board)

    payout_board = expand_wilds(original_board, reels_with_wild(original_board))
    base_win = stake * evaluate_board(payout_board, PAYLINES, PAYTABLE)
    free_spins_win = play_free_spins(rng, stake) if bonus_triggered else 0.0

    return base_win, free_spins_win, bonus_triggered


def reel_frequencies(strip):
    """Zlicza symbole w wierszach po ekspansji, a FS przed ekspansją."""
    rows = [Counter() for _ in range(3)]
    wild_stops = fs_stops = 0

    for stop in range(len(strip)):
        column = reel_window(strip, stop)
        fs_stops += FS in column
        if WILD in column:
            wild_stops += 1
            column = (WILD,) * 3

        for row, symbol in enumerate(column):
            rows[row][symbol] += 1

    return rows, wild_stops, fs_stops


def expected_board_win(reel_rows, reel_outcome_counts, payline_units):
    """Liczy wartość oczekiwaną sumy wypłat w jednostkach paytable."""
    weighted_payout = 0
    for line in PAYLINES:
        # Bębny losują niezależnie. Mnożymy liczby sposobów uzyskania
        # każdego symbolu na wybranej linii. Linie mogą współdzielić pola.
        distributions = [reel_rows[reel][row].items() for reel, row in enumerate(line)]
        for combination in product(*distributions):
            symbols, counts = zip(*combination)
            payout = payline_units(symbols)
            weighted_payout += payout * math.prod(counts)

    return Fraction(weighted_payout, math.prod(reel_outcome_counts))


def exact_metrics(paytable=PAYTABLE):
    # Ułamki zachowują dziesiętne wartości paytable przy obliczaniu RTP i remisów.
    exact_paytable = {
        symbol: tuple(Fraction(str(payout)) for payout in payouts)
        for symbol, payouts in paytable.items()
    }
    units_per_stake = math.lcm(*(
        payout.denominator for payouts in exact_paytable.values() for payout in payouts
    ))

    @cache
    def payline_units(symbols):
        win = evaluate_payline(symbols, exact_paytable)
        return int(win[3] * units_per_stake) if win else 0

    base_frequencies = [reel_frequencies(strip) for strip in BASE_STRIPS]
    base_lengths = [len(strip) for strip in BASE_STRIPS]
    base_units = expected_board_win(
        [rows for rows, _, _ in base_frequencies], base_lengths, payline_units,
    )
    bonus_frequency = math.prod(
        Fraction(base_frequencies[reel][2], base_lengths[reel]) for reel in FS_REELS
    )

    bonus_frequencies = [reel_frequencies(strip) for strip in BONUS_STRIPS]
    bonus_lengths = [len(strip) for strip in BONUS_STRIPS]
    bonus_units = Fraction(0)

    for spin in range(1, FREE_SPIN_COUNT + 1):
        sticky_rows = []
        for length, (rows, wild_stops, _) in zip(bonus_lengths, bonus_frequencies):
            # Rozpatrujemy wszystkie sekwencje stopów do spinu t. Zwykły
            # symbol wymaga braku WILD w poprzednich t-1 spinach i teraz.
            clean_history = (length - wild_stops) ** (spin - 1)
            reel_rows = []
            for row in rows:
                counts = {symbol: count * clean_history for symbol, count in row.items()}
                if wild_stops:
                    counts[WILD] += length ** spin - length * clean_history
                reel_rows.append(counts)
            sticky_rows.append(reel_rows)

        outcome_counts = [length ** spin for length in bonus_lengths]
        bonus_units += expected_board_win(sticky_rows, outcome_counts, payline_units)

    base_rtp = base_units / units_per_stake
    average_bonus_win = bonus_units / units_per_stake
    bonus_rtp = bonus_frequency * average_bonus_win
    return {
        "base_rtp": base_rtp,
        "bonus_rtp": bonus_rtp,
        "total_rtp": base_rtp + bonus_rtp,
        "bonus_frequency": bonus_frequency,
        "average_bonus_win_in_stakes": average_bonus_win,
    }


def simulate(number_of_rounds, seed):
    if number_of_rounds <= 0:
        raise ValueError("Liczba płatnych rund musi być dodatnia.")

    rng = random.Random(seed)
    base_sum = 0.0
    bonus_sum = 0.0
    bonus_count = 0
    payout_counts = Counter()
    max_payout = 0.0
    mean_payout = 0.0
    squared_deviations = 0.0

    for round_number in range(1, number_of_rounds + 1):
        base_win, free_spins_win, bonus_triggered = play_round(rng)
        base_sum += base_win
        bonus_sum += free_spins_win
        bonus_count += int(bonus_triggered)

        # Algorytm Welforda uwzględnia każdą rundę, również wypłatę 0.
        payout_in_stakes = (base_win + free_spins_win) / STAKE
        if payout_in_stakes == 0:
            payout_counts["no_payout"] += 1
        elif math.isclose(payout_in_stakes, 1.0, rel_tol=0, abs_tol=1e-12):
            payout_counts["break_even"] += 1
        elif payout_in_stakes < 1.0:
            payout_counts["below_stake"] += 1
        else:
            payout_counts["above_stake"] += 1
        max_payout = max(max_payout, payout_in_stakes)

        delta = payout_in_stakes - mean_payout
        mean_payout += delta / round_number
        squared_deviations += delta * (payout_in_stakes - mean_payout)

    total_staked = number_of_rounds * STAKE
    base_rtp = base_sum / total_staked
    bonus_rtp = bonus_sum / total_staked

    return {
        "base_rtp": base_rtp,
        "bonus_rtp": bonus_rtp,
        "total_rtp": base_rtp + bonus_rtp,
        "bonus_count": bonus_count,
        "bonus_frequency": bonus_count / number_of_rounds,
        "rounds_per_bonus": number_of_rounds / bonus_count if bonus_count else None,
        "average_bonus_win": bonus_sum / bonus_count if bonus_count else None,
        "payout_std": math.sqrt(squared_deviations / number_of_rounds),
        "rtp_standard_error": (
            math.sqrt(squared_deviations / (number_of_rounds - 1) / number_of_rounds)
            if number_of_rounds > 1 else None
        ),
        "payout_counts": payout_counts,
        "max_payout": max_payout,
    }


def print_results(number_of_rounds, seed, results):
    print(f"Płatne rundy = {number_of_rounds}, ziarno = {seed}, stawka = {STAKE:g}")
    print(f"Szacowane RTP gry bazowej = {results['base_rtp']:.4%}")
    print(f"Szacowany wkład darmowych spinów do RTP = {results['bonus_rtp']:.4%}")
    print(f"Szacowane całkowite RTP = {results['total_rtp']:.4%}")
    print(f"Uruchomienia bonusu = {results['bonus_count']}")
    print(f"Częstotliwość bonusu = {results['bonus_frequency']:.4%}")

    if results["bonus_count"]:
        print(f"Średnio 1 bonus na {results['rounds_per_bonus']:.2f} płatnych rund")
        print(f"Średnia wypłata bonusu = {results['average_bonus_win']:.4f} jednostek")
    else:
        print("Średnio 1 na N = brak danych")
        print("Średnia wypłata bonusu = brak danych")

    print(f"Odchylenie standardowe wypłaty na rundę = {results['payout_std']:.4f}× stawki")
    standard_error = results["rtp_standard_error"]
    if standard_error is not None:
        print(f"Błąd standardowy estymacji RTP = {100 * standard_error:.4f} p.p.")

    counts = results["payout_counts"]
    print(f"Rundy bez wypłaty = {counts['no_payout'] / number_of_rounds:.4%}")
    print(f"Rundy z wypłatą poniżej stawki = {counts['below_stake'] / number_of_rounds:.4%}")
    print(f"Rundy ze zwrotem stawki = {counts['break_even'] / number_of_rounds:.4%}")
    print(f"Rundy z wypłatą powyżej stawki = {counts['above_stake'] / number_of_rounds:.4%}")
    print(f"Najwyższa wypłata w próbie = {results['max_payout']:.3f}× stawki")


def print_exact_results(results):
    print(f"Cel RTP = {float(TARGET_RTP):.4%}")
    print(f"Teoretyczne RTP gry bazowej = {float(results['base_rtp']):.6%}")
    print(f"Teoretyczny wkład darmowych spinów = {float(results['bonus_rtp']):.6%}")
    print(f"Teoretyczne całkowite RTP = {float(results['total_rtp']):.6%}")
    gap = 100 * (results["total_rtp"] - TARGET_RTP)
    print(f"Odchylenie od celu = {float(gap):+.7f} p.p.")
    frequency = results["bonus_frequency"]
    print(f"Częstotliwość bonusu = {float(frequency):.6%}")
    if frequency:
        print(f"Średnio 1 bonus na {float(1 / frequency):.2f} płatnych rund")
    print(f"Średnia wypłata bonusu = {float(results['average_bonus_win_in_stakes']):.4f}× stawki")


def run_checks():
    assert len(PAYLINES) == len(set(PAYLINES)) == 20
    assert all(len(strip) == 21 for strip in BASE_STRIPS + BONUS_STRIPS)
    assert all(set(PAYTABLE) <= set(strip) for strip in BASE_STRIPS + BONUS_STRIPS)
    assert all(0 < pay3 < pay4 < pay5 for pay3, pay4, pay5 in PAYTABLE.values())
    assert all(PAYTABLE[symbol][2] < 1 for symbol in "ABCDE")
    assert all(PAYTABLE[symbol][0] > 1 for symbol in "FGH")
    assert reels_with_wild(BASE_STRIPS) == reels_with_wild(BONUS_STRIPS) == {1, 2, 3}
    fs_reels = {reel for reel, strip in enumerate(BASE_STRIPS) if FS in strip}
    assert fs_reels == set(FS_REELS)
    assert all(FS not in strip for strip in BONUS_STRIPS)

    a3, a4, _ = PAYTABLE["A"]
    assert evaluate_payline(("B", "A", "A", "A", "C"), PAYTABLE) == ("A", 1, 3, a3)
    assert evaluate_payline(("A", "A", FS, "A", "A"), PAYTABLE) is None
    assert evaluate_payline(("A", WILD, "A", "A", "C"), PAYTABLE) == ("A", 0, 4, a4)

    line = ("A", WILD, WILD, WILD, "B")
    competition = {
        "A": (0.3, 0.6, 1.0),
        "B": (0.4, 0.9, 2.0),
        "F": (1.1, 2.0, 5.0),
    }
    assert evaluate_payline(line, competition) == ("F", 1, 3, 1.1)

    # Remisy kolejno według początku, długości i symbolu.
    tied_symbols = {"B": (0.5, 2.0, 5.0), "A": (0.5, 2.0, 4.0)}
    tied_table = {**tied_symbols, "C": (2.0, 3.0, 6.0)}
    assert evaluate_payline(line, tied_table) == ("A", 0, 4, 2.0)
    assert evaluate_payline((WILD, WILD, WILD, "B", FS), tied_table) == ("B", 0, 4, 2.0)
    assert evaluate_payline((FS, WILD, WILD, WILD, FS), tied_symbols) == ("A", 1, 3, 0.5)

    base = (
        (FS, "A", "A"), ("A",) * 3, (FS, WILD, "C"),
        ("D",) * 3, (FS, "E", "E"),
    )
    expanded = expand_wilds(base, {2})
    assert triggers_free_spins(base)
    assert not triggers_free_spins(expanded)
    missing_fs = ((FS, FS, FS),) + base[1:4] + (("E",) * 3,)
    assert not triggers_free_spins(missing_fs)

    clean = tuple((symbol,) * 3 for symbol in ("A", "A", "C", "D", "E"))
    new_wild = clean[:2] + (("C", WILD, "C"),) + clean[3:]
    expanded_bonus = expand_wilds(clean, {2})
    expected_sticky_win = len(PAYLINES) * a3

    # W pierwszym bonusie WILD wpada w drugim spinie.
    # W drugim bonusie losują się same zwykłe symbole.
    draws = [base, clean, new_wild] + [clean] * 8 + [clean] * 10
    rng = random.Random(0)

    with patch(f"{__name__}.spin_board", side_effect=draws) as mocked_spin:
        with patch(f"{__name__}.evaluate_board", wraps=evaluate_board) as mocked_evaluate:
            base_win, bonus_win, triggered = play_round(rng)
            next_bonus_win = play_free_spins(rng)

    assert mocked_spin.call_count == 21
    evaluated = [call.args[0] for call in mocked_evaluate.call_args_list]
    assert evaluated == [expanded, clean] + [expanded_bonus] * 9 + [clean] * 10
    assert triggered and base_win > 0
    assert math.isclose(bonus_win, 9 * expected_sticky_win)
    assert next_bonus_win == 0.0


def main():
    parser = argparse.ArgumentParser(description="Symulacja automatu 5 × 3")
    parser.add_argument("--rounds", type=int, default=100_000, help="liczba płatnych rund")
    parser.add_argument("--seed", type=int, default=42, help="ziarno generatora")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--test-only", action="store_true", help="uruchom tylko sprawdzenia")
    mode.add_argument("--exact", action="store_true", help="oblicz RTP teoretyczne")
    args = parser.parse_args()

    if args.rounds <= 0:
        parser.error("--rounds musi być dodatnie")

    run_checks()
    print("Sprawdzenia deterministyczne zaliczone.")
    if args.exact:
        print_exact_results(exact_metrics())
    elif not args.test_only:
        results = simulate(args.rounds, args.seed)
        print_results(args.rounds, args.seed, results)


if __name__ == "__main__":
    main()
