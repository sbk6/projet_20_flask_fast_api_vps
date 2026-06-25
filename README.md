# ShopAPI : API E-commerce FastAPI

> **Projet 20 : Déploiement complet en production sur VPS**  
> Cours : APIs Web pour le Machine Learning (Flask & FastAPI) - ESGIS Master 1  
> Auteur(s) : Groupe 20

---

## Table des matières

1. [Présentation du projet](#présentation-du-projet)
2. [Architecture globale](#architecture-globale)
3. [Explication de la stack technique](#explication-de-la-stack-technique)
4. [Comprendre Docker (pour débutants)](#comprendre-docker-pour-débutants)
5. [Structure du projet](#structure-du-projet)
6. [Lancer le projet localement](#lancer-le-projet-localement)
7. [Documentation API Swagger](#documentation-api-swagger)
8. [Endpoints disponibles](#endpoints-disponibles)
9. [Tests automatisés](#tests-automatisés)
10. [Variables d'environnement](#variables-denvironnement)

---

## Présentation du projet

**ShopAPI** est une API REST complète pour une plateforme e-commerce. Elle permet de :

- Créer un compte et se connecter (authentification JWT)
- Parcourir un catalogue de produits avec filtres avancés
- Gérer un panier d'achats
- Passer des commandes et suivre leur statut
- Laisser des avis sur les produits
- Administrer le catalogue (rôle admin)

Ce projet constitue la base de l'application déployée en production dans le cadre du **Projet 20** (déploiement VPS avec CI/CD, HTTPS et monitoring).

---

## Architecture globale

```
Internet
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  VPS Hostinger KVM4 (Ubuntu 22.04)                          │
│                                                              │
│  ┌──────────┐   HTTPS    ┌──────────────────────────────┐   │
│  │  Client  │ ────────── │  Nginx (reverse proxy)       │   │
│  │(Browser/ │            │  Port 80 → redirect HTTPS    │   │
│  │  curl)   │            │  Port 443 → proxy :8000      │   │
│  └──────────┘            └──────────────┬───────────────┘   │
│                                         │                    │
│                          ┌──────────────▼───────────────┐   │
│                          │  Docker Container : API       │   │
│                          │  FastAPI + Gunicorn           │   │
│                          │  4 workers Uvicorn            │   │
│                          │  Port 8000 (interne)          │   │
│                          └──────────────┬───────────────┘   │
│                                         │                    │
│                 ┌───────────────────────┼──────────────┐    │
│                 │                       │              │    │
│    ┌────────────▼──────┐  ┌─────────────▼──┐  ┌───────▼──┐ │
│    │ Docker: PostgreSQL│  │Docker:Prometheus│  │Docker:    │ │
│    │ Base de données   │  │Métriques /metr..│  │Grafana    │ │
│    └───────────────────┘  └────────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Flux d'une requête :**
1. Le client envoie une requête HTTPS
2. Nginx reçoit la requête (port 443) et vérifie le certificat SSL
3. Nginx transmet la requête à l'API FastAPI (port 8000, réseau interne)
4. FastAPI traite la requête, interroge PostgreSQL si besoin
5. FastAPI retourne la réponse JSON
6. Nginx retransmet la réponse au client

---

## Explication de la stack technique

### FastAPI : Le framework web

**Qu'est-ce que c'est ?**  
FastAPI est un framework Python moderne pour créer des APIs REST. Il est basé sur les **annotations de type** Python et génère automatiquement une documentation interactive.

**Pourquoi on l'a choisi ?**
- Très rapide (comparable à Node.js, grâce à Uvicorn/ASGI)
- Génère automatiquement Swagger UI et Redoc
- Valide automatiquement les données avec Pydantic
- Code clair et lisible grâce aux type hints Python

**Exemple concret :**
```python
@app.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    # FastAPI valide automatiquement que product_id est un entier
    # Si on passe "abc" au lieu d'un nombre, FastAPI retourne 422 automatiquement
    product = db.query(Product).filter(Product.id == product_id).first()
    return product
```

---

### Pydantic v2 : La validation des données

**Qu'est-ce que c'est ?**  
Pydantic est une bibliothèque qui valide les données entrantes et sortantes de votre API. C'est comme un "garde-fou" qui vérifie que les données ont le bon format avant de les traiter.

**Pourquoi on l'a choisi ?**
- Intégré nativement dans FastAPI
- Génère les exemples dans Swagger automatiquement
- Les erreurs sont claires et standardisées (code 422)
- Pydantic v2 est 5-50x plus rapide que v1 (réécrit en Rust)

**Exemple concret :**
```python
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)  # obligatoire, 2-255 chars
    price: Decimal = Field(..., gt=0)                      # obligatoire, > 0
    stock: int = Field(0, ge=0)                            # optionnel, >= 0

# Si quelqu'un envoie : {"name": "X", "price": -10}
# Pydantic retourne automatiquement une erreur 422 avec le détail :
# "price must be greater than 0"
```

---

### SQLAlchemy : L'ORM (Object-Relational Mapper)

**Qu'est-ce que c'est ?**  
SQLAlchemy permet d'interagir avec la base de données PostgreSQL en écrivant du Python au lieu du SQL. Il fait la traduction Python ↔ SQL automatiquement.

**Pourquoi on l'a choisi ?**
- On écrit des classes Python, SQLAlchemy génère le SQL
- Protection automatique contre les injections SQL
- Supporte PostgreSQL, MySQL, SQLite (on utilise SQLite pour les tests)
- Très mature et bien documenté

**Exemple concret :**
```python
# Avec SQLAlchemy (Python)
products = db.query(Product).filter(Product.price <= 100).all()

# Ce que SQLAlchemy génère en SQL :
# SELECT * FROM products WHERE price <= 100;
```

---

### PostgreSQL : La base de données

**Qu'est-ce que c'est ?**  
PostgreSQL est un système de gestion de bases de données relationnelles (SGBDR) open-source. C'est l'une des bases de données les plus robustes et utilisées au monde.

**Pourquoi on l'a choisi ?**
- Gratuit et open-source
- Supporte les transactions ACID (données cohérentes même en cas de panne)
- Très performant pour les lectures et écritures
- Supporte des types de données avancés (JSON, arrays, etc.)
- Compatible avec Alembic pour les migrations

---

### JWT (JSON Web Tokens) : L'authentification

**Qu'est-ce que c'est ?**  
Un JWT est un "jeton" numérique signé qui prouve l'identité d'un utilisateur. C'est comme un badge d'entrée numérique.

**Comment ça marche ?**
```
1. L'utilisateur se connecte avec email + mot de passe
2. Le serveur vérifie les credentials
3. Le serveur génère un JWT signé avec une clé secrète
   Exemple : eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.xxx
4. L'utilisateur envoie ce JWT dans chaque requête suivante
   Header : Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
5. Le serveur vérifie la signature → si valide, l'utilisateur est authentifié
```

**Pourquoi deux tokens (access + refresh) ?**
- **Access token** : expire en 30 minutes (sécurité)
- **Refresh token** : expire en 7 jours (confort)  
  → Quand l'access token expire, le client utilise le refresh token pour en obtenir un nouveau, sans avoir à se reconnecter

---

### Gunicorn + Uvicorn : Le serveur de production

**Qu'est-ce que c'est ?**

- **Uvicorn** : serveur ASGI (Asynchronous Server Gateway Interface) - il exécute FastAPI
- **Gunicorn** : gestionnaire de processus - il démarre plusieurs instances d'Uvicorn en parallèle

**Pourquoi pas juste `uvicorn app.main:app` ?**

Uvicorn seul ne gère qu'un seul processus. Si 100 utilisateurs font des requêtes en même temps, elles font la queue. Avec Gunicorn, on démarre plusieurs workers en parallèle :

```
Gunicorn (gestionnaire)
├── Worker 1 (Uvicorn) → gère les requêtes 1, 5, 9...
├── Worker 2 (Uvicorn) → gère les requêtes 2, 6, 10...
├── Worker 3 (Uvicorn) → gère les requêtes 3, 7, 11...
└── Worker 4 (Uvicorn) → gère les requêtes 4, 8, 12...
```

**Règle pour le nombre de workers :** `2 × nb_CPU + 1`  
Pour notre VPS 4 vCPU : `2 × 4 + 1 = 9 workers`

---

### Nginx : Le reverse proxy

**Qu'est-ce qu'un reverse proxy ?**  
Nginx est un serveur web qui se place devant votre API. Il reçoit toutes les requêtes et les transmet à l'API. C'est le "portier" de votre application.

**Pourquoi on en a besoin ?**
- Gère le HTTPS / SSL (avec les certificats Let's Encrypt)
- Compresse les réponses (gzip) → plus rapide
- Protège l'API (limite la taille des requêtes, gère les timeouts)
- Peut servir des fichiers statiques directement sans passer par Python
- Cache les réponses pour les routes publiques

```
Client ──HTTPS──► Nginx :443 ──HTTP──► FastAPI :8000
                   (SSL)             (réseau interne)
```

---

### Let's Encrypt + Certbot : Le HTTPS gratuit

**Qu'est-ce que c'est ?**  
Let's Encrypt est une autorité de certification gratuite qui génère des certificats SSL. Certbot est l'outil qui automatise leur obtention et renouvellement.

**Pourquoi c'est important ?**  
Sans HTTPS, les données (passwords, tokens) transitent en clair sur Internet. N'importe qui sur le réseau peut les lire. HTTPS chiffre tout.

**Renouvellement automatique :**  
Les certificats Let's Encrypt expirent après 90 jours. On configure Certbot dans cron pour les renouveler automatiquement tous les 60 jours.

---

### Prometheus + Grafana : Le monitoring

**Prometheus :**  
Prometheus "scrape" (collecte) les métriques de l'API toutes les 15 secondes via l'endpoint `/metrics`. Il stocke ces données dans une base de temps (time-series database).

**Grafana :**  
Grafana lit les données de Prometheus et les affiche en graphiques. On peut créer des alertes (ex: "alerter par Discord si CPU > 90%").

**Métriques collectées :**
- `http_requests_total` : nombre de requêtes par endpoint et code HTTP
- `http_request_duration_seconds` : latence des requêtes
- `http_requests_active` : requêtes en cours

---

### GitHub Actions : La CI/CD

**Qu'est-ce que la CI/CD ?**
- **CI (Continuous Integration)** : à chaque push, les tests sont lancés automatiquement
- **CD (Continuous Deployment)** : si les tests passent, le code est déployé automatiquement

**Notre pipeline :**
```
Push sur main
    │
    ▼
Job 1 : Tests (pytest)
    │ Tests OK ?
    ▼
Job 2 : Build image Docker + push sur ghcr.io
    │
    ▼
Job 3 : SSH sur VPS → pull nouvelle image → restart → healthcheck
    │ Healthcheck OK ?
    ├── OUI → Déploiement réussi 
    └── NON → Rollback vers ancienne image 
```

---

## Comprendre Docker 

### Qu'est-ce que Docker ?

Imagine que tu veux partager une recette de cuisine. Tu peux envoyer la recette (le code), mais le résultat peut varier selon les ingrédients disponibles chez chaque personne (l'environnement).

**Docker, c'est comme envoyer directement la boîte repas complète** : le code + toutes ses dépendances + l'environnement d'exécution, emballés ensemble. Ça marche pareil partout.

### Vocabulaire Docker essentiel

| Terme | Explication simple | Analogie |
|-------|-------------------|---------|
| **Image** | Le "plan" de construction de l'application | Recette de cuisine |
| **Container** | Une instance en cours d'exécution d'une image | Le plat cuisiné |
| **Dockerfile** | Le fichier qui décrit comment construire l'image | La recette écrite |
| **docker-compose** | Outil pour gérer plusieurs containers ensemble | Le chef d'orchestre |
| **Volume** | Stockage persistant (les données survivent si le container s'arrête) | Disque dur externe |
| **Port mapping** | Relie un port du container à un port de la machine hôte | Interprète |
| **Network** | Réseau interne entre containers | Réseau local |

### Notre Dockerfile expliqué ligne par ligne

```dockerfile
# STAGE 1 : On part d'une image Python officielle légère (slim = sans extras)
FROM python:3.11-slim AS builder
#   └─ "python:3.11-slim" est une image officielle sur Docker Hub

WORKDIR /app
# Comme "cd /app" dans le container

COPY requirements.txt .
# Copie requirements.txt depuis ton PC vers /app dans le container

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
# Installe les dépendances Python DANS /install (pas dans /usr/local)
# --no-cache-dir : ne garde pas le cache pip (réduit la taille)
# --prefix=/install : installe dans un dossier séparé pour le stage 2

# STAGE 2 : Image finale (plus légère car on ne garde que le nécessaire)
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local
# Copie les dépendances installées (stage 1) dans l'image finale

COPY . .
# Copie tout le code source

ENV PYTHONDONTWRITEBYTECODE=1
# Ne pas créer les fichiers .pyc (inutiles en prod)

ENV PYTHONUNBUFFERED=1
# Logs visibles en temps réel (pas de buffering)

EXPOSE 8000
# Documente que le container écoute sur le port 8000
# (ne publie PAS le port, juste une documentation)

CMD ["gunicorn", "app.main:app", "--workers", "4", ...]
# Commande lancée quand le container démarre
```

**Pourquoi 2 stages (multi-stage build) ?**  
Le stage 1 installe les dépendances (inclut pip, des compilateurs, etc.). Le stage 2 ne copie que le résultat. Résultat : image finale ~3x plus petite.

### Notre docker-compose.yml expliqué

```yaml
version: "3.9"   # Version de la syntaxe docker-compose

services:         # Les containers à démarrer

  db:             # Nom du service (utilisable comme hostname dans le réseau interne)
    image: postgres:16-alpine   # Image officielle PostgreSQL version 16
    
    environment:                # Variables d'environnement passées au container
      POSTGRES_USER: shopuser   # Identifiant
      POSTGRES_PASSWORD: ...    # Mot de passe
      POSTGRES_DB: ecommerce_db # Nom de la base
    
    volumes:                    # Persistance des données
      - postgres_data:/var/lib/postgresql/data
      #   postgres_data = nom du volume Docker (géré par Docker)
      #   /var/lib/postgresql/data = chemin DANS le container où PostgreSQL stocke ses données
      # Sans ce volume, toutes les données sont perdues si le container redémarre !
    
    healthcheck:                # Docker vérifie si la DB est prête
      test: ["CMD-SHELL", "pg_isready -U shopuser"]
      interval: 10s             # Vérification toutes les 10 secondes
      retries: 5                # 5 tentatives avant de déclarer "unhealthy"
    
    ports:
      - "5432:5432"             # Port_machine_hôte:Port_container
      # Permet d'accéder à PostgreSQL depuis ton PC (outils comme DBeaver)

  api:
    build: .                    # Construire l'image depuis le Dockerfile dans le dossier courant
    
    depends_on:
      db:
        condition: service_healthy   # L'API ne démarre que quand la DB est prête
    
    environment:
      DATABASE_URL: postgresql://shopuser:shoppassword@db:5432/ecommerce_db
      #                                                  ^^
      #                                       "db" = hostname du service db dans le réseau Docker
    
    ports:
      - "8000:8000"

volumes:          # Déclaration des volumes Docker (stockage persistant)
  postgres_data:  # Docker crée et gère ce volume automatiquement
```

### Commandes Docker essentielles

```bash
# Construire et démarrer tous les services en arrière-plan
docker compose up -d

# Voir les containers en cours
docker compose ps

# Voir les logs de l'API
docker compose logs api -f
# -f = follow (temps réel, comme tail -f)

# Arrêter tous les services
docker compose down

# Arrêter ET supprimer les volumes (DANGER : perd toutes les données !)
docker compose down -v

# Reconstruire l'image après modification du code
docker compose up -d --build api

# Entrer dans un container (comme SSH)
docker compose exec api bash

# Voir les images disponibles sur ta machine
docker images

# Supprimer les images inutilisées
docker image prune -f
```

---

## Structure du projet

```
ecommerce_api/
│
├── app/                          # Code source principal
│   ├── main.py                   # Point d'entrée FastAPI, configuration Swagger
│   ├── config.py                 # Variables d'environnement (Settings)
│   ├── database.py               # Connexion SQLAlchemy + session DB
│   ├── dependencies.py           # Dépendances FastAPI (auth, DB)
│   │
│   ├── models/                   # Modèles SQLAlchemy (tables DB)
│   │   ├── user.py               # Table users
│   │   ├── category.py           # Table categories
│   │   ├── product.py            # Table products
│   │   ├── cart.py               # Tables carts + cart_items
│   │   ├── order.py              # Tables orders + order_items
│   │   └── review.py             # Table reviews
│   │
│   ├── schemas/                  # Schémas Pydantic (validation + sérialisation)
│   │   ├── user.py               # UserCreate, UserRead, Token...
│   │   ├── category.py           # CategoryCreate, CategoryRead...
│   │   ├── product.py            # ProductCreate, ProductRead, ProductReadDetail...
│   │   ├── cart.py               # CartRead, CartItemCreate...
│   │   ├── order.py              # OrderCreate, OrderRead, OrderReadDetail...
│   │   └── review.py             # ReviewCreate, ReviewRead...
│   │
│   ├── crud/                     # Opérations base de données (Create/Read/Update/Delete)
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── product.py
│   │   ├── cart.py
│   │   ├── order.py
│   │   └── review.py
│   │
│   ├── routers/                  # Endpoints FastAPI organisés par ressource
│   │   ├── auth.py               # POST /auth/register, /auth/login, /auth/refresh
│   │   ├── categories.py         # GET/POST/PUT/DELETE /categories
│   │   ├── products.py           # GET/POST/PUT/DELETE /products
│   │   ├── cart.py               # GET/POST/PUT/DELETE /cart
│   │   ├── orders.py             # GET/POST /orders
│   │   └── reviews.py            # GET/POST/PUT/DELETE /reviews
│   │
│   └── core/
│       ├── security.py           # Hachage bcrypt, création/vérification JWT
│       └── metrics.py            # Compteurs Prometheus
│
├── tests/                        # Tests automatisés
│   ├── conftest.py               # Fixtures pytest (DB SQLite, client test)
│   ├── test_auth.py              # 12 tests sur l'authentification
│   ├── test_categories.py        # 8 tests sur les catégories
│   ├── test_products.py          # 12 tests sur les produits
│   ├── test_cart.py              # 9 tests sur le panier
│   ├── test_orders.py            # 9 tests sur les commandes
│   ├── test_reviews.py           # 9 tests sur les avis
│   └── test_health.py            # 2 tests sur /health et /metrics
│
├── alembic/                      # Migrations de base de données
│   ├── env.py
│   └── versions/                 # Fichiers de migration (vide au départ)
│
├── monitoring/                   # Configuration Prometheus + Grafana
│   ├── prometheus.yml
│   └── grafana/provisioning/
│
├── deploy/                       # Fichiers de déploiement
│   ├── nginx/shopapi.conf        # Configuration Nginx production
│   └── docker-compose.prod.yml   # docker-compose de production
│
├── .github/workflows/
│   └── deploy.yml                # Pipeline CI/CD GitHub Actions
│
├── Dockerfile                    # Construction de l'image Docker
├── docker-compose.yml            # Configuration Docker locale (dev)
├── gunicorn.conf.py              # Configuration Gunicorn production
├── requirements.txt              # Dépendances Python
├── alembic.ini                   # Configuration Alembic
├── pytest.ini                    # Configuration pytest
├── .env.example                  # Variables d'environnement exemple
└── .gitignore                    # Fichiers à ignorer dans Git
```

---

## Lancer le projet localement

### Option 1 : Avec Docker (recommandé)

```bash
# 1. Cloner le repo
git clone https://github.com/sbk6/projet_20_flask_fast_api_vps.git
cd projet_20_flask_fast_api_vps

# 2. Copier le fichier d'environnement
cp .env.example .env
# Éditer .env et changer SECRET_KEY

# 3. Démarrer tous les services
docker compose up -d

# 4. Exécuter les migrations
docker compose exec api alembic upgrade head

# 5. Créer un admin (optionnel)
docker compose exec api python -c "
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password
db = SessionLocal()
admin = User(email='admin@shopapi.com', username='admin',
             hashed_password=hash_password('Admin123!'),
             role=UserRole.ADMIN, is_active=True)
db.add(admin)
db.commit()
print('Admin créé !')
"

# 6. Accéder à l'API
# Swagger UI : http://localhost:8000/docs
# Redoc     : http://localhost:8000/redoc
# Prometheus: http://localhost:9090
# Grafana   : http://localhost:3000  (admin / admin)
```

### Option 2 : Sans Docker (développement)

```bash
# 1. Cloner et entrer dans le projet
git clone https://github.com/sbk6/projet_20_flask_fast_api_vps.git
cd projet_20_flask_fast_api_vps

# 2. Créer l'environnement virtuel Python
python -m venv venv

# 3. Activer l'environnement virtuel
# Windows :
venv\Scripts\activate
# Linux/Mac :
source venv/bin/activate

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec l'URL de votre PostgreSQL local

# 6. Lancer les migrations
alembic upgrade head

# 7. Démarrer le serveur de développement
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# --reload : redémarre automatiquement si tu modifies le code
```

---

## Documentation API Swagger

Une fois l'API lancée, accède à la documentation interactive :

- **Swagger UI** : `http://localhost:8000/docs`  
  Interface graphique complète pour tester tous les endpoints

- **Redoc** : `http://localhost:8000/redoc`  
  Documentation plus lisible, idéale pour partager

- **OpenAPI JSON** : `http://localhost:8000/openapi.json`  
  Schéma JSON brut (pour générer des SDKs clients)

**Pour tester depuis Swagger :**
1. Crée un compte via `POST /auth/register`
2. Connecte-toi via `POST /auth/login` → copie l'`access_token`
3. Clique sur **Authorize**  en haut à droite
4. Entre : `Bearer <ton_access_token>`
5. Tu peux maintenant appeler tous les endpoints protégés

---

## Endpoints disponibles

### Authentification (`/auth`)
| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| POST | `/auth/register` | Créer un compte | ✗ |
| POST | `/auth/login` | Se connecter | ✗ |
| POST | `/auth/refresh` | Renouveler le token | ✗ |
| GET | `/auth/me` | Mon profil | ✓ |

### Catégories (`/categories`)
| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| GET | `/categories` | Lister les catégories | ✗ |
| GET | `/categories/{id}` | Détail d'une catégorie | ✗ |
| POST | `/categories` | Créer une catégorie | Admin |
| PUT | `/categories/{id}` | Modifier une catégorie | Admin |
| DELETE | `/categories/{id}` | Supprimer une catégorie | Admin |

### Produits (`/products`)
| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| GET | `/products` | Lister (filtres: search, category, price_min/max, in_stock, page/size) | ✗ |
| GET | `/products/{id}` | Détail + avis moyens | ✗ |
| POST | `/products` | Créer un produit | Admin |
| PUT | `/products/{id}` | Modifier un produit | Admin |
| DELETE | `/products/{id}` | Désactiver un produit | Admin |

### Panier (`/cart`)
| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| GET | `/cart` | Voir mon panier | ✓ |
| POST | `/cart/items` | Ajouter un article | ✓ |
| PUT | `/cart/items/{product_id}` | Modifier la quantité | ✓ |
| DELETE | `/cart/items/{product_id}` | Retirer un article | ✓ |
| DELETE | `/cart` | Vider le panier | ✓ |

### Commandes (`/orders`)
| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| POST | `/orders` | Passer une commande (depuis le panier) | ✓ |
| GET | `/orders` | Mes commandes | ✓ |
| GET | `/orders/{id}` | Détail d'une commande | ✓ |
| PUT | `/orders/{id}/cancel` | Annuler (si pending) | ✓ |
| PUT | `/orders/{id}/status` | Changer le statut | Admin |
| GET | `/orders/admin/all` | Toutes les commandes | Admin |

### Avis (`/products/{id}/reviews`)
| Méthode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| GET | `/products/{id}/reviews` | Avis d'un produit | ✗ |
| POST | `/products/{id}/reviews` | Laisser un avis (1 par produit) | ✓ |
| PUT | `/reviews/{id}` | Modifier son avis | ✓ |
| DELETE | `/reviews/{id}` | Supprimer son avis | ✓ |

### Système
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Healthcheck (liveness probe) |
| GET | `/metrics` | Métriques Prometheus |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | Redoc |

---

## Tests automatisés

```bash
# Lancer tous les tests
python -m pytest tests/ -v

# Lancer avec couverture de code
python -m pytest tests/ --cov=app --cov-report=term-missing

# Lancer un fichier de test spécifique
python -m pytest tests/test_auth.py -v

# Lancer un test spécifique
python -m pytest tests/test_products.py::test_filter_by_price -v
```

**Résultats actuels :**
- 60 tests passent
- Couverture : **92%** (requis : 70%)
- Durée : ~90 secondes

**Comment les tests fonctionnent-ils ?**  
Les tests utilisent **SQLite** (base de données en mémoire) au lieu de PostgreSQL. Chaque test repart d'une base vide. Pas besoin de Docker pour lancer les tests.

---

## Variables d'environnement

Copier `.env.example` en `.env` et remplir les valeurs :

```bash
# URL de connexion à PostgreSQL
DATABASE_URL=postgresql://shopuser:shoppassword@localhost:5432/ecommerce_db

# Clé secrète pour signer les JWT (générer avec : openssl rand -hex 32)
SECRET_KEY=changeme-generate-with-openssl-rand-hex-32

# Algorithme JWT
ALGORITHM=HS256

# Durée de vie de l'access token (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Durée de vie du refresh token (jours)
REFRESH_TOKEN_EXPIRE_DAYS=7

# Environnement (development, production, test)
ENVIRONMENT=development
```

> **Ne jamais committer le fichier `.env`** — il est dans `.gitignore`

---

*ShopAPI : Projet 20 ESGIS Master 1 - 2025-2026*
