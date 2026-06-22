from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import Optional
from datetime import datetime
from decimal import Decimal
from .category import CategoryRead


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, examples=["iPhone 15 Pro Max"])
    description: Optional[str] = Field(None, examples=["Smartphone Apple haut de gamme avec puce A17 Pro"])
    price: Decimal = Field(..., gt=0, decimal_places=2, examples=[1299.99])
    stock: int = Field(0, ge=0, examples=[50])
    image_url: Optional[str] = Field(None, examples=["https://example.com/images/iphone15.jpg"])
    category_id: Optional[int] = Field(None, examples=[1])

    @field_validator("price")
    @classmethod
    def price_precision(cls, v: Decimal) -> Decimal:
        return round(v, 2)

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "iPhone 15 Pro Max",
                "description": "Smartphone Apple haut de gamme avec puce A17 Pro, 256 Go",
                "price": 1299.99,
                "stock": 50,
                "image_url": "https://example.com/images/iphone15.jpg",
                "category_id": 1,
            }
        }
    }


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255, examples=["iPhone 15 Pro Max"])
    description: Optional[str] = Field(None, examples=["Description mise à jour"])
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2, examples=[1199.99])
    stock: Optional[int] = Field(None, ge=0, examples=[25])
    image_url: Optional[str] = Field(None, examples=["https://example.com/images/iphone15-v2.jpg"])
    category_id: Optional[int] = Field(None, examples=[1])
    is_active: Optional[bool] = Field(None, examples=[True])

    @field_validator("price")
    @classmethod
    def price_precision(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            return round(v, 2)
        return v


class ProductRead(BaseModel):
    id: int
    name: str
    slug: str
    price: Decimal
    stock: int
    image_url: Optional[str]
    is_active: bool
    category_id: Optional[int]
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "iPhone 15 Pro Max",
                "slug": "iphone-15-pro-max",
                "price": "1299.99",
                "stock": 50,
                "image_url": "https://example.com/images/iphone15.jpg",
                "is_active": True,
                "category_id": 1,
                "created_at": "2025-01-15T10:30:00Z",
            }
        },
    }


class ProductReadDetail(ProductRead):
    description: Optional[str] = None
    category: Optional[CategoryRead] = None
    average_rating: Optional[float] = None
    review_count: int = 0

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "iPhone 15 Pro Max",
                "slug": "iphone-15-pro-max",
                "description": "Smartphone Apple haut de gamme avec puce A17 Pro, 256 Go",
                "price": "1299.99",
                "stock": 50,
                "image_url": "https://example.com/images/iphone15.jpg",
                "is_active": True,
                "category_id": 1,
                "category": {
                    "id": 1,
                    "name": "Électronique",
                    "slug": "electronique",
                    "description": "High-tech",
                    "created_at": "2025-01-10T08:00:00Z",
                },
                "average_rating": 4.7,
                "review_count": 128,
                "created_at": "2025-01-15T10:30:00Z",
            }
        },
    }


class ProductFilter(BaseModel):
    category_id: Optional[int] = Field(None, examples=[1])
    search: Optional[str] = Field(None, min_length=2, examples=["iphone"])
    price_min: Optional[Decimal] = Field(None, ge=0, examples=[100.0])
    price_max: Optional[Decimal] = Field(None, gt=0, examples=[2000.0])
    in_stock: Optional[bool] = Field(None, examples=[True])
    page: int = Field(1, ge=1, examples=[1])
    size: int = Field(20, ge=1, le=100, examples=[20])
