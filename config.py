import os
from dotenv import load_dotenv

# --- Constantes de configuración ---
load_dotenv()

VERSION = "1.0.0"
IS_DEV = os.getenv("NODE_ENV") == "development"
IS_COMMUNITY_VERSION = os.getenv("IS_COMMUNITY_VERSION") == "true"
ROOT_PATH = os.environ.get("ROOT_PATH", "")
DEBRID_API_KEY = os.getenv('DEBRID_API_KEY')

ADMIN_PATH_DB_ENCRYPTED = os.getenv("ADMIN_PATH_DB_ENCRYPTED")
ADMIN_PATH_DB_DECRYPTED = os.getenv("ADMIN_PATH_DB_DECRYPTED")
ADMIN_PATH_RESTART = os.getenv("ADMIN_PATH_RESTART")

# --- Constantes de archivos y URLs ---
DB_PATH_PREFIX = "/tmp/" if not IS_DEV else ""

DB_ENCRYPTED_PATH = f"{DB_PATH_PREFIX}MiPal2025-main/92b33381-pl3-42a1-bee0-bbb9d132e83f.tmp"
DB_DECRYPTED_PATH = f"{DB_PATH_PREFIX}MiPal2025-main/bd.tmp"
UPDATE_LOG_FILE = f"{DB_PATH_PREFIX}actualizar.txt"
VERSION_FILE = f"{DB_PATH_PREFIX}version.txt"


PING_URL = 'https://addonespanol.onrender.com/'
RENDER_API_URL = "https://api.render.com/v1/services/srv-csr7761u0jms73cjf0t0/deploys"
RENDER_AUTH_HEADER = f"Bearer {os.getenv('RENDER_API_KEY')}"

