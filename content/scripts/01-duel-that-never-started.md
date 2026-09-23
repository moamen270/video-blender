# 01 — The Duel That Never Started (v2, after table read)

**Series:** Standoff Etiquette · **Length:** ~30 s · **Cast:** the Ronin, the Oni Warlord (existing samurai kit)
**Hook text:** "Two blades. Zero patience." · **Ending:** callback line → loop back to the opening eye-snap
**Why this one first:** every asset already exists (characters, stage, clash solver, SFX bank, music), so it
is the phase-1 proof of the hook/script machine — the only variable we test is the writing.

| t (s) | shot | action | line / sound |
|---|---|---|---|
| 0.0–2.5 | extreme close-up, Ronin's eyes | eyes snap open at 0.2 s; petals drift | SFX sword-draw shing at 0.1 s · TEXT "Two blades. Zero patience." |
| 2.5–5.5 | wide standoff, moon | both in iai stance, hands on hilts, wind | **Warlord:** "Draw." · **Ronin:** "You draw." |
| 5.5–9.0 | two-shot, slow push | neither moves | **Warlord:** "The challenger draws first." · **Ronin:** "You challenged me." · **Warlord:** "I challenged you… to be challenged." |
| 9.0–9.6 | hold | nothing moves (deliberate beat) | silence |
| 9.6–13.0 | medium on Ronin | Ronin dips his head a little | **Warlord:** "Was that a bow or a nod?" · **Ronin:** "…A deep nod." · **Warlord:** "Bow. Properly." |
| 13.0–15.5 | wide | both bow deeply at the same moment — helmets collide with a CLANK | SFX armour clank · music stops |
| 15.5–18.0 | low close-up, both still bent over | frozen mid-bow, faces inches apart | **Warlord:** "You bowed into my bow." · **Ronin:** "You bowed into mine." |
| 18.0–20.5 | close-up on the Warlord's mask | a cherry petal lands on the tip of his nose; his glowing eyes cross to look at it | **Warlord:** "Get it off." · **Ronin:** "Hold still." |
| 20.5–22.5 | slow motion, then snap | the Ronin draws in one flash — the blade passes a hair from the mask; the petal falls in four pieces | SFX swing + ring · impact frame |
| 22.5–26.0 | top-down on the ground | four petal pieces on the dirt; both look down | **Ronin:** "Who is cleaning that?" · (beat) · **Warlord:** "…The challenger." |
| 26.0–30.0 | wide, both glaring | **Ronin:** "You challenged me." — freeze | TEXT "Round two?" · small @DummySticky · hard cut to frame 1 (loop) |

**Voices:** Ronin — calm, low, clipped. Warlord — deep, theatrical, offended (clone reference with gravel; +FX).
**New assets needed:** `bow` pose (deep and "nod" variants), petal-on-nose + four-piece split FX, helmet-collision contact.
**Words:** ~70. **Deliberate beats:** 9.0 s and the beat before "The challenger."

## Table read (Gemini 3.1 Pro, 2026-09-24) and what changed
- Hook works (eye snap + draw sound). Funniest line: "I challenged you… to be challenged." Score 6/10 — "too dry to demand a share".
- Weakest beat: the silent falling petal (19.5–21 s) would lose viewers → replaced by the petal landing on the
  Warlord's nose while they are still bowed ("Get it off." / "Hold still."), which also motivates the draw.
- Added the callback "You challenged me." as the last line so the ending loops the opening argument.
