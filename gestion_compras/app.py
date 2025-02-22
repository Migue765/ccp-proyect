from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"mensaje": "Pong!"}), 200

@app.route("/procesar-compra", methods=["POST"])
def procesar_compra():
    return jsonify({"compra_aprobada": True}), 200  # Simula éxito en compra


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4043)
