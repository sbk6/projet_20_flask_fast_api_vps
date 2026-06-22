from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError
from ..database import get_db
from ..schemas.user import UserCreate, UserRead, UserLogin, Token, TokenRefresh
from ..crud.user import get_user_by_email, get_user_by_username, create_user, authenticate_user
from ..core.security import create_access_token, create_refresh_token, decode_token
from ..dependencies import get_current_user
from ..models.user import User

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte",
    description="Créer un nouveau compte utilisateur. L'email et le nom d'utilisateur doivent être uniques.",
)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=409, detail="Cet email est déjà utilisé")
    if get_user_by_username(db, user_in.username):
        raise HTTPException(status_code=409, detail="Ce nom d'utilisateur est déjà pris")
    return create_user(db, user_in)


@router.post(
    "/login",
    response_model=Token,
    summary="Se connecter",
    description="Authentification par email/mot de passe. Retourne un access token (30min) et un refresh token (7j).",
)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé")
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Renouveler le token",
    description="Utilise le refresh token pour obtenir un nouvel access token.",
)
def refresh_token(body: TokenRefresh, db: Session = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token invalide")
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Refresh token invalide ou expiré")

    from ..crud.user import get_user_by_id
    user = get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get(
    "/me",
    response_model=UserRead,
    summary="Mon profil",
    description="Retourne les informations du compte connecté.",
)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
