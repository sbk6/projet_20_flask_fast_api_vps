from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from ..database import get_db
from ..schemas.product import ProductCreate, ProductUpdate, ProductRead, ProductReadDetail
from ..crud.product import (
    get_products, get_product_by_id, get_product_with_stats,
    create_product, update_product, delete_product,
)
from ..dependencies import get_current_admin

router = APIRouter(prefix="/products", tags=["Produits"])


@router.get(
    "",
    response_model=dict,
    summary="Lister les produits",
    description="""
Retourne la liste paginée des produits avec filtres optionnels.

**Filtres disponibles :**
- `search` : recherche textuelle sur le nom et la description
- `category_id` : filtrer par catégorie
- `price_min` / `price_max` : fourchette de prix
- `in_stock` : uniquement les produits en stock
- `page` / `size` : pagination
    """,
)
def list_products(
    category_id: Optional[int] = Query(None, description="ID de la catégorie"),
    search: Optional[str] = Query(None, min_length=2, description="Recherche textuelle"),
    price_min: Optional[Decimal] = Query(None, ge=0, description="Prix minimum"),
    price_max: Optional[Decimal] = Query(None, gt=0, description="Prix maximum"),
    in_stock: Optional[bool] = Query(None, description="Uniquement en stock"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    size: int = Query(20, ge=1, le=100, description="Résultats par page"),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * size
    products, total = get_products(
        db,
        category_id=category_id,
        search=search,
        price_min=price_min,
        price_max=price_max,
        in_stock=in_stock,
        skip=skip,
        limit=size,
    )
    return {
        "items": [ProductRead.model_validate(p) for p in products],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 0,
    }


@router.get(
    "/{product_id}",
    response_model=ProductReadDetail,
    summary="Détail d'un produit",
    description="Retourne le détail complet d'un produit, avec sa catégorie, note moyenne et nombre d'avis.",
)
def get_product(product_id: int, db: Session = Depends(get_db)):
    result = get_product_with_stats(db, product_id)
    if not result:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    product = result["product"]
    detail = ProductReadDetail.model_validate(product)
    detail.average_rating = result["average_rating"]
    detail.review_count = result["review_count"]
    return detail


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un produit",
    description="**Admin uniquement.** Ajoute un nouveau produit au catalogue.",
    dependencies=[Depends(get_current_admin)],
)
def create_prod(product_in: ProductCreate, db: Session = Depends(get_db)):
    return create_product(db, product_in)


@router.put(
    "/{product_id}",
    response_model=ProductRead,
    summary="Modifier un produit",
    description="**Admin uniquement.** Modification partielle ou totale d'un produit.",
    dependencies=[Depends(get_current_admin)],
)
def update_prod(product_id: int, product_in: ProductUpdate, db: Session = Depends(get_db)):
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    return update_product(db, product, product_in)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un produit",
    description="**Admin uniquement.** Désactivation logique du produit (soft delete).",
    dependencies=[Depends(get_current_admin)],
)
def delete_prod(product_id: int, db: Session = Depends(get_db)):
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    delete_product(db, product)
