#J, Q, K code 0, 1, 2

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