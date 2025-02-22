from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import pika
import json
import os

app = Flask(__name__)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///inventarios.db")
db = SQLAlchemy(app)

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"mensaje": "Pong!"}), 200

@app.route("/verificar-inventario", methods=["POST"])
def verificar_inventario():
    return jsonify({"disponible": True}), 200  # Siempre devuelve que hay stock


if __name__ == "__main__":
    db.create_all()
    app.run(host="0.0.0.0", port=3033)
