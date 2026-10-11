#Equity is the expected share of the pot, i.e. P(win) + 1/2 P(draw)
#Calculated for heads-up poker, i.e. 2 players only

import itertools
import math
import random

#Automatically write automatically writes boilerplate code for classes used to primarily store data
from dataclasses import dataclass

from evaluator import evaluate, cards

@dataclass
class Equity:
    #win, tie, lose is the fraction of boards won, tied, lost where n is the number of boards played
    win: float
    tie: float
    lose: float

    n:int

    @property
    def equity(self):
        #Return her's expected share of the pot
        return self.win + 0.5 * self.tie


def remaining_deck(hero, villain, board):
    known = list(hero) + list(villain) + list(board)
    if len(set(known)) != len(known):
        #There are duplicate cards. Wrong input
        raise ValueError("Duplicate cards in deck")
    known_set = set(known)
    unkown = [c for c in range(52) if c not in known_set]
    return unkown

def tally(hero, villain, board, runouts):
    #runout is one possible way the rest of the board could have played out
    #After the pocket cards are dealth to the 2 players, there are 48 cards left
    #Hence 48C5 possible hands, as order of dealt cards doesn't affect hands (combination)
    #Or (48 * 47 * 46 * 45 * 44) / (5 * 4 * 3 * 2 * 1) = 1712304
    win = tie = lose = n = 0

    """
    hero	list of 2 ints	hero’s hole cards, e.g. [As, Ks] as card ints
    villain	list of 2 ints	villain’s hole cards
    board	list of 0 to 4 ints	community cards already dealt (empty preflop)
    runouts	iterable of card groups	each item is one possible set of missing board cards
    """
    for extra in runouts:
        fullBoard = board + list(extra)
        h = evaluate(hero + fullBoard)
        v = evaluate(villain + fullBoard)
        if h > v:
            win += 1
        elif h == v:
            tie += 1
        else:
            lose += 1
        n += 1

    return Equity(win / n, tie / n, lose / n, n)

def exact_equity(hero, villain, board=()):
    #Uses tally function
    hero, villain, board = list(hero), list(villain), list(board)
    deck = remaining_deck(hero, villain, board) #remaining cards 0..51 in deck
    need = 5 - len(board) #remaining cards to be dealt
    return tally(hero, villain, board, itertools.combinations(deck, need))

def mc_equity(hero, villain, board=(), n = 100000):
    rng = random.Random()
    hero, villain, board = list(hero), list(villain), list(board)
    deck = remaining_deck(hero, villain, board)
    need = 5 - len(board)
    e = equity_data = tally(hero, villain, board, (rng.sample(deck, need) for _ in range(n)))
    m = approximated_equity = e.equity
    var = e.win * (1 - m) ** 2 + e.tie * (0.5 - m) ** 2 + e.lose * m ** 2
    return e, math.sqrt(var / n)