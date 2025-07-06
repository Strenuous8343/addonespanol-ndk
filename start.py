import os
import subprocess
import getpass
import sys

def main():
    """
    Script lanzador para Uvicorn que solicita una clave secreta de forma segura
    y la pasa a los workers a través de una variable de entorno.
    """
    print("Se requiere la clave privada de AGE para iniciar el servidor.")
    
    try:
        age_key = getpass.getpass("Introduce la clave privada de AGE (SOPS_AGE_KEY): ")
        if not age_key:
            print("No se introdujo ninguna clave. Abortando.", file=sys.stderr)
            sys.exit(1)

    except (EOFError, KeyboardInterrupt):
        print("\nInicio cancelado por el usuario.")
        sys.exit(1)

    env = os.environ.copy()
    env["SOPS_AGE_KEY"] = age_key

    command = [
        sys.executable,
        "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--workers", "8"
    ]

    print("\nIniciando servidor Uvicorn con 8 workers...")
    
    try:
        subprocess.run(command, env=env)
    except FileNotFoundError:
        print(f"Error: No se pudo encontrar el comando '{command[0]}'. ¿Está Python en el PATH?", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServidor detenido.")

if __name__ == "__main__":
    main()