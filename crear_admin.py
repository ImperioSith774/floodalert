"""Crea/actualiza el usuario administrador. Ejecute: python crear_admin.py correo contraseña"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash
from database.conexion import ejecutar, consultar

if len(sys.argv) != 3:
    print("Uso: python crear_admin.py correo contraseña")
    sys.exit(1)

def crear(correo, contrasena):
    hash_nuevo = generate_password_hash(contrasena)
    existe = consultar("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,), uno=True)
    if existe:
        ejecutar("UPDATE usuarios SET contrasena_hash = %s, rol = 'administrador' WHERE correo = %s",
             (hash_nuevo, correo))
        print(f"Administrador actualizado: {correo}")
    else:
        ejecutar("INSERT INTO usuarios (nombre_completo, correo, contrasena_hash, rol) "
             "VALUES ('Administrador', %s, %s, 'administrador')", (correo, hash_nuevo))
        print(f"Administrador creado: {correo}")


if __name__ == '__main__':
    correo, contrasena = sys.argv[1], sys.argv[2]
    hash_nuevo = generate_password_hash(contrasena)
    existe = consultar("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,), uno=True)
    if existe:
        ejecutar("UPDATE usuarios SET contrasena_hash = %s, rol = 'administrador' WHERE correo = %s",
             (hash_nuevo, correo))
        print(f"Administrador actualizado: {correo}")
    else:
        ejecutar("INSERT INTO usuarios (nombre_completo, correo, contrasena_hash, rol) "
             "VALUES ('Administrador', %s, %s, 'administrador')", (correo, hash_nuevo))
        print(f"Administrador creado: {correo}")
