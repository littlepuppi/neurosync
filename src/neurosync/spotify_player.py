"""Spotify playback: OAuth + start playlist on active device."""

from __future__ import annotations

import os
from typing import Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth


def build_spotify_client(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    cache_path: str = ".spotify_token_cache",
) -> spotipy.Spotify:
    scope = " ".join(
        [
            "user-modify-playback-state",
            "user-read-playback-state",
        ]
    )
    auth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        cache_path=cache_path,
        open_browser=True,
    )
    return spotipy.Spotify(auth_manager=auth)


def play_playlist(sp: spotipy.Spotify, playlist_uri: str, device_id: Optional[str] = None) -> None:
    kwargs = {"context_uri": playlist_uri}
    if device_id:
        kwargs["device_id"] = device_id
    sp.start_playback(**kwargs)


def resolve_device_id(sp: spotipy.Spotify, preferred_name: Optional[str]) -> Optional[str]:
    if not preferred_name:
        return None
    preferred_lower = preferred_name.strip().lower()
    devices = sp.devices()
    for d in devices.get("devices") or []:
        name = (d.get("name") or "").lower()
        if preferred_lower in name or name in preferred_lower:
            return d.get("id")
    return None


def spotify_from_env() -> tuple[spotipy.Spotify, Optional[str]]:
    cid = os.environ["SPOTIFY_CLIENT_ID"]
    secret = os.environ["SPOTIFY_CLIENT_SECRET"]
    redirect = os.environ["SPOTIFY_REDIRECT_URI"]
    cache = os.environ.get("SPOTIFY_TOKEN_CACHE", ".spotify_token_cache")
    sp = build_spotify_client(cid, secret, redirect, cache_path=cache)
    dev = os.environ.get("SPOTIFY_DEVICE_NAME")
    device_id = resolve_device_id(sp, dev) if dev else None
    return sp, device_id
