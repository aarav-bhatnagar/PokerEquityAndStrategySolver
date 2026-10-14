from collections import defaultdict
from games import Kuhn, Leduc

#cfr.py - counterfactual regret minimisation
class Node:
    #Everything CFR remembers about one information set
    def __init__(self, actions):
        self.actions = actions #List of legal actions
        self.regret = [0.0] * len(actions) #Cummulative counterfactual regret
        #Positive means I wish I played more.
        #Negative means good thing I didn't

        self.strategy_sum = [0.0] * len(actions) #Used to build average strategy
        #Converges in equilibrium

    def current_strategy(self):
        #Play each action in proportion to it's positive regret
        pos = [r if r > 0 else 0.0 for r in self.regret]
        total = sum(pos)
        n = len(pos)
        #if total == 0, then all have negative regret. If this, then pick uniformally
        return [p / total for p in pos] if total > 0 else [1.0 / n] * n

    def average_strategy(self):
        #Normalises Strategy Sum
        total = sum(self.strategy_sum)
        n = len(self.actions)
        return [x / total for x in self.strategy_sum] if total > 0 else [1.0 / n] * n

class CFR:
    def __init__(self, game, plus=True):
        #game = Kuhhn or Leduc
        #CFR / CFR+
        self.game = game
        self.plus = plus
        self.nodes = {} #dictionary of nodes from (player, infoset) -> node
        self.t = 0 #iterations

    def node(self, key, actions):
        n = self.nodes.get(key) #If there already exists a node from dict, get it, else create a new instance from node class
        if n is None:
            n = self.nodes[key] = Node(actions)
        return n

    def cfr(self, s, pi0, pi1, pic):
        g = self.game
        if g.is_terminal(s):
            #Hand is over so return the payoff
            return g.utility(s)

        if g.is_chance(s):
            #Returns an expected value. The sum of all outcomes weighted by likeliness
            return sum(p * self.cfr(ns, pi0, pi1, pic * p) for ns, p in g.chance_outcomes(s))

        p = g.player(s)
        acts = g.actions(s)
        node = self.node((p, g.infoset(s)), acts)
        sigma = node.current_strategy()

        utils = [0.0] * len(acts)
        value = 0.0
        for i, a in enumerate(acts):
            #index i and action a
            if p == 0:
                #player 0
                u = self.cfr(g.child(s, a), pi0 * sigma[i], pi1, pic)
            else:
                u = self.cfr(g.child(s, a), pi0, pi1 * sigma[i], pic)
            utils[i] += u
            value += sigma[i] * u

        own, opp = (pi0, pi1) if p == 0 else (pi1, pi0)
        sign = 1.0 if p == 0 else -1.0              # utilities are from player 0's point of view
        weight = self.t if self.plus else 1.0       # CFR+ weights later iterations more
        for i in range(len(acts)):
            node.regret[i] += opp * pic * sign * (utils[i] - value)
            if self.plus and node.regret[i] < 0:
                node.regret[i] = 0.0
            node.strategy_sum[i] += weight * own * sigma[i]
        return value

    def run(self, iterations):
        for _ in range(iterations):
            self.t += 1
            self.cfr(self.game.initial(), 1.0, 1.0, 1.0)

    def average_policy(self):
        """{(player, infoset): {action: probability}}"""
        return {k: dict(zip(n.actions, n.average_strategy())) for k, n in self.nodes.items()}

#TESTING

def _probs(policy, key, actions):
    d = policy.get(key)
    if d is None:                       # infoset never reached in training
        return {a: 1.0 / len(actions) for a in actions}
    return d

def expected_value(game, policy):
    """Expected payoff to player 0 when both players follow `policy`."""
    def rec(s):
        if game.is_terminal(s):
            return game.utility(s)
        if game.is_chance(s):
            return sum(p * rec(c) for c, p in game.chance_outcomes(s))
        pr = _probs(policy, (game.player(s), game.infoset(s)), game.actions(s))
        return sum(pr[a] * rec(game.child(s, a)) for a in game.actions(s))
    return rec(game.initial())

def best_response_value(game, policy, br_player):
    members = defaultdict(list)          # infoset -> [(state, weight)]

    def collect(s, w):                   # pass 1
        if game.is_terminal(s):
            return
        if game.is_chance(s):
            for c, p in game.chance_outcomes(s):
                collect(c, w * p)
            return
        p = game.player(s)
        acts = game.actions(s)
        if p == br_player:
            members[game.infoset(s)].append((s, w))
            for a in acts:
                collect(game.child(s, a), w)
        else:
            pr = _probs(policy, (p, game.infoset(s)), acts)
            for a in acts:
                collect(game.child(s, a), w * pr[a])

    collect(game.initial(), 1.0)

    sign = 1.0 if br_player == 0 else -1.0
    best_action, val_cache = {}, {}

    def value(s):                        # pass 2
        if s in val_cache:
            return val_cache[s]
        if game.is_terminal(s):
            v = sign * game.utility(s)
        elif game.is_chance(s):
            v = sum(p * value(c) for c, p in game.chance_outcomes(s))
        else:
            p = game.player(s)
            acts = game.actions(s)
            if p == br_player:
                v = value(game.child(s, choose(game.infoset(s))))
            else:
                pr = _probs(policy, (p, game.infoset(s)), acts)
                v = sum(pr[a] * value(game.child(s, a)) for a in acts)
        val_cache[s] = v
        return v

    def choose(key):
        if key in best_action:
            return best_action[key]
        states = members[key]
        best, best_v = None, float("-inf")
        for act in game.actions(states[0][0]):
            tot = sum(w * value(game.child(s, act)) for s, w in states)
            if tot > best_v + 1e-12:
                best, best_v = act, tot
        best_action[key] = best
        return best

    return value(game.initial())

def exploitability(game, policy):
    return (best_response_value(game, policy, 0) +
            best_response_value(game, policy, 1)) / 2.0

def uniform_policy(game):
    """Uniform-random policy over every infoset (built by walking the whole tree)."""
    pol = {}

    def walk(s):
        if game.is_terminal(s):
            return
        if game.is_chance(s):
            for c, _ in game.chance_outcomes(s):
                walk(c)
            return
        acts = game.actions(s)
        key = (game.player(s), game.infoset(s))
        if key not in pol:
            pol[key] = {a: 1.0 / len(acts) for a in acts}
        for a in acts:
            walk(game.child(s, a))

    walk(game.initial())
    return pol

if __name__ == "__main__":
    #Explotability is how many chips per hand a perfect opponent could win against your strategy, on average
    #Expected payoff per hand when both player's follow strategy
    g = Leduc()
    for T in (1000, 2000, 5000, 10000, 20000):
        s = CFR(Leduc(), plus=True); s.run(T)
        print(T, exploitability(Leduc(), s.average_policy()))

    """
    g = Kuhn()
    s = CFR(g, plus=True); s.run(2000)
    p = s.average_policy()
    print(exploitability(g, p), expected_value(g, p))
    """

    """
    solver = CFR(Leduc(), plus=True)   # plus=False is vanilla CFR
    solver.run(20000)

    policy = solver.average_policy()
    for key in sorted(policy, key=str):
        print(key, {a: round(p, 3) for a, p in policy[key].items()})
    """