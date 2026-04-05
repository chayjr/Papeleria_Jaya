from flask import Flask, render_template

app = Flask (__name__)

@app.route("/")
def home ():
    return render_template("index.html")

from flask import Flask, render_template, request, redirect, url_for, session
app = Flask(__name__)
app.secret_key = "secreto"

carrito = []

productos_fake = [
    {"id": 1, "nombre": "Cuaderno", "cantidad": 10, "precio": 25},
    {"id": 2, "nombre": "Lápiz", "cantidad": 50, "precio": 5},
    {"id": 3, "nombre": "Pluma", "cantidad": 30, "precio": 10}
]

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # LOGIN FALSO
        session["user"] = "admin"
        return redirect("/ventas")

    return render_template("login.html")


# VENTAS
@app.route("/ventas")
def ventas():
    productos = productos_fake

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

# AGREGAR
@app.route("/agregar", methods=["POST"])
def agregar():
    producto_id = int(request.form["producto"])
    cantidad = int(request.form["cantidad"])

    producto = next((p for p in productos_fake if p["id"] == producto_id), None)

    if not producto:
        return redirect("/ventas")

    subtotal = producto["precio"] * cantidad

    carrito.append({
        "id": producto["id"],
        "nombre": producto["nombre"],
        "cantidad": cantidad,
        "precio": producto["precio"],
        "subtotal": subtotal
    })

    return redirect("/ventas")


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


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/gestion")
def gestion():
    return render_template("gestion.html", productos=productos_fake)


@app.route("/usuarios")
def usuarios():
    return "<h1>Usuarios (en construcción)</h1>"


if __name__ == "__main__":
    app.run(debug=True)