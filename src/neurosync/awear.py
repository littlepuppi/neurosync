"""Fetch AWEAR member EEG CSV and prepare it for band extraction."""

from __future__ import annotations

import io
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import pytz
import requests


def fetch_recent_eeg(
    base_url: str,
    api_key: str,
    member_email: str,
    minutes_ago: float = 1.0,
    timeout: float = 30.0,
) -> Optional[pd.DataFrame]:
    """Fetch the last ``minutes_ago`` minutes of EEG CSV from the AWEAR API."""
    base = base_url.rstrip("/")
    now = datetime.now().astimezone(pytz.utc).replace(microsecond=0)
    start_time = now - timedelta(minutes=minutes_ago)
    params = {
        "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tz": "UTC",
        "format": "csv",
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"{base}/members/{member_email}/data"
    resp = requests.get(url, headers=headers, params=params, timeout=timeout)
    if resp.status_code != 200:
        return None
    df = pd.read_csv(io.StringIO(resp.text))
    return df.dropna(how="all")
