# Configuration Gunicorn pour la production
# Ce fichier est utilisé quand on lance gunicorn sans Docker (systemd)

import multiprocessing

# Adresse d'écoute
bind = "0.0.0.0:8000"

# Nombre de workers : règle = 2 * CPU + 1
# Pour un VPS 4 vCPU : 2*4+1 = 9 workers
workers = multiprocessing.cpu_count() * 2 + 1

# Type de worker : UvicornWorker pour FastAPI (async)
worker_class = "uvicorn.workers.UvicornWorker"

# Timeout d'une requête (secondes)
timeout = 120

# Keep-alive HTTP
keepalive = 5

# Logs
accesslog = "-"   # stdout
errorlog = "-"    # stderr
loglevel = "info"

# Redémarrage automatique si un worker dépasse cette limite mémoire (octets)
max_requests = 1000
max_requests_jitter = 50

# PID file (pour systemd)
pidfile = "/tmp/gunicorn.pid"
