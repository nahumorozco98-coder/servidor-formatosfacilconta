from flask import Flask, request, jsonify, send_file
import stripe
import os

app = Flask(__name__)
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")

PRODUCTOS = {
    "prod_001": {"nombre": "Nomina RESICO 2025", "precio": 29900},
    "prod_002": {"nombre": "Declaracion IVA", "precio": 19900},
    "prod_003": {"nombre": "Control ISR Anual", "precio": 24900},
    "prod_004": {"nombre": "Flujo de Caja", "precio": 17900},
    "prod_005": {"nombre": "Balance General", "precio": 22900},
    "prod_006": {"nombre": "Control IMSS INFONAVIT", "precio": 21900},
    "prod_007": {"nombre": "Nomina Semanal", "precio": 18900},
    "prod_008": {"nombre": "Declaracion Anual PM", "precio": 34900},
    "prod_009": {"nombre": "Cuentas por Cobrar", "precio": 15900},
    "paquete": {"nombre": "Paquete Contable Completo", "precio": 79900},
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)