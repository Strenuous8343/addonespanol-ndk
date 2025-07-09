import os
import getpass
import sys
import uvicorn
import subprocess
import json

def main():
    """
    Script lanzador para el primer arranque. Pide la clave de SOPS,
    la usa para descifrar los secretos y los carga en una variable de entorno
    antes de iniciar Uvicorn.
    """
    # Esta variable de entorno contendrá los secretos y se pasará en los reinicios.
    DECRYPTED_SECRETS_VAR = "DECRYPTED_SECRETS"

    if DECRYPTED_SECRETS_VAR in os.environ:
        print("Los secretos ya están cargados en el entorno. Iniciando servidor...")
    else:
        print("Se requiere la clave privada de AGE para el primer inicio.")
        try:
            age_key = getpass.getpass("Introduce la clave privada de AGE (SOPS_AGE_KEY): ")
            if not age_key:
                print("No se introdujo ninguna clave. Abortando.", file=sys.stderr)
                sys.exit(1)
            
            # Descifrar secretos usando sops y la clave proporcionada
            env = os.environ.copy()
            env["SOPS_AGE_KEY"] = age_key.strip()
            result = subprocess.run(
                ['sops', '-d', 'secrets.json'],
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            
            # Cargar los secretos descifrados en la variable de entorno
            os.environ[DECRYPTED_SECRETS_VAR] = result.stdout
            print("✅ Secretos descifrados y cargados en el entorno de la aplicación.")

        except FileNotFoundError:
            print("❌ Error: El comando 'sops' no se encontró. Asegúrate de que esté instalado y en el PATH.", file=sys.stderr)
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"❌ Ocurrió un error al descifrar los secretos con sops: {e.stderr}", file=sys.stderr)
            sys.exit(1)
        except (EOFError, KeyboardInterrupt):
            print("\nInicio cancelado por el usuario.")
            sys.exit(1)

    print("\nIniciando servidor Uvicorn...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        lifespan="on"
    )

if __name__ == "__main__":
    main()