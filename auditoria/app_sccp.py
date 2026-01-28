import os
import json
import functools
import sys
from flask import Flask, render_template, request, redirect, url_for, session, flash

# Fix path to locate modules if necessary
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_dev_mode')

print("=== STARTUP DIAGNOSTICS ===")
print("RUNNING SCCP FULL MVP")
print(f"CWD: {os.getcwd()}")
print(f"Template Folder: {app.template_folder}")
print(f"Static Folder: {app.static_folder}")
print(f"Abs Template Path: {os.path.abspath(app.template_folder)}")
print("===========================")

# --- CONFIG & DATA LOADING ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROLES_FILE = os.path.join(BASE_DIR, 'config', 'roles.json')
LOGS_FILE = os.path.join(BASE_DIR, 'data', 'auditoria_logs.json')

def load_roles():
    try:
        with open(ROLES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get('users', {})
    except Exception as e:
        print(f"Error loading roles: {e}")
        return {}

def load_logs():
    try:
        with open(LOGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading logs: {e}")
        return []

USERS_DB = load_roles()

# --- DECORATORS ---
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

def role_required(required_role):
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if 'user' not in session:
                return redirect(url_for('login'))
            
            user_role = session.get('role')
            # Simply check if role matches. In a real app, hierarchy logic matches better.
            # Here we follow the prompt strictly: specific roles for specific paths.
            # Hierarchy mapping for simplicity:
            hierarchy = {
                'EJECUTIVO': 4,
                'GERENCIAL': 3,
                'GESTOR_ERRORES': 2,
                'MESA_DEL_USUARIO': 1
            }
            
            req_level = hierarchy.get(required_role, 0)
            user_level = hierarchy.get(user_role, 0)

            # Strict check or Hierarchy check? Prompt says "Roles mínimos". Let's assume hierarchy.
            if user_level < req_level:
                return "403 Forbidden: Acceso restringido para su rol.", 403
                
            return view(**kwargs)
        return wrapped_view
    return decorator

print("Running gunicorn auditoria.app_sccp:app - FULL MVP MODE")

# --- ROUTES ---

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('validador'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_data = USERS_DB.get(email)
        
        if user_data and user_data['password'] == password:
            session['user'] = email
            session['role'] = user_data['role']
            # Intelligent redirect based on role
            role = user_data['role']
            if role == 'EJECUTIVO': return redirect(url_for('tablero_ejecutivo'))
            if role == 'GERENCIAL': return redirect(url_for('tablero_gerencial'))
            if role == 'GESTOR_ERRORES': return redirect(url_for('tablero_operador')) # Or gerencial
            return redirect(url_for('validador')) # Default Op
        else:
            return render_template('login.html', error="Credenciales inválidas")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/validador')
@login_required
@role_required('MESA_DEL_USUARIO')
def validador():
    return render_template('validador.html')

@app.route('/tablero/operador')
@login_required
@role_required('MESA_DEL_USUARIO')
def tablero_operador():
    logs = load_logs()
    # Simple simulation logic pass
    return render_template('tablero_operador.html', logs=logs)

@app.route('/tablero/gerencial')
@login_required
@role_required('GERENCIAL')
def tablero_gerencial():
    return render_template('tablero_gerencial.html')

@app.route('/tablero/ejecutivo')
@login_required
@role_required('EJECUTIVO')
def tablero_ejecutivo():
    return render_template('tablero_ejecutivo.html')

# Start logic for debugging locally
if __name__ == '__main__':
    app.run(debug=True, port=8080)
