from decimal import Decimal

from flask import Blueprint, Flask, render_template,request, session,url_for,redirect
from conexion import conectar
from login import sesion_bp

app = Flask (__name__)
app.secret_key = "david"

app.register_blueprint(sesion_bp)


@app.route("/dashboard")
def dashboard():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.callproc ("sp_dashboard")

    for result in cursor.stored_results():
        datos= result.fetchone()

        total_productos = datos["total_productos"]
        total_ventas = datos["total_ventas"]
        total_ingresos = datos["total_ingresos"]
    return render_template("dashboard.html", Productos=total_productos, ventas=total_ventas, Total=total_ingresos)

#ruta solo para dirigir al html de agregar producto
@app.route("/agregar_producto", methods=["POST"])
def pagina_agregar():
    return render_template ("agregar_producto.html")

#ruta para ingresar datos del producto y guardarlos en la base de datos 
@app.route("/agregar_productos", methods=["GET", "POST"])
def agregarp():
    if request.method == "POST":
        Nombre_producto = request.form["nombre"].strip()
        Descripcion = request.form["descripcion"].strip()
        Cantidad = int(request.form["cantidad"])
        Precio = Decimal(request.form["precio"])
        conn = conectar()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("INSERT INTO producto (nombre, descripcion, cantidad, precio) VALUES (%s, %s, %s, %s)", (Nombre_producto, Descripcion, Cantidad, Precio))
        conn.commit()
        conn.close()

        return redirect(url_for("productos"))
    return render_template ("gestion.html")

#Muestra los productos ingresados
@app.route("/productos")
def productos():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM producto ORDER BY id_producto DESC")
    inventario = cursor.fetchall()

    conn.close()

    return render_template("gestion.html", inventario=inventario)

@app.route("/eliminar_producto/<int:id>", methods=["POST"])
def eliminarproductos(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.callproc("eliminar_producto", [id])
    
    conn.commit()
    conn.close()
    return redirect(url_for("productos"))

inventario = [
        {"id": 1, "nombre": "Cuaderno A5", "precio": 5.00, "stock": 10},
        {"id": 2, "nombre": "Lapicero Azul", "precio": 1.50, "stock": 25},
        {"id": 3, "nombre": "Marcador Permanente", "precio": 2.75, "stock": 15},
    ]

carrito = []
# VENTAS
@app.route("/ventas")
def ventas():
    productos = inventario

    total = sum(item["subtotal"] for item in carrito)

    return render_template("ventas.html",
                           productos=productos,
                           carrito=carrito,
                           total=total)

# REPORTES
@app.route("/reportes")
def reportes():
    #DATOS FALSOS
    reportes = [
        {"id": 1, "nombre": "Cuaderno", "cantidad": 2, "total": 50, "fecha": "2026-01-01"},
        {"id": 2, "nombre": "Lápiz", "cantidad": 5, "total": 25, "fecha": "2026-01-02"}
    ]

    total = sum(r["total"] for r in reportes)
    cantidad = len(reportes)

    return render_template("reportes.html",
                           reportes=reportes,
                           total=total,
                           cantidad=cantidad)



# ELIMINAR
@app.route("/eliminar/<int:index>")
def eliminar(index):
    carrito.pop(index)
    return redirect("/ventas")


# GUARDAR VENTA (FAKE)
@app.route("/guardar_venta")
def guardar_venta():
    carrito.clear()
    return redirect("/ventas")


# NUEVA
@app.route("/nueva")
def nueva():
    carrito.clear()
    return redirect("/ventas")


#Lista los usuarios y los muestra en la tabla
@app.route("/usuarios")
def usuarios():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.callproc("mostrar_usuarios")
    usuarios = []
    for result in cursor.stored_results():
        usuarios = result.fetchall()

    conn.close()

    return render_template("usuarios.html", usuarios=usuarios)

#Ruta solo para acceder a la pagina de agregar usuarios
@app.route("/agregar_usuario", methods=["POST"])
def pagina_agregar_usuario():
    return render_template ("agregar_usuario.html")

if __name__ == "__main__":
    app.run(debug=True)