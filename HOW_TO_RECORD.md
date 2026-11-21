# Record the male voice (one time, about 10 minutes)

This records the app's words, phrases and sound examples (about 3,100 characters)
with a male European Portuguese voice from Google Cloud Text-to-Speech, then pushes
the clips here. That is far below Google's free monthly allowance.

## 1. Install the Google Cloud CLI
- Mac: `brew install --cask google-cloud-sdk`
- Windows or Mac without Homebrew: https://cloud.google.com/sdk/docs/install

## 2. Sign in
```
gcloud auth login
```

## 3. Make a project and turn on billing
```
gcloud projects create portugues-voice-$RANDOM
gcloud projects list            # copy the new project's ID
gcloud config set project PROJECT_ID
```
Then link a billing account to it (required by Google even for free-tier use):
https://console.cloud.google.com/billing/linkedaccount

## 4. Turn on Text-to-Speech
```
gcloud services enable texttospeech.googleapis.com
```

## 5. Record and upload
```
git clone https://github.com/nosajholt/portuguese
cd portuguese
python3 make_voice.py
```
It picks the lightest-sounding male Portugal voice, records every clip and pushes them.
Then tell Claude "recorded".

Optional: `python3 make_voice.py --list` shows the male voices on offer, and
`python3 make_voice.py --voice NAME` records with a different one.
