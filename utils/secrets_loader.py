import subprocess
import json
import os
import sys

_secrets = None

def load_secrets():
    """
    Carga la clave privada de age desde la variable de entorno SOPS_AGE_KEY,
    descifra secrets.json usando sops y carga los secretos en memoria.
    """
    global _secrets
    if _secrets is not None:
        return _secrets

    age_key = os.environ.get("SOPS_AGE_KEY")

    if not age_key:
        print("❌ Error: La variable de entorno 'SOPS_AGE_KEY' no está definida.", file=sys.stderr)
        print("Este script debe ser ejecutado a través de 'start.py'.", file=sys.stderr)
        sys.exit(1)

    try:
        env = os.environ.copy()
        env["SOPS_AGE_KEY"] = age_key.strip()

        result = subprocess.run(
            ['sops', '-d', 'secrets.json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        _secrets = json.loads(result.stdout)
        print("✅ Secretos cargados en memoria correctamente.")
        return _secrets
    except Exception as e:
        print(f"❌ Ocurrió un error al cargar los secretos: {e}", file=sys.stderr)
        sys.exit(1)


def get_secret(key, default=None):
    if _secrets is None:
        load_secrets()
    return _secrets.get(key, default)