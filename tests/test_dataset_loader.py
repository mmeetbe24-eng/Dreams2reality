# tests/test_dataset_loader.py
import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bci-service"))

from ingestion.dataset_loader import PhysioNetDatasetLoader

def test_dataset_loader_records_and_streaming():
    loader = PhysioNetDatasetLoader()

    # 1. Verify benchmark records exist
    records = loader.list_records()
    assert len(records) >= 3

    rec_ids = [r["record_id"] for r in records]
    assert "SC4001E0" in rec_ids
    assert "ST7011J0" in rec_ids
    assert "SC4012E0" in rec_ids

    # 2. Test loading record SC4001E0
    loaded = loader.load_record("SC4001E0")
    assert loaded is True
    assert loader.active_data is not None
    assert loader.active_data.shape[0] == 2 # 2 channels T7, T8

    # 3. Test streaming samples
    chunk, gt_stage, meta = loader.get_next_samples(count=32)
    assert chunk.shape == (2, 32)
    assert gt_stage in ["Wake", "N1", "N2", "N3", "REM"]
    assert meta["source"] == "PhysioNet Sleep-EDFx Benchmark"
    assert meta["record_id"] == "SC4001E0"
