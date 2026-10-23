import json
import sys

import numpy as np

from conftest import HashEmbedder, ROOT

sys.path.insert(0, ROOT)


def test_benchmark_runs_end_to_end(tmp_path, frame, monkeypatch, capsys):
    from eval import evaluate

    emb = HashEmbedder()
    frame.to_parquet(tmp_path / "catalog.parquet", index=False)
    np.save(tmp_path / "embeddings.npy", np.stack([emb.vec(d) for d in frame["doc"]]).astype(np.float16))
    (tmp_path / "meta.json").write_text(json.dumps({"model": "hash", "built_at": "2026-10-23"}))
    monkeypatch.setattr(evaluate, "FastEmbedder", lambda name: emb)
    monkeypatch.setattr(sys, "argv", ["evaluate.py", "--data", str(tmp_path), "--out", str(tmp_path / "r.md")])
    assert evaluate.main() == 0
    report = (tmp_path / "r.md").read_text()
    assert "| **hybrid** |" in report and "Can raw similarity label a match?" in report
