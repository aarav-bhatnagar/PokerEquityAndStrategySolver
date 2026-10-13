# Poker Equity And Strategy Solver

## Evaluator.py
Through evaluate gives each possible hand of 7 cards a score using a 24 bit integer
<br>
First 4 bits represent 9 categories (high card(0) to straight flush(8)
<br>
Next 5 sets of 4 bits represent kickers

## Equity.py
Computes exact and monte carlo equity for hold'em poker
<br>
Equity = P(win) + 1/2 P(tie)

## Games.py
Kuhn poker full game tree and analysis

<img width="600" alt="1791758579432-738a92ee-d10d-49e0-878a-97550e3de779_1" src="https://github.com/user-attachments/assets/e62dcb59-45bc-478c-b6f3-8e98cb001f13" />

Implemented Ludec poker with more game theory to same system
