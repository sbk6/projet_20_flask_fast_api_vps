from pydantic import BaseModel, Field
from typing import List
from decimal import Decimal
from .product import ProductRead


class CartItemCreate(BaseModel):
    product_id: int = Field(..., examples=[1])
    quantity: int = Field(1, ge=1, le=99, examples=[2])

    model_config = {
        "json_schema_extra": {
            "example": {"product_id": 1, "quantity": 2}
        }
    }


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, le=99, examples=[3])

    model_config = {
        "json_schema_extra": {
            "example": {"quantity": 3}
        }
    }


class CartItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    product: ProductRead
    subtotal: Decimal

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "product_id": 1,
                "quantity": 2,
                "product": {
                    "id": 1,
                    "name": "iPhone 15 Pro Max",
                    "slug": "iphone-15-pro-max",
                    "price": "1299.99",
                    "stock": 50,
                    "image_url": "https://example.com/images/iphone15.jpg",
                    "is_active": True,
                    "category_id": 1,
                    "created_at": "2025-01-15T10:30:00Z",
                },
                "subtotal": "2599.98",
            }
        },
    }


class CartRead(BaseModel):
    id: int
    user_id: int
    items: List[CartItemRead]
    total: Decimal

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "user_id": 42,
                "items": [],
                "total": "0.00",
            }
        },
    }
