import os
import sqlite3
import base64
from Crypto.Cipher import AES

# Cargar la cadena Base64 desde las variables de entorno
ENCRYPTION_KEY_B64 = os.getenv('ENCRYPTION_KEY_B64').encode('utf-8')
DECODED_KEY = base64.b64decode(ENCRYPTION_KEY_B64)

# Separar IV y clave
iv = DECODED_KEY[:16]
key = DECODED_KEY[16:]

def decrypt_link(encrypted_link):
    """
    Descifra un enlace cifrado con AES en modo OFB.

    Args:
        encrypted_link (str): El enlace cifrado y codificado en URL-safe Base64.

    Returns:
        str: El enlace descifrado en formato UTF-8.
    """
    encrypted_data = base64.urlsafe_b64decode(encrypted_link)
    cipher = AES.new(key, AES.MODE_OFB, iv)
    decrypted_bytes = cipher.decrypt(encrypted_data)
    return decrypted_bytes.decode('utf-8')

def decryptbd(db_path):
    """
    Descifra los enlaces en las tablas de la base de datos especificada.

    Args:
        db_path (str): La ruta al archivo de la base de datos SQLite.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        for table in ['enlaces_pelis', 'enlaces_series']:
            cursor.execute(f"SELECT rowid, link FROM {table} WHERE link LIKE 'btof%'")
            rows = cursor.fetchall()
            
            for rowid, link in rows:
                decrypted_link = decrypt_link(link)
                cursor.execute(f"UPDATE {table} SET link = ? WHERE rowid = ?", (decrypted_link, rowid))
        
        conn.commit()
    finally:
        conn.close()