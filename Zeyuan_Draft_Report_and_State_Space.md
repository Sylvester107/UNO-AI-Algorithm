Observable contains:[ 
    The cards I have,
    top card of the discard pile, 
    all players' history, 
    The number of cards that each player left, 
    current game color, 
    current game direction
]

Unobservable contains: [
    the exact cards that other players have,
    the exact cards remain on deck
    ]

Let's say the depth/iterations will be 100, I am the player1, opponents start from player2, have totally k players(including myself)

Mathematical Description:

I would develop the State:

S = (Cur_Color, Cur_Dir, Cur_Top, Skip, Sum_Plus, Hand_Cards, Opponents_Cards_Num, Belief)

Where:
- Cur_color is the current valid color
- Cur_Dir is {-1, 1}, the current direction
- Cur_Top is the current top discard card
- Skip is {0, 1}, saying next player should skip or not
- Sum_Plus is the summary of +2/+4 numbers
- Hand_Cards is the cards that I have
- Opponents_Cards_Num is (OCN2, OCN3,...,OCNk), saying the number of cards that opponents have
- Belief is {OH2, OH3,..., OHk}, saying the sample cards that each opponents may have


Actions = {V_Card, Next_Col, Plus_N, Sk, Rev}U{GNC}U{UNO}

Where:
- V_Card: Use a valid card from hand(same color or same number), 
- Next_Col: Choose the next color for the wild card when play a wild card,
- Plus_N: Play a +2 or +4 wild card
- Sk: Play a skip card, will skip next player, skip'= 1
- Rev: Play a reverse card, will reverse the current direction, Cur_Dir' = -Cur_Dir
- GNC: Get a new card if there are no valid cards in hand
- UNO: When player has only left 2 hand cards, should do "UNO" action, announce to others; or else he will be penal by add 2 cards

Transitions: S' <- T(S,A)

- Means, in state S, take action A, will go to state S'

    Including transitions:
    - Cur_Top' = A.V_Card
    - Cur_Col' = A.Next_Col
    - Cur_Dir' = - Cur_Dir, when A = A.Rev
    - Skip' = 1, when A = A.Sk
    - Sum_Plus' += k, where k={2,4}, when A=A.Plus_N
    - Hand_Cards' = Hand_Cards.append(card), when A = A.GNC


Observations:
observations are parts of the whole game state
O(S) = (Cur_Col, Cur_Dir, Cur_Top, Skip, Sum_Plus, Hand_Cards, Opponents_Cards_Num, B)

Unobservables: 
- opponents cards details information
- the details information for each cards remains on the deck
