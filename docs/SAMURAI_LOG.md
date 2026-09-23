# Samurai duel — senior's log (evidence for the Blender verdict)

Worker: gemini-3.8-flash-high via agy. Senior: Claude Code (runs commands, reviews).

| task | worker time | attempts | result | notes |
|---|---|---|---|---|
| T1 toon | 2 min | 1 | ACCEPT | Correct node chain + inverted-hull outline first try. Test lighting shows only the lit tone (test design, not code). |
| T2 rig | 3 min | 2 | ACCEPT | Bone table exact first try. Fix round: test compared bone order (Blender sorts by hierarchy); pole search too coarse (my spec) → 1° refine, err 0.3 mm. |
