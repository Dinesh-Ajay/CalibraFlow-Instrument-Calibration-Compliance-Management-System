import json
import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Dict

from app.dependencies import require_roles
from app.models.user import User

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])


def _get_data_dir() -> str:
    # Resolve project root data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.abspath(os.path.join(current_dir, "..", "..", "..", "data")),
        os.path.abspath(os.path.join(current_dir, "..", "..", "data")),
        os.path.abspath("data"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]


@router.get("/report")
def get_data_quality_report(
    current_user: User = Depends(require_roles(["Administrator", "Quality Engineer", "admin", "quality_eng"])),
) -> Dict[str, Any]:
    """
    Returns data quality validation report and ground-truth comparison metrics.
    Restricted strictly to Administrator and Quality Engineer.
    All other roles receive HTTP 403 Forbidden.
    """
    data_dir = _get_data_dir()
    validation_file = os.path.join(data_dir, "validation_report.json")
    generation_file = os.path.join(data_dir, "generation_summary.json")

    validation_report: Dict[str, Any] = {}
    generation_summary: Dict[str, Any] = {}

    if os.path.exists(validation_file):
        try:
            with open(validation_file, "r", encoding="utf-8") as f:
                validation_report = json.load(f)
        except Exception:
            validation_report = {}

    if os.path.exists(generation_file):
        try:
            with open(generation_file, "r", encoding="utf-8") as f:
                generation_summary = json.load(f)
        except Exception:
            generation_summary = {}

    # If report is missing or empty, attempt on-demand validation
    if not validation_report:
        try:
            from scripts.validate_data import validate_dataset
            validation_report = validate_dataset(data_dir)
        except Exception:
            pass

    return {
        "seed": 20261022,
        "validation_report": validation_report,
        "generation_summary": generation_summary,
    }
