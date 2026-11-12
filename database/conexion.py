"""Capa de acceso a datos con SQLite3 (stdlib, sin servidor).

API pública (sin cambios respecto a la versión MySQL):
- ejecutar(consulta, parametros, obtener_id) -> id insertado o None
- consultar(consulta, parametros, uno) -> dict o lista de dicts

Internamente traduce los marcadores %s a ? y devuelve filas como
diccionarios para compatibilidad con las plantillas Jinja.
"""
import os
import re
import sqlite3
import datetime
from flask import current_app
from config import Config

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema_sqlite.sql")
_parametros_pattern = re.compile(r"%s")


def _inicializar_bd(conexion):
    """Crea tablas y datos semilla si la base está recién creada."""
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conexion.executescript(f.read())


def obtener_conexion():
    nueva = not os.path.exists(Config.SQLITE_PATH) or os.path.getsize(Config.SQLITE_PATH) == 0
    conexion = sqlite3.connect(
        Config.SQLITE_PATH,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    )
    conexion.row_factory = _fila_dict
    conexion.execute("PRAGMA foreign_keys = ON")
    if nueva:
        _inicializar_bd(conexion)
    return conexion


def _fila_dict(cursor, fila):
    """Convierte cada fila en un diccionario {columna: valor}."""
    return {col[0]: valor for col, valor in zip(cursor.description, fila)}


def _adaptar_parametros(parametros):
    adapta = []
    for p in parametros:
        if isinstance(p, datetime.datetime):
            adapta.append(p.strftime("%Y-%m-%d %H:%M:%S"))
        elif isinstance(p, datetime.date):
            adapta.append(p.strftime("%Y-%m-%d"))
        else:
            adapta.append(p)
    return tuple(adapta)


def ejecutar(consulta, parametros=(), obtener_id=False):
    """Ejecuta INSERT/UPDATE/DELETE de forma segura (parametrizada)."""
    sql = _parametros_pattern.sub("?", consulta)
    conexion = obtener_conexion()
    try:
        cursor = conexion.execute(sql, _adaptar_parametros(parametros))
        conexion.commit()
        nuevo_id = cursor.lastrowid if obtener_id else None
        cursor.close()
        return nuevo_id
    except sqlite3.Error as e:
        conexion.rollback()
        _log_error(e)
        raise
    finally:
        conexion.close()


def consultar(consulta, parametros=(), uno=False):
    """Ejecuta SELECT de forma segura. Devuelve dict o lista de dicts."""
    sql = _parametros_pattern.sub("?", consulta)
    conexion = obtener_conexion()
    try:
        cursor = conexion.execute(sql, _adaptar_parametros(parametros))
        resultado = cursor.fetchone() if uno else cursor.fetchall()
        cursor.close()
        return dict(resultado) if (uno and resultado) else resultado
    except sqlite3.Error as e:
        _log_error(e)
        raise
    finally:
        conexion.close()


def _log_error(e):
    try:
        current_app.logger.error("Error SQL: %s", e)
    except RuntimeError:
        print("Error SQL:", e)
