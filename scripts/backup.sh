#!/bin/bash
# Sauvegarde quotidienne PostgreSQL — ShopAPI
# Cron : 0 2 * * * /opt/shopapi/scripts/backup.sh >> /var/log/shopapi-backup.log 2>&1

set -e

BACKUP_DIR="/opt/shopapi/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ecommerce_db_$DATE.sql.gz"
RETENTION_DAYS=7

mkdir -p "$BACKUP_DIR"

echo "[$DATE] Debut de la sauvegarde..."

# Dump PostgreSQL compressé
docker compose -f /opt/shopapi/deploy/docker-compose.prod.yml exec -T db \
    pg_dump -U shopuser ecommerce_db | gzip > "$BACKUP_FILE"

echo "[$DATE] Sauvegarde creee : $BACKUP_FILE ($(du -sh "$BACKUP_FILE" | cut -f1))"

# Supprimer les sauvegardes de plus de 7 jours
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "[$DATE] Nettoyage : sauvegardes de plus de $RETENTION_DAYS jours supprimees"

# Lister les sauvegardes conservees
echo "[$DATE] Sauvegardes disponibles :"
ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null || echo "  Aucune sauvegarde"

echo "[$DATE] Sauvegarde terminee avec succes."
