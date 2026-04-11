"""Poll AWEAR EEG, classify mood, switch Spotify playlists in real time."""

from __future__ import annotations

import logging
import os
import sys
import time

from dotenv import load_dotenv

from neurosync.awear import fetch_recent_eeg
from neurosync.bands import extract_bands_mne
from neurosync.spotify_player import play_playlist, spotify_from_env
from neurosync.state import HysteresisController, Mood, StateConfig, bands_to_raw_mood

log = logging.getLogger("neurosync")


def _env_float(key: str, default: float) -> float:
    v = os.environ.get(key)
    if v is None or v == "":
        return default
    return float(v)


def _env_int(key: str, default: int) -> int:
    v = os.environ.get(key)
    if v is None or v == "":
        return default
    return int(v)


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    load_dotenv()

    base = os.environ.get("AWEAR_BASE_URL", "").strip()
    key = os.environ.get("AWEAR_API_KEY", "").strip()
    email = os.environ.get("AWEAR_MEMBER_EMAIL", "").strip()
    pl_focus = os.environ.get("SPOTIFY_PLAYLIST_FOCUS", "").strip()
    pl_calm = os.environ.get("SPOTIFY_PLAYLIST_CALM", "").strip()

    if not all([base, key, email, pl_focus, pl_calm]):
        log.error(
            "Set AWEAR_BASE_URL, AWEAR_API_KEY, AWEAR_MEMBER_EMAIL, "
            "SPOTIFY_PLAYLIST_FOCUS, SPOTIFY_PLAYLIST_CALM (and Spotify OAuth env vars)."
        )
        sys.exit(1)

    poll = _env_float("POLL_SECONDS", 6.0)
    fetch_minutes = _env_float("AWEAR_FETCH_MINUTES", 1.5)
    sampling = _env_int("AWEAR_SAMPLING_HZ", 256)

    cfg = StateConfig(
        stress_beta_alpha_ratio=_env_float("STRESS_BETA_ALPHA_RATIO", 2.2),
        focus_beta_alpha_ratio=_env_float("FOCUS_BETA_ALPHA_RATIO", 1.35),
        min_epochs=_env_int("STATE_MIN_EPOCHS", 2),
        smooth_window=_env_int("STATE_SMOOTH_WINDOW", 5),
        confirm_ticks=_env_int("STATE_CONFIRM_TICKS", 3),
    )

    log.info("Starting Spotify auth (browser may open once)...")
    sp, device_id = spotify_from_env()
    if device_id:
        log.info("Using Spotify device id from SPOTIFY_DEVICE_NAME match.")
    else:
        log.info("Using Spotify active device (open Spotify on a device and press play once).")

    ctrl = HysteresisController(cfg)
    last_played: Mood | None = None

    log.info("Polling AWEAR every %.1fs — Ctrl+C to stop.", poll)

    while True:
        try:
            raw_df = fetch_recent_eeg(base, key, email, minutes_ago=fetch_minutes)
            bands = extract_bands_mne(raw_df, sampling_rate=sampling)
            raw_mood = bands_to_raw_mood(bands, cfg)
            changed = ctrl.update(raw_mood)

            if bands is not None and len(bands):
                last = bands.iloc[-1]
                ratio = float(last["Beta"]) / (float(last["Alpha"]) + 1e-12)
                log.info(
                    "β/α≈%.2f → raw=%s active=%s",
                    ratio,
                    raw_mood.value if raw_mood else "—",
                    ctrl.current.value if ctrl.current else "—",
                )
            elif raw_df is None:
                log.warning("AWEAR request failed or returned no data.")
            else:
                log.warning("No EEG epochs in window (wear device / check email).")

            if changed and ctrl.current is not None:
                uri = pl_focus if ctrl.current == Mood.FOCUS else pl_calm
                label = ctrl.current.value
                if ctrl.current != last_played:
                    try:
                        play_playlist(sp, uri, device_id=device_id)
                        log.info("Switched to %s playlist.", label)
                        last_played = ctrl.current
                    except Exception as e:
                        log.warning("Spotify playback failed: %s", e)
        except KeyboardInterrupt:
            log.info("Stopped.")
            break
        except Exception as e:
            log.exception("Loop error: %s", e)

        time.sleep(poll)


if __name__ == "__main__":
    run()
