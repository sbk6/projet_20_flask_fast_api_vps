from sqlalchemy.orm import Session, joinedload
from typing import Optional
from decimal import Decimal
from ..models.cart import Cart, CartItem
from ..models.product import Product


def get_or_create_cart(db: Session, user_id: int) -> Cart:
    cart = (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.product))
        .filter(Cart.user_id == user_id)
        .first()
    )
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def add_item_to_cart(db: Session, cart: Cart, product_id: int, quantity: int) -> Cart:
    existing = db.query(CartItem).filter(
        CartItem.cart_id == cart.id, CartItem.product_id == product_id
    ).first()
    if existing:
        existing.quantity += quantity
    else:
        item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        db.add(item)
    db.commit()
    db.refresh(cart)
    return get_or_create_cart(db, cart.user_id)


def update_cart_item(db: Session, cart_id: int, product_id: int, quantity: int) -> Optional[CartItem]:
    item = db.query(CartItem).filter(
        CartItem.cart_id == cart_id, CartItem.product_id == product_id
    ).first()
    if item:
        item.quantity = quantity
        db.commit()
        db.refresh(item)
    return item


def remove_cart_item(db: Session, cart_id: int, product_id: int) -> bool:
    item = db.query(CartItem).filter(
        CartItem.cart_id == cart_id, CartItem.product_id == product_id
    ).first()
    if item:
        db.delete(item)
        db.commit()
        return True
    return False


def clear_cart(db: Session, cart: Cart) -> Cart:
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    db.refresh(cart)
    return cart


def compute_cart_total(cart: Cart) -> Decimal:
    total = Decimal("0.00")
    for item in cart.items:
        if item.product:
            total += item.product.price * item.quantity
    return total
