from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas.review import ReviewCreate, ReviewUpdate, ReviewRead
from ..crud.review import (
    get_product_reviews, get_review_by_id, get_user_product_review,
    create_review, update_review, delete_review,
)
from ..crud.product import get_product_by_id
from ..dependencies import get_current_user
from ..models.user import User, UserRole

router = APIRouter(tags=["Avis & Notes"])


@router.get(
    "/products/{product_id}/reviews",
    response_model=List[ReviewRead],
    summary="Avis d'un produit",
    description="Retourne tous les avis clients pour un produit, du plus récent au plus ancien.",
)
def list_reviews(
    product_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    reviews = get_product_reviews(db, product_id, skip=skip, limit=limit)
    result = []
    for r in reviews:
        rv = ReviewRead.model_validate(r)
        rv.username = r.user.username if r.user else None
        result.append(rv)
    return result


@router.post(
    "/products/{product_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Laisser un avis",
    description="Poste un avis sur un produit. Un utilisateur ne peut laisser qu'un seul avis par produit.",
)
def post_review(
    product_id: int,
    review_in: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    existing = get_user_product_review(db, current_user.id, product_id)
    if existing:
        raise HTTPException(status_code=409, detail="Vous avez déjà laissé un avis pour ce produit")
    review = create_review(db, current_user.id, product_id, review_in)
    result = ReviewRead.model_validate(review)
    result.username = current_user.username
    return result


@router.put(
    "/reviews/{review_id}",
    response_model=ReviewRead,
    summary="Modifier un avis",
    description="Modifie votre avis. Seul l'auteur peut modifier son avis.",
)
def edit_review(
    review_id: int,
    review_in: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Avis introuvable")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Vous ne pouvez modifier que vos propres avis")
    review = update_review(db, review, review_in)
    result = ReviewRead.model_validate(review)
    result.username = current_user.username
    return result


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un avis",
    description="Supprime un avis. L'auteur ou un admin peut supprimer.",
)
def remove_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Avis introuvable")
    if review.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Accès interdit")
    delete_review(db, review)
