# Assert: the origin uno.py is from rosettacode: https://rosettacode.org/wiki/Uno_%28Card_Game%29/Python
# We modify the original uno.py to add MCTS integration.

import tkinter as tk
from tkinter import messagebox, scrolledtext
from random import shuffle, choice
from random import random as rand
from time import sleep
from threading import Thread
from collections import deque
import argparse
import sys

# MCTS integration (optional - only import if MCTS is available)
# Delay import to avoid circular dependency issues
MCTS_AVAILABLE = False
MCTSPlayer = None

def _import_mcts():
    """Lazy import of MCTS to avoid circular dependencies."""
    global MCTS_AVAILABLE, MCTSPlayer
    if MCTS_AVAILABLE:
        return  # Already imported
    
    try:
        from mcts_integration import MCTSPlayer as MCTSPlayerClass
        MCTSPlayer = MCTSPlayerClass
        MCTS_AVAILABLE = True
    except (ImportError, Exception):
        MCTS_AVAILABLE = False
        MCTSPlayer = None
""" channel is a queue which communicates player's mouse choice of card or color to game logic """
channel = []

""" flush the channel from mouse choice to game logic """
def flushchannel():
    while len(channel) > 0:
        channel.popleft()

""" challenge flag: true if challenge taken by player """
challengetaken = [False]

""" display change flag: first true if any discard done, second if player drew or discard """
displaychanged = [True, True]

#============ Game play section ==================#

class UnoCard:
    """ The Uno card. The first field is color, second field is number or command. """
    def __init__(self, c, t):
        self.cardcolor = c
        self.cardtype = t
        return
    def __str__(self):
        return 'UnoCard(' + self.cardcolor + ', ' + self.cardtype + ')'


class UnoCardGamePlayer:
    """ Each Uno player has a name, a score, may be a bot, and has a hand of UnoCards. """
    def __init__(self, name, score, isabot, hand):
        self.name = name
        self.score = score
        self.isabot = isabot
        self.hand = hand
        return

""" classifications of colors and types for card faces """
colors = ['Blue', 'Green', 'Red', 'Yellow']  # suit colors
tkcolor = {'Blue': 'blue', 'Green': 'green', 'Red': 'red', 'Yellow': 'gold',
           'Wild': 'black', 'None': 'lightyellow'}
types = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'Skip', 'Draw Two', 'Reverse']
numtypes = types[:-3]
wildtypes = ['Wild', 'Draw Four']
cmdtypes = types[-3:] +  wildtypes
alltypes = types + wildtypes
unopreferred = ['Skip', 'Draw Two', 'Reverse', 'Draw Four']
ttypes = sorted(types + types)[1:]
typeordering = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'Wild', 'Skip',
    'Reverse', 'Draw Two', 'Draw Four']

""" The Uno card game deck, unshuffled. """
originaldeck = [UnoCard(c, v) for v in ttypes for c in colors] + \
    [UnoCard('Wild', 'Wild') for _ in range(4)] + \
    [UnoCard('Wild', 'Draw Four') for _ in range(4)]


class UnoCardGameState:
    """
    Encapsulates a board state of the gane, including players, cards, color being played,
    order of play, current player, and whether the card showing has had its command used
    """
    def __init__(self, playernames=['Player', 'Bot1', 'Bot2', 'Bot3'], oldscores = []):
        """
        Construct and initialize Uno game. Includes dealing hands and picking who is to start.
        """
        deck = originaldeck.copy()
        shuffle(deck)
        while True:  # cannot start with a Draw Four on discard pile top
            discardpile, drawpile = [deck[28]], deck[29:]
            if discardpile[-1].cardtype != 'Draw Four':
                break
            shuffle(deck[28:])

        hands = [deck[i:i+7] for i in range(0, 27, 7)]

        self.drawpile = drawpile
        self.discardpile = discardpile
        self.players = [UnoCardGamePlayer(playernames[i], 0,
            playernames[i][:3] == 'Bot', hands[i]) for i in range(len(playernames))]
        if len(oldscores) > 0:
            for i, n in enumerate(oldscores):
                self.players[i].score = n

        self.pnow = 0
        self.colornow = 'Wild'
        self.lastcolor = 'Wild'
        self.clockwise = True
        self.commandsvalid = True

        dealer = choice(range(len(playernames)))
        logline(f"Player {playernames[dealer]} is dealer.")
        # handle an initial Reverse card
        if discardpile[-1].cardtype == 'Reverse':
                self.clockwise = False
                logline('First card Reverse, so starting counterclockwise with dealer.')
                self.commandsvalid = False
                self.pnow = dealer
        else:
            self.nextplayer(dealer)
        logline(f"Player {playernames[self.pnow]} starts play.")
        if discardpile[-1].cardcolor == 'Wild':
            self.choosecolor()
            self.commandsvalid = False
        else:
            self.colornow = discardpile[-1].cardcolor
        displaychanged[0], displaychanged[1] = True, True
        return

    def nextplayer(self, idx=None):
        """ Set the next player to play to game.pnow (clockwise or counterclockwise) """
        if idx == None:
            idx = self.pnow
        self.pnow = (idx + 1 if self.clockwise else idx - 1) % len(self.players)

    def nextsaiduno(self):
        """
        Returns true if the next player to play has said Uno, which means they have
        only one card left. If so, it is best for the current player if they play
        to make the Uno sayer draw cards or lose a turn.
        """
        nextp = (self.pnow + (1 if self.clockwise else -1)) % len(self.players)
        return len(self.players[nextp].hand) == 1

    def playableindices(self):
        """ Return a vector of indices of cards in hand that are legal to discard """
        hand = self.players[self.pnow].hand
        mcolor, mtype = self.colornow, self.discardpile[-1].cardtype
        return [i for i, c in enumerate(hand) if \
            c.cardcolor == mcolor or c.cardtype == mtype or c.cardcolor == 'Wild']

    def nextgame(self):
        scores = [x.score for x in self.players]
        self.__init__([p.name for p in self.players], scores)

    def drawcardsfromdeck(self, n=1):
        """ Current player to draw n cards from the draw pile. """
        if n in [2, 4]:
            self.commandsvalid = False
        if n == 4:  # draw four
            # bot will challenge half the time, player must challenge in 5 seconds.
            if (self.players[self.pnow].isabot and rand() < 0.5) or \
                ((not self.players[self.pnow].isabot) and challengetaken[0]):
                challengetaken[0] = False
                logline(f"{self.players[self.pnow].name} challenged Draw Four!")
                challenger, savecolor = self.pnow, self.colornow
                self.nextplayer(); self.nextplayer(); self.nextplayer(); # prior player
                self.colornow = self.lastcolor
                hand = self.players[self.pnow].hand
                if any([x.cardcolor == self.colornow for x in hand]):
                    logline('Challenge sustained! Challenged Draw Four player draws 4.')
                    self.drawcardsfromdeck(2)
                    self.drawcardsfromdeck(2)  # draw 2 twice, avoids case with draw 4 code
                    self.pnow, self.colornow = challenger, savecolor
                    return
                else:
                    logline('Challenge fails. Challenging player now draws 6.')
                    n = 6
                self.pnow, self.colornow = challenger, savecolor
            challengetaken[0] = False

        s = "1 card." if n == 1 else f"{n} cards."
        logline(f"Player {self.players[self.pnow].name} draws {s}")
        for _ in range(n):
            self.players[self.pnow].hand.append(self.drawpile.pop())
            if len(self.drawpile) == 0:  # out of draw pile
                temp = self.discardpile[:-2].copy()
                shuffle(temp)
                self.drawpile = temp
                self.discardpile = [self.discardpile[-1]]
        
        # Update MCTS belief if opponent drew cards
        if MCTS_AVAILABLE and MCTS_PLAYER is not None and self.pnow > 0:
            from Transitions import UNOAction, ActionType
            action = UNOAction(type=ActionType.GET_NEW_CARD, card=None)
            MCTS_PLAYER.update_belief(self, action, self.pnow)

        if self.pnow == 0:
            displaychanged[1] = True


    def discard(self, idx=-1):
        """
        Current player to discard card at index idx in hand (last card in hand as default).
        Handle wild card discard by having current player choose the new self.colornow.
        """
        hand = self.players[self.pnow].hand
        hand[idx], hand[-1] = hand[-1], hand[idx]
        self.discardpile.append(hand.pop())
        lastdiscard = self.discardpile[-1]
        logline(f"Player {self.players[self.pnow].name} discarded {str(lastdiscard)}")
        
        # Update MCTS belief if opponent played a card
        if MCTS_AVAILABLE and MCTS_PLAYER is not None and self.pnow > 0:
            from Transitions import UNOAction, ActionType
            from UNOState import card_to_string
            card_str = card_to_string(lastdiscard)
            action = UNOAction(type=ActionType.V_CARD, card=card_str)
            MCTS_PLAYER.update_belief(self, action, self.pnow)
        
        self.lastcolor = self.colornow
        if lastdiscard.cardcolor == 'Wild':  # wild card discard, so choose a color to be colornow
            self.choosecolor()
            logline(f"New color chosen: {self.colornow}")
        else:
            self.colornow = lastdiscard.cardcolor
        self.commandsvalid = True
        if self.pnow == 0:
            displaychanged[1] = True
        displaychanged[0] = True


    def turn(self):
        """
        Execute a single turn of the game for one player.  Command cards are followed
        only the first turn after played even if the still show as a discard.
        """
        name, hand = self.players[self.pnow].name, self.players[self.pnow].hand
        lastdiscard, indices = self.discardpile[-1], self.playableindices()
        mtype = lastdiscard.cardtype
        assert len(hand) > 0, f"Empty hand held by {name}"
        if mtype in cmdtypes and self.commandsvalid and mtype != 'Wild':
            self.commandsvalid = False
            if mtype == 'Draw Four':
                self.drawcardsfromdeck(4)
            elif mtype == 'Draw Two':
                self.drawcardsfromdeck(2)
            elif mtype == 'Skip':    # skip, no uno check
                logline(f"{name} skips a turn.")
            elif mtype == 'Reverse':
                self.clockwise = not self.clockwise
                logline('Reverse: now going ' + \
                    ('clockwise' if self.clockwise else 'counter-clockwise.'))
                self.nextplayer()
            self.nextplayer()
            return
        else:  # num card, or command card is already used
            if len(indices) == 0:
                logline(f'[{name}] No playable cards, drawing...')
                self.drawcardsfromdeck(1)  # draw, then discard if drawn card is a match
                indices  = self.playableindices()
                if len(indices) > 0:
                    drawn_card = self.players[self.pnow].hand[indices[0]]
                    logline(f'[{name}] Drawn card was playable: {str(drawn_card)}')
                    self.discard(indices[0])

            elif name[:3] != 'Bot':  # not bot, so player moves
                # Use MCTS if available and enabled
                if USE_MCTS and MCTS_PLAYER is not None:
                    logline(f'[Player 0] MCTS is thinking... (hand: {len(hand)} cards)')
                    top.update()
                    
                    # Get action from MCTS
                    card_index = MCTS_PLAYER.get_action(self)
                    
                    if card_index is not None and card_index in indices:
                        # Get card before discarding (for belief update)
                        from UNOState import card_to_string
                        from Transitions import UNOAction, ActionType
                        card = self.players[self.pnow].hand[card_index]
                        card_str = card_to_string(card)
                        
                        # Play the card chosen by MCTS
                        self.discard(card_index)
                        logline(f'[Player 0] MCTS chose to play: {card_str}')
                        
                        # Update belief after playing (card already discarded, so use discard pile)
                        action = UNOAction(type=ActionType.V_CARD, card=card_str)
                        MCTS_PLAYER.update_belief(self, action, 0)  # Player 0
                    elif len(indices) == 0:
                        # No playable cards, must draw
                        self.drawcardsfromdeck(1)
                        logline('[Player 0] MCTS chose to draw a card')
                        
                        # Update belief after drawing
                        from Transitions import UNOAction, ActionType
                        action = UNOAction(type=ActionType.GET_NEW_CARD, card=None)
                        MCTS_PLAYER.update_belief(self, action, 0)  # Player 0
                    else:
                        logline('[Player 0] MCTS returned invalid action, falling back to manual')
                        # Fall back to manual clicking
                        logline('Click on a card to play.')
                        flushchannel()
                        while True:
                            if len(channel) > 0:
                                item = channel.pop(0)
                                if item in indices:
                                    self.discard(item)
                                    break
                                else:
                                    logline('That card is not playable.')
                            else:
                                sleep(0.1)
                                top.update()
                else:
                    # Manual clicking (original behavior)
                    logline('Click on a card to play.')
                    flushchannel()
                    while True:
                        if len(channel) > 0:
                            item = channel.pop(0)
                            if item in indices:
                                self.discard(item)
                                break
                            else:
                                logline('That card is not playable.')

                        else:
                            sleep(0.1)
                            top.update()

            elif self.nextsaiduno():  # bot might need to stop next player win
                hand.sort(key=cardvalue)
                indices = self.playableindices()
                played_card = self.players[self.pnow].hand[indices[-1]]
                self.discard(indices[-1])
                logline(f'[{name}] Bot played {str(played_card)} (blocking opponent)')
            else: # bot play any playable in hand
                chosen_idx = choice(indices)
                played_card = self.players[self.pnow].hand[chosen_idx]
                self.discard(chosen_idx)
                logline(f'[{name}] Bot played {str(played_card)}')

        if len(hand) == 1:
            logline(f"{name} says UNO!")
        self.nextplayer()

    def choosecolor(self):
        """
        Choose a new self.colornow, automatically if a bot, via player choice if not a bot.
        """
        logline(f"Player {self.players[self.pnow].name} choosing color")
        hand = self.players[self.pnow].hand
        if len(hand) == 0:
            self.colornow = choice(colors)
        elif self.players[self.pnow].isabot or (USE_MCTS and self.pnow == 0 and MCTS_PLAYER is not None):
            # If Player 0 is controlled by MCTS, auto-pick color instead of waiting for UI input
            self.colornow = preferredcolor(hand)
        else:
            # For non-bot players, try GUI first, fallback to auto-choice if GUI unavailable
            try:
                if 'top' in globals() and top.winfo_exists():
                    flushchannel()
                    while True:
                        if len(channel) > 0:
                            item = channel.pop(0)
                            if item in colors:
                                self.colornow = item
                                break
                        else:
                            sleep(0.1)
                            top.update()
                else:
                    # GUI not available - auto-choose based on hand
                    self.colornow = preferredcolor(hand) if len(hand) > 0 else choice(colors)
            except (tk.TclError, AttributeError, NameError):
                # GUI widget doesn't exist - auto-choose based on hand
                self.colornow = preferredcolor(hand) if len(hand) > 0 else choice(colors)

        logline(f"Current color is now {self.colornow}.")

def cardscore(c):
    t = c.cardtype
    return 50 if t == 'Draw Four' else 20 if t in cmdtypes else int(t)

def handscore(hand):
    return 0 if len(hand) == 0 else sum(cardscore(x) for x in hand)

def cardvalue(c):
    return next(filter(lambda x: x == c.cardtype, typeordering), 0)

def countcolor(cards, clr):
    return sum([c.cardcolor == clr for c in cards])

def colorcounts(cards):
    return sorted([(countcolor(cards, clr), clr) for clr in colors])

""" Preferred color is the one that is most counted in the hand. """
def preferredcolor(hand):
    return colorcounts(hand)[-1][1]


#================  required documentation section ======================#

unodocs = """
Official Rules For Uno Card Game
The aim of the game is to be the first player to score 500 points, achieved (usually over several rounds of play) by being the first to play all of one's own cards and scoring points for the cards still held by the other players.
The deck consists of 108 cards: four each of "Wild" and "Wild Draw Four", and 25 each of four colors (red, yellow, green, blue). Each color consists of one zero, two each of 1 through 9, and two each of "Skip", "Draw Two", and "Reverse". These last three types are known as "action cards".
To start a hand, seven cards are dealt to each player, and the top card of the remaining deck is flipped over and set aside to begin the discard pile. The player to the dealer's left plays first unless the first card on the discard pile is an action or Wild card (see below). On a player's turn, they must do one of the following:
*    play one card matching the discard in color, number, or symbol
*    play a Wild card, or a playable Wild Draw Four card (see restriction below)
*    draw the top card from the deck, then play it if possible
Cards are played by laying them face-up on top of the discard pile. Play proceeds clockwise around the table.
Action or Wild cards have the following effects:
===============================================================================================================================================================
Card            Effect when played from hand                                                                                                     Effect as first discard
---------------------------------------------------------------------------------------------------------------------------------------------------------------
Skip            Next player in sequence misses a turn                                                                                       Player to dealer's left misses a turn
Reverse         Order of play switches directions (clockwise to counterclockwise, or vice versa)            Dealer plays first; play proceeds counterclockwise
Draw Two        Next player in sequence draws two cards and misses a turn                                             Player to dealer's left draws two cards and misses a turn
Wild            Player declares the next color to be matched ; current color may be chosen                       Player to dealer's left declares the first color to be matched and plays a card in it
Wild Draw Four  Player declares the next color to be matched; next player in sequence draws four   Return card to the deck, shuffle, flip top card to start discard pile
A player who draws from the deck must either play or keep that card and may play no other card from their hand on that turn.
A player may play a Wild card at any time, even if that player has other playable cards.
A player may play a Wild Draw Four card only if that player has no cards matching the current color. The player may have cards of a different color matching the current number or symbol or a Wild card and still play the Wild Draw Four card.[5] A player who plays a Wild Draw Four may be challenged by the next player in sequence (see Penalties) to prove that their hand meets this condition.
If the entire deck is used during play, the top discard is set aside and the rest of the pile is shuffled to create a new deck. Play then proceeds normally.
It is illegal to trade cards of any sort with another player.
A player who plays their next-to-last-card must call "uno" as a warning to the other players.[6]
The first player to get rid of their last card ("going out") wins the hand and scores points for the cards held by the other players. Number cards count their face value, all action cards count 20, and Wild and Wild Draw Four cards count 50. If a Draw Two or Wild Draw Four card is played to go out, the next player in the sequence must draw the appropriate number of cards before the score is tallied.
The first player to score 500 points wins the game.
Penalties
=========
If a player does not call "uno" after laying down their next-to-last card and is caught before the next player in sequence takes a turn (i.e., plays a card from their hand, draws from the deck, or touches the discard pile), they must draw two cards as a penalty. If the player is not caught in time (subject to interpretation) or remembers to call "uno" before being caught, they suffer no penalty.
If a player plays a Wild Draw Four card, the following player can challenge its use. The player who used the Wild Draw Four must privately show their hand to the challenging player, in order to demonstrate that they had no matching colored cards. If the challenge is correct, then the challenged player draws four cards instead. If the challenge is wrong, then the challenger must draw six cards; the four cards they were already required to draw plus two more cards.
"""

#============ GUI interface section =======================#

top = tk.Tk()
righthandside = tk.Frame(top, height=700, width=310)
righthandside.pack(side=tk.RIGHT)
lefthandside = tk.Frame(top, height=700, width=810)
lefthandside.pack(side=tk.LEFT)

def chalcmd(): challengetaken[0] = True 
chal = tk.Button(righthandside, width=50, text='Challenge', command = chalcmd)
chal.pack(side=tk.BOTTOM)

def cb(): channel.append('Blue')
def cg(): channel.append('Green')
def cr(): channel.append('Red')
def cy(): channel.append('Yellow')
cmd = [cb, cg, cr, cy]
for i, c in enumerate(colors):
    b = tk.Button(righthandside, bg=tkcolor[c], width=50, text=c, fg="white",
                  command=cmd[i])
    b.pack(side=tk.BOTTOM)

log_area = scrolledtext.ScrolledText(righthandside, wrap=tk.WORD, width=50, height=40, font=("Courier", 8))
log_area.insert('1.0', ' ')
log_area.pack(side=tk.TOP)

canvas = tk.Canvas(lefthandside, width=810, height=700, bg='lightyellow')
canvas.pack()

""" Lines are logged by extending logtxt at its start. """
def logline(txt):
    # Always print to console/command line
    print(f"[LOG] {txt}")
    
    # Also update GUI if available
    try:
        # Check if GUI is available (log_area exists and is valid)
        if 'log_area' in globals():
            try:
                if log_area.winfo_exists():
                    log_area.insert('1.0', '\n' + txt)
                    log_area.update()
            except (tk.TclError, AttributeError):
                pass  # Widget destroyed or invalid, fall through
    except (NameError, Exception):
        pass  # GUI widget doesn't exist, that's okay

# Removed unused cbutton() function

def drawunocard(canvas, card, x0, y0, width, height, bcolor='white'):
    fcolor = tkcolor[card.cardcolor]
    radius = (width + height) / 4
    x1 = x0 + width
    y1 = y0 + height
    points = [x0 + radius, y0, x0 + radius, y0, x1 - radius, y0, x1 - radius, y0, x1, y0,
              x1, y0 + radius, x1, y0 + radius, x1, y1 - radius, x1, y1 - radius, x1, y1,
              x1 - radius, y1, x1 - radius, y1, x0 + radius, y1, x0 + radius, y1, x0, y1,
              x0, y1 - radius, x0, y1 - radius, x0, y0 + radius, x0, y0 + radius, x0, y0]
    canvas.create_polygon(points, outline=fcolor, fill=fcolor, smooth=True)
    txt = card.cardtype.upper()
    if txt[0] in ['R', 'S', 'W']:
        txt = txt[0]
    elif txt[0] == 'D':
        txt = 'D' + ('2' if txt[-1] == 'O' else '4')
    canvas.create_text(x0 + 0.5 * width, y0 + height / 3, fill=bcolor, text=txt)

def drawfacedowncard(canvas, x0, y0, width, height, bcolor="darkgray"):
    """ Face down Uno cards are blank dark gray rectangles with rounded corners. """
    drawunocard(canvas, UnoCard("Wild", " "), x0, y0, width, height, bcolor)

cardpositions = {}

def clickcallback(evt):
    """ Tk mouse callback: translates valid mouse clicks to a channel item """
    for p in cardpositions.items():
        x0, y0, x1, y1 = p[1]
        if x0 < evt.x < x1 and y0 < evt.y < y1:
            channel.append(p[0])
            return

canvas.bind("<Button-1>", clickcallback)

# announce the rules and penalties per task description
messagebox.showinfo(title=None, message=unodocs)

# display the game on the Tk canvas
def drawposition(canvas, game):
    hand = game.players[0].hand
    if displaychanged[0]:
        """ Draw the game board on the canvas including player's hand """
        canvas.update()
        height, width = canvas.winfo_reqheight(), canvas.winfo_reqwidth()
        canvas.create_polygon(0, 0, width, height, fill='lightyellow')
        canvas.create_text(360, 420, fill="navy", text=game.players[0].name)
        canvas.create_text(60, 300, fill="navy", text=game.players[1].name)
        canvas.create_text(370, 60, fill="navy", text=game.players[2].name)
        canvas.create_text(680, 300, fill="navy", text=game.players[3].name)
        drawunocard(canvas, game.discardpile[-1], 310, 240, 40, 80)
        drawfacedowncard(canvas, 370, 240, 40, 80)
        displaychanged[0] = False
    if displaychanged[1] and len(hand) > 0:
        canvas.create_polygon(30, 500, 800, 500, 800, 690, 30, 690, fill='lightyellow')
        canvas.update()
        nrow = (len(hand) - 1) // 16 + 1
        for row in range(nrow):
            cards = hand[row * 16 : min(len(hand), (row + 1) * 16)]
            startx, starty = 40 + (16 - len(cards)) * 20, 500 + 85 * row
            for i, card in enumerate(cards):
                idx, x0 = i, startx + 50 * i
                cardpositions[idx] = [x0, starty, x0 + 40, starty + 80]
                drawunocard(canvas, card, x0, starty, 40, 80)
        
        displaychanged[1] = False
    sleep(0.5)

# Parse command line arguments
def parse_arguments():
    """Parse command line arguments for MCTS parameters."""
    parser = argparse.ArgumentParser(
        description='UNO Game with MCTS AI',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--gamma', 
        type=float, 
        default=0.99,
        help='Discount factor for MCTS (default: 0.99)'
    )
    parser.add_argument(
        '--c_param', 
        type=float, 
        default=1.4,
        help='UCB1 exploration parameter for MCTS (default: 1.4)'
    )
    parser.add_argument(
        '--max_depth', 
        type=int, 
        default=20,
        help='Maximum depth for MCTS rollout (default: 20)'
    )
    parser.add_argument(
        '--num_particles', 
        type=int, 
        default=100,
        help='Number of belief particles for POMDP (default: 100)'
    )
    parser.add_argument(
        '--num_simulations', 
        type=int, 
        default=500,
        help='Number of MCTS simulations per decision (default: 500)'
    )
    parser.add_argument(
        '--use_mcts', 
        action='store_true',
        default=True,
        help='Use MCTS for Player 0 (default: True)'
    )
    parser.add_argument(
        '--no_mcts', 
        action='store_false',
        dest='use_mcts',
        help='Disable MCTS and use manual clicking'
    )
    parser.add_argument(
        '--num_rounds', 
        type=int, 
        default=10,
        help='Number of rounds to play (default: 10)'
    )
    
    return parser.parse_args()

# Parse arguments
args = parse_arguments()

# Global variables for tracking game statistics
NUM_ROUNDS_TARGET = args.num_rounds
rounds_played = 0
player_0_wins = 0

# Run the game itself.

GAME = UnoCardGameState()
ROUND = [1]

# Try to import MCTS now (after argparse, before game starts)
_import_mcts()

# Initialize MCTS player if available
if MCTS_AVAILABLE and args.use_mcts:
    MCTS_PLAYER = MCTSPlayer(
        gamma=args.gamma,
        c_param=args.c_param,
        max_depth=args.max_depth,
        num_particles=args.num_particles,
        num_simulations=args.num_simulations
    )
    USE_MCTS = True
    print(f"\n{'='*60}")
    print(f"MCTS Player initialized with parameters:")
    print(f"  gamma: {args.gamma}")
    print(f"  c_param: {args.c_param}")
    print(f"  max_depth: {args.max_depth}")
    print(f"  num_particles: {args.num_particles}")
    print(f"  num_simulations: {args.num_simulations}")
    print(f"  USE_MCTS: {USE_MCTS}")
    print(f"{'='*60}\n")
else:
    MCTS_PLAYER = None
    USE_MCTS = False
    if not MCTS_AVAILABLE:
        print("WARNING: MCTS not available. Falling back to manual clicking.\n")
    else:
        print("MCTS disabled. Using manual clicking.\n")

# Global variables for tracking game statistics
NUM_ROUNDS_TARGET = args.num_rounds
rounds_played = 0
player_0_wins = 0

class UnoGameApp(Thread):
    def __init__(self):
        self.data = {}                      # initial data value
        super().__init__()

    def run(self):
        global rounds_played, player_0_wins
        
        while True:
            # do the turns of play in the game, keeping score totals from the rounds
            drawposition(canvas, GAME)
            canvas.update()
            if all([len(x.hand) > 0 for x in GAME.players]):
                GAME.turn()
                if not USE_MCTS and GAME.players[GAME.pnow].name[:4] == "Play" and \
                    GAME.discardpile[-1].cardtype == "Draw Four" and GAME.commandsvalid:
                    drawposition(canvas, GAME)
                    messagebox.showinfo(title=None,
                        message="Click Challenge within 5 seconds to challenge Draw Four")
                    sleep(5)

                drawposition(canvas, GAME)
            else:
                winner = [i for i in range(len(GAME.players)) \
                    if len(GAME.players[i].hand) == 0][0]
                if GAME.discardpile[-1].cardtype == "Draw Two":
                    GAME.nextplayer()  # next player might have to draw before scoring done
                    GAME.drawcardsfromdeck(2)
                elif GAME.discardpile[-1].cardtype == "Draw Four":
                    GAME.nextplayer()
                    GAME.drawcardsfromdeck(2)
                    GAME.drawcardsfromdeck(2)   # D2 twice because not to be contested as a D4

                handsums = sum([handscore(x.hand) for x in GAME.players])
                GAME.players[winner].score += handsums

                # Track wins
                rounds_played += 1
                if winner == 0:
                    player_0_wins += 1
                
                logline(f"Player {GAME.players[winner].name} wins round {ROUND[0]}!")
                logline(f"Round {rounds_played}/{NUM_ROUNDS_TARGET} - Player 0 wins: {player_0_wins}/{rounds_played}")
                messagebox.showinfo(title=None,
                    message=f"The winner of round {ROUND[0]} is {GAME.players[winner].name}.\n" + \
                    f"Winner gains {handsums} points.")
                logline(f"Scores: {[x.score for x in GAME.players]}")
                
                # Check if we've played enough rounds
                if rounds_played >= NUM_ROUNDS_TARGET:
                    logline(f"\n{'='*60}")
                    logline(f"Game Statistics:")
                    logline(f"  Total rounds played: {rounds_played}")
                    logline(f"  Player 0 (MCTS) wins: {player_0_wins}")
                    logline(f"  Win rate: {player_0_wins/rounds_played*100:.1f}%")
                    # logline(f"  Target: {NUM_ROUNDS_TARGET-1}/{NUM_ROUNDS_TARGET} wins")

                    
                    if any([x.score >= 500 for x in GAME.players]):
                        s = "Game over. Scores:\n\n"
                        for p in GAME.players:
                            s += f"   {p.name}:  {p.score}  {'WINNER!' if p.score >= 500 else ''}\n"
                        messagebox.showinfo(title="Game Over", message=s)
                    else:
                        messagebox.showinfo(title="Rounds Complete", 
                            message=f"Completed {NUM_ROUNDS_TARGET} rounds.\n" +
                            f"Player 0 won {player_0_wins} out of {rounds_played} rounds.")
                    sleep(2)
                    exit()

                if any([x.score >= 500 for x in GAME.players]):
                    s = "Game over. Scores:\n\n"
                    for p in GAME.players:
                        s += f"   {p.name}:  {p.score}  {'WINNER!' if p.score >= 500 else ''}\n"

                    messagebox.showinfo(title="Game Over", message=s)
                    sleep(1)
                    exit()

                logline("-------------------------\nNew round!\n-----------------------")
                GAME.nextgame()
                ROUND[0] += 1
                
                # Reset MCTS belief for new round
                if MCTS_AVAILABLE and MCTS_PLAYER is not None:
                    MCTS_PLAYER.reset()
                
                drawposition(canvas, GAME)
                sleep(0.1)


app = UnoGameApp()
app.setDaemon(True)
app.start()
top.mainloop()
