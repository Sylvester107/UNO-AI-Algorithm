---
layout: default
title: Project Overview
nav_order: 2
---
## The Game 👾
- we designed an algorithm to pplay the UNO Game these are the rules of the Game:

- Goal: Be first to 500 points by winning hands; you win a hand by playing your last card, then score opponents’ remaining cards (numbers face value, action 20, wilds 50).
- Setup: 108-card deck; colors red/yellow/green/blue. Deal 7 cards each; flip one card to start the discard.
- On your turn: Play a card matching the top discard by color/number/symbol, or play any Wild (Wild Draw 4 only if you lack the current color). If you can’t play, draw one: if it fits, you may play it; otherwise keep it and end your turn.
- Direction/turn order: Clockwise unless a Reverse flips direction.
- Action cards: Skip (next player loses turn), Reverse (changes direction), Draw Two (next player draws 2 and skips), Wild (choose color), Wild Draw Four (choose color; next player draws 4 and skips; playable only with no card of the current color).
- UNO call: When you’re down to one card, you must say “UNO”; if caught not saying it before the next player acts, draw 2 as penalty.
- Deck exhaustion: If the draw pile empties, reshuffle the discard (keep its top card) to form a new draw pile.
- Wild Draw Four challenge: Next player may challenge; if the wild was illegal, the user draws 4; if the challenge fails, challenger draws 6.


## Objective
Our goal was to create an AI agent that:
- takes game state as input
- predicts an optimal action
- improves perfermance through repeated gameplay

we focused on designing an algorithm that is:
- Efficient
- Able to handle uncertainty
- adatptive against multiple opponents

## Approach 
The Project blends
- advanced search algorithms and modeling(MCSTS with POMDP)

The next pages breaks down our method and results


