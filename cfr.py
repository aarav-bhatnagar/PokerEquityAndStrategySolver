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

if __name__ == "__main__":
    from games import Kuhn, Leduc
    solver = CFR(Leduc(), plus=True)   # plus=False is vanilla CFR
    solver.run(20000)

    policy = solver.average_policy()
    for key in sorted(policy, key=str):
        print(key, {a: round(p, 3) for a, p in policy[key].items()})