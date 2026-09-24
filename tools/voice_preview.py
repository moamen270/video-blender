"""Script-order voice preview: shared shouts mixed with their ENDS aligned (both 'KEN!' land together),
Ryu panned left, Ken right, trailing silence trimmed. -> review/<p>/voices_preview.mp3 + an index json.

python tools/voice_preview.py --project sf01 --order "r_h1+k_h1,r_mine,k_mine,r_h2+k_h2,r_h3+k_h3,k_mine2,r_mine2" --scratch F:/PoCs/agy_scratch/sffinal
"""
import argparse, json, os, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("--project", required=True); ap.add_argument("--order", required=True); ap.add_argument("--scratch", required=True)
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
m = json.load(open(os.path.join(ROOT, "projects", a.project, "voice", "manifest.json")))["lines"]
out = a.scratch; os.makedirs(out, exist_ok=True)
TRIM = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"

def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout)

parts, idx, t = [], [], 0.0
for grp in a.order.split(","):
    ids = grp.split("+"); trimmed = []
    for i in ids:
        f = f"{out}/{i}_t.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", m[i]["wav"], "-af", f"aresample=24000,{TRIM}", "-ac", "1", f], check=True)
        trimmed.append(f)
    if len(ids) == 2:
        d0, d1 = dur(trimmed[0]), dur(trimmed[1]); lag0, lag1 = max(0, d1 - d0), max(0, d0 - d1)
        f = f"{out}/{ids[0]}_{ids[1]}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", trimmed[0], "-i", trimmed[1], "-filter_complex",
                        f"[0:a]adelay={int(lag0*1000)},pan=stereo|c0=0.9*c0|c1=0.45*c0[a];[1:a]adelay={int(lag1*1000)},pan=stereo|c0=0.45*c0|c1=0.9*c0[b];[a][b]amix=inputs=2:normalize=0[o]",
                        "-map", "[o]", f], check=True)
    else:
        f = f"{out}/{ids[0]}_s.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", trimmed[0], "-af", "pan=stereo|c0=c0|c1=c0", f], check=True)
    d = dur(f); idx.append({"ids": ids, "text": " / ".join(m[i]["text"] for i in ids), "start": round(t, 2), "end": round(t + d, 2)})
    parts.append(f); t += d + 0.9
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=stereo", "-t", "0.9", f"{out}/gap.wav"], check=True)
with open(f"{out}/list.txt", "w") as fh:
    for p in parts: fh.write(f"file '{p}'\nfile '{out}/gap.wav'\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{out}/list.txt", "-af", "loudnorm=I=-16:TP=-1", "-ar", "48000", f"{out}/preview.wav"], check=True)
json.dump(idx, open(f"{out}/index.json", "w"), indent=0)
os.makedirs(os.path.join(ROOT, "review", a.project), exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{out}/preview.wav", "-b:a", "192k", os.path.join(ROOT, "review", a.project, "voices_preview.mp3")], check=True)
print(round(t, 1), "s;", [(x["text"], x["start"], x["end"]) for x in idx])
