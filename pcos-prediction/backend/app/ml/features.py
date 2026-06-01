"""Shared feature engineering utilities for training and inference."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


BLOOD_GROUP_MAPPING = {
    "A+": 11,
    "A-": 12,
    "B+": 13,
    "B-": 14,
    "O+": 15,
    "O-": 16,
    "AB+": 17,
    "AB-": 18,
}

DATASET_COLUMN_MAP = {
    " Age (yrs)": "age",
    "Weight (Kg)": "weight",
    "Height(Cm) ": "height",
    "BMI": "bmi",
    "Blood Group": "blood_group_code",
    "Cycle(R/I)": "cycle_code",
    "Cycle length(days)": "cycle_length",
    "Marraige Status (Yrs)": "marriage_years",
    "Pregnant(Y/N)": "pregnant",
    "No. of abortions": "abortions",
    "FSH(mIU/mL)": "fsh",
    "LH(mIU/mL)": "lh",
    "Hip(inch)": "hip_inches",
    "Waist(inch)": "waist_inches",
    "TSH (mIU/L)": "tsh",
    "AMH(ng/mL)": "amh",
    "PRL(ng/mL)": "prl",
    "Vit D3 (ng/mL)": "vit_d3",
    "PRG(ng/mL)": "prg",
    "RBS(mg/dl)": "rbs",
    "Weight gain(Y/N)": "weight_gain",
    "hair growth(Y/N)": "hair_growth",
    "Skin darkening (Y/N)": "skin_darkening",
    "Hair loss(Y/N)": "hair_loss",
    "Pimples(Y/N)": "pimples",
    "Fast food (Y/N)": "fast_food",
    "Reg.Exercise(Y/N)": "exercise",
    "BP _Systolic (mmHg)": "bp_systolic",
    "BP _Diastolic (mmHg)": "bp_diastolic",
    "Follicle No. (L)": "follicle_l",
    "Follicle No. (R)": "follicle_r",
    "Avg. F size (L) (mm)": "avg_f_size_l",
    "Avg. F size (R) (mm)": "avg_f_size_r",
    "Endometrium (mm)": "endometrium",
    "PCOS (Y/N)": "target",
}

RAW_INPUT_COLUMNS = [
    "age",
    "weight",
    "height",
    "bmi",
    "blood_group_code",
    "cycle_regularity",
    "cycle_length",
    "marriage_years",
    "pregnant",
    "abortions",
    "fsh",
    "lh",
    "hip",
    "waist",
    "tsh",
    "amh",
    "prl",
    "vit_d3",
    "prg",
    "rbs",
    "weight_gain",
    "hair_growth",
    "skin_darkening",
    "hair_loss",
    "pimples",
    "fast_food",
    "exercise",
    "bp_systolic",
    "bp_diastolic",
    "follicle_l",
    "follicle_r",
    "avg_f_size_l",
    "avg_f_size_r",
    "afc",
    "endometrium",
]

ENGINEERED_COLUMNS = [
    "lh_fsh_ratio",
    "bmi_category",
    "cycle_irregularity_score",
    "testosterone_z_score",
    "amh_percentile",
]

MODEL_FEATURE_COLUMNS = RAW_INPUT_COLUMNS + ENGINEERED_COLUMNS

DISPLAY_NAME_MAP = {
    "age": "Age",
    "weight": "Weight",
    "height": "Height",
    "bmi": "BMI",
    "blood_group_code": "Blood Group",
    "cycle_regularity": "Cycle Regularity",
    "cycle_length": "Cycle Length",
    "marriage_years": "Marriage Years",
    "pregnant": "Pregnancy History",
    "abortions": "Abortions",
    "fsh": "FSH",
    "lh": "LH",
    "hip": "Hip Circumference",
    "waist": "Waist Circumference",
    "tsh": "TSH",
    "amh": "AMH",
    "prl": "PRL",
    "vit_d3": "Vitamin D3",
    "prg": "Progesterone",
    "rbs": "Random Blood Sugar",
    "weight_gain": "Weight Gain",
    "hair_growth": "Hair Growth",
    "skin_darkening": "Skin Darkening",
    "hair_loss": "Hair Loss",
    "pimples": "Pimples",
    "fast_food": "Fast Food",
    "exercise": "Exercise",
    "bp_systolic": "Systolic BP",
    "bp_diastolic": "Diastolic BP",
    "follicle_l": "Follicles Left",
    "follicle_r": "Follicles Right",
    "avg_f_size_l": "Avg Follicle Size Left",
    "avg_f_size_r": "Avg Follicle Size Right",
    "afc": "AFC",
    "endometrium": "Endometrium",
    "lh_fsh_ratio": "LH/FSH Ratio",
    "bmi_category": "BMI Category",
    "cycle_irregularity_score": "Cycle Irregularity",
    "testosterone_z_score": "Testosterone z-score",
    "amh_percentile": "AMH Percentile",
}


def blood_group_to_code(value: Any) -> int:
    """Convert a blood group string or numeric code into the dataset code."""

    if value is None:
        return 15
    if isinstance(value, (int, float)) and not pd.isna(value):
        return int(value)

    normalized = str(value).strip().upper().replace(" ", "")
    if normalized.isdigit():
        return int(normalized)
    return BLOOD_GROUP_MAPPING.get(normalized, 15)


def bmi_category_from_value(bmi: float) -> int:
    """Map BMI into a simple ordinal category."""

    if pd.isna(bmi):
        return 1
    if bmi < 18.5:
        return 0
    if bmi < 25:
        return 1
    if bmi < 30:
        return 2
    return 3


def cycle_irregularity_score(cycle_regularity: float, cycle_length: float) -> float:
    """Compute a composite cycle irregularity score."""

    score = 0.0 if int(cycle_regularity) == 1 else 3.0
    if cycle_length > 35:
        score += 2.0
    elif cycle_length < 24:
        score += 1.0
    return score


def testosterone_proxy(row: Any) -> float:
    """Estimate androgenic burden when serum testosterone is unavailable."""

    if isinstance(row, dict):
        lookup = row.get
    else:
        lookup = row.get
    return float(
        24
        + (lookup("hair_growth", 0) * 9)
        + (lookup("pimples", 0) * 6)
        + (lookup("hair_loss", 0) * 7)
        + (lookup("skin_darkening", 0) * 4)
        + (lookup("weight_gain", 0) * 3)
    )


def compute_amh_percentile(amh_value: float, amh_reference: list[float]) -> float:
    """Return the percentile rank of AMH against the training reference values."""

    if pd.isna(amh_value):
        return 0.5
    if not amh_reference:
        return 0.5
    reference = np.asarray(amh_reference, dtype=float)
    position = np.searchsorted(np.sort(reference), amh_value, side="right")
    return float(position / len(reference))


def compute_engineered_features(frame: pd.DataFrame, reference_stats: dict[str, Any] | None = None) -> pd.DataFrame:
    """Add engineered model features to the input frame."""

    engineered = frame.copy()
    engineered["lh_fsh_ratio"] = np.where(
        engineered["fsh"].replace(0, np.nan).notna(),
        engineered["lh"] / engineered["fsh"].replace(0, np.nan),
        0.0,
    )
    engineered["lh_fsh_ratio"] = engineered["lh_fsh_ratio"].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    engineered["bmi_category"] = engineered["bmi"].apply(bmi_category_from_value)
    engineered["cycle_irregularity_score"] = engineered.apply(
        lambda row: cycle_irregularity_score(row["cycle_regularity"], row["cycle_length"]),
        axis=1,
    )

    proxy = engineered.apply(testosterone_proxy, axis=1)
    if reference_stats:
        mean_value = float(reference_stats.get("testosterone_proxy_mean", proxy.mean()))
        std_value = float(reference_stats.get("testosterone_proxy_std", proxy.std(ddof=0) or 1.0))
    else:
        mean_value = float(proxy.mean())
        std_value = float(proxy.std(ddof=0) or 1.0)
    std_value = std_value or 1.0
    engineered["testosterone_z_score"] = (proxy - mean_value) / std_value

    if reference_stats:
        amh_reference = reference_stats.get("amh_reference", engineered["amh"].tolist())
    else:
        amh_reference = engineered["amh"].tolist()
    engineered["amh_percentile"] = engineered["amh"].apply(
        lambda value: compute_amh_percentile(float(value) if value is not None else np.nan, amh_reference)
    )

    for column in MODEL_FEATURE_COLUMNS:
        if column not in engineered.columns:
            engineered[column] = 0.0

    return engineered[MODEL_FEATURE_COLUMNS]


def prepare_inference_frame(payload: dict[str, Any], reference_stats: dict[str, Any] | None = None) -> pd.DataFrame:
    """Convert a validated request payload into a model-ready DataFrame."""

    frame = pd.DataFrame(
        [
            {
                "age": payload["age"],
                "weight": payload["weight"],
                "height": payload["height"],
                "bmi": payload["bmi"],
                "blood_group_code": blood_group_to_code(payload["blood_group"]),
                "cycle_regularity": payload["cycle_regularity"],
                "cycle_length": payload["cycle_length"],
                "marriage_years": payload["marriage_years"],
                "pregnant": payload["pregnant"],
                "abortions": payload["abortions"],
                "fsh": payload["fsh"],
                "lh": payload["lh"],
                "hip": payload["hip"],
                "waist": payload["waist"],
                "tsh": payload["tsh"],
                "amh": payload["amh"],
                "prl": payload["prl"],
                "vit_d3": payload["vit_d3"],
                "prg": payload["prg"],
                "rbs": payload["rbs"],
                "weight_gain": payload["weight_gain"],
                "hair_growth": payload["hair_growth"],
                "skin_darkening": payload["skin_darkening"],
                "hair_loss": payload["hair_loss"],
                "pimples": payload["pimples"],
                "fast_food": payload["fast_food"],
                "exercise": payload["exercise"],
                "bp_systolic": payload["bp_systolic"],
                "bp_diastolic": payload["bp_diastolic"],
                "follicle_l": payload["follicle_l"],
                "follicle_r": payload["follicle_r"],
                "avg_f_size_l": payload["avg_f_size_l"],
                "avg_f_size_r": payload["avg_f_size_r"],
                "afc": payload["afc"],
                "endometrium": payload["endometrium"],
            }
        ]
    )
    logger.debug("Prepared inference frame with columns: %s", list(frame.columns))
    return compute_engineered_features(frame, reference_stats)


def load_training_dataset(csv_path: str | Path) -> tuple[pd.DataFrame, pd.Series, dict[str, Any]]:
    """Load and normalize the Kaggle PCOS dataset."""

    dataset_path = Path(csv_path)
    logger.info("Loading training dataset from %s", dataset_path)
    raw = pd.read_csv(dataset_path)
    raw = raw.loc[:, ~raw.columns.str.contains("^Unnamed")]
    raw = raw.rename(columns=DATASET_COLUMN_MAP)

    def numeric(column_name: str) -> pd.Series:
        """Return a numeric series with invalid values coerced to NaN."""

        return pd.to_numeric(raw[column_name], errors="coerce")

    frame = pd.DataFrame()
    frame["age"] = numeric("age")
    frame["weight"] = numeric("weight")
    frame["height"] = numeric("height")
    frame["bmi"] = numeric("bmi")
    frame["blood_group_code"] = raw["blood_group_code"].apply(blood_group_to_code)
    frame["cycle_regularity"] = numeric("cycle_code").apply(lambda value: 1 if value == 2 else 0)
    frame["cycle_length"] = numeric("cycle_length")
    frame["marriage_years"] = numeric("marriage_years")
    frame["pregnant"] = numeric("pregnant")
    frame["abortions"] = numeric("abortions")
    frame["fsh"] = numeric("fsh")
    frame["lh"] = numeric("lh")
    frame["hip"] = numeric("hip_inches") * 2.54
    frame["waist"] = numeric("waist_inches") * 2.54
    frame["tsh"] = numeric("tsh")
    frame["amh"] = numeric("amh")
    frame["prl"] = numeric("prl")
    frame["vit_d3"] = numeric("vit_d3")
    frame["prg"] = numeric("prg")
    frame["rbs"] = numeric("rbs")
    frame["weight_gain"] = numeric("weight_gain")
    frame["hair_growth"] = numeric("hair_growth")
    frame["skin_darkening"] = numeric("skin_darkening")
    frame["hair_loss"] = numeric("hair_loss")
    frame["pimples"] = numeric("pimples")
    frame["fast_food"] = numeric("fast_food")
    frame["exercise"] = numeric("exercise")
    frame["bp_systolic"] = numeric("bp_systolic")
    frame["bp_diastolic"] = numeric("bp_diastolic")
    frame["follicle_l"] = numeric("follicle_l")
    frame["follicle_r"] = numeric("follicle_r")
    frame["avg_f_size_l"] = numeric("avg_f_size_l")
    frame["avg_f_size_r"] = numeric("avg_f_size_r")
    frame["afc"] = numeric("follicle_l").fillna(0) + numeric("follicle_r").fillna(0)
    frame["endometrium"] = numeric("endometrium")

    proxy_values = frame.apply(testosterone_proxy, axis=1)
    reference_stats = {
        "testosterone_proxy_mean": float(proxy_values.mean()),
        "testosterone_proxy_std": float(proxy_values.std(ddof=0) or 1.0),
        "amh_reference": sorted(frame["amh"].dropna().astype(float).tolist()),
    }
    features = compute_engineered_features(frame, reference_stats)
    target = numeric("target").fillna(0).astype(int)
    logger.info("Loaded training dataset with shape %s", features.shape)
    return features, target, reference_stats
