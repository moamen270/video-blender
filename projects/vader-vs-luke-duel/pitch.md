# Vader vs Luke — pitch (phase 1, gate G1)

**Idea card:** `content/IDEAS.md` → "card: vader-vs-luke-duel".
- Darth Vader and Luke Skywalker (parody) in a lightsaber duel. The joke is in the father-and-son duel.
- Evergreen, no event. Famous cast, per the owner, 2026-09-26.

Rules: skill `comedy-pitch`. Three different joke mechanisms. The owner judges the joke.

## Pitch A: "The Hand" (mechanism: absurd continuation, the loser's hand wins)
- **Logline:** Vader cuts off Luke's hand, just like in the film. The hand, still holding the saber, keeps fighting on its own and beats Vader.
- **Why it is funny:** the most famous defeat in Star Wars keeps going. The duel carries on without the person. A proud Sith Lord gets out-fenced by a hand, and Luke just watches, as surprised as Vader.
- **Beats:**
  1. The duel on a gantry. Vader's red blade cuts, and Luke's hand flies off with the green saber still in its grip. Luke stares at his wrist. *"NOOO!"*
  2. The hand lands on its fingers, stands up like a spider, and ignites the saber.
  3. It duels Vader: parry, parry, a flip off the railing. Vader is losing ground to a hand.
  4. The turn: the hand disarms Vader, and his red saber falls down the shaft.
  5. The payoff (a new surprise): the hand walks back to Luke and high-fives his other hand. Vader, alone: *"...Impressive. Most impressive."*
- **Punchline:** the high-five between Luke's two hands, then Vader's famous line said to a hand.
- **First frame and hook text:** the hand spinning in the air with the lit saber, and Luke's shocked face behind it.
  Hook text: **"He lost a hand. The hand didn't lose."**
- **Build:** Vader, Luke and a saber prop (new). The gantry set is new. The hand is a detached hand mesh with finger "legs" (simple). The duel moves reuse the fight IK.
- **Risk:** the hand's fencing must read clearly at phone size. It is cartoon violence: no blood (sabers cauterise), but check platform rules for severed limbs.

## Pitch B: "The Longest Fall" (mechanism: an endless loop, space bends)
- **Logline:** Luke refuses to join Vader and drops into the shaft, as in the film, then falls from the ceiling behind Vader. Again. And again.
- **Why it is funny:** the most dramatic exit in Star Wars becomes a doorway that loops. Vader's patience wears down with every return, while Luke keeps the same heroic face.
- **Beats:**
  1. *"Join me."* Luke: *"Never!"* He lets go and falls into the shaft.
  2. A second later he drops from the ceiling behind Vader and lands, confused. Vader turns around: *"...Join me?"* *"Never!"* He jumps again.
  3. The escalation. Each return is faster and messier: Luke lands on Vader, then lands already holding a cup of tea from somewhere. Vader starts saying "Join me" in a flat, tired voice.
  4. The turn: Vader jumps into the shaft himself to end it.
  5. The payoff (a new surprise): Vader falls from the ceiling behind Luke. Now Luke turns: *"...Join me?"* Then they are back to the first frame. It is a real loop: the last frame sets up frame 1.
- **Punchline:** the role swap, with Luke offering "Join me?" to his fallen father.
- **First frame and hook text:** Luke letting go of the gantry, falling.
  Hook text: **"The longest fall in the galaxy."**
- **Build:** Vader, Luke, the saber, and a shaft/gantry set (new, the same set as A). There is little fencing, mostly falls and landings.
- **Risk:** the viewer must read "he came back from above" in the first repeat. That needs one clear establishing shot of the shaft and the ceiling.

## Pitch C: "Luke, I Am Your WHAT?" (mechanism: a communication failure that escalates)
- **Logline:** Vader tries to deliver the biggest reveal in film history, but the lightsaber hum is too loud and Luke can't hear it.
- **Why it is funny:** the grand moment keeps being ruined by the one prop that makes the scene cool. Every fix creates a new problem. It escalates from the hum, to shouting, to the dark.
- **Beats:**
  1. Blades crossed, loud humming. Vader: *"Luke... I am your father."* Luke: *"WHAT?"*
  2. Vader repeats it louder, and the sabers get louder too (a clash, sparks). *"I AM YOUR—"* **BZZZT.** Luke: *"YOU'RE MY WHAT?"*
  3. Vader holds up a finger. Both switch off their sabers.
  4. The turn: pitch black, except for the blinking lights on Vader's chest. Vader, calm: *"...I am your father."* A pause. Luke: *"...Where are you?"*
  5. The payoff: both ignite their sabers again. HUMMM. Luke: *"WHAT?"* Then back to the top (a loop).
- **Punchline:** Luke's *"...Where are you?"* in the dark, with only the chest lights blinking.
- **First frame and hook text:** crossed red and green blades between the two faces.
  Hook text: **"Luke, I am your WHAT?"**
- **Build:** Vader (the chest panel lights matter here), Luke and the saber. The set is the smallest: a close two-shot.
- **Risk:**
  - The joke depends on the voices and the timing, so it is weaker as a silent 3-panel comic.
  - The dark shot must not be flat black. It needs a dim blue light and the chest lights, or it fails the border check.
  - A dark screen can also cost viewers.

## Pitch PoC
Storyboard stills, two per pitch: the hook frame and the punchline frame. They are rendered in Blender with
stand-ins: the Quaternius base rig coloured as Vader (black, with the approved cape) and as Luke (dark tunic),
emissive sabers, and a simple lit corridor/gantry. The stills are made by `tools/storyboard.py` from
`poc/storyboard.json`, and the output goes to `poc/board.jpg`.

## Owner decision (G1)
chosen: **C — Luke, I Am Your WHAT?** · date: 2026-09-26 · notes: in the dark, Vader: "It's so dark now... wait a minute..." — pulls a hanging lamp's rope, light on — "...that's better." Then continue.
