"""EEG frequency band powers from AWEAR CSV epochs (MindfulMakers-AWEAR style)."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

import mne

def _integrate_psd(y: np.ndarray, x: np.ndarray) -> float:
    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(y, x))
    return float(np.trapz(y, x))


FREQ_BANDS = {
    "Delta": (1, 4),
    "Theta": (4, 8),
    "Alpha": (8, 13),
    "Beta": (13, 30),
    "Gamma": (30, 50),
}


def extract_bands_mne(df: Optional[pd.DataFrame], sampling_rate: int = 256) -> Optional[pd.DataFrame]:
    """
    Absolute band power per 1 s epoch using Welch PSD (same idea as MindfulMakers-AWEAR).

    CSV columns: timestamp, device, then 256 samples per row.
    """
    if df is None or df.empty:
        return None

    timestamps = df.iloc[:, 0].values
    devices = df.iloc[:, 1].values
    eeg_data = df.iloc[:, 2:].values.astype(float)
    n_epochs = eeg_data.shape[0]

    eeg_epochs_volts = eeg_data.reshape(n_epochs, 1, eeg_data.shape[1]) * 1e-6
    info = mne.create_info(ch_names=["AWEAR_EEG"], sfreq=sampling_rate, ch_types=["eeg"])
    epochs = mne.EpochsArray(eeg_epochs_volts, info, verbose=False)

    spectrum = epochs.compute_psd(
        method="welch", fmin=1, fmax=50, n_fft=sampling_rate, verbose=False
    )
    psds, freqs = spectrum.get_data(return_freqs=True)

    results = []
    for i in range(n_epochs):
        epoch_psd = psds[i, 0, :]
        row = {"Timestamp": timestamps[i], "Device": devices[i]}
        for band_name, (fmin, fmax) in FREQ_BANDS.items():
            freq_mask = np.logical_and(freqs >= fmin, freqs <= fmax)
            row[band_name] = _integrate_psd(epoch_psd[freq_mask], freqs[freq_mask])
        results.append(row)
    return pd.DataFrame(results)
