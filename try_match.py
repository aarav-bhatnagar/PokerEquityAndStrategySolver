from games import Leduc
from cfr import CFR
from match import *

g = Leduc()
s = CFR(g, plus=True); s.run(20000)
bot = s.average_policy()
control = uniform_policy(g)

for name, make in BASELINES.items():
    opp = make(g)
    pairs = play_match(g, bot, opp, 100_000, seed=7)
    ctrl = play_match(g, control, opp, 100_000, seed=8)
    print(name, summarise(pairs))
    print("  exact EV:", exact_profit_per_hand(g, bot, opp))
    print("  Welch vs random bot:", welch(pairs, ctrl))

"""
random {'hands': 100000, 'mean_per_hand': 0.71398, 'ci95_per_hand': 0.03278182154816397, 't': 42.68831730244035, 'p': 0.0}
  exact EV: 0.7193669172654847
  Welch vs random bot: (31.243541959501854, 2.9591670247208297e-213)
calling_station {'hands': 100000, 'mean_per_hand': 0.65814, 'ci95_per_hand': 0.03104036418282789, 't': 41.55732169900335, 'p': 0.0}
  exact EV: 0.6329220137870255
  Welch vs random bot: (26.987286095922745, 7.900833523594818e-160)
maniac {'hands': 100000, 'mean_per_hand': 0.39149, 'ci95_per_hand': 0.054960508764251355, 't': 13.961304530337568, 'p': 3.25112880596383e-44}
  exact EV: 0.3847391912158876
  Welch vs random bot: (63.11536865438679, 0.0)
"""