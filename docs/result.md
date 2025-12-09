---
layout: default
title: Results
nav_order: 4
---

## Performance Summary 📊📈
- our algorithm achieved 20% win rate over 10 games
- This is rate is based on the fact that it is being played agains other bots as defined in the rossetta code
- we did not play the game against our algorihtm(yet, meaning no humans have played with it

## Observations and future work

The search tree stores visit counts and average scores for each child action.
While the current code returns only the best action, the system can be extended to return multiple candidate actions with their associated win probabilities. 
These probabilities can be derived from:
- **Visit counts** (how often each action was explored)
- **Average scores** (average reward from simulations that took that action)
- **Win rate estimates** (proportion of simulations that led to wins)

This would allow ranking actions by expected value and selecting based on risk tolerance or other criteria, rather than always picking the single most-visited action.

## Demo

HEAD:docs/result.md
here is a demo of our algorithm playing the game
=======
Here is a demo of our algorithm playing the game
We played 1 round with num_simulations = 50 for faster game play
It won!!
f61de6091e5694e31de3538493deaaaa6776d903:docs/pages/result.md

<iframe width="560" height="315"
src="https://youtu.be/5Gujk1apuf4"
title="YouTube video player"
frameborder="0"
allowfullscreen></iframe>
