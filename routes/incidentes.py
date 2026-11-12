from datetime import datetime
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, current_app, send_from_directory,
                   jsonify)
import os
from database.conexion import consultar, ejecutar
from auth_utils import validar_imagen, login_requerido

r_incidentes = Blueprint("r_incidentes", __name__)

NIVELES = ("tobillo", "rodilla", "cintura", "pecho", "techo")


@r_incidentes.route("/index")
def index():
    resumen = {        "total": consultar("SELECT COUNT(*) n FROM incidentes", uno=True)["n"],
        "semana": consultar(
            "SELECT COUNT(*) n FROM incidentes WHERE creado_en >= DATETIME('now', '-7 days')", uno=True)["n"],
        "verificados": consultar(
            "SELECT COUNT(*) n FROM incidentes WHERE estado IN ('verificado','seguimiento')", uno=True)["n"],
        "municipios": consultar(
            "SELECT COUNT(DISTINCT id_municipio) n FROM incidentes", uno=True)["n"],
    }
    recientes = consultar("""
        SELECT i.*, m.nombre AS municipio,
          (SELECT archivo FROM evidencias e WHERE e.id_incidente = i.id_incidente LIMIT 1) AS foto
        FROM incidentes i JOIN municipios m ON m.id_municipio = i.id_municipio
        WHERE i.estado IN ('verificado','seguimiento','atendido','cerrado')
        ORDER BY i.creado_en DESC LIMIT 4""")
    return render_template("index.html", titulo="Inicio",
                           resumen=resumen, recientes=recientes)


@r_incidentes.route("/reportar", methods=["GET", "POST"])
@login_requerido
def reportar():
    municipios = consultar("SELECT * FROM municipios ORDER BY nombre")
    if request.method == "POST":
        municipio = request.form.get("municipio", type=int)
        barrio = request.form.get("barrio", "").strip()[:120]
        descripcion = request.form.get("descripcion", "").strip()[:2000]
        nivel = request.form.get("nivel", "")
        lat = request.form.get("lat", type=float)
        lng = request.form.get("lng", type=float)
        fecha = request.form.get("fecha", "").strip()

        if not municipio or not barrio or not descripcion or len(descripcion) < 20:
            flash("Completa todos los campos (descripción de al menos 20 caracteres).", "error")
        elif nivel not in NIVELES:
            flash("Selecciona el nivel del agua.", "error")
        elif lat is None or lng is None or not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            flash("Marca la ubicación en el mapa.", "error")
        else:
            try:
                fecha_inc = datetime.strptime(fecha, "%Y-%m-%dT%H:%M") if fecha else datetime.now()
            except ValueError:
                fecha_inc = datetime.now()

            id_inc = ejecutar(
                """INSERT INTO incidentes
                   (id_usuario, id_municipio, barrio, descripcion, nivel_agua, lat, lng, fecha_incidente)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (session["usuario_id"], municipio, barrio, descripcion,
                 nivel, lat, lng, fecha_inc), obtener_id=True)

            adjuntos = 0
            for archivo in request.files.getlist("fotos")[:3]:
                nombre = validar_imagen(archivo)
                if nombre:
                    archivo.save(os.path.join(current_app.config["UPLOAD_FOLDER"], nombre))
                    ejecutar("INSERT INTO evidencias (id_incidente, archivo) VALUES (%s,%s)",
                             (id_inc, nombre))
                    adjuntos += 1

            flash("Reporte enviado. Está pendiente de revisión.", "exito")
            return redirect(url_for("r_incidentes.detalle", id_inc=id_inc))

    return render_template("reportar.html", titulo="Reportar inundación",
                           municipios=municipios, niveles=NIVELES,
                           now=datetime.now())


@r_incidentes.route("/detalle/<int:id_inc>")
def detalle(id_inc):
    inc = consultar("""
        SELECT i.*, m.nombre AS municipio,
               u.nombre_completo AS reportador
        FROM incidentes i
        JOIN municipios m ON m.id_municipio = i.id_municipio
        JOIN usuarios u ON u.id_usuario = i.id_usuario
        WHERE i.id_incidente = %s""", (id_inc,), uno=True)
    if not inc:
        return render_template("404.html"), 404
    es_admin = session.get("rol") == "administrador"
    es_autor = session.get("usuario_id") == inc["id_usuario"]
    if inc["estado"] in ("pendiente", "rechazado") and not (es_admin or es_autor):
        flash("Este reporte aún no ha sido aprobado por el administrador.", "aviso")
        return redirect(url_for("r_incidentes.index"))
    evidencias = consultar(
        "SELECT * FROM evidencias WHERE id_incidente = %s", (id_inc,))
    historial = consultar(
        "SELECT * FROM seguimiento WHERE id_incidente = %s ORDER BY creado_en DESC", (id_inc,))
    inc["lat"], inc["lng"] = float(inc["lat"]), float(inc["lng"])
    return render_template("detalle.html", titulo="Detalle del reporte",
                           incidente=inc, evidencias=evidencias, historial=historial)


@r_incidentes.route("/uploads/<nombre>")
def subir_archivo(nombre):
    if not validar_nombre(nombre):
        return "", 400
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], nombre)


def validar_nombre(nombre):
    import re
    return bool(re.match(r"^[a-f0-9]{16}\.(png|jpg|jpeg|webp)$", nombre))


@r_incidentes.route("/denunciar/<int:id_inc>", methods=["POST"])
@login_requerido
def denunciar(id_inc):
    motivo = request.form.get("motivo", "").strip()[:255]
    existe = consultar("SELECT id_incidente FROM incidentes WHERE id_incidente = %s", (id_inc,), uno=True)
    if existe and motivo:
        ejecutar("INSERT INTO denuncias (id_incidente, motivo) VALUES (%s,%s)", (id_inc, motivo))
        flash("Gracias, revisaremos la información de este reporte.", "exito")
    else:
        flash("No pudimos registrar la denuncia.", "error")
    return redirect(url_for("r_incidentes.detalle", id_inc=id_inc))
