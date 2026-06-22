from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from decimal import Decimal
from ..models.order import Order, OrderItem, OrderStatus
from ..models.cart import Cart, CartItem
from ..schemas.order import OrderCreate


def create_order_from_cart(db: Session, user_id: int, cart: Cart, order_in: OrderCreate) -> Order:
    total = Decimal("0.00")
    order_items = []
    for item in cart.items:
        if not item.product or item.product.stock < item.quantity:
            raise ValueError(f"Stock insuffisant pour '{item.product.name if item.product else item.product_id}'")
        unit_price = item.product.price
        total += unit_price * item.quantity
        order_items.append(
            OrderItem(product_id=item.product_id, quantity=item.quantity, unit_price=unit_price)
        )
        item.product.stock -= item.quantity

    order = Order(
        user_id=user_id,
        total_price=total,
        shipping_address=order_in.shipping_address,
    )
    db.add(order)
    db.flush()

    for oi in order_items:
        oi.order_id = order.id
        db.add(oi)

    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    db.refresh(order)
    return order


def get_orders_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> List[Order]:
    return (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_order_by_id(db: Session, order_id: int) -> Optional[Order]:
    return (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )


def update_order_status(db: Session, order: Order, status: OrderStatus) -> Order:
    order.status = status
    db.commit()
    db.refresh(order)
    return order


def get_all_orders(db: Session, skip: int = 0, limit: int = 50) -> List[Order]:
    return db.query(Order).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
