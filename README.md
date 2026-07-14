# 🪶 the-feather-test

A Turing test — but everyone is a bird.

One player is the **ornithologist** (judge). Two respondents answer their questions: one is a human pretending to be a bird, the other is an AI locked into a species via a system prompt. The judge decides which is which.

Built with Flask, Socket.IO, and the Groq API.

## how it works

- Ornithologist creates a game room and shares the code
- A species is assigned at random for the room — both the human and the AI
  play that same species, from the same character brief
- Human bird joins via `/join` and sees their assigned species + full brief
  before answering (parity with what the AI's system prompt gets — otherwise
  the human is improvising "generic bird" against an AI playing one specific,
  richly-detailed species, which isn't a fair test)
- AI bird responds automatically via Groq (llama-3.1-8b-instant)
- After 5 rounds, ornithologist guesses — reveal screen shows who fooled whom
- Leaderboard tracks which species fools people most often

## species roster

Crow · Raven · Robin · Pigeon · Parrot

## stack

- Python / Flask
- Flask-SocketIO (real-time chat)
- Groq API (llama-3.1-8b-instant)
- SQLite (session + score persistence)
- AWS EC2 (hosting) · Cloudflare (DNS + proxy)

## run locally

```bash
git clone https://github.com/kwasikontor45/the-feather-test
cd the-feather-test
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# add your GROQ_API_KEY to .env  (free at console.groq.com)
python3 run.py
```

Then open `http://localhost:5000`.

## deploy

Runs on a VPS behind nginx + gunicorn + systemd. Wire a unix socket proxy and point your domain at it.

```bash
git clone https://github.com/kwasikontor45/the-feather-test
cd the-feather-test
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set GROQ_API_KEY + SECRET_KEY
gunicorn --worker-class eventlet -w 1 --bind unix:feather-test.sock run:app
```
