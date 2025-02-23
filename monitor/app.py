from flask import Flask, request, jsonify
import pika
import json
import os

app = Flask(__name__)

# Conectar a RabbitMQ
def conectar_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters(os.getenv("RABBITMQ_HOST", "localhost")))
    channel = connection.channel()
    channel.queue_declare(queue="monitor_pedidos")  # Cola de respuesta
    return connection, channel

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"mensaje": "Pong!"}), 200

@app.route("/validar-pedido", methods=["POST"])
def validar_pedido():
    data = request.json
    if not data.get("id"):
        return jsonify({"error": "ID del pedido requerido"}), 400

    try:
        connection, channel = conectar_rabbitmq()
        channel.queue_declare(queue="pedidos")  # Cola de entrada
        channel.basic_publish(
            exchange="",
            routing_key="pedidos",
            body=json.dumps(data)
        )
        connection.close()
    except Exception as e:
        return jsonify({"error": "Error enviando a la cola"}), 500

    return jsonify({"mensaje": "Pedido enviado para validación"}), 202

# Worker para recibir respuestas
def recibir_respuesta():
    connection, channel = conectar_rabbitmq()

    def callback(ch, method, properties, body):
        respuesta = json.loads(body)
        print(f"📩 Respuesta recibida: {respuesta}")

    channel.basic_consume(queue="monitor_pedidos", on_message_callback=callback, auto_ack=True)
    print("🚀 Esperando respuestas de pedidos...")
    channel.start_consuming()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
