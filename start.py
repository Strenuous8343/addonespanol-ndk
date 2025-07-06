import os
import getpass
import sys
import uvicorn

def main():
    """
    Script lanzador que solicita una clave de forma segura y ejecuta
    Uvicorn mediante programación.
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

    os.environ["SOPS_AGE_KEY"] = age_key

    print("\nIniciando servidor Uvicorn con 8 workers...")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        workers=8
    )

if __name__ == "__main__":
    main()