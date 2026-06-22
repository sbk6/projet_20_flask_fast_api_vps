from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas.order import OrderCreate, OrderRead, OrderReadDetail, OrderStatusUpdate
from ..crud.order import (
    create_order_from_cart, get_orders_by_user, get_order_by_id,
    update_order_status, get_all_orders,
)
from ..crud.cart import get_or_create_cart
from ..dependencies import get_current_user, get_current_admin
from ..models.user import User
from ..models.order import OrderStatus

router = APIRouter(prefix="/orders", tags=["Commandes"])


@router.post(
    "",
    response_model=OrderReadDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Passer une commande",
    description="Crée une commande à partir du contenu actuel du panier. Le panier est vidé après la commande.",
)
def create_order(
    order_in: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart = get_or_create_cart(db, current_user.id)
    if not cart.items:
        raise HTTPException(status_code=400, detail="Votre panier est vide")
    try:
        order = create_order_from_cart(db, current_user.id, cart, order_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    order = get_order_by_id(db, order.id)
    result = OrderReadDetail.model_validate(order)
    for item in result.items:
        item.subtotal = item.unit_price * item.quantity
    return result


@router.get(
    "",
    response_model=List[OrderRead],
    summary="Mes commandes",
    description="Liste toutes les commandes de l'utilisateur connecté.",
)
def list_my_orders(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_orders_by_user(db, current_user.id, skip=skip, limit=limit)


@router.get(
    "/{order_id}",
    response_model=OrderReadDetail,
    summary="Détail d'une commande",
    description="Retourne le détail d'une commande. L'utilisateur ne peut voir que ses propres commandes.",
)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    if order.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Accès interdit")
    result = OrderReadDetail.model_validate(order)
    for item in result.items:
        item.subtotal = item.unit_price * item.quantity
    return result


@router.put(
    "/{order_id}/cancel",
    response_model=OrderRead,
    summary="Annuler une commande",
    description="Annule une commande si elle est encore au statut `pending`.",
)
def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès interdit")
    if order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Seules les commandes en attente peuvent être annulées")
    return update_order_status(db, order, OrderStatus.CANCELLED)


@router.put(
    "/{order_id}/status",
    response_model=OrderRead,
    summary="Changer le statut (Admin)",
    description="**Admin uniquement.** Modifie le statut d'une commande.",
    dependencies=[Depends(get_current_admin)],
)
def change_status(order_id: int, body: OrderStatusUpdate, db: Session = Depends(get_db)):
    order = get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    return update_order_status(db, order, body.status)


@router.get(
    "/admin/all",
    response_model=List[OrderRead],
    summary="Toutes les commandes (Admin)",
    description="**Admin uniquement.** Liste toutes les commandes de la plateforme.",
    dependencies=[Depends(get_current_admin)],
)
def list_all_orders(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return get_all_orders(db, skip=skip, limit=limit)
