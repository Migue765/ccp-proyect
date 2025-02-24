from flask import Flask, request, jsonify
import pika
import json
import os
import random

app = Flask(__name__)

# Almacenar respuestas recibidas
respuestas_recibidas = []

# Conectar a RabbitMQ
def conectar_rabbitmq():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
        channel = connection.channel()
        channel.queue_declare(queue="monitor_pedidos")  # Cola de respuesta
        return connection, channel
    except Exception as e:
        print(f"❌ Error conectando a RabbitMQ: {e}")
        return None, None

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"mensaje": "Pong!"}), 200

@app.route("/ping/labotario", methods=["POST"])
def laboratorio_post():
    if random.random() < 0.1:
        return jsonify({"mensaje": "Error en el laboratorio"}), 500
    
    data = request.json
    required_keys = ["producto", "cantidad", "direccion"]
    for key in required_keys:
        if key not in data:
            return jsonify({"error": f"Falta el parámetro {key}"}), 400

    if data["cantidad"] <= 0:
        return jsonify({"error": "La cantidad debe ser mayor a 0"}), 400
    
    if data["cantidad"] > 10000:
        return jsonify({"error": "No existe suficiente stock para cubrir el pedido"}), 400

    if len(data["direccion"]) <= 2:
        return jsonify({"error": "La dirección debe tener más de 2 caracteres"}), 400
    return jsonify({"mensaje": "Pong!"}), 200

@app.route("/validar-pedido", methods=["POST"])
def validar_pedido():
    data = request.json
    if not data.get("id"):
        return jsonify({"error": "ID del pedido requerido"}), 400

    connection, channel = conectar_rabbitmq()
    if not connection or not channel:
        return jsonify({"error": "Error conectando a RabbitMQ"}), 500

    try:
        channel.queue_declare(queue="pedidos")  # Cola de entrada
        channel.basic_publish(
            exchange="",
            routing_key="pedidos",
            body=json.dumps(data)
        )
        connection.close()
    except Exception as e:
        return jsonify({"error": f"Error enviando a la cola: {e}"}), 500

    return jsonify({"mensaje": "Pedido enviado para validación"}), 202

@app.route("/respuestas", methods=["GET"])
def obtener_respuestas():
    return jsonify(respuestas_recibidas), 200

# Worker para recibir respuestas
def recibir_respuesta():
    connection, channel = conectar_rabbitmq()
    if not connection or not channel:
        print("❌ No se pudo conectar a RabbitMQ. Worker no iniciado.")
        return

    def callback(ch, method, properties, body):
        respuesta = json.loads(body)
        respuestas_recibidas.append(respuesta)
        print(f"📩 Respuesta recibida: {respuesta}")

    channel.basic_consume(queue="monitor_pedidos", on_message_callback=callback, auto_ack=True)
    print("🚀 Esperando respuestas de pedidos...")
    channel.start_consuming()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4053)
