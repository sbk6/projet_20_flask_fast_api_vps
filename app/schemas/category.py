from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re


def generate_slug(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[àáâãäå]", "a", slug)
    slug = re.sub(r"[èéêë]", "e", slug)
    slug = re.sub(r"[ìíîï]", "i", slug)
    slug = re.sub(r"[òóôõö]", "o", slug)
    slug = re.sub(r"[ùúûü]", "u", slug)
    slug = re.sub(r"[ç]", "c", slug)
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    return slug.strip("-")


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Électronique"])
    description: Optional[str] = Field(None, examples=["Produits électroniques et high-tech"])

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Électronique",
                "description": "Smartphones, ordinateurs, tablettes et accessoires high-tech",
            }
        }
    }


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100, examples=["Électronique"])
    description: Optional[str] = Field(None, examples=["Produits électroniques et high-tech"])


class CategoryRead(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Électronique",
                "slug": "electronique",
                "description": "Smartphones, ordinateurs, tablettes et accessoires high-tech",
                "created_at": "2025-01-10T08:00:00Z",
            }
        },
    }
