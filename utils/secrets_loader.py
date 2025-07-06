import subprocess
import json
import os
import sys
from getpass import getpass

_secrets = None

def load_secrets():
    """
    Solicita la clave privada de age, descifra secrets.json usando sops
    y carga los secretos en una variable global en memoria.
    """
    global _secrets
    if _secrets is not None:
        return _secrets

    try:
        age_key = getpass("Introduce la clave privada de AGE (SOPS_AGE_KEY): ")

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

    except FileNotFoundError:
        print("❌ Error: El comando 'sops' no se encontró. Asegúrate de que esté instalado y en el PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al descifrar los secretos. Clave incorrecta o archivo corrupto.", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("❌ Error: No se pudo decodificar el JSON de los secretos descifrados.", file=sys.stderr)
        sys.exit(1)

def get_secret(key, default=None):
    """
    Obtiene un secreto específico del diccionario cargado en memoria.
    """
    if _secrets is None:
        raise Exception("Los secretos no han sido cargados. Llama a load_secrets() primero.")
    return _secrets.get(key, default)