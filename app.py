from flask import Flask, request, jsonify, send_file
import stripe
import os

app = Flask(__name__)
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")

PRODUCTOS = {
    "prod_001": {"nombre": "Nomina RESICO 2025", "precio": 29900, "archivo": "nomina_resico.xlsx"},
    "prod_002": {"nombre": "Declaracion IVA", "precio": 19900, "archivo": "declaracion_iva.xlsx"},
    "prod_003": {"nombre": "Control ISR Anual", "precio": 24900, "archivo": "control_isr.xlsx"},
    "prod_004": {"nombre": "Flujo de Caja", "precio": 17900, "archivo": "flujo_caja.xlsx"},
    "prod_005": {"nombre": "Balance General", "precio": 22900, "archivo": "balance_general.xlsx"},
    "prod_006": {"nombre": "Control IMSS INFONAVIT", "precio": 21900, "archivo": "imss_infonavit.xlsx"},
    "prod_007": {"nombre": "Nomina Semanal", "precio": 18900, "archivo": "nomina_semanal.xlsx"},
    "prod_008": {"nombre": "Declaracion Anual PM", "precio": 34900, "archivo": "declaracion_anual.xlsx"},
    "prod_009": {"nombre": "Cuentas por Cobrar", "precio": 15900, "archivo": "cuentas_cobrar_pagar.xlsx"},
    "paquete":  {"nombre": "Paquete Contable Completo", "precio": 79900, "archivo": None},
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
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=email,
            line_items=[{"price_data": {"currency": "mxn", "product_data": {"name": producto["nombre"]}, "unit_amount": producto["precio"]}, "quantity": 1}],
            mode="payment",
            success_url=os.environ.get("FRONTEND_URL", "") + "?pago=exitoso&session_id={CHECKOUT_SESSION_ID}&producto=" + producto_id,
            cancel_url=os.environ.get("FRONTEND_URL", "") + "?pago=cancelado",
            metadata={"producto_id": producto_id}
        )
        return jsonify({"url": session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/descargar/<producto_id>/<session_id>")
def descargar(producto_id, session_id):
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status != "paid":
            return jsonify({"error": "Pago no verificado"}), 403
        producto = PRODUCTOS.get(producto_id)
        if not producto or not producto["archivo"]:
            return jsonify({"error": "Archivo no disponible"}), 404
        ruta = os.path.join("formatos", producto["archivo"])
        if not os.path.exists(ruta):
            return jsonify({"error": "Archivo no encontrado"}), 404
        return send_file(ruta, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
```

Guarda con **⌘ + S**, cierra TextEdit y en Terminal:
```
git add app.py
git commit -m "Servidor simplificado"
git push origin main