from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas.category import CategoryCreate, CategoryUpdate, CategoryRead
from ..crud.category import (
    get_categories, get_category_by_id, create_category,
    update_category, delete_category,
)
from ..dependencies import get_current_admin

router = APIRouter(prefix="/categories", tags=["Catégories"])


@router.get(
    "",
    response_model=List[CategoryRead],
    summary="Lister les catégories",
    description="Retourne toutes les catégories disponibles.",
)
def list_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_categories(db, skip=skip, limit=limit)


@router.get(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Détail d'une catégorie",
)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie introuvable")
    return category


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une catégorie",
    description="**Admin uniquement.** Crée une nouvelle catégorie de produits.",
    dependencies=[Depends(get_current_admin)],
)
def create_cat(category_in: CategoryCreate, db: Session = Depends(get_db)):
    return create_category(db, category_in)


@router.put(
    "/{category_id}",
    response_model=CategoryRead,
    summary="Modifier une catégorie",
    description="**Admin uniquement.**",
    dependencies=[Depends(get_current_admin)],
)
def update_cat(category_id: int, category_in: CategoryUpdate, db: Session = Depends(get_db)):
    category = get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie introuvable")
    return update_category(db, category, category_in)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une catégorie",
    description="**Admin uniquement.**",
    dependencies=[Depends(get_current_admin)],
)
def delete_cat(category_id: int, db: Session = Depends(get_db)):
    category = get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Catégorie introuvable")
    delete_category(db, category)
