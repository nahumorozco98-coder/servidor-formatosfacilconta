from flask import Flask, request, jsonify, send_file
import stripe
import resend
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
resend.api_key = os.getenv("RESEND_API_KEY")

PRODUCTOS = {
    "prod_001": {"nombre": "Nomina RESICO 2025", "precio": 29900, "archivo": "nomina_resico.xlsx"},
    "prod_002": {"nombre": "Declaracion IVA", "precio": 19900, "archivo": "declaracion_iva.xlsx"},
    "prod_003": {"nombre": "Control ISR Anual", "precio": 24900, "archivo": "control_isr.xlsx"},
    "prod_004": {"nombre": "Flujo de Caja", "precio": 17900, "archivo": "flujo_caja.xlsx"},
    "prod_005": {"nombre": "Balance General", "precio": 22900, "archivo": "balance_general.xlsx"},
    "prod_006": {"nombre": "Control IMSS INFONAVIT", "precio": 21900, "archivo": "imss_infonavit.xlsx"},
    "prod_007": {"nombre": "Nomina Semanal", "precio": 18900, "archivo": "nomina_semanal.xlsx"},
    "prod_008": {"nombre": "Declaracion Anual PM", "precio": 34900, "archivo": "declaracion_anual.xlsx"},
    "prod_009": {"nombre": "Cuentas por Cobrar y Pagar", "precio": 15900, "archivo": "cuentas_cobrar_pagar.xlsx"},
    "paquete":  {"nombre": "Paquete Contable Completo", "precio": 79900, "archivo": None},
}

@app.route("/")
def home():
    return jsonify({"status": "FormatosFacilConta servidor activo"})

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
            line_items=[{
                "price_data": {
                    "currency": "mxn",
                    "product_data": {"name": producto["nombre"]},
                    "unit_amount": producto["precio"],
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=os.getenv("FRONTEND_URL") + "/exito?session_id={CHECKOUT_SESSION_ID}&producto=" + producto_id,
            cancel_url=os.getenv("FRONTEND_URL") + "/cancelado",
            metadata={"producto_id": producto_id}
        )

        return jsonify({"url": session.url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/confirmar-pago", methods=["POST"])
def confirmar_pago():
    try:
        data = request.json
        session_id = data.get("session_id")
        producto_id = data.get("producto_id")

        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status != "paid":
            return jsonify({"error": "Pago no completado"}), 400

        email = session.customer_email
        producto = PRODUCTOS.get(producto_id)

        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 400

        enviar_correo(email, producto["nombre"], producto_id)

        return jsonify({"status": "ok", "mensaje": "Correo enviado con exito"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/descargar/<producto_id>/<session_id>")
def descargar(producto_id, session_id):
    try:
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status != "paid":
            return jsonify({"error": "Pago no verificado"}), 403

        if session.metadata.get("producto_id") != producto_id:
            return jsonify({"error": "Acceso no autorizado"}), 403

        producto = PRODUCTOS.get(producto_id)
        if not producto or not producto["archivo"]:
            return jsonify({"error": "Archivo no disponible"}), 404

        ruta = os.path.join("formatos", producto["archivo"])
        if not os.path.exists(ruta):
            return jsonify({"error": "Archivo no encontrado en servidor"}), 404

        return send_file(ruta, as_attachment=True, download_name=producto["archivo"])

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def enviar_correo(email, nombre_producto, producto_id):
    url_descarga = f"{os.getenv('BACKEND_URL')}/descargar/{producto_id}"
    resend.Emails.send({
        "from": "FormatosFacilConta <ventas@formatosfacilconta.com>",
        "to": email,
        "subject": f"Tu formato esta listo: {nombre_producto}",
        "html": f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:30px;background:#f9f9f9">
          <div style="background:#0d4a2f;padding:30px;border-radius:12px;text-align:center">
            <h1 style="color:#c9a84c;margin:0;font-size:24px">FormatosFacilConta</h1>
            <p style="color:white;margin:10px 0 0">Tu compra fue exitosa</p>
          </div>
          <div style="background:white;padding:30px;border-radius:12px;margin-top:20px">
            <h2 style="color:#0d4a2f">Hola, gracias por tu compra</h2>
            <p style="color:#555">Tu formato <strong>{nombre_producto}</strong> esta listo para descargar.</p>
            <div style="text-align:center;margin:30px 0">
              <a href="{url_descarga}"
                style="background:#0d4a2f;color:white;padding:15px 30px;border-radius:50px;text-decoration:none;font-weight:bold;font-size:16px">
                Descargar mi formato
              </a>
            </div>
            <p style="color:#999;font-size:13px">Si tienes dudas escribenos a hola@formatosfacilconta.com</p>
          </div>
        </div>
        """
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port))