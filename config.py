import os
from utils.secrets_loader import load_secrets, get_secret

# --- Constantes de configuración ---
load_secrets()

VERSION = "1.0.0"
IS_DEV = os.getenv("NODE_ENV") == "development"
IS_COMMUNITY_VERSION = os.getenv("IS_COMMUNITY_VERSION") == "true"

ROOT_PATH = os.environ.get("ROOT_PATH", "")

DEBRID_API_KEY = get_secret('DEBRID_API_KEY')
FICHIER_API_KEY = get_secret('FICHIER_API_KEY')
ENCRYPTION_KEY_B64 = get_secret('ENCRYPTION_KEY_B64')
ZIP_DECODE_BASE64 = get_secret('ZIP_DECODE_BASE64')
ADMIN_PATH_DB_ENCRYPTED = get_secret("ADMIN_PATH_DB_ENCRYPTED")
ADMIN_PATH_DB_DECRYPTED = get_secret("ADMIN_PATH_DB_DECRYPTED")
ADMIN_PATH_RESTART = get_secret("ADMIN_PATH_RESTART")
RENDER_API_KEY = get_secret('RENDER_API_KEY')
RENDER_DEPLOY_HOOK = get_secret("RENDER_DEPLOY_HOOK")

# --- Constantes de archivos y URLs ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH_PREFIX = "tmp" if not IS_DEV else ""
WORKING_PATH = os.path.join(BASE_DIR, DB_PATH_PREFIX)

DB_ENCRYPTED_PATH = os.path.join(WORKING_PATH, "Mipal2025-main", "92b33381-pl3-42a1-bee0-bbb9d132e83f.tmp")
DB_DECRYPTED_PATH = os.path.join(WORKING_PATH, "Mipal2025-main", "bd.tmp")
UPDATE_LOG_FILE = os.path.join(WORKING_PATH, "actualizar.txt")
VERSION_FILE = os.path.join(WORKING_PATH, "version.txt")


PING_URL = 'https://addonespanol.onrender.com/'
RENDER_API_URL = RENDER_DEPLOY_HOOK
RENDER_AUTH_HEADER = f"Bearer {RENDER_API_KEY}"

