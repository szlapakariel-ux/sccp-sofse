# 🛠️ LISTA DE CORRECCIONES CRÍTICAS (P0 FIXLIST)
**Fecha:** 28/01/2026
**Estado:** Pendiente de Ejecución

Esta lista contiene las acciones atómicas para resolver los hallazgos de riesgo crítico (P0) detectados en la auditoría.

---

## 🗑️ 1. LIMPIEZA DE ARQUITECTURA (H-03)
**Acción:** Eliminar archivos obsoletos que confunden el mantenimiento.
```bash
# Ejecutar en terminal:
git rm app_minimal.py
git rm logica_simple.py
git rm dashboard_operadores.html
git rm generate_data.py
# (Opcional) Mover revalidador a utils
mkdir -p auditoria/utils
git mv revalidador.py auditoria/utils/
```

## 🔒 2. SEGURIDAD DE SESIÓN (H-01)
**Archivo:** `auditoria/app_sccp.py`
**Acción:** Reemplazar hardcode por variable de entorno robusta.
```python
# ANTES:
# app.secret_key = 'super_secret_key_gov_mode'

# DESPUÉS:
import secrets
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
```

## 💾 3. INTEGRIDAD DE DATOS / CONCURRENCIA (H-02)
**Archivo:** `auditoria/app_sccp.py`
**Acción:** Implementar bloqueo simple para evitar corrupción de JSON.
```python
from filelock import FileLock

def save_logs(logs):
    lock = FileLock(f"{LOGS_FILE}.lock")
    with lock:
        with open(LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2)
```
*Requiere:* `pip install filelock`

## 🚀 4. PAGINACIÓN DE PANELES (H-04)
**Archivo:** `auditoria/app_sccp.py`
**Acción:** No renderizar lista completa si N > 50.
```python
@app.route('/auditoria/decision')
def panel_auditoria_decision():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    # ... cargar logs ...
    pending_logs = [l for l in logs if l['estado'] == 'PRE_ANALIZADO']
    
    # Slice simple
    start = (page - 1) * per_page
    end = start + per_page
    items = pending_logs[start:end]
    
    return render_template('panel_2_decision.html', logs=items, page=page)
```

## 🛡️ 5. BACKUP DIARIO (H-10)
**Nuevo Archivo:** `auditoria/utils/backup_job.py`
**Acción:** Script simple para cron/scheduller.
```python
import shutil
import datetime
import os

src = "../data/auditoria_logs.json"
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
dst = f"../data/backups/logs_{ts}.json"

os.makedirs(os.path.dirname(dst), exist_ok=True)
shutil.copy2(src, dst)
print(f"Backup creado: {dst}")
```

---

## ⚠️ INSTRUCCIONES PARA DESARROLLADOR
1. Ejecutar limpieza de archivos (Punto 1).
2. Aplicar cambio de `SECRET_KEY` (Punto 2).
3. Instalar `filelock` y aplicar patch de concurrencia (Punto 3).
4. Hacer Commit: `Fix: Apply P0 Audit Findings`.
