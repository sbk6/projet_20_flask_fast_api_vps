from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, examples=[5])
    title: Optional[str] = Field(None, max_length=200, examples=["Excellent produit !"])
    comment: Optional[str] = Field(None, examples=["Très satisfait de mon achat, livraison rapide et produit conforme."])

    model_config = {
        "json_schema_extra": {
            "example": {
                "rating": 5,
                "title": "Excellent produit !",
                "comment": "Très satisfait de mon achat, livraison rapide et produit conforme.",
            }
        }
    }


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, examples=[4])
    title: Optional[str] = Field(None, max_length=200, examples=["Très bon produit"])
    comment: Optional[str] = Field(None, examples=["Bon produit mais légèrement cher."])


class ReviewRead(BaseModel):
    id: int
    user_id: int
    product_id: int
    rating: int
    title: Optional[str] = None
    comment: Optional[str] = None
    username: Optional[str] = None
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "user_id": 42,
                "product_id": 1,
                "rating": 5,
                "title": "Excellent produit !",
                "comment": "Très satisfait de mon achat.",
                "username": "jean_dupont",
                "created_at": "2025-01-22T09:15:00Z",
            }
        },
    }
