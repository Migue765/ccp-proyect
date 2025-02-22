from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/verificar-inventario", methods=["POST"])
def verificar_inventario():
    return jsonify({"disponible": True}), 200  # Siempre devuelve que hay stock

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
