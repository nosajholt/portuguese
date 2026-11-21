#!/usr/bin/env python3
"""
Records every word, phrase and sound example of the app with a male
European Portuguese (pt-PT) voice from Google Cloud Text-to-Speech,
then commits and pushes the clips so both versions of the app use them.

Needs: Python 3.8+, git, and the gcloud CLI logged in to a project that has
the Text-to-Speech API enabled (see HOW_TO_RECORD.md). Standard library only.

  python3 make_voice.py              # pick the best male pt-PT voice, record, push
  python3 make_voice.py --list       # show the pt-PT voices your project offers
  python3 make_voice.py --voice NAME # use a specific voice (re-records everything)
  python3 make_voice.py --no-push    # record only
"""
import argparse, base64, hashlib, json, os, re, subprocess, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, "audio")
API = "https://texttospeech.googleapis.com/v1"
# Lighter, friendly male voices first ("not too low"); deeper ones last.
PREFERRED = ["Puck", "Achird", "Zubenelgenubi", "Sadachbia", "Orus", "Fenrir", "Umbriel",
             "Iapetus", "Enceladus", "Algenib", "Rasalgethi", "Schedar", "Sadaltager",
             "Alnilam", "Algieba", "Charon"]

def sh(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()

def gcloud(*args):
    exe = "gcloud.cmd" if os.name == "nt" else "gcloud"
    try:
        return sh(exe, *args)
    except FileNotFoundError:
        sys.exit("gcloud isn't installed. See HOW_TO_RECORD.md, step 1.")
    except subprocess.CalledProcessError as e:
        sys.exit("gcloud said: " + (e.stderr or e.stdout).strip() + "\nRun: gcloud auth login")

def api(path, body=None):
    token = gcloud("auth", "print-access-token")
    project = gcloud("config", "get-value", "project")
    if not project:
        sys.exit("No Google Cloud project set. Run: gcloud config set project YOUR_PROJECT_ID")
    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body else None,
        headers={"Authorization": "Bearer " + token, "x-goog-user-project": project,
                 "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")
            if e.code == 429 and attempt < 3:
                time.sleep(5 * (attempt + 1)); continue
            if e.code == 403 and ("SERVICE_DISABLED" in msg or "has not been used" in msg):
                sys.exit("The Text-to-Speech API is off for this project. Run:\n  gcloud services enable texttospeech.googleapis.com")
            if e.code == 403 and "billing" in msg.lower():
                sys.exit("This project needs billing turned on (the free tier covers this). See HOW_TO_RECORD.md, step 3.")
            sys.exit(f"Google returned {e.code}: {msg[:400]}")

def male_voices():
    vs = api("/voices?languageCode=pt-PT").get("voices", [])
    return [v for v in vs if "pt-PT" in v.get("languageCodes", []) and v.get("ssmlGender") == "MALE"]

def rank(v):
    n = v["name"]
    if "Chirp3-HD" in n:
        style = n.rsplit("-", 1)[-1]
        return (0, PREFERRED.index(style) if style in PREFERRED else 50)
    for i, kind in enumerate(["Chirp-HD", "Neural2", "Wavenet", "Standard"], start=1):
        if kind in n:
            return (i, n)
    return (9, n)

def synth(text, voice):
    cfg = {"audioEncoding": "MP3", "sampleRateHertz": 24000}
    if "Chirp" not in voice:            # older voices take a pitch tweak; lift it a little
        cfg["pitch"] = 2.0
    r = api("/text:synthesize", {"input": {"text": text},
            "voice": {"languageCode": "pt-PT", "name": voice}, "audioConfig": cfg})
    return base64.b64decode(r["audioContent"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--voice")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()

    voices = sorted(male_voices(), key=rank)
    if a.list:
        for v in voices: print(v["name"])
        return
    if not voices:
        sys.exit("Google offers no male pt-PT voice to this project.")
    voice = a.voice or voices[0]["name"]
    print("Voice:", voice)

    texts = json.load(open(os.path.join(AUDIO, "texts.json"), encoding="utf-8"))
    idx_path = os.path.join(AUDIO, "index.json")
    old = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else {}
    same_voice = old.get("voice") == voice
    clips = {}
    for i, t in enumerate(texts, 1):
        name = hashlib.sha1((voice + "|" + t).encode()).hexdigest()[:12] + ".mp3"
        path = os.path.join(AUDIO, name)
        if not (same_voice and os.path.exists(path)):
            open(path, "wb").write(synth(t, voice))
        clips[t] = "audio/" + name
        print(f"\r{i}/{len(texts)}  {t[:40]:<40}", end="", flush=True)
    print()
    # remove clips from an older voice
    keep = {os.path.basename(f) for f in clips.values()}
    for f in os.listdir(AUDIO):
        if f.endswith(".mp3") and f not in keep:
            os.remove(os.path.join(AUDIO, f))
    json.dump({"voice": voice, "clips": clips}, open(idx_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    # new cache name so installed offline apps download the new audio
    sw = os.path.join(HERE, "sw.js")
    tag = hashlib.sha1(json.dumps(clips, sort_keys=True).encode()).hexdigest()[:8]
    s = open(sw, encoding="utf-8").read()
    open(sw, "w", encoding="utf-8").write(re.sub(r'const CACHE="[^"]*"', f'const CACHE="portugues-{tag}"', s, 1))
    print(f"Recorded {len(clips)} clips.")

    if a.no_push:
        return
    os.chdir(HERE)
    subprocess.run(["git", "add", "-A", "audio", "sw.js"], check=True)
    subprocess.run(["git", "commit", "-qm", f"Record audio with {voice}"], check=False)
    subprocess.run(["git", "push", "-q"], check=True)
    print("Pushed. Tell Claude 'recorded' and it will add the audio to the Claude page too.")

if __name__ == "__main__":
    main()
