import mysql.connector

def conectar():
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="pos_user",
            password="flask123",
            database="papeleria_jaya"
        )

        if conexion.is_connected():
            print ("Se conecto de manera exitosa la base de datos")
        return conexion 
    except mysql.connector.Error as error:
        print("Error al conectar:", error)
        return None