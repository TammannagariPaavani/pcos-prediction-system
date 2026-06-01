"""PDF report generation and storage helpers."""

from __future__ import annotations

import logging
from io import BytesIO
from urllib.parse import urljoin

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import settings
from app.models import Patient, Prediction

logger = logging.getLogger(__name__)


def _build_pdf(prediction: Prediction, patient: Patient) -> bytes:
    """Render the PDF report for a prediction."""

    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm)
    styles = getSampleStyleSheet()

    story = [
        Paragraph("PCOS Prediction Report", styles["Title"]),
        Spacer(1, 0.5 * cm),
        Paragraph(f"Patient ID: {patient.id}", styles["BodyText"]),
        Paragraph(f"Prediction ID: {prediction.id}", styles["BodyText"]),
        Paragraph(f"Risk score: {prediction.risk_score:.2%}", styles["BodyText"]),
        Paragraph(f"Risk label: {prediction.risk_label}", styles["BodyText"]),
        Paragraph(f"Model version: {prediction.model_version}", styles["BodyText"]),
        Spacer(1, 0.5 * cm),
        Paragraph("Top contributing factors", styles["Heading2"]),
    ]

    table_rows = [["Feature", "Impact", "Observed Value"]]
    for item in prediction.top_features[:5]:
        table_rows.append(
            [
                item["feature"],
                f"{item['impact']:.4f}",
                str(item["value"]),
            ]
        )
    table = Table(table_rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#103E52")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5FBFC")]),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            "This report supports clinical review and should be interpreted alongside full hormonal evaluation "
            "and ultrasound findings.",
            styles["Italic"],
        )
    )

    document.build(story)
    return buffer.getvalue()


def _minio_client():
    """Create an S3-compatible MinIO client."""

    return boto3.client(
        "s3",
        endpoint_url=f"http{'s' if settings.minio_secure else ''}://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def store_report(prediction: Prediction, patient: Patient, base_url: str) -> dict[str, str]:
    """Generate, store, and return the downloadable report location."""

    pdf_bytes = _build_pdf(prediction, patient)
    object_key = f"{prediction.id}.pdf"
    settings.resolved_report_storage_path.mkdir(parents=True, exist_ok=True)

    local_path = settings.resolved_report_storage_path / object_key
    local_path.write_bytes(pdf_bytes)
    logger.info("Stored local report at %s", local_path)

    try:
        client = _minio_client()
        existing_buckets = {bucket["Name"] for bucket in client.list_buckets().get("Buckets", [])}
        if settings.minio_bucket_reports not in existing_buckets:
            client.create_bucket(Bucket=settings.minio_bucket_reports)
        client.put_object(
            Bucket=settings.minio_bucket_reports,
            Key=object_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )
        logger.info(
            "Uploaded report %s to MinIO bucket %s",
            object_key,
            settings.minio_bucket_reports,
        )
    except (BotoCoreError, ClientError, OSError) as exc:
        logger.warning("MinIO upload failed for %s: %s", object_key, exc)

    download_url = urljoin(str(base_url), f"/report-files/{object_key}")
    return {"prediction_id": prediction.id, "download_url": download_url, "object_key": object_key}
