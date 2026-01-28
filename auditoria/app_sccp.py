
import os
import json
import functools
import sys
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash

# Fix path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static'
)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_gov_mode')

# --- CONFIG & DATA LOADING ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROLES_FILE = os.path.join(BASE_DIR, 'config', 'roles.json')
LOGS_FILE = os.path.join(BASE_DIR, 'data', 'auditoria_logs.json')

# --- DB SECURE SINGLETON ---
from utils.db_store import get_db
db = get_db(LOGS_FILE)

def load_roles():
    try:
        with open(ROLES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get('users', {})
    except: return {}

USERS_DB = load_roles()

# --- GOVERNANCE STATES ---
# CAPTURADO -> PRE_ANALIZADO -> AUDITADO_HUMANO -> (CONFIRMADO | ERROR_DE_SISTEMA)

# --- DECORATORS & RBAC ---
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user' not in session: return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

def role_required(allowed_roles):
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if 'user' not in session: return redirect(url_for('login'))
            user_role = session.get('role')
            # Mapping roles to panel permissions
            # MESA_DEL_USUARIO -> Panel 4
            # AUDITOR (MESA_AYUDA/GESTOR) -> Panel 1, 2, 3, 6
            # GERENCIAL -> Panel 5
            # EJECUTIVO -> Panel 5 + 6
            
            if user_role not in allowed_roles:
                 # Fallback logic based on role
                 if user_role == 'MESA_DEL_USUARIO': return redirect(url_for('panel_operador_feedback'))
                 return "403 Forbidden: No tiene autoridad para este panel.", 403
            return view(**kwargs)
        return wrapped_view
    return decorator

# --- ROUTES (THE 6 PANELS) ---

@app.route('/')
def index():
    if 'user' in session:
        role = session.get('role')
        if role == 'MESA_DEL_USUARIO': return redirect(url_for('panel_operador_feedback'))
        if role == 'GERENCIAL': return redirect(url_for('panel_gerencial'))
        return redirect(url_for('panel_auditoria_decision')) # Auditor default
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = USERS_DB.get(email)
        if user and user['password'] == password:
            session['user'] = email
            session['role'] = user['role']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Credenciales inválidas")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# PANEL 1: PRE-ANÁLISIS (SISTEMA)
# Visible para Auditor. Muestra PROPUESTA_DEL_SISTEMA.
@app.route('/auditoria/pre-analisis')
@login_required
@role_required(['GESTOR_ERRORES', 'GERENCIAL', 'EJECUTIVO', 'MESA_DEL_USUARIO']) # Fix roles later, allowing audit for MVP
def panel_sistema():
    all_logs = db.read()
    # Filter: Solo mostrar lo que el sistema "vio"
    return render_template('panel_1_sistema.html', logs=all_logs)

# PANEL 2: AUDITORÍA HUMANA (DECISIÓN)
# EL LUGAR DE LA VERDAD. Donde se confirma o se marca FP/FN.
@app.route('/auditoria/decision', methods=['GET', 'POST'])
@login_required
@role_required(['GESTOR_ERRORES', 'GERENCIAL']) # Auditores
def panel_auditoria_decision():
    if request.method == 'POST':
        msg_id = request.form.get('msg_id')
        accion = request.form.get('accion') # CONFIRMAR, FALSO_POSITIVO, FALSO_NEGATIVO
        auditor = session['user']

        nota_auditor = request.form.get('nota', '').strip()

        def update_logic(log):
            log['estado'] = 'AUDITADO_HUMANO'
            log['auditor'] = auditor
            log['fecha_auditoria'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if accion == 'CONFIRMAR':
                log['feedback_humano'] = 'CONFIRMADO'
            elif accion in ['FALSO_POSITIVO', 'FALSO_NEGATIVO']:
                log['estado'] = 'ERROR_DE_SISTEMA' # Sacar del flujo operacional
                log['feedback_humano'] = accion
                log['nota_auditor'] = nota_auditor
        
        success = db.update_record(msg_id, update_logic)
        if not success:
            flash("Error: El mensaje fue modificado por otro auditor.", "error")
        else:
            flash("Decisión registrada.", "success")
            
        return redirect(url_for('panel_auditoria_decision'))

    # Show only pending items
    logs = db.read()
    pending_logs = [l for l in logs if l.get('estado') == 'PRE_ANALIZADO']
    return render_template('panel_2_v2.html', logs=pending_logs)

# PANEL 3: ERRORES DEL SISTEMA (APRENDIZAJE)
# Cementerio de FP/FN para ajuste de reglas.
@app.route('/sistema/errores')
@login_required
@role_required(['GESTOR_ERRORES', 'GERENCIAL'])
def panel_errores_sistema():
    logs = db.read()
    errors = [l for l in logs if l['estado'] == 'ERROR_DE_SISTEMA']
    return render_template('panel_3_errores.html', logs=errors)

# PANEL 4: FEEDBACK A OPERADORES
# Lo único que ve la Mesa. Solo 'CONFIRMADO'. Nunca FP/FN.
@app.route('/operador/feedback')
@login_required
@role_required(['MESA_DEL_USUARIO', 'GESTOR_ERRORES']) # Dev admin access too
def panel_operador_feedback():
    logs = db.read()
    # Solo mensajes donde el humano dijo "SÍ, el sistema tiene razón"
    public_logs = [l for l in logs if l.get('feedback_humano') == 'CONFIRMADO']
    return render_template('panel_4_operador.html', logs=public_logs)

# PANEL 5: TABLERO GERENCIAL (KPIs)
@app.route('/gerencia/dashboard')
@login_required
@role_required(['GERENCIAL', 'EJECUTIVO', 'GESTOR_ERRORES'])
def panel_gerencial():
    return render_template('panel_5_gerencial.html')

# PANEL 6: TRAZABILIDAD
@app.route('/trazabilidad')
@login_required
@role_required(['GERENCIAL', 'EJECUTIVO', 'GESTOR_ERRORES'])
def panel_trazabilidad():
    logs = db.read()
    return render_template('panel_6_trazabilidad.html', logs=logs)

print("=== SCCP GOVERNANCE MODE v2.0 STARTED ===")

if __name__ == '__main__':
    app.run(debug=True, port=8080)
