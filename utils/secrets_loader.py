import json
import os
import sys

_secrets = None
DECRYPTED_SECRETS_VAR = "DECRYPTED_SECRETS"

def load_secrets():
    """
    Carga los secretos desde la variable de entorno 'DECRYPTED_SECRETS'.
    Esta variable es establecida por 'start.py' en el primer arranque.
    """
    global _secrets
    if _secrets is not None:
        return

    decrypted_json_string = os.environ.get(DECRYPTED_SECRETS_VAR)

    if not decrypted_json_string:
        print(f"❌ Error: La variable de entorno '{DECRYPTED_SECRETS_VAR}' no está definida.", file=sys.stderr)
        print("Este script debe ser ejecutado a través de 'start.py' en el primer inicio.", file=sys.stderr)
        sys.exit(1)
    
    try:
        _secrets = json.loads(decrypted_json_string)
        print("✅ Secretos cargados en memoria desde el entorno correctamente.")
    except json.JSONDecodeError as e:
        print(f"❌ Ocurrió un error al parsear los secretos desde el entorno: {e}", file=sys.stderr)
        sys.exit(1)


def get_secret(key, default=None):
    if _secrets is None:
        load_secrets()
    return _secrets.get(key, default)