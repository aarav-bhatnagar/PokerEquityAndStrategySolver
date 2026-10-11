RANKS = "23456789TJQKA" #Remeber 1 is not a real card
SUITS = "cdhs"
#9 Categories index 0-8. Royal Flush is simply a straight flush with a sub-category
CATEGORY_NAMES = ["High card", "Pair", "Two pair", "Three of a kind", "Straight",
                  "Flush", "Full house", "Four of a kind", "Straight flush"]

def card(s):
    #Given the string code i.e. Qc (queen of clubs) return appropriate integer
    return RANKS.index(s[0].upper()) * 4 + SUITS.index(s[1].lower())

def card_str(n):
    #Given the integer returns the string code
    return RANKS[n // 4] + SUITS[n % 4]

def cards(S):
    #Given a string which represents a list of cards, i.e. 'Kd 2c ... ' reutn list of ints where each card in string has appropriate integer
    return [card(x) for x in S.split()]

def _build_tables():
    #precomputes table information over 13 bit hand masks. There are 13 possible cards 2 - A (14) / or A (1) - K(13). Hence we need a 13 bit mask where, the 0th bit = deuce and 12th bit = ace
    straight_high = [-1] * 8192 #Initialize first such that over every possible rank mask, there is a -1
    #-1 describes no straight hand possible, if there is a straigght hand, the hghighest card is stored as tis is the only info we need as by definition a straight is made from consecutive cards
    top5 = [0] * 8192 #Stores the best 5 ranks of a hand with the same 0 = deuce, 12 = ace rule

    for mask in range(8192):
        #Basically looping across to 2^13

        #filling up straight_high
        for high in range(12, 3, -1):
            #From ace (12) to 6 (4) as lowest straight that is not the wheel is [2, 3, 4, 5, 6]
            #Creates the expected mask that the algorithm needs for that high card
            need = sum (1 << r for r in range(high - 4, high + 1))
            #i.e. if high = 5, then need = 111110

            #check that if all the ones in need are in mask. (mask can have extra ones)
            if mask & need == need:
                straight_high[mask] = high
                break
        else:
            #if loop finished normally, meaning that the mask is not a straight, then check if wheel
            wheel = (1 << 12) | 0b1111  # A,2,3,4,5 i.e 0b1000000001111
            if mask & wheel == wheel:
                straight_high[mask] = 3

        packed, n = 0, 0
        #packed accumualtes the result and n counts how many ranks have been added so far

        for r in range(12, -1, -1):
            #counts down from ace (12) to deuce (0), so higher cards are given priority
            if mask >> r & 1:
                #if the current rank r is present
                packed = packed << 4 | r
                #shifts everything to the left by 4 and slots in the bit rep of r
                n += 1
                if n == 5:
                    #if 5 highest cards have already been found
                    break

        top5[mask] = packed << (4 * (5 - n))
        #shift to the left such that 1st ranks are used even if in hand only 3 ranks
    
    return straight_high, top5

def pack(ranks):
    #takes in (up to) 5 ranks individually and packs into one string, link in build table
    packed = 0
    for rank in ranks[:5]:
        packed = packed << 4 | rank
    return packed << (4 * (5 - min(5, len(ranks))))

def category(score):
    #Given the full score, what is the category
    return CATEGORY_NAMES[score >> 20]

def evaluate(hand):
    #Takes 7 cards (2 cards from player and 5 from board) as ints 0-51 as described earlier and converts to a score also as described earlier
    #The final output should obey the following:
    #if int A > int B: Hand A wins.
    #if int A = int B: (Draw) - split the pot
    #hand is list of integers - built from the cards helper function

    #Recall that score is an integer s.t. | category (0-8) | rank 1 | rank 2 | rank 3 | rank 4 | rank 5 |
    #                                       score >> 20      4 bits   4 bits   4 bits   4 bits   4 bits


    rank_count = [0] * 13 #each index i shows the number of cards indexed i

    #for the lists, each index represents a different suit clubs, diamonds, hearts and spades

    suit_mask = [0, 0, 0, 0] #Each entry itself is a 13 bit int, where bit r is 1 if that suit contains 1
    suit_n = [0, 0, 0, 0] #The number of cards of that suit index i
    mask = 0 #Repersents just one 13 bit int such that each bit is 1, if that rank appears at least one in the hand. i.e. OR everything in suit_mask

    for c in hand:
        #for each card (integer) in hand
        #rank, suit
        r, s = c >> 2, c & 3
        rank_count[r] += 1
        suit_mask[s] |= 1 << r
        suit_n[s] += 1
        mask |= 1 << r

    #Returns when highest hand is found

    #straight flush
    flush_mask = 0
    for s in range(4):
        if suit_n[s] >= 5:
            flush_mask = suit_mask[s]
            sh = _STRAIGHT_HIGH[flush_mask] #sh = straight high
            if sh >= 0:
                return 8 << 20 | sh << 16 #First bit category 8 highest. Then the highest straight cards using the next nibble

    quads, trips, pairs = [], [], []
    for r in range(12, -1, -1):
        #Scans from ace down to 2
        n = rank_count[r]
        if n == 4: quads.append(r)
        elif n == 3: trips.append(r)
        elif n == 2: pairs.append(r)
        #Simply populates the lists such that each list has a rank r if it has that named feature i.e. if pair has 12, it has ace pair

    #Big If statement for other hands
    if quads:
        q = quads[0] #Only one quad can exists as 4/7 cards
        #rest/other cards needed if quad is on the board and determined by kickers etc
        rest = [r for r in range(12, -1, -1) if rank_count[r] and r != q]
        #Only rest[0] needed as only 1 kicker left apart from quads
        return 7 << 20 | pack([q, rest[0]])

    if trips and (len(trips) > 1 or pairs):
        #Full house
        t = trips[0]
        p = max(trips[1:] + pairs) #i.e. 8 would be returned if [3] + [8, 5]
        return 6 << 20 | pack([t, p])

    if flush_mask:
        #if flush return the top 5 cards in the flush
        return 5 << 20 | _TOP5[flush_mask]

    sh = _STRAIGHT_HIGH[mask]
    if sh >= 0:
        return 4 << 20 | sh << 16

    if trips:
        t = trips[0]
        kickers = [r for r in range(12, -1, -1) if rank_count[r] and r != t][:2]
        #if kickers were the same it would be a full house
        return 3 << 20 | pack([t] + kickers)

    if len(pairs) >= 2:
        #2 pairs
        a, b = pairs[0], pairs[1]
        kick = [r for r in range(12, -1, -1) if rank_count[r] and r != a and r != b][0]
        return 2 << 20 | pack([a, b] + [kick])

    if pairs:
        p = pairs[0]
        kickers = [r for r in range(12, -1, -1) if rank_count[r] and r != p][:3]
        return 1 << 20 | pack([p] + kickers)

    #category 0 is high card
    return _TOP5[mask]

#TESTING
if __name__ == "__main__":
    #Build and store the tables as global readable variables
    _STRAIGHT_HIGH, _TOP5 = _build_tables()
    hand1 = cards(input())
    hand2 = cards(input())

    score1 = evaluate(hand1)
    score2 = evaluate(hand2)

    print(score1, score2)

    if score1 > score2:
        print("player1 won")
    elif score1 == score2:
        print("split the pot")
    else:
        print("player 2 won")
    