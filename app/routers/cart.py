from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.cart import CartRead, CartItemCreate, CartItemUpdate, CartItemRead
from ..crud.cart import (
    get_or_create_cart, add_item_to_cart, update_cart_item,
    remove_cart_item, clear_cart, compute_cart_total,
)
from ..crud.product import get_product_by_id
from ..dependencies import get_current_user
from ..models.user import User
from decimal import Decimal

router = APIRouter(prefix="/cart", tags=["Panier"])


def build_cart_response(cart, db) -> CartRead:
    from ..schemas.product import ProductRead
    items = []
    for item in cart.items:
        if item.product:
            subtotal = item.product.price * item.quantity
            items.append(
                CartItemRead(
                    id=item.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    product=ProductRead.model_validate(item.product),
                    subtotal=subtotal,
                )
            )
    total = compute_cart_total(cart)
    return CartRead(id=cart.id, user_id=cart.user_id, items=items, total=total)


@router.get(
    "",
    response_model=CartRead,
    summary="Voir mon panier",
    description="Retourne le contenu du panier de l'utilisateur connecté.",
)
def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, current_user.id)
    return build_cart_response(cart, db)


@router.post(
    "/items",
    response_model=CartRead,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter un article",
    description="Ajoute un produit au panier. Si l'article existe déjà, la quantité est cumulée.",
)
def add_to_cart(
    item_in: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = get_product_by_id(db, item_in.product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    if product.stock < item_in.quantity:
        raise HTTPException(status_code=400, detail=f"Stock insuffisant (disponible : {product.stock})")
    cart = get_or_create_cart(db, current_user.id)
    cart = add_item_to_cart(db, cart, item_in.product_id, item_in.quantity)
    return build_cart_response(cart, db)


@router.put(
    "/items/{product_id}",
    response_model=CartRead,
    summary="Modifier la quantité",
    description="Met à jour la quantité d'un article dans le panier.",
)
def update_item(
    product_id: int,
    item_in: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    if product.stock < item_in.quantity:
        raise HTTPException(status_code=400, detail=f"Stock insuffisant (disponible : {product.stock})")
    cart = get_or_create_cart(db, current_user.id)
    updated = update_cart_item(db, cart.id, product_id, item_in.quantity)
    if not updated:
        raise HTTPException(status_code=404, detail="Article absent du panier")
    cart = get_or_create_cart(db, current_user.id)
    return build_cart_response(cart, db)


@router.delete(
    "/items/{product_id}",
    response_model=CartRead,
    summary="Retirer un article",
    description="Supprime un article du panier.",
)
def remove_item(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = get_or_create_cart(db, current_user.id)
    removed = remove_cart_item(db, cart.id, product_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Article absent du panier")
    cart = get_or_create_cart(db, current_user.id)
    return build_cart_response(cart, db)


@router.delete(
    "",
    response_model=CartRead,
    summary="Vider le panier",
    description="Supprime tous les articles du panier.",
)
def empty_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, current_user.id)
    cart = clear_cart(db, cart)
    return build_cart_response(cart, db)
