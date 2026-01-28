from flask import Flask
import validador_mensajes
import logica_simple

app = Flask(__name__)

@app.route('/')
def index():
    return "Auditoría Post-Envío (LEGACY)"

@app.route('/audit')
def audit():
    return "Audit endpoint"

if __name__ == '__main__':
    app.run()
