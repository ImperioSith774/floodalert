from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app)
import os
from database.conexion import consultar, ejecutar
from auth_utils import admin_requerido, validar_imagen

r_admin = Blueprint("r_admin", __name__)

NOMBRES_ESTADO = {
    "pendiente": "Pendiente de revisión",
    "verificado": "Verificado",
    "seguimiento": "En seguimiento",
    "atendido": "Atendido",
    "cerrado": "Cerrado",
    "rechazado": "Rechazado",
}


@r_admin.route("/admin/dashboard")
@admin_requerido
def dashboard():
    stats = {
        "total": consultar("SELECT COUNT(*) n FROM incidentes", uno=True)["n"],
        "pendientes": consultar("SELECT COUNT(*) n FROM incidentes WHERE estado='pendiente'", uno=True)["n"],
        "semana": consultar("SELECT COUNT(*) n FROM incidentes WHERE creado_en >= DATETIME('now', '-7 days')", uno=True)["n"],
        "usuarios": consultar("SELECT COUNT(*) n FROM usuarios WHERE activo=1", uno=True)["n"],
        "denuncias": consultar("SELECT COUNT(*) n FROM denuncias", uno=True)["n"],
    }
    por_municipio = consultar("""
        SELECT m.nombre, COUNT(i.id_incidente) n FROM municipios m
        LEFT JOIN incidentes i ON i.id_municipio = m.id_municipio
        GROUP BY m.id_municipio ORDER BY n DESC LIMIT 8""")
    por_estado = consultar("SELECT estado, COUNT(*) n FROM incidentes GROUP BY estado")
    estados = {p["estado"]: p["n"] for p in por_estado}
    pendientes = consultar("""
        SELECT i.*, m.nombre AS municipio, u.nombre_completo AS reportador,
          (SELECT archivo FROM evidencias e WHERE e.id_incidente = i.id_incidente LIMIT 1) AS foto,
          (SELECT COUNT(*) FROM denuncias d WHERE d.id_incidente = i.id_incidente) AS denuncias
        FROM incidentes i
        JOIN municipios m ON m.id_municipio = i.id_municipio
        JOIN usuarios u ON u.id_usuario = i.id_usuario
        WHERE i.estado = 'pendiente'
        ORDER BY i.creado_en ASC""")
    return render_template("admin/dashboard.html", titulo="Panel administrativo",
                           stats=stats, por_municipio=por_municipio, estados=estados,
                           pendientes=pendientes,
                           nombres_estado=NOMBRES_ESTADO)


@r_admin.route("/admin/revisiones")
@admin_requerido
def reportes():
    estado = request.args.get("estado", "")
    municipio = request.args.get("municipio", "")
    q = request.args.get("q", "").strip()

    sql = """
        SELECT i.*, m.nombre AS municipio, u.nombre_completo AS reportador,
          (SELECT archivo FROM evidencias e WHERE e.id_incidente = i.id_incidente LIMIT 1) AS foto,
          (SELECT COUNT(*) FROM denuncias d WHERE d.id_incidente = i.id_incidente) AS denuncias
        FROM incidentes i
        JOIN municipios m ON m.id_municipio = i.id_municipio
        JOIN usuarios u ON u.id_usuario = i.id_usuario
        WHERE 1=1
    """
    params = []
    if estado in NOMBRES_ESTADO:
        sql += " AND i.estado = %s"
        params.append(estado)
    if municipio:
        sql += " AND i.id_municipio = %s"
        params.append(municipio)
    if q:
        sql += " AND (i.barrio LIKE %s OR i.descripcion LIKE %s)"
        params += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY i.creado_en DESC LIMIT 200"

    filas = consultar(sql, tuple(params))
    municipios = consultar("SELECT id_municipio, nombre FROM municipios ORDER BY nombre")
    return render_template("admin/reportes.html", titulo="Gestión de reportes",
                           reportes=filas, municipios=municipios,
                           estado=estado, municipio=municipio, q=q,
                           nombres_estado=NOMBRES_ESTADO)


def _registrar_cambio(id_inc, nuevo_estado, comentario):
    ejecutar(
        """INSERT INTO seguimiento (id_incidente, id_admin, estado_nuevo, comentario)
           VALUES (%s,%s,%s,%s)""",
        (id_inc, session["usuario_id"], nuevo_estado, comentario or None))


@r_admin.route("/admin/reportes/<int:id_inc>/estado", methods=["POST"])
@admin_requerido
def cambiar_estado(id_inc):
    nuevo_estado = request.form.get("estado", "")
    comentario = request.form.get("comentario", "").strip()[:500]
    if nuevo_estado not in NOMBRES_ESTADO:
        flash("Estado inválido.", "error")
        return redirect(url_for("r_admin.reportes"))
    actualizar = ejecutar("UPDATE incidentes SET estado = %s WHERE id_incidente = %s",
                          (nuevo_estado, id_inc))
    _registrar_cambio(id_inc, nuevo_estado, comentario)
    flash(f"Reporte actualizado a «{NOMBRES_ESTADO[nuevo_estado]}».", "exito")
    destino = request.referrer
    if destino and "/admin/revisiones" in destino:
        return redirect(destino)
    return redirect(url_for("r_admin.reportes"))


@r_admin.route("/admin/usuarios")
@admin_requerido
def usuarios():
    filas = consultar(
        "SELECT id_usuario, nombre_completo, correo, rol, activo, creado_en "
        "FROM usuarios ORDER BY creado_en DESC")
    return render_template("admin/usuarios.html", titulo="Gestión de usuarios", usuarios=filas)


@r_admin.route("/admin/usuarios/<int:id_usuario>/rol", methods=["POST"])
@admin_requerido
def cambiar_rol(id_usuario):
    nuevo_rol = request.form.get("rol", "")
    if nuevo_rol not in ("ciudadano", "administrador"):
        flash("Rol inválido.", "error")
    elif id_usuario == session["usuario_id"]:
        flash("No puedes cambiar tu propio rol.", "error")
    else:
        ejecutar("UPDATE usuarios SET rol = %s WHERE id_usuario = %s", (nuevo_rol, id_usuario))
        flash("Rol actualizado.", "exito")
    return redirect(url_for("r_admin.usuarios"))


@r_admin.route("/admin/usuarios/<int:id_usuario>/activo", methods=["POST"])
@admin_requerido
def cambiar_activo(id_usuario):
    if id_usuario == session["usuario_id"]:
        flash("No puedes desactivar tu propia cuenta.", "error")
        return redirect(url_for("r_admin.usuarios"))
    usuario = consultar("SELECT activo FROM usuarios WHERE id_usuario = %s", (id_usuario,), uno=True)
    if usuario:
        ejecutar("UPDATE usuarios SET activo = %s WHERE id_usuario = %s",
                 (0 if usuario["activo"] else 1, id_usuario))
        flash("Cuenta actualizada.", "exito")
    return redirect(url_for("r_admin.usuarios"))
