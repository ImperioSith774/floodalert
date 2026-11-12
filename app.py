from flask import Flask
from config import Config
import os


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    from routes.usuarios import r_usuarios
    from routes.incidentes import r_incidentes
    from routes.administrador import r_admin
    from routes.mapa import r_mapa

    app.register_blueprint(r_usuarios)
    app.register_blueprint(r_incidentes)
    app.register_blueprint(r_admin)
    app.register_blueprint(r_mapa)

    @app.errorhandler(404)
    def no_encontrado(e):
        from flask import render_template
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    app = crear_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
