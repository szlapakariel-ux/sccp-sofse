import sys
import os
from flask import Flask

# Ensure root is in path if not already (mostly for local testing safety)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sccp.gatekeeper import Gatekeeper

app = Flask(__name__)

print("Running gunicorn auditoria.app_sccp:app")

@app.route('/')
def index():
    return "SCCP Pre-Publicación"

@app.route('/login')
def login():
    return "Login"

@app.route('/validador')
def validador():
    return "Validador"

@app.route('/tablero/operador')
def tablero_operador():
    return "Tablero Operador"

@app.route('/tablero/gerencial')
def tablero_gerencial():
    return "Tablero Gerencial"

@app.route('/tablero/ejecutivo')
def tablero_ejecutivo():
    return "Tablero Ejecutivo"

# Print routes for validation in logs
with app.app_context():
    print("Registered Routes:")
    for rule in app.url_map.iter_rules():
        print(rule)

if __name__ == '__main__':
    app.run()
