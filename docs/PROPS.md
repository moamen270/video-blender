# Props with actions: the rules (owner, 2026-09-26)

"Characters interact with props. Some props come with actions, so there must be rules for using them."
A prop's **state never changes by itself**: every change is an **action** = a character's motion + a contact + the
state change + its sound, on the same frames. Every prop lists its actions and rules in `library/catalog.json`
(`actions`, `rules`) and in its kit class; `kit/checks.py prop_rules()` checks them on every build (animatic onwards)
and writes the violations to the build's `checks.json`. A violation is a bug, not a style note.

## General
1. **Held props are held**: the grip sits in the fist (bone-parented at the grip point), never floating, never through
   the hand. Two-handed props: both fists on the grip.
2. **State changes need their action** (below). No cut, fade or pop may change a prop's state without it.
3. **Sound on the contact frame** (ignite, click, clash), not before.
4. **Consequences show**: a pulled lamp swings, a clash throws sparks, a light that comes on lights the scene.

## Lightsaber (`kit.starwars.Lightsaber`, prop/lightsaber)
| action | who / motion | state | sound |
|---|---|---|---|
| **ignite** | the holder, hilt in the fist: a thumb press (wrist tick, 2 frames) | blade grows from the emitter over 5 frames | ignite (on the first grow frame), then the hum loop |
| **retract** | the holder: a thumb press | blade shrinks into the emitter over 4 frames | retract; the hum stops |
| **clash / bind** | two lit blades meet | contact point on both blades | clash + sparks at the contact point |

Rules:
- **Nobody touches a lit blade.** A lit blade must keep ≥ 4 cm from every character's body, including its holder
  (the check measures blade core to mesh on every frame). A blade touching a person would be a "very bad scene".
- Blades may touch other blades (clash/bind) and nothing else; never through walls or the floor.
- The blade points away from the holder's body; the emitter end is never toward the holder's face.
- An unlit hilt can be held or clipped to the belt. It is never thrown or dropped in this series unless the script says so.

## Pull-cord lamp (`kit.starwars.PullLamp`, prop/pull-cord-lamp)
| action | who / motion | state | sound |
|---|---|---|---|
| **pull** (toggle) | a hand reaches the bead (≥ 6 frames), pulls it down ~8 cm (3 frames), releases | on ↔ off at the lowest point of the pull | click at the lowest point |

Rules:
- **The lamp switches on or off only by pulling the cord.** The fist must be on the bead (≤ 4 cm) on the switch frame.
- After a pull the lamp swings (damped, ~2.5 s); the light swings with it.
- When on, the bulb is the scene's key light (the corridor's own lights are off in that mood).
