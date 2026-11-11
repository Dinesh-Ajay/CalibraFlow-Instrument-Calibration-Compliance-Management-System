import os
import sys
import shutil
import hashlib
import json
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.generate_data import run_generator
from scripts.validate_data import validate_dataset


def file_hash(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def compare_runs(seed: int = 20261022, scale: str = "starter"):
    print(f"=== Reproducibility Comparison Test ===")
    print(f"Seed: {seed} | Scale: {scale}\n")

    dir_run1 = os.path.abspath("data_repro_run1")
    dir_run2 = os.path.abspath("data_repro_run2")

    for d in [dir_run1, dir_run2]:
        if os.path.exists(d):
            shutil.rmtree(d)

    print("Executing Run 1...")
    summary1 = run_generator(seed=seed, scale=scale, output_dir=dir_run1)
    val1 = validate_dataset(dir_run1)

    print("\nExecuting Run 2...")
    summary2 = run_generator(seed=seed, scale=scale, output_dir=dir_run2)
    val2 = validate_dataset(dir_run2)

    print("\n=== Comparing Run 1 vs Run 2 ===")
    csv_dir1 = os.path.join(dir_run1, "synthetic")
    csv_dir2 = os.path.join(dir_run2, "synthetic")

    files = sorted(os.listdir(csv_dir1))
    all_matched = True

    comparison_results = []
    for f in files:
        p1 = os.path.join(csv_dir1, f)
        p2 = os.path.join(csv_dir2, f)
        h1 = file_hash(p1)
        h2 = file_hash(p2)
        match = (h1 == h2)
        if not match:
            all_matched = False
        comparison_results.append({
            "file": f,
            "hash_run1": h1[:12],
            "hash_run2": h2[:12],
            "identical": match
        })
        print(f"  {f:30s}: {'IDENTICAL [OK]' if match else 'MISMATCH [FAIL]'}")

    # Check ground truth
    gt1_hash = file_hash(os.path.join(dir_run1, "ground_truth.csv"))
    gt2_hash = file_hash(os.path.join(dir_run2, "ground_truth.csv"))
    gt_match = (gt1_hash == gt2_hash)
    if not gt_match:
        all_matched = False
    print(f"  {'ground_truth.csv':30s}: {'IDENTICAL [OK]' if gt_match else 'MISMATCH [FAIL]'}")

    # Clean up test directories
    for d in [dir_run1, dir_run2]:
        if os.path.exists(d):
            shutil.rmtree(d)

    print("\n=== Reproducibility Verdict ===")
    if all_matched and summary1["counts"] == summary2["counts"]:
        print("[SUCCESS] 100% Deterministic Reproducibility Verified! All checksums, counts, and anomalies match exactly.")
    else:
        print("[FAIL] Differences detected between identical seed executions.")

    return all_matched


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CalibraFlow Reproducibility Verifier")
    parser.add_argument("--seed", type=int, default=20261022)
    parser.add_argument("--scale", type=str, default="starter")
    args = parser.parse_args()

    compare_runs(args.seed, args.scale)
