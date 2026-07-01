from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import time
import logging

from .routers import auth, categories, products, cart, orders, reviews
from .core.metrics import (
    REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_REQUESTS, metrics_endpoint
)
from .config import get_settings

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API E-commerce",
    description="""
## Bienvenue sur ShopAPI ecommerce public

API REST complète pour une plateforme e-commerce, développée avec **FastAPI** et **PostgreSQL**.

### Fonctionnalités principales

- **Authentification JWT** : Inscription, connexion, refresh token
- **Catalogue Produits** : CRUD complet avec filtres avancés (catégorie, prix, stock, recherche)
- **Catégories** : Organisation hiérarchique des produits
- **Panier** : Gestion complète du panier d'achat
- **Commandes** : Création, suivi et annulation des commandes
- **Avis & Notes** : Système d'avis clients (note de 1 à 5)
- **Monitoring** : Métriques Prometheus sur `/metrics`

### Authentification

L'API utilise des **JWT Bearer tokens**. Pour accéder aux endpoints protégés :
1. Créez un compte via `POST /auth/register`
2. Connectez-vous via `POST /auth/login` pour obtenir votre token
3. Cliquez sur **Authorize** et entrez : `Bearer <votre_token>`

### Rôles utilisateurs

| Rôle | Droits |
|------|--------|
| `client` | Voir produits, gérer son panier, passer des commandes, laisser des avis |
| `admin` | Tous les droits + gestion catalogue, catégories, tous les statuts de commandes |

### Codes d'erreur

| Code | Signification |
|------|--------------|
| 400 | Données invalides |
| 401 | Non authentifié |
| 403 | Accès interdit (droits insuffisants) |
| 404 | Ressource introuvable |
| 409 | Conflit (email déjà utilisé, etc.) |
| 422 | Erreur de validation Pydantic |
    """,
    version="1.0.0",
    contact={
        "name": "Support ShopAPI",
        "email": "support@shopapi.example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    ACTIVE_REQUESTS.inc()
    start = time.time()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        duration = time.time() - start
        endpoint = request.url.path
        REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status_code="500").inc()
        REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(duration)
        ACTIVE_REQUESTS.dec()
        raise
    duration = time.time() - start
    endpoint = request.url.path
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=status_code,
    ).inc()
    REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(duration)
    ACTIVE_REQUESTS.dec()
    logger.info(f"method={request.method} path={endpoint} status={status_code} duration={duration:.3f}s")
    return response


@app.get(
    "/health",
    tags=["Système"],
    summary="Vérification de santé",
    description="Endpoint de liveness/readiness pour le monitoring et les load balancers.",
    response_description="Statut de l'application",
)
def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get(
    "/metrics",
    tags=["Système"],
    summary="Métriques Prometheus",
    description="Expose les métriques au format Prometheus pour le scraping.",
    include_in_schema=True,
)
def get_metrics():
    return metrics_endpoint()


app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(reviews.router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        contact=app.contact,
        license_info=app.license_info,
    )
    schema["info"]["x-logo"] = {"url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"}
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Entrez votre JWT token. Obtenez-le via `POST /auth/login`.",
        }
    }
    for path in schema.get("paths", {}).values():
        for operation in path.values():
            if isinstance(operation, dict) and "security" not in operation:
                tags = operation.get("tags", [])
                if tags and tags[0] not in ["Système", "Catégories", "Produits"]:
                    operation["security"] = [{"BearerAuth": []}]
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi
