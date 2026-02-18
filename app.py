from flask import Flask, request, jsonify, send_file
import stripe
import os

from flask_cors import CORS
app = Flask(__name__)
CORS(app)
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")

PRODUCTOS = {
    "1": {"nombre": "Nomina RESICO 2025", "precio": 34900},
    "2": {"nombre": "Control de IVA Mensual", "precio": 24900},
    "3": {"nombre": "Balance General", "precio": 29900},
    "4": {"nombre": "Conciliacion Bancaria", "precio": 19900},
    "5": {"nombre": "Declaracion Anual ISR PF", "precio": 39900},
    "6": {"nombre": "Registro de Facturas CFDI 4.0", "precio": 17900},
    "paquete": {"nombre": "Paquete Contable Completo", "precio": 79900},
}
ARCHIVOS = {
    "1": "https://drive.google.com/uc?export=download&id=1mFD43SeLpBWgdqLyEgWJcYcTfIrN2uOG",
}
@app.route("/")
def home():
    return jsonify({"status": "FormatosFacilConta activo"})

@app.route("/crear-sesion-pago", methods=["POST"])
def crear_sesion_pago():
    try:
        data = request.json
        producto_id = data.get("producto_id")
        email = data.get("email")
        if not producto_id or producto_id not in PRODUCTOS:
            return jsonify({"error": "Producto no encontrado"}), 400
        producto = PRODUCTOS[producto_id]
        frontend = os.environ.get("FRONTEND_URL", "")
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=email,
            line_items=[{
                "price_data": {
                    "currency": "mxn",
                    "product_data": {"name": producto["nombre"]},
                    "unit_amount": producto["precio"]
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=frontend + "?pago=exitoso&session_id={CHECKOUT_SESSION_ID}&producto=" + producto_id,
            cancel_url=frontend + "?pago=cancelado",
            metadata={"producto_id": producto_id}
        )
        return jsonify({"url": session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/confirmacion-pago", methods=["POST"])
def confirmacion_pago():
    try:
        data = request.json
        session_id = data.get("session_id")
        producto_id = data.get("producto_id")
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status != "paid":
            return jsonify({"error": "Pago no completado"}), 400
        email = session.customer_email
        link = ARCHIVOS.get(producto_id, "")
        producto = PRODUCTOS.get(producto_id, {})
        nombre = producto.get("nombre", "tu formato")
        return jsonify({"status": "ok", "email": email, "link": link, "nombre": nombre})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)