from decimal import Decimal

from flask import Blueprint, Flask, render_template,request, session,url_for,redirect,jsonify
from conexion import conectar
from login import sesion_bp ,requiere_privilegio
from werkzeug.security import generate_password_hash

app = Flask (__name__)
app.secret_key = "david"

app.register_blueprint(sesion_bp)


@app.route("/dashboard")
@requiere_privilegio("Panel principal")
def dashboard():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.callproc ("sp_dashboard")

    for result in cursor.stored_results():
        datos= result.fetchone()

        total_productos = datos["total_productos"]
        total_ventas = datos["total_ventas"]
        total_ingresos = datos["total_ingresos"]

    cursor.close()
    conn.close()
    return render_template("dashboard.html", Productos=total_productos, ventas=total_ventas, Total=total_ingresos, bajos=[])

@app.route("/bajo_stock", methods=["POSt"])
@requiere_privilegio("Panel principal")
def bajo_stock():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    cursor.callproc("sp_dashboard")
    for result in cursor.stored_results():

        datos = result.fetchone()

        total_productos = datos["total_productos"]
        total_ventas = datos["total_ventas"]
        total_ingresos = datos["total_ingresos"]

    cursor.close()

    cursor = conn.cursor(dictionary=True)
    cursor.callproc("sp_bajo_stock")

    for result in cursor.stored_results():
        bajos = result.fetchall()

    cursor.close()
    conn.close()

    return render_template("dashboard.html", Productos=total_productos, ventas=total_ventas, Total=total_ingresos, bajos=bajos)

#ruta solo para dirigir al html de agregar producto
@app.route("/agregar_producto", methods=["POST"])
@requiere_privilegio("Productos")
def pagina_agregar():
    return render_template ("agregar_producto.html")

#ruta para ingresar datos del producto y guardarlos en la base de datos 
@app.route("/agregar_productos", methods=["GET", "POST"])
@requiere_privilegio("Productos")
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
@requiere_privilegio("Productos")
def productos():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM producto ORDER BY id_producto DESC")
    inventario = cursor.fetchall()

    conn.close()

    return render_template("gestion.html", inventario=inventario)

@app.route("/actualizar_producto/<int:id>", methods=["GET","POST"])
@requiere_privilegio("Productos")
def actualizar_producto(id):
    conn = conectar()
    cursor = conn.cursor(dictionary=True)
    #Si el usuario envía el formulario
    if request.method == "POST":

        nombre = request.form["nombre"].strip()
        descripcion = request.form["descripcion"].strip()
        cantidad = int(request.form["cantidad"])
        precio = Decimal(request.form["precio"])

        cursor.execute("""
            UPDATE producto 
            SET nombre = %s,
                descripcion = %s,
                cantidad = %s,
                precio = %s
            WHERE id_producto = %s
        """, (nombre, descripcion, cantidad, precio, id))

        conn.commit()
        conn.close()

        return redirect(url_for("productos"))

    #Mostrar datos actuales del producto
    cursor.execute("SELECT * FROM producto WHERE id_producto = %s", (id,))
    producto = cursor.fetchone()

    conn.close()

    return render_template("actualizar_producto.html", producto=producto)

@app.route("/eliminar_producto/<int:id>", methods=["POST"])
def eliminarproductos(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.callproc("eliminar_producto", [id])
    
    conn.commit()
    conn.close()
    return redirect(url_for("productos"))


#VENTAS
venta_actual = []

@app.route("/ventas")
@requiere_privilegio("Ventas")
def ventas():
    conn = conectar()
    cursor = conn.cursor()

    texto = request.args.get("buscar", "")

    productosc = []

    #Si el usuario escribio algo
    if texto != "":

        valor = f"%{texto}%"

        cursor.execute("""
            SELECT id_producto, nombre, precio
            FROM producto
            WHERE nombre LIKE %s
            OR CAST(id_producto AS CHAR) LIKE %s
            LIMIT 10
        """, (valor, valor))

        productosc = cursor.fetchall()

    total = sum(item["subtotal"] for item in venta_actual)

    cursor.close()
    conn.close()

    return render_template("ventas.html",productosc=productosc,carrito=venta_actual,total=total)

@app.route("/agregar_producto_venta", methods=["POST"])
@requiere_privilegio("Ventas")
def agregar_productoaventa():
    conn = conectar()
    cursor = conn.cursor()

    producto_id = request.form["producto"]
    cursor.execute("SELECT id_producto, nombre, precio FROM producto WHERE id_producto = %s", (producto_id,))

    producto = cursor.fetchone()

    cursor.close()
    conn.close()

    if producto :
        existe = False

        for item in venta_actual:
            if item["id_producto"] == producto[0]:
                item["cantidad"] += 1

                item["subtotal"] = (item["cantidad"]* item["precio"]
                ) 
                existe = True
                break
        if not existe:
                venta_actual.append({
                    "id_producto":producto[0],
                    "nombre":producto[1],
                    "precio":float(producto[2]),
                    "cantidad":1,
                    "subtotal":float(producto[2]),
                }) 

    return redirect("/ventas")

@app.route("/calcular_cambio", methods=["POST"])
@requiere_privilegio("Ventas")
def cambio_calculado():
    total = float(request.form["total"])
    pago_texto = request.form ["pago"]

    productosc = []
    if pago_texto == "":
        return render_template("ventas.html", total=total, productoc=productosc, carrito=venta_actual, error="Ingrese una cantidad")
    pago = float(pago_texto)

    if pago < 0:
        return render_template("ventas.html", total=total, productoc=productosc, carrito=venta_actual, error="No se permiten números negativos")
    if pago < total:
        return render_template("ventas.html", total=total, pago=pago, productoc=productosc, carrito=venta_actual, error="La cantidad ingresada es insuficiente")

    cambio = pago - total

    return render_template("ventas.html", total=total, pago=pago, cambio=cambio, productoc=productosc, carrito=venta_actual, metodo_pago="Efectivo")

# Guardar venta
@app.route("/guardar_venta",methods=["POST"])
@requiere_privilegio("Ventas")
def guardar_venta():
    if len(venta_actual) == 0:
        return redirect("/ventas")

    conn = conectar()
    cursor = conn.cursor()

    total = float(request.form["total"])
    pago = float(request.form["pago"])
    cambio = float(request.form["cambio"])
    metodo_pago = request.form["metodo_pago"]

    id_usuario = 1
    cursor.execute("""INSERT INTO venta(fecha,total,id_usuario,metodo_pago,efectivo_recibido,cambio) VALUES (CURDATE(),%s,%s,%s,%s,%s)
    """, 
    (
        total,
        id_usuario,
        metodo_pago,
        pago,
        cambio
    ))
    conn.commit()

    id_venta = cursor.lastrowid
    for item in venta_actual:

        cursor.execute("""INSERT INTO item_venta(id_venta,id_producto,cantidad,subtotal)VALUES(%s,%s,%s,%s)
        """, (
            id_venta,
            item["id_producto"],
            item["cantidad"],
            item["subtotal"]
        ))

        # DESCONTAR STOCK
        cursor.execute("""
            UPDATE producto
            SET cantidad = cantidad - %s
            WHERE id_producto = %s
        """, (
            item["cantidad"],
            item["id_producto"]
        ))

    conn.commit()

    cursor.close()
    conn.close()
    venta_actual.clear()
    return redirect("/ventas")

# NUEVA
@app.route("/nueva") 
def nueva():
    venta_actual.clear()
    return redirect("/ventas")

# REPORTES
@app.route("/reportes")
@requiere_privilegio("Reportes")
def reportes():
    conn = conectar()

    inicio = request.args.get("inicio")
    fin = request.args.get("fin")

    reportes = []
    total = 0
    cantidad = 0
    cursor=conn.cursor(dictionary=True)

    # Si no seleccionan fechas
    if not inicio or not fin or inicio == "" or fin == "":

        cursor.execute("""
            SELECT
                v.id_venta AS id,
                p.nombre,
                iv.cantidad,
                iv.subtotal AS total,
                v.fecha
            FROM venta v
            INNER JOIN item_venta iv ON v.id_venta = iv.id_venta
            INNER JOIN producto p ON iv.id_producto = p.id_producto
            ORDER BY v.fecha DESC
        """)

        reportes = cursor.fetchall()

        cursor.execute("""
            SELECT
                IFNULL(SUM(total),0) AS total_ventas,
                COUNT(*) AS cantidad_ventas
            FROM venta
        """)

        resumen = cursor.fetchone()

    else:
        # PROCEDURE REPORTES
        cursor.callproc("obtener_reportes", [inicio, fin])

        for resultado in cursor.stored_results():
            reportes = resultado.fetchall()

        cursor.close()
        cursor = conn.cursor(dictionary=True)

        # PROCEDURE RESUMEN
        cursor.callproc("resumen_reportes", [inicio, fin])

        for resultado in cursor.stored_results():
            resumen = resultado.fetchone()

    total = resumen["total_ventas"] if resumen else 0
    cantidad = resumen["cantidad_ventas"] if resumen else 0

    cursor.close()
    conn.close()

    return render_template("reportes.html", reportes=reportes, total=total, cantidad=cantidad)

# ELIMINAR
@app.route("/eliminar/<int:index>")
def eliminar(index):
    venta_actual.pop(index)
    return redirect("/ventas")


#Lista los usuarios y los muestra en la tabla
@app.route("/usuarios")
@requiere_privilegio("Usuarios")
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
@requiere_privilegio("Usuarios")
def pagina_agregar_usuario():
    conn = conectar()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM rol")
    roles = cursor.fetchall()

    cursor.execute("SELECT * FROM privilegio")
    privilegios = cursor.fetchall()

    conn.close()
    return render_template ("agregar_usuario.html", roles=roles, privilegios=privilegios)

@app.route("/guardar_usuario", methods=["POST"])
@requiere_privilegio("Usuarios")
def guardar_usuario():

    nombre = request.form["nombre"]
    usuario = request.form["usuario"]

    contrasena = generate_password_hash(request.form["contrasena"])
    id_rol = request.form["id_rol"]

    privilegios = request.form.getlist("privilegios")

    conn = conectar()
    cursor = conn.cursor()

    # INSERTAR USUARIO
    cursor.execute("""
        INSERT INTO usuario
        (nombre, usuario, contrasena, id_rol)
        VALUES(%s,%s,%s,%s)
    """, (
        nombre,
        usuario,
        contrasena,
        id_rol
    ))

    conn.commit()

    # ID DEL NUEVO USUARIO
    id_usuario = cursor.lastrowid

    # GUARDAR PRIVILEGIOS
    for id_privilegio in privilegios:

        cursor.execute("""
            INSERT INTO usuario_privilegio
            (id_usuario, id_privilegio)
            VALUES(%s,%s)
        """, (
            id_usuario,
            id_privilegio
        ))

    conn.commit()
    conn.close()

    return redirect("/usuarios")

if __name__ == "__main__":
    app.run(debug=True)