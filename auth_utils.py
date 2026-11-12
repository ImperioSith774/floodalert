"""Guardianes de acceso: roles, sesiones y utilidades de seguridad."""
import re
import os
import secrets
from functools import wraps
from flask import session, redirect, url_for, flash, request, current_app
from werkzeug.security import generate_password_hash, check_password_hash


def hash_contrasena(contrasena):
    return generate_password_hash(contrasena)


def verificar_contrasena(contrasena, hash_almacenado):
    return check_password_hash(hash_almacenado, contrasena)


def login_requerido(f):
    @wraps(f)
    def envuelto(*args, **kwargs):
        if not session.get("usuario_id"):
            flash("Debes iniciar sesión para acceder.", "aviso")
            return redirect(url_for("r_usuarios.login", siguiente=request.path))
        return f(*args, **kwargs)
    return envuelto


def admin_requerido(f):
    @wraps(f)
    def envuelto(*args, **kwargs):
        if not session.get("usuario_id"):
            flash("Debes iniciar sesión para acceder.", "aviso")
            return redirect(url_for("r_usuarios.login", siguiente=request.path))
        if session.get("rol") != "administrador":
            flash("No tienes permisos para esta sección.", "error")
            return redirect(url_for("r_incidentes.index"))
        return f(*args, **kwargs)
    return envuelto


EXT_IMAGENES = {"png", "jpg", "jpeg", "webp"}


def validar_imagen(archivo):
    """Valida extensión, tamaño y contenido básico. Devuelve nombre seguro o None."""
    if not archivo or not archivo.filename:
        return None
    nombre = os.path.basename(archivo.filename)
    ext = nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""
    if ext not in EXT_IMAGENES:
        return None
    archivo.seek(0, os.SEEK_END)
    if archivo.tell() > current_app.config["MAX_FILE_SIZE"]:
        archivo.seek(0)
        return None
    archivo.seek(0)
    # Verificar cabecera (magic bytes)
    cabecera = archivo.read(16)
    archivo.seek(0)
    firmas = (b"\x89PNG", b"\xff\xd8\xff", b"RIFF")
    if not any(cabecera.startswith(f) for f in firmas):
        return None
    aleatorio = secrets.token_hex(8)
    return f"{aleatorio}.{ext}"


def validar_contrasena(contrasena):
    if len(contrasena) < 8:
        return False
    if not re.search(r"[A-Za-z]", contrasena) or not re.search(r"\d", contrasena):
        return False
    return True


def validar_correo(correo):
    return re.match(r"^[\w.+-]+@[\w-]+\.[\w.-]+$", correo or "") is not None
