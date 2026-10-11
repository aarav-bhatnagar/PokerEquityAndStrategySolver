import random
from equity import exact_equity, mc_equity, cards

H, V = cards("As Ks"), cards("Qh Qd")
b = cards("Jc 7d 2s")

print("EXACT")
print(exact_equity(H, V).equity) #pre flop
print(exact_equity(H, V, b).equity) #post flop
print("MONTE CARLO")
print(mc_equity(H, V))
print(mc_equity(H, V, b))