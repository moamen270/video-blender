# Samurai duel — senior's log (evidence for the Blender verdict)

Worker: gemini-3.8-flash-high via agy. Senior: Claude Code (runs commands, reviews).

| task | worker time | attempts | result | notes |
|---|---|---|---|---|
| T1 toon | 2 min | 1 | ACCEPT | Correct node chain + inverted-hull outline first try. Test lighting shows only the lit tone (test design, not code). |
| T2 rig | 3 min | 2 | ACCEPT | Bone table exact first try. Fix round: test compared bone order (Blender sorts by hierarchy); pole search too coarse (my spec) → 1° refine, err 0.3 mm. |
| T3 poses | 5 min | 3 | ACCEPT | 1st run died (worker tried a web URL; agy headless denies it). Code right otherwise; lean/side signs flipped — caught by the sign test, fixed in 1 round. 17 poses, IK reach 0.000 in all. Pose sheet reads as a real fighter; kneel blade goes into the floor (tune in T9). |
