from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

SERVICES = {
    "pedidos": "http://gestion_pedidos:5000", # pedidos:5000
    "inventarios": "http://inventarios:3033",
    "compras": "http://compras:4043"
}

@app.route("/api/<servicio>/<path:endpoint>", methods=["GET", "POST","PUT","DELETE"])
def proxy(servicio, endpoint):
    if servicio not in SERVICES:
        return jsonify({"error": "Servicio no encontrado"}), 404

    url = f"{SERVICES[servicio]}/{endpoint}"
    if request.method == "POST":
        response = requests.post(url, json=request.json)
    elif request.method == "PUT":
        response = requests.put(url, json=request.json)
    elif request.method == "DELETE":
        response = requests.delete(url, json=request.json)
    else:
        print("hola")
        response = requests.Response()
        # response.status_code = 200
        # response._content = b'{"message": "Respuesta hardcodeada para pruebas"}'
        response = requests.get(url, params=request.args)
    

    return jsonify(response.json()), response.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8020)
