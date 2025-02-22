from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

SERVICES = {
    "pedidos": "http://pedidos:5000",
    "inventarios": "http://inventarios:5001",
    "compras": "http://compras:5002"
}

@app.route("/api/<servicio>/<path:endpoint>", methods=["GET", "POST"])
def proxy(servicio, endpoint):
    if servicio not in SERVICES:
        return jsonify({"error": "Servicio no encontrado"}), 404

    url = f"{SERVICES[servicio]}/{endpoint}"
    if request.method == "POST":
        response = requests.post(url, json=request.json)
    else:
        response = requests.get(url)

    return jsonify(response.json()), response.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
