"""Feature engineering tests."""

import pandas as pd

from app.ml.features import blood_group_to_code, prepare_inference_frame


def test_blood_group_mapping_handles_labels_and_codes():
    """Blood group inputs should normalize to the dataset encoding."""

    assert blood_group_to_code("O+") == 15
    assert blood_group_to_code("17") == 17


def test_prepare_inference_frame_creates_engineered_columns():
    """Inference preprocessing should produce the full model feature set."""

    payload = {
        "age": 29,
        "weight": 63,
        "height": 160,
        "bmi": 24.6,
        "blood_group": "A+",
        "cycle_regularity": 0,
        "cycle_length": 40,
        "marriage_years": 4,
        "pregnant": 0,
        "abortions": 0,
        "fsh": 6.2,
        "lh": 11.4,
        "hip": 100,
        "waist": 91,
        "tsh": 2.7,
        "amh": 7.8,
        "prl": 19.5,
        "vit_d3": 20.2,
        "prg": 0.5,
        "rbs": 99,
        "weight_gain": 1,
        "hair_growth": 1,
        "skin_darkening": 1,
        "hair_loss": 1,
        "pimples": 1,
        "fast_food": 1,
        "exercise": 0,
        "bp_systolic": 118,
        "bp_diastolic": 79,
        "follicle_l": 11,
        "follicle_r": 14,
        "avg_f_size_l": 17.0,
        "avg_f_size_r": 18.0,
        "afc": 25,
        "endometrium": 8.9,
    }
    reference = {
        "testosterone_proxy_mean": 30.0,
        "testosterone_proxy_std": 4.0,
        "amh_reference": [1.2, 2.1, 4.4, 6.0, 8.0, 9.3],
    }

    frame = prepare_inference_frame(payload, reference)

    assert "lh_fsh_ratio" in frame.columns
    assert "bmi_category" in frame.columns
    assert "cycle_irregularity_score" in frame.columns
    assert "testosterone_z_score" in frame.columns
    assert "amh_percentile" in frame.columns
    assert frame.iloc[0]["lh_fsh_ratio"] > 1


def test_prepare_inference_frame_handles_missing_optional_clinical_values():
    """Inference preprocessing should keep optional clinical fields nullable for imputation."""

    payload = {
        "age": 24,
        "weight": 58,
        "height": 161,
        "bmi": 22.4,
        "blood_group": "O+",
        "cycle_regularity": 0,
        "cycle_length": 41,
        "marriage_years": 0,
        "pregnant": 0,
        "abortions": 0,
        "fsh": None,
        "lh": None,
        "hip": None,
        "waist": None,
        "tsh": None,
        "amh": None,
        "prl": None,
        "vit_d3": None,
        "prg": None,
        "rbs": None,
        "weight_gain": 1,
        "hair_growth": 1,
        "skin_darkening": 0,
        "hair_loss": 0,
        "pimples": 1,
        "fast_food": 1,
        "exercise": 0,
        "bp_systolic": None,
        "bp_diastolic": None,
        "follicle_l": None,
        "follicle_r": None,
        "avg_f_size_l": None,
        "avg_f_size_r": None,
        "afc": None,
        "endometrium": None,
    }
    reference = {
        "testosterone_proxy_mean": 30.0,
        "testosterone_proxy_std": 4.0,
        "amh_reference": [1.2, 2.1, 4.4, 6.0, 8.0, 9.3],
    }

    frame = prepare_inference_frame(payload, reference)

    assert pd.isna(frame.iloc[0]["fsh"])
    assert pd.isna(frame.iloc[0]["amh"])
    assert frame.iloc[0]["amh_percentile"] == 0.5
