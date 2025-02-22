from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pika
import json
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///pedidos.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Modelo de la base de datos
class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto = db.Column(db.String(80), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    estado = db.Column(db.String(20), default="pendiente")  # pendiente, validado, error

# Conectar a RabbitMQ
def conectar_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters(os.getenv("RABBITMQ_HOST", "localhost")))
    channel = connection.channel()
    channel.queue_declare(queue="pedidos")
    channel.queue_declare(queue="monitor_pedidos")  # Cola para enviar respuesta
    return connection, channel
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"mensaje": "Pong!"}), 200

# API para consultar pedidos
@app.route("/pedidos", methods=["GET"])
def obtener_pedidos():
    pedidos = Pedido.query.all()
    resultado = [
        {"id": p.id, "producto": p.producto, "cantidad": p.cantidad, "direccion": p.direccion, "estado": p.estado}
        for p in pedidos
    ]
    return jsonify(resultado)

# API para crear pedidos directamente sin RabbitMQ (para pruebas)
@app.route("/crear-pedido", methods=["POST"])
def crear_pedido():
    data = request.json
    if not data.get("producto") or not data.get("cantidad") or not data.get("direccion"):
        return jsonify({"error": "Datos de pedido incompletos"}), 400

    nuevo_pedido = Pedido(
        producto=data["producto"],
        cantidad=data["cantidad"],
        direccion=data["direccion"],
        estado="pendiente"
    )
    db.session.add(nuevo_pedido)
    db.session.commit()

    return jsonify({"mensaje": "Pedido creado correctamente", "id": nuevo_pedido.id}), 201

# Función para procesar los pedidos desde la cola de RabbitMQ
def procesar_pedido(ch, method, properties, body):
    pedido_data = json.loads(body)
    print(f"📦 Procesando pedido {pedido_data['id']}...")

    # Buscar pedido en la DB (o crearlo si no existe)
    pedido = Pedido.query.get(pedido_data["id"])
    if not pedido:
        pedido = Pedido(
            id=pedido_data["id"],
            producto=pedido_data["producto"],
            cantidad=pedido_data["cantidad"],
            direccion=pedido_data["direccion"],
            estado="pendiente"
        )
        db.session.add(pedido)

    # Validación de pedido
    if pedido.cantidad <= 0:
        pedido.estado = "error"
        respuesta = {"id": pedido.id, "estado": "error", "motivo": "Cantidad inválida"}
    else:
        pedido.estado = "validado"
        respuesta = {"id": pedido.id, "estado": "validado"}

    db.session.commit()

    # Enviar respuesta a `monitor_pedidos`
    connection, channel = conectar_rabbitmq()
    channel.basic_publish(
        exchange="",
        routing_key="monitor_pedidos",
        body=json.dumps(respuesta)
    )
    connection.close()

    ch.basic_ack(delivery_tag=method.delivery_tag)

# Worker para consumir pedidos de la cola
def iniciar_worker():
    connection, channel = conectar_rabbitmq()
    channel.basic_consume(queue="pedidos", on_message_callback=procesar_pedido)
    print("🚀 Esperando pedidos...")
    channel.start_consuming()

if __name__ == "__main__":
    db.create_all()
    app.run(host="0.0.0.0", port=5000)
