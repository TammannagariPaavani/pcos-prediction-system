"""Organization service helpers."""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.core.dependencies import APIError
from app.models import Organization


def slugify_organization_name(name: str) -> str:
    """Convert an organization name into a stable slug."""

    normalized = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return normalized or "organization"


def get_or_create_organization(db: Session, organization_name: str) -> Organization:
    """Find an organization by name or create it."""

    clean_name = organization_name.strip()
    existing = db.query(Organization).filter(Organization.name == clean_name).one_or_none()
    if existing is not None:
        return existing

    base_slug = slugify_organization_name(clean_name)
    slug = base_slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).one_or_none() is not None:
        counter += 1
        slug = f"{base_slug}-{counter}"

    organization = Organization(name=clean_name, slug=slug)
    db.add(organization)
    db.flush()
    return organization


def require_organization_name(role: str, organization_name: str | None) -> None:
    """Ensure the required roles always carry an organization name."""

    if role in {"doctor", "admin"} and not organization_name:
        raise APIError(
            "Organization name is required for doctor and admin accounts.",
            "ORGANIZATION_REQUIRED",
            422,
        )
