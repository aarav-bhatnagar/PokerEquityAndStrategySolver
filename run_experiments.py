"""Reproduce every result in the README.   Usage: python run_experiments.py [--quick]"""
import sys, time, random

from evaluator import cards
from equity import exact_equity, mc_equity
from games import Kuhn, Leduc
from cfr import CFR, exploitability, expected_value, uniform_policy
from match import BASELINES, play_match, summarise, welch, exact_profit_per_hand

QUICK = "--quick" in sys.argv


def part1_equity():
    print("=" * 70 + "\n1. EXACT vs MONTE CARLO EQUITY\n" + "=" * 70)
    spots = [
        ("AsKs vs QhQd, preflop", "As Ks", "Qh Qd", ""),
        ("7h6h vs AcKd, preflop", "7h 6h", "Ac Kd", ""),
        ("AsKs vs QhQd, flop Jc 7d 2s", "As Ks", "Qh Qd", "Jc 7d 2s"),
        ("9h9d vs AcKc, turn Kh 9c 4s 2d", "9h 9d", "Ac Kc", "Kh 9c 4s 2d"),
    ]
    if QUICK:
        spots = spots[2:]
    rng = random.Random(42)
    print(f"{'spot':38s} {'exact':>8s} {'MC (n=200k)':>13s} {'95% CI':>8s} {'inside CI':>10s}")
    for label, h, v, b in spots:
        t = time.time()
        ex = exact_equity(cards(h), cards(v), cards(b))
        mc, se = mc_equity(cards(h), cards(v), cards(b), n=200_000)
        ci = 1.96 * se
        ok = abs(mc.equity - ex.equity) <= ci
        print(f"{label:38s} {ex.equity:8.4f} {mc.equity:13.4f} {ci:8.4f} {str(ok):>10s}   "
              f"({ex.n:,} boards, {time.time()-t:.0f}s)")


def part2_cfr():
    print("\n" + "=" * 70 + "\n2. CFR: KUHN AND LEDUC\n" + "=" * 70)
    k = Kuhn()
    c = CFR(k, plus=False)
    c.run(20_000)
    pol = c.average_policy()
    print(f"Kuhn  vanilla CFR, 20,000 iters: exploitability = {exploitability(k, pol):.5f}, "
          f"value = {expected_value(k, pol):.5f} (theory {-1/18:.5f})")
    print(f"      uniform-random exploitability = {exploitability(k, uniform_policy(k)):.4f}")

    g = Leduc()
    print(f"Leduc uniform-random exploitability = {exploitability(g, uniform_policy(g)):.4f}")
    c = CFR(g, plus=True)
    history, t0 = [], time.time()
    checkpoints = [10, 50, 100, 250, 500, 1000, 2000, 4000, 8000, 12000, 16000, 20000]
    if QUICK:
        checkpoints = checkpoints[:8]
    for cp in checkpoints:
        c.run(cp - c.t)
        e = exploitability(g, c.average_policy())
        history.append((cp, e))
        print(f"Leduc CFR+ iter {cp:6d}: exploitability = {e:.5f}  ({time.time()-t0:.0f}s)")
    pol = c.average_policy()
    print(f"Leduc final: exploitability = {history[-1][1]:.5f} chips/game, "
          f"game value = {expected_value(g, pol):.4f} (literature about -0.0856)")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        xs, ys = zip(*history)
        plt.figure(figsize=(5.5, 3.6))
        plt.loglog(xs, ys, marker="o")
        plt.axhline(0.01, color="r", ls="--", lw=0.8, label="0.01 target")
        plt.xlabel("CFR+ iterations"); plt.ylabel("exploitability (chips/game)")
        plt.title("Leduc poker: CFR+ convergence"); plt.legend(); plt.tight_layout()
        plt.savefig("leduc_convergence.png", dpi=150)
    except Exception as e:
        print("(plot skipped:", e, ")")
    return g, pol


def fmt_p(p):
    return "<1e-100" if p < 1e-100 else f"{p:.2g}"


def part3_match(g, pol):
    print("\n" + "=" * 70 + "\n3. BOT vs NAIVE BASELINES (duplicate deals)\n" + "=" * 70)
    n = 20_000 if QUICK else 100_000
    control = BASELINES["random"](g)
    for name, make in BASELINES.items():
        base = make(g)
        pairs = play_match(g, pol, base, n_hands=n, seed=7)
        s = summarise(pairs)
        exact = exact_profit_per_hand(g, pol, base)
        cs = summarise(play_match(g, control, base, n_hands=n, seed=8))
        ctrl_pairs = play_match(g, control, base, n_hands=n, seed=8)
        t, p = welch(pairs, ctrl_pairs)
        print(f"\nvs {name} ({s['hands']:,} hands)")
        print(f"  CFR bot    : {s['mean_per_hand']:+.4f} +/- {s['ci95_per_hand']:.4f} chips/hand (95% CI); "
              f"t={s['t']:.1f}, p={fmt_p(s['p'])}; exact {exact:+.4f}")
        print(f"  random bot : {cs['mean_per_hand']:+.4f} +/- {cs['ci95_per_hand']:.4f} chips/hand")
        print(f"  Welch (CFR vs random bot, same opponent): t={t:.1f}, p={fmt_p(p)}")


if __name__ == "__main__":
    part1_equity()
    g, pol = part2_cfr()
    part3_match(g, pol)