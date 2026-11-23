# Dataset/download_physionet.py
"""
Utility script to download official European Data Format (.edf) whole-night polysomnographic
recordings from the PhysioNet Sleep-EDF Database Expanded (Sleep-EDFx).
Repository: https://physionet.org/files/sleep-edfx/1.0.0/
"""

import sys
import urllib.request
from pathlib import Path

BASE_URL = "https://physionet.org/files/sleep-edfx/1.0.0/sleep-cassette/"
TARGET_DIR = Path(__file__).resolve().parent / "records"

RECORDS = [
    {
        "psg": "SC4001E0-PSG.edf",
        "hypnogram": "SC4001EC-Hypnogram.edf",
        "desc": "Subject 01 (Male, 21yr) - Night 1 Sleep Cassette"
    },
    {
        "psg": "SC4011E0-PSG.edf",
        "hypnogram": "SC4011EH-Hypnogram.edf",
        "desc": "Subject 02 (Female, 28yr) - Night 1 Sleep Cassette"
    }
]

def download_record(record_filename: str):
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    out_file = TARGET_DIR / record_filename
    if out_file.exists():
        print(f"[ALREADY EXISTS] {record_filename} ({out_file.stat().st_size} bytes)")
        return

    url = BASE_URL + record_filename
    print(f"[DOWNLOADING] {url} -> {out_file}...")
    try:
        urllib.request.urlretrieve(url, out_file)
        print(f"[SUCCESS] Downloaded {record_filename} ({out_file.stat().st_size} bytes)")
    except Exception as e:
        print(f"[FAILED] Could not download {record_filename}: {e}")

if __name__ == "__main__":
    print("=" * 65)
    print(" PhysioNet Sleep-EDFx Clinical Polysomnography Downloader")
    print("=" * 65)
    for rec in RECORDS:
        print(f"\n--- {rec['desc']} ---")
        download_record(rec["psg"])
        download_record(rec["hypnogram"])
    print("\nDataset download process completed.")
