import random
from equity import exact_equity, mc_equity, cards

H, V = cards("As Ah"), cards("Kc Kd")

print("MONTE CARLO")
print(mc_equity(H, V).equity)