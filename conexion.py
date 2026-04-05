import mysql.connector

def conectar():
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="contraseña",
            database="base_de_datos "
        )
        return conexion
    except mysql.connector.Error as error:
        print("Error al conectar:", error)
        return None
    

