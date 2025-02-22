from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pika
import json
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///pedidos.db")
db = SQLAlchemy(app)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto = db.Column(db.String(80), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    estado = db.Column(db.String(20), default="pendiente")  # Estados: pendiente, validado, error

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"mensaje": "Pong!"}), 200

@app.route("/crear-pedido", methods=["POST"])
def crear_pedido():
    data = request.json
    if not data.get("producto") or not data.get("cantidad") or not data.get("direccion"):
        return jsonify({"error": "Datos de pedido incompletos"}), 400

    nuevo_pedido = Pedido(
        producto=data["producto"],
        cantidad=data["cantidad"],
        direccion=data["direccion"]
    )
    db.session.add(nuevo_pedido)
    db.session.commit()

    try:
        # Enviar mensaje a la cola RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
        channel = connection.channel()
        channel.queue_declare(queue="pedidos")
        channel.basic_publish(
            exchange="",
            routing_key="pedidos",
            body=json.dumps({
                "id": nuevo_pedido.id,
                "producto": nuevo_pedido.producto,
                "cantidad": nuevo_pedido.cantidad,
                "direccion": nuevo_pedido.direccion
            })
        )
        connection.close()
    except Exception as e:
        # Enmascarar el error para que no afecte al usuario final
        return jsonify({"mensaje": "Pedido registrado, pero hay retrasos en validación"}), 202

    return jsonify({"mensaje": "Pedido creado correctamente"}), 201

if __name__ == "__main__":
    db.create_all()
    app.run(host="0.0.0.0", port=5000)
