# neurosync

A command-line tool that polls EEG data from an AWEAR API, classifies the current mood from frequency-band ratios, and switches a Spotify account between a focus playlist and a calming playlist in real time.

The package metadata describes the project as “AWEAR EEG-driven Spotify playback: focus vs calming playlists.” On each poll it fetches recent EEG, extracts bands with MNE, maps them to a mood through a hysteresis controller (to avoid rapid playlist flipping), and tells Spotify to play the matching playlist.

## Features

- Polls the AWEAR API on a configurable interval
- Extracts EEG frequency bands with MNE and classifies mood (focus vs calming/stress heuristics)
- Hysteresis / smoothing so the playlist does not change on every tick
- Controls Spotify playback with Spotipy (browser OAuth on first run)
- Configuration through environment variables

## Tech stack

- Python 3.10+
- requests, pandas, numpy, MNE, python-dotenv, pytz, spotipy

## Getting started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
# Fill in the required variables in .env (names below). Do not commit .env.
neurosync
```

On first run, Spotify may open a browser window for authorization. The token cache path is configurable.

### Environment variables

Required (the app exits if any of these are missing or empty):

- `AWEAR_BASE_URL`
- `AWEAR_API_KEY`
- `AWEAR_MEMBER_EMAIL`
- `SPOTIFY_PLAYLIST_FOCUS`
- `SPOTIFY_PLAYLIST_CALM`

Also required for Spotify OAuth (used when creating the Spotify client):

- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_REDIRECT_URI`
- `SPOTIFY_TOKEN_CACHE`

Optional:

- `SPOTIFY_DEVICE_NAME` — substring match for a Spotify device name
- `AWEAR_FETCH_MINUTES`
- `AWEAR_SAMPLING_HZ`
- `POLL_SECONDS`
- `STRESS_BETA_ALPHA_RATIO`
- `FOCUS_BETA_ALPHA_RATIO`
- `STATE_MIN_EPOCHS`
- `STATE_SMOOTH_WINDOW`
- `STATE_CONFIRM_TICKS`

## Project structure

```
src/neurosync/
  main.py             # poll loop and playlist switching
  awear.py            # AWEAR EEG fetch
  bands.py            # MNE band extraction
  state.py            # mood classification and hysteresis
  spotify_player.py   # Spotipy playback helpers
```
