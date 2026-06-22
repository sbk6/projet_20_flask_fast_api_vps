from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from ..models.order import OrderStatus


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Optional[Decimal] = None

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    shipping_address: str = Field(..., min_length=10, max_length=500, examples=["12 Rue de la Paix, 75001 Paris, France"])

    model_config = {
        "json_schema_extra": {
            "example": {"shipping_address": "12 Rue de la Paix, 75001 Paris, France"}
        }
    }


class OrderStatusUpdate(BaseModel):
    status: OrderStatus = Field(..., examples=["confirmed"])

    model_config = {
        "json_schema_extra": {
            "example": {"status": "confirmed"}
        }
    }


class OrderRead(BaseModel):
    id: int
    user_id: int
    status: OrderStatus
    total_price: Decimal
    shipping_address: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "user_id": 42,
                "status": "pending",
                "total_price": "2599.98",
                "shipping_address": "12 Rue de la Paix, 75001 Paris, France",
                "created_at": "2025-01-20T14:00:00Z",
            }
        },
    }


class OrderReadDetail(OrderRead):
    items: List[OrderItemRead]

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "user_id": 42,
                "status": "pending",
                "total_price": "2599.98",
                "shipping_address": "12 Rue de la Paix, 75001 Paris, France",
                "created_at": "2025-01-20T14:00:00Z",
                "items": [
                    {
                        "id": 1,
                        "product_id": 1,
                        "quantity": 2,
                        "unit_price": "1299.99",
                        "subtotal": "2599.98",
                    }
                ],
            }
        },
    }
