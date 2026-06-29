# Guide de Déploiement : A à Z

> **VPS :** Hostinger KVM4 - Ubuntu 22.04 - 4 vCPU - 16 GB RAM - 160 GB NVMe  
> **Projet :** ShopAPI (Projet 20 )

---

## Table des matières

1. [Vue d'ensemble du déploiement](#vue-densemble-du-déploiement)
2. [Étape 0 : Prérequis locaux](#étape-0--prérequis-locaux)
3. [Étape 1 : Sécurisation initiale du VPS](#étape-1--sécurisation-initiale-du-vps)
4. [Étape 2 : Installation de Docker sur le VPS](#étape-2--installation-de-docker-sur-le-vps)
5. [Étape 3 : Nom de domaine (DuckDNS gratuit)](#étape-3--nom-de-domaine-duckdns-gratuit)
6. [Étape 4 : Installation de Nginx](#étape-4--installation-de-nginx)
7. [Étape 5 : Certificat HTTPS avec Let's Encrypt](#étape-5--certificat-https-avec-lets-encrypt)
8. [Étape 6 : Premier déploiement manuel](#étape-6--premier-déploiement-manuel)
9. [Étape 7 : Configuration GitHub Actions (CI/CD)](#étape-7--configuration-github-actions-cicd)
10. [Étape 8 : Monitoring Prometheus + Grafana](#étape-8--monitoring-prometheus--grafana)
11. [Étape 9 : Sauvegardes automatiques](#étape-9--sauvegardes-automatiques)
12. [Étape 10 : Alertes Discord/Telegram](#étape-10--alertes-discordtelegram)
13. [Plan de reprise d'activité (PRA)](#plan-de-reprise-dactivité-pra)
14. [Commandes utiles au quotidien](#commandes-utiles-au-quotidien)
15. [Résolution de problèmes fréquents](#résolution-de-problèmes-fréquents)

---

## Vue d'ensemble du déploiement

```
┌─────────────────────────────────────────────────────┐
│              CE QUI VA TOURNER SUR LE VPS            │
│                                                       │
│  Nginx (port 80/443) - géré par le système Ubuntu    │
│       ↓ proxy vers                                   │
│  Docker Compose :                                     │
│    ├── api         (FastAPI + Gunicorn) → port 8000   │
│    ├── db          (PostgreSQL)         → port 5432   │
│    ├── prometheus  (métriques)          → port 9090   │
│    └── grafana     (dashboards)         → port 3000   │
│                                                       │
│  Certbot (cron) : renouvellement SSL automatique      │
│  Cron backup : sauvegarde PostgreSQL quotidienne      │
└─────────────────────────────────────────────────────┘
```

**Pourquoi Nginx en dehors de Docker ?**  
Certbot (Let's Encrypt) fonctionne plus simplement quand Nginx est installé directement sur Ubuntu. Il modifie automatiquement les fichiers de config Nginx.

---

## Étape 0 : Prérequis locaux

Sur **ta machine Windows**, installe :

1. **Git** : https://git-scm.com/download/win
2. **SSH client** : déjà inclus dans Windows 10/11 (PowerShell ou CMD)
3. **VS Code** (optionnel) : pour éditer les fichiers

Vérifie que SSH fonctionne :
```powershell
ssh -V
# OpenSSH_for_Windows_9.x, ...
```

---

## Étape 1 : Sécurisation initiale du VPS

### 1.1 Première connexion (depuis ton PC Windows)

Hostinger t'a fourni une IP et un mot de passe root. Connecte-toi :

```powershell
# Remplace IP_DU_VPS par l'IP fournie par Hostinger
ssh root@IP_DU_VPS
# Accepte l'empreinte SSH (yes) et entre le mot de passe root
```

### 1.2 Créer un utilisateur non-root (bonne pratique de sécurité)

Il est dangereux de tout faire en root. On crée un utilisateur `deploy` :

```bash
# Sur le VPS (tu es connecté en root)

# Créer l'utilisateur
adduser deploy
# → Entrer un mot de passe fort
# → Appuyer sur Entrée pour les autres champs

# Donner les droits sudo (pour exécuter des commandes admin)
usermod -aG sudo deploy

# Vérifier
id deploy
# uid=1001(deploy) gid=1001(deploy) groups=1001(deploy),27(sudo)
```

### 1.3 Configurer l'authentification par clé SSH

L'authentification par clé est plus sécurisée que le mot de passe.

**Sur ton PC Windows (PowerShell) :**
```powershell
# Générer une paire de clés SSH (si tu n'en as pas déjà une)
ssh-keygen -t ed25519 -C "deploy@shopapi" -f "$env:USERPROFILE\.ssh\shopapi_deploy"
# → Appuie sur Entrée (pas de passphrase si tu veux l'utiliser dans GitHub Actions)

# Afficher la clé publique (à copier)
Get-Content "$env:USERPROFILE\.ssh\shopapi_deploy.pub"
# Exemple : ssh-ed25519 AAAAC3Nz... deploy@shopapi
```

**Sur le VPS :**
```bash
# Passer sur l'utilisateur deploy
su - deploy

# Créer le dossier .ssh
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Coller la clé publique (celle affichée sur ton PC)
nano ~/.ssh/authorized_keys
# → Coller la clé publique
# → Ctrl+X, Y, Entrée pour sauvegarder

chmod 600 ~/.ssh/authorized_keys
```

**Tester la connexion par clé (sur ton PC) :**
```powershell
ssh -i "$env:USERPROFILE\.ssh\shopapi_deploy" deploy@IP_DU_VPS
# Tu devrais être connecté SANS mot de passe
```

### 1.4 Désactiver la connexion root et le mot de passe SSH

```bash
# Sur le VPS, éditer la config SSH
sudo nano /etc/ssh/sshd_config

# Trouver et modifier ces lignes :
PermitRootLogin no          # Interdire connexion root
PasswordAuthentication no   # Interdire authentification par mot de passe
PubkeyAuthentication yes    # Garder l'auth par clé

# Sauvegarder (Ctrl+X, Y, Entrée)

# Redémarrer SSH
sudo systemctl restart sshd

# IMPORTANT : Ne ferme PAS ta session actuelle avant d'avoir testé !
# Ouvre un NOUVEAU terminal et teste :
# ssh -i ~/.ssh/shopapi_deploy deploy@IP_DU_VPS
```

### 1.5 Configurer le pare-feu UFW

UFW (Uncomplicated Firewall) est le pare-feu d'Ubuntu. On n'ouvre que les ports nécessaires :

```bash
# Réinitialiser les règles
sudo ufw reset

# Politique par défaut : bloquer tout entrant, autoriser tout sortant
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Autoriser SSH (TOUJOURS en premier pour ne pas se bloquer !)
sudo ufw allow 22/tcp comment 'SSH'

# Autoriser HTTP et HTTPS
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Activer le pare-feu
sudo ufw enable
# → Répondre "y"

# Vérifier les règles
sudo ufw status verbose
```

**Résultat attendu :**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    Anywhere    # SSH
80/tcp                     ALLOW IN    Anywhere    # HTTP
443/tcp                    ALLOW IN    Anywhere    # HTTPS
```

### 1.6 Mettre à jour le système

```bash
sudo apt update && sudo apt upgrade -y
sudo apt autoremove -y
```

---

## Étape 2 : Installation de Docker sur le VPS

Docker n'est pas installé par défaut sur Ubuntu. Voici la procédure officielle :

```bash
# 1. Installer les dépendances nécessaires
sudo apt install -y ca-certificates curl gnupg

# 2. Ajouter la clé GPG officielle de Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# 3. Ajouter le dépôt Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 4. Installer Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 5. Permettre à l'utilisateur deploy d'utiliser Docker sans sudo
sudo usermod -aG docker deploy

# 6. Démarrer Docker au démarrage du système
sudo systemctl enable docker
sudo systemctl start docker

# 7. SE DÉCONNECTER et se reconnecter pour que le groupe soit pris en compte
exit
ssh -i ~/.ssh/shopapi_deploy deploy@IP_DU_VPS

# 8. Vérifier
docker --version
# Docker version 26.x.x
docker compose version
# Docker Compose version v2.x.x
```

---

## Étape 3 : Nom de domaine (DuckDNS gratuit)

DuckDNS offre des sous-domaines gratuits (ex: `monprojet.duckdns.org`).

### 3.1 Créer un sous-domaine DuckDNS

1. Va sur https://www.duckdns.org
2. Connecte-toi avec ton compte Google/GitHub
3. Crée un domaine (ex: `shopapi-esgis.duckdns.org`)
4. Note le **token** affiché (tu en auras besoin)
5. Dans le champ "current ip", entre l'**IP de ton VPS** et clique "update ip"

### 3.2 Vérifier que le DNS pointe vers ton VPS

```powershell
# Sur ton PC Windows
nslookup shopapi-esgis.duckdns.org
# Doit retourner l'IP de ton VPS
```

### 3.3 Mise à jour automatique de l'IP (au cas où l'IP change)

```bash
# Sur le VPS, créer un cron pour mettre à jour DuckDNS toutes les 5 minutes
crontab -e
# → Sélectionner nano (option 1)

# Ajouter à la fin du fichier (remplacer TOKEN et DOMAINE) :
*/5 * * * * curl -s "https://www.duckdns.org/update?domains=VOTRE_DOMAINE&token=VOTRE_TOKEN&ip=" > /var/log/duckdns.log 2>&1

# Sauvegarder (Ctrl+X, Y, Entrée)
```

> **Note :** Hostinger KVM4 a généralement une IP fixe, donc ce cron est surtout une précaution.

---

## Étape 4 : Installation de Nginx

Nginx sera installé directement sur Ubuntu (pas dans Docker) pour simplifier la gestion SSL.

```bash
# Installer Nginx
sudo apt install -y nginx

# Démarrer et activer au démarrage
sudo systemctl enable nginx
sudo systemctl start nginx

# Vérifier
sudo systemctl status nginx
# Active: active (running)

# Tester depuis ton PC
curl http://IP_DU_VPS
# Doit retourner la page par défaut Nginx ("Welcome to nginx!")
```

### Créer la configuration Nginx pour l'API

```bash
# Créer le dossier pour les fichiers de validation Certbot
sudo mkdir -p /var/www/certbot

# Créer la config Nginx (pour HTTP d'abord, HTTPS après Certbot)
sudo nano /etc/nginx/sites-available/shopapi
```

**Coller ce contenu (remplacer VOTRE_DOMAINE) :**
```nginx
server {
    listen 80;
    server_name VOTRE_DOMAINE.duckdns.org;

    # Validation Certbot
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Proxy temporaire vers l'API (on ajoutera HTTPS après)
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Activer la configuration
sudo ln -s /etc/nginx/sites-available/shopapi /etc/nginx/sites-enabled/

# Supprimer la config par défaut
sudo rm /etc/nginx/sites-enabled/default

# Tester la config (cherche "syntax is ok")
sudo nginx -t

# Recharger Nginx
sudo systemctl reload nginx
```

---

## Étape 5 : Certificat HTTPS avec Let's Encrypt

```bash
# Installer Certbot et le plugin Nginx
sudo apt install -y certbot python3-certbot-nginx

# Obtenir un certificat (remplacer VOTRE_DOMAINE et TON_EMAIL)
sudo certbot --nginx -d VOTRE_DOMAINE.duckdns.org --email TON_EMAIL@gmail.com --agree-tos --non-interactive

# Certbot va automatiquement :
# 1. Vérifier que le domaine pointe vers ce serveur
# 2. Générer le certificat
# 3. Modifier /etc/nginx/sites-available/shopapi pour ajouter HTTPS
```

### Configurer le renouvellement automatique

Les certificats Let's Encrypt expirent après 90 jours. Certbot peut les renouveler automatiquement :

```bash
# Tester le renouvellement (dry-run = simulation)
sudo certbot renew --dry-run
# Si tout va bien : "Congratulations, all simulated renewals succeeded"

# Certbot a déjà ajouté un timer systemd, vérifions :
sudo systemctl status certbot.timer
# Active: active (waiting)

# Si le timer n'est pas là, ajouter un cron manuellement :
sudo crontab -e
# Ajouter :
0 3 * * * certbot renew --quiet && systemctl reload nginx
```

### Remplacer la config Nginx par la version production complète

```bash
# Copier la config de production depuis le repo
sudo cp /opt/shopapi/deploy/nginx/shopapi.conf /etc/nginx/sites-available/shopapi
# Puis éditer pour remplacer VOTRE_DOMAINE par le vrai domaine
sudo nano /etc/nginx/sites-available/shopapi

# Tester et recharger
sudo nginx -t && sudo systemctl reload nginx

# Vérifier HTTPS
curl https://VOTRE_DOMAINE.duckdns.org/health
# {"status":"healthy","version":"1.0.0","environment":"production"}
```

---

## Étape 6 : Premier déploiement manuel

### 6.1 Préparer le dossier projet sur le VPS

```bash
# Créer le dossier de déploiement
sudo mkdir -p /opt/shopapi
sudo chown deploy:deploy /opt/shopapi

# Cloner le repo
cd /opt/shopapi
git clone https://github.com/sbk6/projet_20_flask_fast_api_vps.git .
```

### 6.2 Créer le fichier .env de production

```bash
# Créer le fichier .env (NE PAS committer ce fichier !)
nano /opt/shopapi/.env
```

**Contenu du .env :**
```bash
# Base de données
POSTGRES_USER=shopuser
POSTGRES_PASSWORD=MOT_DE_PASSE_FORT_ICI
POSTGRES_DB=ecommerce_db
DATABASE_URL=postgresql://shopuser:MOT_DE_PASSE_FORT_ICI@db:5432/ecommerce_db

# JWT (générer avec : openssl rand -hex 32)
SECRET_KEY=CLEF_SECRETE_64_CARACTERES_ICI
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
ENVIRONMENT=production

# Grafana
GRAFANA_ADMIN_PASSWORD=MOT_DE_PASSE_GRAFANA_ICI
```

```bash
# Protéger le fichier (lisible seulement par deploy)
chmod 600 /opt/shopapi/.env
```

**Générer une SECRET_KEY sécurisée :**
```bash
openssl rand -hex 32
# Exemple : a3f8b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0
```

### 6.3 Construire et lancer l'application

```bash
cd /opt/shopapi

# Construire l'image Docker localement (première fois)
docker build -t ghcr.io/sbk6/projet_20_flask_fast_api_vps:latest .

# Lancer tous les services
docker compose -f deploy/docker-compose.prod.yml up -d

# Vérifier que tout tourne
docker compose -f deploy/docker-compose.prod.yml ps
```

**Résultat attendu :**
```
NAME                STATUS          PORTS
shopapi_db_1        running (healthy)
shopapi_api_1       running (healthy)
shopapi_prometheus_1 running
shopapi_grafana_1   running
```

### 6.4 Exécuter les migrations Alembic

```bash
# Créer les tables dans PostgreSQL
docker compose -f deploy/docker-compose.prod.yml exec api alembic upgrade head

# Vérifier
docker compose -f deploy/docker-compose.prod.yml exec api alembic current
```

### 6.5 Créer le premier compte admin

```bash
docker compose -f deploy/docker-compose.prod.yml exec api python -c "
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password
db = SessionLocal()
admin = User(
    email='admin@shopapi.com',
    username='admin',
    hashed_password=hash_password('MotDePasseAdmin123!'),
    role=UserRole.ADMIN,
    is_active=True
)
db.add(admin)
db.commit()
print('Admin créé avec succès !')
"
```

### 6.6 Tester que tout fonctionne

```bash
# Healthcheck
curl https://VOTRE_DOMAINE.duckdns.org/health

# Tester l'API
curl -X POST https://VOTRE_DOMAINE.duckdns.org/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@shopapi.com","password":"MotDePasseAdmin123!"}'
```

---

## Étape 7 : Configuration GitHub Actions (CI/CD)

Le pipeline CI/CD déploie automatiquement à chaque push sur `main`.

### 7.1 Configurer les secrets GitHub

Dans ton repo GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret** :

| Nom du secret | Valeur |
|--------------|--------|
| `VPS_HOST` | L'IP de ton VPS (ex: `123.456.789.0`) |
| `VPS_USER` | `deploy` |
| `VPS_SSH_KEY` | Contenu de la clé **privée** SSH (`shopapi_deploy`, pas `.pub`) |

**Pour récupérer la clé privée sur Windows :**
```powershell
Get-Content "$env:USERPROFILE\.ssh\shopapi_deploy"
# Copier TOUT le contenu (-----BEGIN OPENSSH PRIVATE KEY----- ... -----END OPENSSH PRIVATE KEY-----)
```

### 7.2 Autoriser le VPS à pull depuis ghcr.io

GitHub Container Registry (ghcr.io) est utilisé pour stocker l'image Docker.

```bash
# Sur le VPS, créer un Personal Access Token GitHub :
# GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
# Permissions nécessaires : read:packages

# Se connecter au registry sur le VPS
echo "VOTRE_GITHUB_TOKEN" | docker login ghcr.io -u sbk6 --password-stdin
# Login Succeeded
```

### 7.3 Tester le pipeline

```bash
# Sur ton PC, faire un commit sur main :
git add -A
git commit -m "test: trigger CI/CD pipeline"
git push origin main
```

Aller sur GitHub → **Actions** pour voir le pipeline s'exécuter.

**Durée typique :**
- Job 1 (Tests) : ~2 minutes
- Job 2 (Build Docker) : ~3-4 minutes
- Job 3 (Déploiement) : ~1 minute
- **Total : ~6-7 minutes**

### 7.4 Vérifier un déploiement automatique

Après un push, vérifier sur le VPS :

```bash
# L'image a été mise à jour ?
docker images | grep projet_20

# Les containers tournent ?
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml ps

# Les logs du déploiement ?
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml logs api --tail=20
```

---

## Étape 8 : Monitoring Prometheus + Grafana

### 8.1 Accéder à Grafana

Grafana tourne sur le port 3000 mais n'est pas exposé publiquement (sécurité). On utilise un tunnel SSH pour y accéder :

```powershell
# Sur ton PC Windows, créer un tunnel SSH
ssh -i "$env:USERPROFILE\.ssh\shopapi_deploy" -L 3000:127.0.0.1:3000 deploy@IP_DU_VPS -N
# Laisser cette fenêtre ouverte
```

Accéder à Grafana : http://localhost:3000  
Login : `admin` / (le mot de passe dans ton .env)

### 8.2 Configurer le dashboard FastAPI

1. Dans Grafana → **Dashboards** → **Import**
2. Entrer l'ID **`11074`** (dashboard FastAPI officiel)
3. Sélectionner la datasource Prometheus
4. Cliquer **Import**

Tu verras :
- Nombre de requêtes par seconde
- Latence (p50, p95, p99)
- Taux d'erreurs
- Requêtes actives

### 8.3 Accéder à Prometheus

```powershell
# Tunnel SSH pour Prometheus
ssh -i "$env:USERPROFILE\.ssh\shopapi_deploy" -L 9090:127.0.0.1:9090 deploy@IP_DU_VPS -N
```

Accéder à Prometheus : http://localhost:9090

Exemples de requêtes Prometheus (PromQL) :
```promql
# Nombre de requêtes par minute
rate(http_requests_total[1m])

# Latence moyenne
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])

# Taux d'erreurs 5xx
rate(http_requests_total{status_code=~"5.."}[5m])
```

---

## Étape 9 : Sauvegardes automatiques

Les sauvegardes quotidiennes de PostgreSQL sont stockées sur le même VPS puis transférées vers un stockage externe.

### 9.1 Script de sauvegarde

```bash
# Créer le dossier de sauvegardes
sudo mkdir -p /opt/shopapi/backups
sudo chown deploy:deploy /opt/shopapi/backups

# Créer le script de sauvegarde
nano /opt/shopapi/backup.sh
```

**Contenu du script :**
```bash
#!/bin/bash
# backup.sh — Sauvegarde PostgreSQL quotidienne

set -e

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/shopapi/backups"
BACKUP_FILE="$BACKUP_DIR/shopapi_$DATE.sql.gz"

# Charger les variables d'environnement
source /opt/shopapi/.env

echo "=== Sauvegarde du $DATE ==="

# Dump PostgreSQL compressé
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml exec -T db \
    pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > "$BACKUP_FILE"

echo "Sauvegarde créée : $BACKUP_FILE ($(du -sh $BACKUP_FILE | cut -f1))"

# Garder seulement les 7 dernières sauvegardes
ls -t $BACKUP_DIR/shopapi_*.sql.gz | tail -n +8 | xargs -r rm -f
echo "Anciennes sauvegardes nettoyées"

# OPTIONNEL : Transférer vers un bucket S3-compatible (ex: Backblaze B2)
# Décommenter si tu as un bucket S3 configuré :
# aws s3 cp "$BACKUP_FILE" "s3://ton-bucket/backups/$(basename $BACKUP_FILE)" \
#   --endpoint-url https://s3.eu-central-003.backblazeb2.com

echo "=== Sauvegarde terminée ==="
```

```bash
# Rendre le script exécutable
chmod +x /opt/shopapi/backup.sh

# Tester manuellement
/opt/shopapi/backup.sh

# Vérifier
ls -lh /opt/shopapi/backups/
```

### 9.2 Automatiser avec cron

```bash
crontab -e
# Ajouter (sauvegarde tous les jours à 2h du matin) :
0 2 * * * /opt/shopapi/backup.sh >> /var/log/shopapi_backup.log 2>&1
```

### 9.3 Restaurer une sauvegarde

```bash
# Lister les sauvegardes disponibles
ls -lh /opt/shopapi/backups/

# Restaurer une sauvegarde spécifique
BACKUP_FILE="/opt/shopapi/backups/shopapi_20250120_020000.sql.gz"

# Arrêter l'API (pour éviter les écritures pendant la restauration)
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml stop api

# Restaurer
zcat $BACKUP_FILE | docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml exec -T db \
    psql -U shopuser ecommerce_db

# Redémarrer l'API
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml start api
```

---

## Étape 10 : Alertes Discord/Telegram

### Option A : Alertes Discord via Webhook

**Créer un webhook Discord :**
1. Sur ton serveur Discord → Paramètres du canal → Intégrations → Webhooks
2. Créer un nouveau webhook → Copier l'URL

**Configurer une alerte dans Grafana :**
1. Grafana → **Alerting** → **Contact points** → New
2. Type : **Webhook**
3. URL : l'URL du webhook Discord
4. Template du message : `{ "content": "ALERTE ShopAPI : {{ .Message }}" }`

**Créer une règle d'alerte :**
1. Grafana → **Alerting** → **Alert rules** → New
2. Condition : CPU > 90% pendant 5 minutes
3. Condition 2 : Liveness check échoue (healthcheck)
4. Contact : Discord webhook

### Option B : Alertes Telegram via Bot

```bash
# 1. Créer un bot Telegram via @BotFather
# 2. Obtenir le TOKEN du bot
# 3. Obtenir le CHAT_ID (ID de ton groupe/canal)

# Script d'alerte simple
nano /opt/shopapi/alert.sh
```

```bash
#!/bin/bash
# alert.sh — Envoi d'alertes Telegram

BOT_TOKEN="VOTRE_BOT_TOKEN"
CHAT_ID="VOTRE_CHAT_ID"
MESSAGE=" ShopAPI ALERTE : $1"

curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
  -d "chat_id=$CHAT_ID&text=$MESSAGE"
```

```bash
chmod +x /opt/shopapi/alert.sh

# Tester
/opt/shopapi/alert.sh "Test d'alerte depuis le VPS"
```

**Script de monitoring automatique :**
```bash
nano /opt/shopapi/healthcheck.sh
```

```bash
#!/bin/bash
# healthcheck.sh — Vérifie l'API toutes les minutes

HEALTH_URL="http://127.0.0.1:8000/health"
LOG_FILE="/var/log/shopapi_health.log"

# Vérifier le healthcheck
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$HTTP_CODE" != "200" ]; then
    MSG="API ShopAPI inaccessible ! Code HTTP: $HTTP_CODE ($(date))"
    echo "$MSG" >> $LOG_FILE
    /opt/shopapi/alert.sh "$MSG"
fi
```

```bash
chmod +x /opt/shopapi/healthcheck.sh

# Lancer toutes les minutes
crontab -e
# Ajouter :
* * * * * /opt/shopapi/healthcheck.sh
```

---

## Plan de reprise d'activité (PRA)

> **Objectif :** Restaurer l'API sur un nouveau VPS en moins de 30 minutes.

### Scénario : VPS complètement perdu (panne matérielle, etc.)

```
TEMPS ESTIMÉ PAR ÉTAPE :
├── Créer nouveau VPS Hostinger      :  3 min
├── Sécurisation + UFW               :  5 min
├── Installer Docker                 :  3 min
├── Configurer DNS DuckDNS           :  2 min
├── Installer Nginx + Certbot        :  5 min
├── Cloner le repo + .env            :  2 min
├── Lancer docker-compose            :  3 min
├── Migrations + restauration backup :  5 min
├── Vérifier et tester               :  2 min
└── TOTAL ESTIMÉ                     : ~30 min
```

### Checklist PRA détaillée

#### Phase 1 : Nouveau VPS (0-5 min)
```bash
# 1. Créer un nouveau VPS Hostinger KVM4 Ubuntu 22.04
# 2. Mettre à jour le DNS DuckDNS avec la nouvelle IP
#    → Aller sur duckdns.org → changer l'IP

# 3. Première connexion
ssh root@NOUVELLE_IP_VPS

# 4. Créer l'utilisateur deploy + firewall
adduser deploy
usermod -aG sudo deploy
ufw allow 22,80,443/tcp
ufw enable
```

#### Phase 2 : Docker + Nginx (5-13 min)
```bash
# Installer Docker (commandes groupées pour aller vite)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker deploy

# Installer Nginx + Certbot
sudo apt install -y nginx certbot python3-certbot-nginx
```

#### Phase 3 : Application (13-25 min)
```bash
# Cloner le repo
sudo mkdir -p /opt/shopapi && sudo chown deploy:deploy /opt/shopapi
cd /opt/shopapi
git clone https://github.com/sbk6/projet_20_flask_fast_api_vps.git .

# Recréer le .env (avoir les variables mémorisées ou dans un gestionnaire de mots de passe)
nano .env   # Remplir avec les mêmes valeurs

# Pull l'image Docker
echo "GITHUB_TOKEN" | docker login ghcr.io -u sbk6 --password-stdin
docker pull ghcr.io/sbk6/projet_20_flask_fast_api_vps:latest

# Lancer les services
docker compose -f deploy/docker-compose.prod.yml up -d

# Restaurer la dernière sauvegarde
# (si la sauvegarde est sur S3 : aws s3 cp s3://bucket/latest.sql.gz .)
zcat backups/shopapi_DERNIERE.sql.gz | docker compose -f deploy/docker-compose.prod.yml exec -T db psql -U shopuser ecommerce_db
```

#### Phase 4 : HTTPS + vérification (25-30 min)
```bash
# Config Nginx
cp deploy/nginx/shopapi.conf /etc/nginx/sites-available/shopapi
# Éditer le domaine dans le fichier
sudo ln -s /etc/nginx/sites-available/shopapi /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Certbot
sudo certbot --nginx -d VOTRE_DOMAINE.duckdns.org --non-interactive --agree-tos -m TON_EMAIL

# Vérification finale
curl https://VOTRE_DOMAINE.duckdns.org/health
```

### Ce qu'il faut TOUJOURS garder en sécurité

Stocke ces informations dans un gestionnaire de mots de passe (Bitwarden, etc.) :

- [ ] IP et credentials Hostinger (panneau d'administration)
- [ ] Contenu complet du fichier `.env` (toutes les variables)
- [ ] Token DuckDNS
- [ ] Token GitHub (pour ghcr.io)
- [ ] Clé SSH privée `shopapi_deploy`
- [ ] URL du bucket S3 de sauvegarde + credentials

---

## Commandes utiles au quotidien

### Gestion des containers

```bash
# Voir l'état de tous les services
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml ps

# Voir les logs en temps réel
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml logs -f api

# Redémarrer l'API seulement
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml restart api

# Arrêter tout
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml down

# Redémarrer tout
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml up -d

# Utilisation des ressources
docker stats
```

### Mise à jour manuelle (sans CI/CD)

```bash
cd /opt/shopapi

# Récupérer le nouveau code
git pull origin main

# Reconstruire l'image
docker build -t ghcr.io/sbk6/projet_20_flask_fast_api_vps:latest .

# Redémarrer l'API avec la nouvelle image
docker compose -f deploy/docker-compose.prod.yml up -d --no-deps api

# Vérifier
curl http://127.0.0.1:8000/health
```

### Surveillance du VPS

```bash
# Utilisation CPU, RAM, disque
htop          # Interactif (installer : sudo apt install htop)
free -h       # RAM
df -h         # Disque

# Logs système
sudo journalctl -f                    # Tous les logs système
sudo journalctl -u nginx -f           # Logs Nginx
sudo journalctl -u docker -f          # Logs Docker

# Connexions réseau ouvertes
sudo ss -tlnp                         # Ports en écoute
```

### Base de données

```bash
# Se connecter à PostgreSQL
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml exec db psql -U shopuser ecommerce_db

# Requêtes utiles dans psql :
# \dt           → lister les tables
# \d products   → structure de la table products
# SELECT count(*) FROM orders;
# \q            → quitter

# Sauvegarde manuelle
/opt/shopapi/backup.sh
```

---

## Résolution de problèmes fréquents

### L'API ne répond pas

```bash
# 1. Vérifier les containers
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml ps

# 2. Voir les logs d'erreur
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml logs api --tail=50

# 3. Vérifier que Nginx fonctionne
sudo systemctl status nginx
sudo nginx -t

# 4. Vérifier les ports
sudo ss -tlnp | grep -E "80|443|8000"
```

### Erreur 502 Bad Gateway

Nginx reçoit la requête mais ne peut pas joindre l'API :

```bash
# L'API tourne-t-elle ?
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml ps api
# Si STATUS != "running (healthy)" → regarder les logs

# L'API écoute-t-elle sur le bon port ?
curl http://127.0.0.1:8000/health
```

### Erreur de base de données

```bash
# La DB est-elle en bonne santé ?
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml exec db pg_isready

# Voir les logs PostgreSQL
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml logs db --tail=30
```

### Certificat SSL expiré

```bash
# Renouveler manuellement
sudo certbot renew --force-renewal
sudo systemctl reload nginx
```

### Plus d'espace disque

```bash
# Voir ce qui prend de la place
df -h
du -sh /opt/shopapi/backups/    # Taille des backups
docker system df                 # Espace utilisé par Docker

# Nettoyer Docker
docker system prune -f           # Supprimer containers/images/networks inutilisés
docker image prune -af           # Supprimer toutes les images non utilisées
```

---

*Guide de déploiement : Projet 20 ESGIS Master 1 - 2025-2026*
