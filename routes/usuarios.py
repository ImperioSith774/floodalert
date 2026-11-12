from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash)
from database.conexion import consultar, ejecutar
from auth_utils import (hash_contrasena, verificar_contrasena,
                        validar_contrasena, validar_correo,
                        login_requerido)

r_usuarios = Blueprint("r_usuarios", __name__)


@r_usuarios.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()[:120]
        correo = request.form.get("correo", "").strip().lower()[:150]
        contrasena = request.form.get("contrasena", "")
        confirmacion = request.form.get("confirmacion", "")

        if not nombre or len(nombre) < 3:
            flash("Escribe tu nombre completo.", "error")
        elif not validar_correo(correo):
            flash("Ingresa un correo válido.", "error")
        elif not validar_contrasena(contrasena):
            flash("La contraseña debe tener al menos 8 caracteres, letras y números.", "error")
        elif contrasena != confirmacion:
            flash("Las contraseñas no coinciden.", "error")
        elif consultar("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,), uno=True):
            flash("Este correo ya está registrado.", "error")
        else:
            ejecutar(
                "INSERT INTO usuarios (nombre_completo, correo, contrasena_hash) VALUES (%s,%s,%s)",
                (nombre, correo, hash_contrasena(contrasena)))
            flash("Cuenta creada. Ahora inicia sesión.", "exito")
            return redirect(url_for("r_usuarios.login"))

    return render_template("registro.html", titulo="Crear cuenta")


@r_usuarios.route("/login", methods=["GET", "POST"])
def login():
    siguiente = request.args.get("siguiente") or request.form.get("siguiente")
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()[:150]
        contrasena = request.form.get("contrasena", "")
        usuario = consultar(
            "SELECT * FROM usuarios WHERE correo = %s AND activo = 1", (correo,), uno=True)
        if usuario and verificar_contrasena(contrasena, usuario["contrasena_hash"]):
            session.clear()
            session["usuario_id"] = usuario["id_usuario"]
            session["nombre"] = usuario["nombre_completo"]
            session["rol"] = usuario["rol"]
            session.permanent = True
            if usuario["rol"] == "administrador":
                destino = url_for("r_admin.dashboard")
            else:
                destino = siguiente if (siguiente or "").startswith("/") else "/index"
            return redirect(destino)
        flash("Correo o contraseña incorrectos.", "error")
    return render_template("login.html", titulo="Iniciar sesión", siguiente=siguiente)


@r_usuarios.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "exito")
    return redirect("/index")


@r_usuarios.route("/mis-reportes")
@login_requerido
def mis_reportes():
    filas = consultar(f"""
        SELECT i.*, m.nombre AS municipio,
          (SELECT archivo FROM evidencias e WHERE e.id_incidente = i.id_incidente LIMIT 1) AS foto
        FROM incidentes i JOIN municipios m ON m.id_municipio = i.id_municipio
        WHERE i.id_usuario = %s ORDER BY i.creado_en DESC""", (session["usuario_id"],))
    return render_template("seguimiento.html", titulo="Mis reportes", reportes=filas)
