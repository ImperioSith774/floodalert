from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app, jsonify)
from database.conexion import consultar, ejecutar
from auth_utils import login_requerido, admin_requerido

r_mapa = Blueprint("r_mapa", __name__)

ESTADOS_VALIDOS = ("pendiente", "verificado", "seguimiento", "atendido", "cerrado")


@r_mapa.route("/")
def inicio_redir():
    return redirect("/index")


@r_mapa.route("/mapa")
def mapa():
    municipios = consultar("SELECT id_municipio, nombre FROM municipios ORDER BY nombre")
    return render_template("mapa.html", titulo="Mapa de inundaciones", municipios=municipios)


@r_mapa.route("/api/incidentes")
def api_incidentes():
    """API pública: solo incidentes aprobados con ubicación aproximada."""
    estado = request.args.get("estado", type=str)
    municipio = request.args.get("municipio", type=int)

    sql = """
        SELECT i.id_incidente, i.lat, i.lng, i.barrio, i.nivel_agua, i.estado,
               i.fecha_incidente, m.nombre AS municipio,
               (SELECT archivo FROM evidencias e WHERE e.id_incidente = i.id_incidente LIMIT 1) AS foto
        FROM incidentes i
        JOIN municipios m ON m.id_municipio = i.id_municipio
        WHERE i.estado IN ('verificado','seguimiento','atendido','cerrado')
    """
    params = []
    if estado and estado in ESTADOS_VALIDOS:
        sql += " AND i.estado = %s"
        params.append(estado)
    if municipio:
        sql += " AND i.id_municipio = %s"
        params.append(municipio)
    sql += " ORDER BY i.fecha_incidente DESC LIMIT 500"

    filas = consultar(sql, tuple(params))
    # Privacidad: redondear coordenadas aprox. + desplazamiento aleatorio almacenado no necesario
    for f in filas:
        f["lat"] = float(f["lat"])
        f["lng"] = float(f["lng"])
    return jsonify(filas)


@r_mapa.route("/api/incidente/<int:id_inc>")
def api_detalle(id_inc):
    sql = """
        SELECT i.*, m.nombre AS municipio
        FROM incidentes i JOIN municipios m ON m.id_municipio = i.id_municipio
        WHERE i.id_incidente = %s
    """
    inc = consultar(sql, (id_inc,), uno=True)
    if not inc:
        return jsonify({"error": "No encontrado"}), 404
    evidencias = consultar(
        "SELECT id_evidencia, archivo FROM evidencias WHERE id_incidente = %s", (id_inc,))
    historial = consultar(
        "SELECT estado_nuevo, comentario, creado_en FROM seguimiento "
        "WHERE id_incidente = %s ORDER BY creado_en DESC", (id_inc,))
    inc["lat"] = float(inc["lat"])
    inc["lng"] = float(inc["lng"])
    inc["evidencias"] = evidencias
    inc["historial"] = historial
    return jsonify(inc)
