import os
import io
import re
import json
import base64
import zipfile
import shutil
import hashlib
import sqlite3
import requests
import xml.etree.ElementTree as ET
from urllib import parse
from threading import Lock
from utils.bd import add_flag
from utils.crypt import decryptbd
from utils.logger import setup_logger

from config import (
    DB_ENCRYPTED_PATH,
    DB_DECRYPTED_PATH,
    VERSION_FILE,
    DB_PATH_PREFIX
)

logger = setup_logger(__name__)

BASE_DIR = DB_PATH_PREFIX
REPO_URL = 'https://github.com/Maniac2017/Mipal2025.git'
REPO_DIR = os.path.join(BASE_DIR, 'Mipal2025-main')
VERSION_FILE = os.path.join(REPO_DIR, 'version.txt')
db_lock = Lock()

def clone_or_update_repo():
    """
    Descarga la última versión del repositorio desde GitHub como un archivo ZIP y la extrae.
    """
    zip_url = REPO_URL.replace('.git', '/archive/refs/heads/main.zip')
    logger.info("Descargando ZIP del repositorio...")
    resp = requests.get(zip_url, timeout=120)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content), 'r') as z:
        z.extractall(BASE_DIR)
    logger.info(f"Repositorio descomprimido en '{REPO_DIR}'")

def download_and_process_file(url_or_path):
    """
    Descarga (o lee localmente) un archivo, lo combina con datos decodificados de Base64
    para formar un ZIP, lo extrae y renombra el archivo 'settings.xml' resultante.

    Args:
        url_or_path (str): URL para descargar el archivo o ruta local para leerlo.

    Returns:
        bool: True si el procesamiento fue exitoso, False en caso contrario.
    """
    if os.path.isfile(url_or_path):
        with open(url_or_path, 'rb') as f:
            content = f.read()
    else:
        response = requests.get(url_or_path, timeout=120)
        response.raise_for_status()
        content = response.content

    zip_header_b64 = os.getenv('ZIP_DECODE_BASE64')
    decoded_data = base64.b64decode(zip_header_b64) + content
    
    with zipfile.ZipFile(io.BytesIO(decoded_data), 'r') as zfile:
        zfile.extractall(REPO_DIR)
        logger.info(f"Archivos extraídos en: {os.path.abspath(REPO_DIR)}")
        
    old_file = os.path.join(REPO_DIR, 'settings.xml')
    new_file = os.path.join(REPO_DIR, '92b33381-pl3-42a1-bee0-bbb9d132e83f.tmp')
    
    if os.path.exists(old_file):
        shutil.move(old_file, new_file)
        logger.info(f"Archivo renombrado a: {os.path.abspath(new_file)}")
        return True
    
    logger.warning("El archivo settings.xml no se encontró en el ZIP.")
    return False

def add_flag_to_inserts(up_content):
    """
    Añade columnas adicionales ('FLAG', 'enlace_modificado') a las sentencias
    INSERT de SQL para compatibilidad con la base de datos.

    Args:
        up_content (str): El contenido del script SQL.

    Returns:
        str: El script SQL modificado.
    """
    pattern = r"(INSERT OR REPLACE INTO (enlaces_pelis|enlaces_series)[^;]*\);)"
    def add_flag(match):
        original = match.group(0)
        if original.endswith(");"):
            return original[:-2] + ", 0, '');"
        return original
    return re.sub(pattern, add_flag, up_content)

def p3b64decode_exacto(encoded_text):
    """
    Decodifica un texto usando un algoritmo Base64 modificado específico.
    El proceso incluye decodificación de URL, eliminación de '?', adición de padding
    y una transformación de inversión por partes antes de la decodificación Base64 final.

    Args:
        encoded_text (str or bytes): El texto codificado.

    Returns:
        bytes: Los datos decodificados.
    """
    if not isinstance(encoded_text, bytes):
        decoded_bytes = parse.unquote(encoded_text).encode('utf-8')
    else:
        decoded_bytes = parse.unquote(encoded_text.decode('utf-8')).encode('utf-8')

    decoded_bytes = re.sub(rb'\?', b'', decoded_bytes)
    current_len = len(decoded_bytes)
    missing_padding = (4 - current_len % 4) % 4
    padding = b'=' * missing_padding
    
    padded_len = current_len + missing_padding
    split_point = padded_len // 4
    
    part1 = decoded_bytes[:split_point]
    part2 = decoded_bytes[split_point:]
    
    transformed_bytes = part1[::-1] + part2[::-1]
    final_to_decode = transformed_bytes + padding
    
    return base64.b64decode(final_to_decode)

def process_up_file(url_or_path):
    """
    Procesa un archivo '.up', decodificándolo, modificando su contenido SQL
    y ejecutándolo contra la base de datos.

    Args:
        url_or_path (str): URL o ruta local del archivo '.up'.

    Returns:
        bool: True si el procesamiento fue exitoso, False en caso contrario.
    """
    if os.path.isfile(url_or_path):
        with open(url_or_path, 'r', encoding='utf-8') as f:
            up_content_encoded = f.read()
    else:
        response = requests.get(url_or_path, timeout=120)
        response.raise_for_status()
        up_content_encoded = response.text

    try:
        decoded_bytes = p3b64decode_exacto(up_content_encoded)
        up_content = decoded_bytes.decode('utf-8')
        logger.info(f"Contenido de '{url_or_path}' decodificado con éxito.")
    except Exception as e:
        logger.error(f"Fallo CRÍTICO al decodificar '{url_or_path}': {e}", exc_info=True)
        return False

    final_sql_script = add_flag_to_inserts(up_content)
    db_file = os.path.join(REPO_DIR, '92b33381-pl3-42a1-bee0-bbb9d132e83f.tmp')
    
    with db_lock:
        try:
            conn = sqlite3.connect(db_file)
            conn.executescript(final_sql_script)
            conn.commit()
            logger.info(f"Archivo .up procesado e insertado: {url_or_path}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error de base de datos al procesar .up: {e}", exc_info=True)
            return False
        finally:
            if conn:
                conn.close()

def compute_hash(path, chunk_size=8192):
    """
    Calcula el hash SHA256 de un archivo.

    Args:
        path (str): Ruta al archivo.
        chunk_size (int): Tamaño de los bloques a leer.

    Returns:
        str: El hash hexadecimal del archivo.
    """
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            h.update(chunk)
    return h.hexdigest()

def check_and_download():
    """
    Verifica si hay nuevos commits en el repositorio de GitHub. Si los hay,
    descarga los cambios y procesa los archivos '.zm3' y '.up' que han sido modificados,
    asegurando procesar primero todos los '.zm3' y luego los '.up'.

    Returns:
        bool: True si se realizaron actualizaciones, False en caso contrario.
    """
    version_data = {}
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            try:
                version_data = json.load(f)
            except json.JSONDecodeError:
                logger.warning("El archivo version.txt está corrupto o vacío.")
                pass # Se continuará con un diccionario vacío

    resp = requests.get("https://github.com/Maniac2017/Mipal2025/commits/main.atom", timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    
    entry = root.find('{http://www.w3.org/2005/Atom}entry')
    if entry is None or entry.find('{http://www.w3.org/2005/Atom}id') is None:
        logger.error("No se encontró ID de commit en el feed.")
        return False

    commit_id = entry.find('{http://www.w3.org/2005/Atom}id').text
    commit_sha = commit_id.split('/')[-1]

    if commit_sha == version_data.get("last_commit"):
        logger.info("No hay nuevos commits. Nada que actualizar.")
        return False

    version_data["last_commit"] = commit_sha
    clone_or_update_repo()
    updated = False

    zm3_files = []
    up_files = []
    for fname in os.listdir(REPO_DIR):
        path = os.path.join(REPO_DIR, fname)
        if not os.path.isfile(path):
            continue
        if fname.endswith('.zm3'):
            zm3_files.append(fname)
        elif '.up' in fname:
            up_files.append(fname)

    zm3_files.sort()
    up_files.sort()

    # Procesar primero todos los archivos .zm3
    for fname in zm3_files:
        path = os.path.join(REPO_DIR, fname)
        current_hash = compute_hash(path)
        if version_data.get(fname) != current_hash:
            logger.info(f"Procesando .zm3: {fname}")
            if download_and_process_file(path):
                version_data[fname] = current_hash
                updated = True
                logger.info("Base de datos descargada.")
                logger.info("Descifrando base de datos...")
                add_flag(DB_ENCRYPTED_PATH)
                shutil.copy(DB_ENCRYPTED_PATH, DB_DECRYPTED_PATH)
                decryptbd(DB_DECRYPTED_PATH)
                logger.info("Base de datos descifrada.")
                
        else:
            logger.info(f"Sin cambios en {fname}")
            
    # Procesar después todos los archivos .up
    for fname in up_files:
        path = os.path.join(REPO_DIR, fname)
        current_hash = compute_hash(path)
        if version_data.get(fname) != current_hash:
            logger.info(f"Procesando .up: {fname}")
            if process_up_file(path):
                version_data[fname] = current_hash
                updated = True
        else:
            logger.info(f"Sin cambios en {fname}")

    with open(VERSION_FILE, 'w') as f:
        json.dump(version_data, f, indent=4)

    return updated