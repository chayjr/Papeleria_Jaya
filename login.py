from datetime import datetime

from flask import Blueprint, flash,redirect,render_template, session,url_for,request
from werkzeug.security import check_password_hash
import secrets

from conexion import conectar
sesion_bp = Blueprint('sesion', __name__)


#Ruta para loguarte a la hora de entrar al sistema
@sesion_bp.route("/", methods=["GET","POST"])
def home ():
    if request.method == "POST":
        usuario = request.form["usuario"].strip()
        password = request.form["contrasena"].strip()

        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute ("SELECT * FROM usuario WHERE usuario = %s", (usuario,))
        usuario_db = cursor.fetchone()

        #Verifica usuario y contraseña
        if usuario_db and check_password_hash(usuario_db["contrasena"],password):
            if "token" in session:
                flash ("Este usuario se encuentra activo")
                return render_template("base_login.html")
            #Genera token 
            token = secrets.token_hex(32)
            #Guarda token y ultima actividad en la base de datos
            cursor.execute("UPDATE usuario SET sesion_token = %s, ultima_actividad = %s WHERE id_usuario = %s", (token,datetime.now(),usuario_db["id_usuario"]))
            conn.commit()

            session["id_usuario"] = usuario_db["id_usuario"]
            session["usuario"] = usuario_db["usuario"]
            session["id_rol"] = usuario_db["id_rol"]
            session["token"] = token

            if usuario_db["id_rol"] == 1:
                return redirect(url_for("dashboard"))
            else: 
                return redirect(url_for("productos"))
        else: 
            flash ("Usuario o contraseña incorrectos","error")
    return render_template("base_login.html")

#Ruta para cerrar la sesion
@sesion_bp.route("/logout")
def logout():
    if "token" in session:

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE usuario
            SET sesion_token = NULL,
                ultima_actividad = NULL
            WHERE sesion_token = %s
        """, (session["token"],))

        conn.commit()
        conn.close()

    session.clear()
    return redirect(url_for("sesion.home")) 
