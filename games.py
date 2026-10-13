#J, Q, K code 0, 1, 2
from functools import lru_cache

"""
Kuhn possible endings

bp	P0 bet, P1 folded	+1
pbp	P0 passed, P1 bet, P0 folded	−1
pp	both passed, showdown	±1 (higher card wins)
bb	bet and call, showdown	±2
pbb	pass, bet, call, showdown	±2

"""

class Kuhn:
    #s = (cards, history)
    #cards is a tuple of the cards dealt so far where cards[0] = player 1's card and cards[1] = player 2's card
    #history is a string of the actions taken so far i.e a list of characters 'p' for pass and 'b' for bet (or call)

    name = "kuhn"
    DECK = [0, 1, 2]
    N_DEAL = 2

    def initial(self):
        return ((), "") #initial state of s

    def is_chance(self, s):
        #s = tuple of dealt cards. While the length is less than 2, still dealing
        return len(s[0]) < 2

    def chance_outcomes(self, s):
        cards, history = s
        rest = [c for c in range(3) if c not in cards]
        return [((cards + (c,), history), 1 / len(rest)) for c in rest] #returns list of pairs such that each pair represents (next_state (new s), probability)

    def is_terminal(self, s):
        return s[1] in ("pp", "bb", "pbp", "bp", "pbb")

    def utility(self, s):
        #Terminal state that represents payoff as net chips won or lost
        #As kuhn is a zero sum game player 1's utility + player 2's utlity = 0
        (c0, c1), history = s
        if history == "bp":
            return 1.0

        if history == "pbp":
            return -1.0

        stake = 2.0 if "b" in history else 1.0
        return stake if c0 > c1 else -stake

    def player(self, s):
        #returns player 0 or 1 based on odd/even parity of length of cards, i.e. s[1]
        return len(s[1]) % 2

    def actions(self, s):
        return ["p", "b"]

    def child(self, s, a):
        #given a state and action, the next state is simply, the current cards as betting doesn't affect the players cards, with the history just being with the action appended
        return (s[0], s[1] + a)

    def infoset(self, s):
        #returns a key describing exactly what the player to act knows
        #s[0] is cards. self.player(s) is 0 or 1 depending on who's turn it is. The history is common to both players regardless of what turn it is
        return (s[0][self.player(s)], s[1])       # own card + history only

def walk(g, s, stats):
    #g = instance of kuhn
    #s = current state
    #stats = dictionary of current encountered nodes for testing
    if g.is_terminal(s):
        stats["term"] += 1
        return
    if g.is_chance(s):
        #assert abs(sum(p for _, p in g.chance_outcomes(s)) - 1) < 1e-9, tests sum of probabilities
        stats["chance"] += 1
        for c, _ in g.chance_outcomes(s):
            walk(g, c, stats) #for every new state, walk along that recursively
        return
    stats["dec"] += 1 #if not terminal, or chance
    #Also decision node is part of information set
    #Set is used to avoid dupliicates
    stats["inf"].add((g.player(s), g.infoset(s)))
    for a in g.actions(s):
        walk(g, g.child(s, a), stats)

"""
g = Kuhn()
stats = {"term": 0, "dec": 0, "inf": set(), "chance": 0}
walk(g, g.initial(), stats)
print(stats["term"], stats["dec"], len(stats["inf"]), stats["chance"])    # expect: 30 24 12 - check drawn diagram in readme
"""


#LEDUC
@lru_cache(maxsize=None)
def analyse(hist):
    #rnd, contrib[0], contrib[1], player, ended, folder, raises
    contrib = [1,1] #where contrib[0] = money player 1 has put in and contrib[1] = money player 2 has put in
    rnd, player, raises, acted = 0, 0, 0, 0
    #rnd = betting round 0 or 1
    #player = who's turn is next
    #raises = raises made so far this round (capped at 2)
    #acted = checks made this round

    ended, folder = False, None

    #loop through history
    for ch in hist:
        if ch == "/":
            #End of round 1 so reset
            rnd, player, raises, acted, ended = 1, 0, 0, 0, False
            continue
        facing = contrib[1 - player] > contrib[player]
        if ch == "f":
            #fold
            ended, folder = True, player
        elif ch == "c":
            #call
            if facing:
                contrib[player] = contrib[1 - player]
                ended = True
            else:
                acted += 1
                ended = (acted == 2)
        elif ch == "r":
            contrib[player] = contrib[1 - player] + (2 if rnd == 0 else 4) #Increase contribution based on betting size of round
            raises += 1
        player = 1 - player

    return rnd, contrib[0], contrib[1], player, ended, folder, raises

class Leduc:
    name = "Leduc"
    DECK = [0, 0, 1, 1, 2, 2]
    N_DEAL = 3

    def initial(self):
        return ((), "")

    def is_chance(self, s):
        #is false when time to act
        cards, history = s
        return len(cards) < 2 or (len(cards) == 2 and history.endswith("/"))

    def chance_outcomes(self, s):
        cards, history = s
        counts = [2, 2, 2]
        for c in cards:
            counts[c] -= 1
        total = sum(counts)
        #returns list of tuples (next state, probability)
        return [((cards + (r,), history), (counts[r] / total)) for r in range(3) if counts[r]]

    def is_terminal(self, s):
        cards, history = s
        if history.endswith("/"):
            #2 rounds,so if only first round has ended then not end of hand
            return False

        rnd, _, _, _, ended, folder, _ = analyse(history)
        return folder is not None or (ended and rnd == 1)

    def utility(self, s):
        cards, history = s
        rnd, c0, c1, _, ended, folder, _ = analyse(history)
        if folder is not None:
            #if folded, other person takes money
            return -float(c0) if folder == 0 else float(c1)
        p0, p1, pub = cards
        #Compare hand at end with pair highest and then high card already 0, 1, 2
        s0 = (10 if p0 == pub else 0) + p0
        s1 = (10 if p1 == pub else 0) + p1
        if s0 == s1:
            return 0.0
        #From player 0's perspective, if they win they take player 1's contribution.
        #if they lose they lose their/player 0's contribution
        return float(c1) if s0 > s1 else -float(c0)

    def player(self, s):
        return analyse(s[1])[3]

    def actions(self, s):
        #What are a playerss next available actions, c, f, r, check, call fold, raise
        rnd, c0, c1, p, _, _, raises = analyse(s[1])
        facing = (c1 > c0) if p == 0 else (c0 > c1)
        acts = ["f", "c"] if facing else ["c"]
        if raises < 2:
            acts.append('r')
        return acts

    def child(self, s, a):
        cards, history = s
        newHistory = history + a
        if a != "f":
            rnd, _, _, _, ended, _, _ = analyse(newHistory)
            if ended and rnd == 0:
                newHistory += "/" #Add next round indicator
        return (cards, newHistory)

    def infoset(self, s):
        cards, history = s
        p = self.player(s) #Get acting player
        pub = cards[2] if len(cards) == 3 else None
        return (cards[p], pub, history)


g = Leduc()
stats = {"term": 0, "dec": 0, "inf": set(), "chance": 0}
walk(g, g.initial(), stats)
print(stats["term"], stats["dec"], len(stats["inf"]), stats["chance"])    # expect: 1116 774 288 - check drawn diagram in readme