from datetime import datetime

from flask import Blueprint, flash,redirect,render_template, session,url_for,request
from werkzeug.security import check_password_hash
import secrets
from functools import wraps
from datetime import datetime, timedelta

from conexion import conectar
sesion_bp = Blueprint('sesion', __name__)

#Decorador para proteger login y rutas con privilegios
from functools import wraps
from flask import session, redirect

def requiere_privilegio(nombre_privilegio):
    def decorator(func):
        @wraps(func)
        def envoltura(*args, **kwargs):
            #Validar login
            if "id_usuario" not in session:
                return redirect(url_for("sesion.home"))
            
            #Validar sesion
            respuesta = validar_sesion()
            
            if respuesta is not True:
                return respuesta

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
            
            cursor.close()
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
            flash("No tienes permisos para acceder","error")
            return render_template("acceso_denegado.html")
        return envoltura
    return decorator

#Decorador para validar sesion
def validar_sesion():
    if "id_usuario" not in session:
        return False

    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            sesion_token,
            ultima_actividad
        FROM usuario
        WHERE id_usuario = %s
    """, (session["id_usuario"],))

    usuario = cursor.fetchone()

    #Si no existe
    if not usuario:
        conn.close()
        session.clear()
        return False

    #Tiempo limite
    tiempo_limite = timedelta(minutes=10)

    ahora = datetime.now()

    #Validar inactividad
    if usuario["ultima_actividad"]:

        diferencia = ahora - usuario["ultima_actividad"]

        #Sesion expirada
        if diferencia > tiempo_limite:

            cursor.execute("""
                UPDATE usuario
                SET sesion_token = NULL,
                    ultima_actividad = NULL
                WHERE id_usuario = %s
            """, (session["id_usuario"],))

            conn.commit()
            conn.close()

            flash("Sesión expirada por inactividad","warning")
            session.pop("id_usuario",None)
            session.pop("usuario",None)
            session.pop("id_rol",None)
            session.pop("token",None)
            return redirect(url_for("sesion.home"))

    #Validar Token
    if usuario["sesion_token"] != session["token"]:

        conn.close()
        flash("Sesión inválida","error")
        session.pop("id_usuario",None)
        session.pop("usuario",None)
        session.pop("id_rol",None)
        session.pop("token",None)
        return redirect(url_for("sesion.home"))

    #Actualizar actividad
    cursor.execute("""
        UPDATE usuario
        SET ultima_actividad = %s
        WHERE id_usuario = %s
    """, (ahora,session["id_usuario"],))

    conn.commit()
    conn.close()

    return True


#Ruta para loguarte a la hora de entrar al sistema
@sesion_bp.route("/", methods=["GET","POST"])
def home ():
    if request.method == "POST":
        usuario = request.form["usuario"].strip()
        password = request.form["contrasena"].strip()

        conn = conectar()
        try:

            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)
            cursor.execute ("SELECT * FROM usuario WHERE BINARY usuario = %s FOR UPDATE", (usuario,))
            usuario_db = cursor.fetchone()


            #Verifica usuario y contraseña
            if usuario_db and check_password_hash(usuario_db["contrasena"],password):
                #Sesion activda
                if usuario_db["sesion_token"] is not None:
                    #Validar tiempo
                    if usuario_db["ultima_actividad"]:

                        diferencia = (datetime.now()- usuario_db["ultima_actividad"])

                        #Si ya expiró
                        if diferencia > timedelta(minutes=10):

                            cursor.execute("""UPDATE usuario SET sesion_token = NULL, ultima_actividad = NULL WHERE id_usuario = %s
                            """, (usuario_db["id_usuario"],))
                            conn.commit()
                        else:
                            flash("Este usuario ya tiene sesión activa","warning")
                            conn.close()
                            return render_template("base_login.html")
                #Genera token 
                token = secrets.token_hex(32)
                #Guarda token y ultima actividad en la base de datos
                cursor.execute("UPDATE usuario SET sesion_token = %s, ultima_actividad = %s WHERE id_usuario = %s", (token,datetime.now(),usuario_db["id_usuario"]))
                conn.commit()
                #Sesion flask
                session.permanent = True
            
                session["id_usuario"] = usuario_db["id_usuario"]
                session["usuario"] = usuario_db["usuario"]
                session["id_rol"] = usuario_db["id_rol"]
                session["token"] = token

                flash("Bienvenido al sistema","success")

                if usuario_db["id_rol"] == 1:
                    return redirect(url_for("dashboard"))
                else: 
                    return redirect(url_for("productos"))
            else:
                conn.rollback() 
                flash ("Usuario o contraseña incorrectos","error")
        except Exception as e:
            conn.rollback()
            flash(f"Error al iniciar sesió: {str(e)}", "error")
        finally:
            cursor.close()
            conn.close()
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

    flash("Sesión cerrada correctamente","success")
    session.pop("id_usuario",None)
    session.pop("usuario",None)
    session.pop("id_rol",None)
    session.pop("token",None)
    return redirect(url_for("sesion.home")) 
