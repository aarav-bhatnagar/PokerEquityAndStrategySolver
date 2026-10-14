"""Run with `python -m pytest -q` or simply `python test_poker.py`."""
import itertools
import random

from evaluator import evaluate, cards, category
from equity import exact_equity, mc_equity
from games import Kuhn, Leduc
from cfr import CFR, exploitability, expected_value, uniform_policy
from match import BASELINES, play_match, summarise, exact_profit_per_hand


def _rank5(hand):
    """Score exactly 5 cards as a tuple; a higher tuple is a better hand."""
    rs = sorted((c >> 2 for c in hand), reverse=True)   # ranks, high to low
    flush = len({c & 3 for c in hand}) == 1             # one distinct suit

    counts = {}
    for r in rs:
        counts[r] = counts.get(r, 0) + 1
    # most frequent rank first; ties broken by higher rank
    groups = sorted(counts.items(), key=lambda kv: (-kv[1], -kv[0]))
    shape = [n for _, n in groups]      # e.g. [3, 2] for a full house
    order = [r for r, _ in groups]      # ranks in tiebreak order

    uniq = sorted(set(rs), reverse=True)
    straight = None
    if len(uniq) == 5 and uniq[0] - uniq[4] == 4:
        straight = uniq[0]              # high card of the straight
    elif uniq == [12, 3, 2, 1, 0]:
        straight = 3                    # the wheel: A-2-3-4-5, five-high

    if straight is not None and flush:
        return (8, straight)
    if shape == [4, 1]:
        return (7, *order)
    if shape == [3, 2]:
        return (6, *order)
    if flush:
        return (5, *rs)
    if straight is not None:
        return (4, straight)
    if shape == [3, 1, 1]:
        return (3, *order)
    if shape == [2, 2, 1]:
        return (2, *order)
    if shape == [2, 1, 1, 1]:
        return (1, *order)
    return (0, *rs)

def _ref7(hand):
    return max(_rank5(list(c)) for c in itertools.combinations(hand, 5))


def test_named_hands():
    # category() names must match whatever your category() returns
    cases = [("As Ks Qs Js Ts 2c 3d", "Straight flush"), ("5s 4s 3s 2s As Kc Kd", "Straight flush"),
             ("9c 9d 9h 9s 2c 3d 4h", "Four of a kind"), ("Kc Kd Kh 2s 2c 3d 4h", "Full house"),
             ("2c 5c 9c Jc Kc 3d 4h", "Flush"), ("Ac 2d 3h 4s 5c 9d Kh", "Straight"),
             ("Kc Kd Kh 2s 5c 3d 9h", "Three of a kind"), ("Kc Kd 2h 2s 5c 3d 9h", "Two pair"),
             ("Kc Kd 2h 7s 5c 3d 9h", "Pair"), ("Kc Qd 2h 7s 5c 3d 9h", "High card")]
    for h, name in cases:
        assert category(evaluate(cards(h))) == name


def test_evaluator_matches_reference_on_random_hands():
    rng = random.Random(0)
    for _ in range(3000):
        a, b = rng.sample(range(52), 7), rng.sample(range(52), 7)
        ours = (evaluate(a) > evaluate(b)) - (evaluate(a) < evaluate(b))
        ref = (_ref7(a) > _ref7(b)) - (_ref7(a) < _ref7(b))
        assert ours == ref


def test_equity_symmetry_and_known_value():
    e = exact_equity(cards("As Ks"), cards("Qh Qd"), cards("Jc 7d 2s"))
    f = exact_equity(cards("Qh Qd"), cards("As Ks"), cards("Jc 7d 2s"))
    assert abs(e.equity + f.equity - 1) < 1e-12
    assert abs(e.equity - 0.2899) < 1e-3


def test_monte_carlo_agrees_with_exact():
    ex = exact_equity(cards("9h 9d"), cards("Ac Kc"), cards("Kh 4s 2d"))
    mc, se = mc_equity(cards("9h 9d"), cards("Ac Kc"), cards("Kh 4s 2d"), n=50_000)
    assert abs(mc.equity - ex.equity) < 0.01


def test_kuhn_solution():
    g = Kuhn()
    c = CFR(g, plus=False)
    c.run(10_000)
    pol = c.average_policy()
    assert abs(expected_value(g, pol) - (-1 / 18)) < 1e-3
    assert exploitability(g, pol) < 0.01
    assert exploitability(g, uniform_policy(g)) > 0.4


def test_leduc_game_value_and_convergence():
    g = Leduc()
    c = CFR(g, plus=True)
    c.run(1500)
    pol = c.average_policy()
    assert abs(expected_value(g, pol) - (-0.0856)) < 0.005
    assert exploitability(g, pol) < 0.05
    assert len(pol) == 288


def test_best_response_of_uniform_is_large():
    g = Leduc()
    assert exploitability(g, uniform_policy(g)) > 1.0


def test_match_matches_exact_expected_value():
    g = Leduc()
    c = CFR(g); c.run(300)
    pol = c.average_policy()
    base = BASELINES["calling_station"](g)
    s = summarise(play_match(g, pol, base, n_hands=20_000, seed=3))
    assert abs(s["mean_per_hand"] - exact_profit_per_hand(g, pol, base)) < 3 * s["ci95_per_hand"] / 1.96


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok  ", name)