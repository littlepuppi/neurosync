"""Map recent band powers to focus vs stress with smoothing and hysteresis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd


class Mood(str, Enum):
    FOCUS = "focus"
    STRESS = "stress"


@dataclass
class StateConfig:
    """Tunable thresholds; literature often links high beta / low alpha to arousal."""

    stress_beta_alpha_ratio: float = 2.2
    focus_beta_alpha_ratio: float = 1.35
    min_epochs: int = 2
    smooth_window: int = 5
    confirm_ticks: int = 3


def _beta_alpha_ratio(row: pd.Series) -> float:
    a = float(row.get("Alpha", 0.0)) + 1e-12
    b = float(row.get("Beta", 0.0))
    return b / a


def bands_to_raw_mood(bands_df: Optional[pd.DataFrame], cfg: StateConfig) -> Optional[Mood]:
    if bands_df is None or len(bands_df) < cfg.min_epochs:
        return None
    tail = bands_df.tail(cfg.smooth_window)
    ratios = tail.apply(_beta_alpha_ratio, axis=1)
    r = float(np.median(ratios.values))
    if r >= cfg.stress_beta_alpha_ratio:
        return Mood.STRESS
    if r <= cfg.focus_beta_alpha_ratio:
        return Mood.FOCUS
    mid = 0.5 * (cfg.stress_beta_alpha_ratio + cfg.focus_beta_alpha_ratio)
    return Mood.STRESS if r >= mid else Mood.FOCUS


class HysteresisController:
    """Require the same raw mood several ticks in a row before committing."""

    def __init__(self, cfg: StateConfig):
        self.cfg = cfg
        self._pending: Optional[Mood] = None
        self._count = 0
        self.current: Optional[Mood] = None

    def update(self, raw: Optional[Mood]) -> Optional[Mood]:
        if raw is None:
            return None
        if raw == self._pending:
            self._count += 1
        else:
            self._pending = raw
            self._count = 1
        if self._count >= self.cfg.confirm_ticks and raw != self.current:
            self.current = raw
            return self.current
        return None
