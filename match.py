# match.py
import math
import random
from scipy import stats
from cfr import uniform_policy, expected_value

def _all_keys(game):
    """{(player, infoset): legal actions} for every decision point."""
    keys = {}
    def walk(s):
        if game.is_terminal(s):
            return
        if game.is_chance(s):
            for c, _ in game.chance_outcomes(s):
                walk(c)
            return
        keys.setdefault((game.player(s), game.infoset(s)), game.actions(s))
        for a in game.actions(s):
            walk(game.child(s, a))
    walk(game.initial())
    return keys

def calling_station(game):
    return {k: {a: 1.0 if a in ("c", "p") else 0.0 for a in acts}
            for k, acts in _all_keys(game).items()}

def maniac(game):
    out = {}
    for k, acts in _all_keys(game).items():
        pick = "r" if "r" in acts else ("b" if "b" in acts else ("c" if "c" in acts else acts[0]))
        out[k] = {a: 1.0 if a == pick else 0.0 for a in acts}
    return out

BASELINES = {"random": uniform_policy, "calling_station": calling_station, "maniac": maniac}

def _sample(dist, rng):
    r, acc, last = rng.random(), 0.0, None
    for a, p in dist.items():
        if p > 0:
            acc += p
            last = a
            if r < acc:
                return a
    return last

def play_hand(game, deal, policies, rng):
    """deal = cards in dealing order. Returns payoff to player 0."""
    s, k = game.initial(), 0
    while not game.is_terminal(s):
        if game.is_chance(s):
            card = deal[k]; k += 1
            s = next(c for c, p in game.chance_outcomes(s) if c[0][-1] == card and p > 0)
            continue
        p = game.player(s)
        dist = policies[p].get((p, game.infoset(s)))
        a = _sample(dist, rng) if dist else rng.choice(game.actions(s))
        s = game.child(s, a)
    return game.utility(s)

def play_match(game, bot, opponent, n_hands=100_000, seed=0):
    """Per-deal-pair profit of `bot` (two hands per pair)."""
    rng = random.Random(seed)
    pairs = []
    for _ in range(n_hands // 2):
        d = game.DECK[:]
        rng.shuffle(d)
        deal = tuple(d[:game.N_DEAL])
        swapped = (deal[1], deal[0]) + deal[2:]
        a = play_hand(game, deal, (bot, opponent), rng)        # bot is player 0
        b = -play_hand(game, swapped, (opponent, bot), rng)    # bot is player 1, same cards
        pairs.append(a + b)
    return pairs

def exact_profit_per_hand(game, bot, opponent):
    def merge(p0, p1):
        m = {k: v for k, v in p0.items() if k[0] == 0}
        m.update({k: v for k, v in p1.items() if k[0] == 1})
        return m
    as_p0 = expected_value(game, merge(bot, opponent))
    as_p1 = -expected_value(game, merge(opponent, bot))
    return (as_p0 + as_p1) / 2

def summarise(pairs):
    n = len(pairs)
    m = sum(pairs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in pairs) / (n - 1))
    se = sd / math.sqrt(n)
    t, p = stats.ttest_1samp(pairs, 0.0)
    return {"hands": 2 * n, "mean_per_hand": m / 2, "ci95_per_hand": 1.96 * se / 2,
            "t": float(t), "p": float(p)}

def welch(pairs_a, pairs_b):
    t, p = stats.ttest_ind(pairs_a, pairs_b, equal_var=False)
    return float(t), float(p)