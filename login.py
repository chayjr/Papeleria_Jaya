from datetime import datetime

from flask import Blueprint, flash,redirect,render_template, session,url_for,request
from werkzeug.security import check_password_hash
import secrets

from conexion import conectar
sesion_bp = Blueprint('sesion', __name__)

#Decorador para proteger login y rutas con privilegios
from functools import wraps
from flask import session, redirect

def requiere_privilegio(nombre_privilegio):
    def decorator(func):
        @wraps(func)
        def envoltura(*args, **kwargs):
            # VALIDAR LOGIN
            if "id_usuario" not in session:
                return redirect("/")

            conn = conectar()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT privilegio.nombre

                FROM usuario_privilegio

                INNER JOIN privilegio
                ON usuario_privilegio.id_privilegio = privilegio.id_privilegio

                WHERE usuario_privilegio.id_usuario = %s
            """, (
                session["id_usuario"],
            ))

            privilegios = cursor.fetchall()

            conn.close()

            lista_privilegios = []

            for p in privilegios:
                lista_privilegios.append(p["nombre"])

            #administrador
            if "Todos" in lista_privilegios:
                return func(*args, **kwargs)

            #privilegio especifico
            if nombre_privilegio in lista_privilegios:
                return func(*args, **kwargs)
            return """
                <h1>No tienes acceso</h1>
            """
        return envoltura
    return decorator


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
                cursor.execute("SELECT sesion_token FROM usuario WHERE id_usuario = %s", (session["id_usuario"],))
                usuario_token = cursor.fetchone()

                #Verifica que el token de la base sea nula
                if usuario_token and usuario_token["sesion_token"] == session["token"]:
                    flash ("Este usuario se encuentra activo")
                    return render_template("base_login.html")
                else:
                    session.clear()
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
