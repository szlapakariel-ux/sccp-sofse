# 🔍 INFORME DE AUDITORÍA TÉCNICA Y MEJORES PRÁCTICAS - SOFSE
**Fecha:** 28/01/2026
**Auditor:** Ariel Szlapak (Assist by AI)
**Versión Repo:** 3.1
**Objetivo:** Revisión integral de arquitectura, seguridad y mantenibilidad.

---

## 1. 📋 RESUMEN EJECUTIVO
El repositorio ha evolucionado exitosamente de una prueba de concepto (PoC) a una aplicación Web de Gobierno estructurada.
*   **Fortalezas:** El núcleo de validación (`validador_mensajes.py`) es robusto y experto. La nueva interfaz "Premium" resuelve la deuda de UX. La arquitectura de carpetas en `auditoria/` es limpia.
*   **Debilidades:** Persisten "archivos basura" en la raíz que ensucian el despliegue. La capa de persistencia (JSON plano) es un riesgo de concurrencia P0. Faltan pruebas unitarias automatizadas.
*   **Estado:** **LISTO PARA BETA INTERNA** (Con fixes P0 aplicados).

---

## 2. 📂 ANÁLISIS ARCHIVO POR ARCHIVO

### 🐍 NÚCLEO PYTHON

#### `validador_mensajes.py`
*   **Propósito:** Motor de lógica de negocio y validación de reglas (Regex).
*   **👍 Qué hace bien:** Centraliza toda la inteligencia. Manejo de excepciones en regex.
*   **👎 Riesgo:** Monolítico (1000+ líneas). Contiene lógica de negocio mezclada con parsing.
*   **💡 Recomendación:** Extraer definiciones de Regex a `config/regex_patterns.json` para no tocar código al ajustar reglas.
*   **Prioridad:** P2 | **Impacto:** Mantenibilidad.

#### `auditoria/app_sccp.py`
*   **Propósito:** Controlador Web (Flask), rutas y seguridad.
*   **👍 Qué hace bien:** Usa Decoradores para RBAC (`@role_required`). Estructura clara de rutas.
*   **👎 Riesgo:** `SECRET_KEY` harcodeada o dependencia débil de ENV. Bloqueo de archivos JSON no gestionado.
*   **💡 Recomendación:** Implementar `python-dotenv` para secretos y `filelock` para escritura segura.
*   **Prioridad:** **P0** | **Impacto:** Seguridad/Integridad de Datos.

#### `revalidador.py`
*   **Propósito:** Adaptador para procesar lotes históricos con lógica nueva.
*   **👍 Qué hace bien:** Patrón Adapter para normalizar esquemas de datos distintos (viejos vs nuevos).
*   **👎 Riesgo:** Lógica de fechas duplicada respecto al validador principal.
*   **💡 Recomendación:** Unificar parser de fechas en una utilidad común `utils/date_parser.py`.
*   **Prioridad:** P2 | **Impacto:** Calidad de Datos.

### 🗑️ ARCHIVOS LEGACY (BASURA)
*   `app_minimal.py`, `logica_simple.py`, `dashboard_operadores.html`
*   **Propósito:** Vestigios de versiones anteriores.
*   **👎 Riesgo:** Confunden al desarrollador nuevo y ensucian el entorno de producción.
*   **💡 Recomendación:** **ELIMINAR INMEDIATAMENTE.**
*   **Prioridad:** **P1** | **Impacto:** Operación.

### 🌐 FRONTEND (TEMPLATES)

#### `auditoria/templates/layout.html`
*   **Propósito:** Estructura base y estilos globales.
*   **👍 Qué hace bien:** Inyección de CSS crítico (Fallback) para robustez visual.
*   **👎 Riesgo:** Lógica de navegación un poco dispersa con múltiples `if session`.
*   **💡 Recomendación:** Crear un `macro` de Jinja para el menú de navegación basado en roles.
*   **Prioridad:** P2 | **Impacto:** UX/Mantenibilidad.

#### `auditoria/templates/panel_2_decision.html`
*   **Propósito:** Interfaz crítica de auditoría humana.
*   **👍 Qué hace bien:** Uso de tarjetas ("Cards") y feedback visual inmediato (Badges).
*   **👎 Riesgo:** No tiene paginación (si hay 500 mensajes, colapsa el DOM).
*   **💡 Recomendación:** Implementar paginación simple (20 por página) en el backend.
*   **Prioridad:** **P1** | **Impacto:** Performance.

---

## 3. 📚 BIBLIOTECA DE MEJORES PRÁCTICAS (PATRONES EXTRAÍDOS)

A continuación, los patrones "Dorados" detectados en el código que deben estandarizarse:

### A. Compatibilidad y Resiliencia
*   **Patrón:** *Importación Defensiva*
    ```python
    try:
        import win32com.client
    except ImportError:
        class MockClient: ... # Fallback para Linux/Cloud
    ```
    *Aplicable a:* Integraciones con Outlook, Excel, Pandas.

### B. Separación de Responsabilidades
*   **Patrón:** *Validador Puro*
    El `validador_mensajes.py` no sabe de HTML ni de bases de datos. Recibe un Diccionario, devuelve un Diccionario con Score.
    *Regla:* Mantener el núcleo agnóstico a la interfaz.

### C. UX Gubernamental
*   **Patrón:** *Feedback Constructivo*
    En lugar de "Error Fatal", el sistema devuelve:
    > "Observación: Se detectó X, se sugiere Y. (Regla R-05)"
    *Regla:* El tono debe ser pedagógico, no punitivo.

### D. Seguridad por Diseño
*   **Patrón:** *Decoradores de Rol*
    ```python
    @role_required(['GESTOR', 'GERENCIA'])
    def ver_tablero(): ...
    ```
    *Regla:* Nunca confiar en la ocultación de menús. Proteger la ruta en el servidor.

---

## 4. 🚨 TOP 10 HALLAZGOS P0 (Riesgo Crítico)

| ID | Hallazgo | Riesgo | Recomendación (Fix) |
|:---|:---|:---|:---|
| **H-01** | `SECRET_KEY` Default | Secuestro de sesiones | Usar `os.environ.get()` obligatorio. |
| **H-02** | Escritura JSON Concurrente | **Pérdida de Datos** | Implementar `filelock` o migrar a SQLite. |
| **H-03** | Archivos Basura en Root | Confusión en Deploy | `git rm app_minimal.py logica_simple.py ...` |
| **H-04** | Paginación Ausente | Bloqueo de Navegador | Limitar logs a 50 en `app_sccp.py`. |
| **H-05** | Rutas Estáticas Hardcode | Error 404 en Prod | Usar siempre `url_for('static', ...)` (Ya corregido en layout). |
| **H-06** | Falta de Logs de Auditoría | Repudio de Acciones | Loguear *quién* aprobó el mensaje en archivo texto aparte/DB. |
| **H-07** | Input no Sanitizado (Teórico) | XSS | Asegurar que Jinja use `autoescape=True` (Default, verificar). |
| **H-08** | Dependencia de CSV/Excel | Lentitud | Migrar todo config a JSON (En proceso, OK). |
| **H-09** | Feedback Loop Roto | Operador ciego | Activar envío real de email o notificación en Panel 4. |
| **H-10** | Sin Backup Automático | Desastre | Script diario que copie `auditoria_logs.json` a `/backup`. |

---

## 5. 🗺️ MAPA DE ROLES Y PANTALLAS (PROPUESTA FINAL)

### 🤖 PRE-CLASIFICADOR (Sistema)
*   **Input:** Mensajes crudos (API/Excel).
*   **Pantalla:** *Panel 1 (Pre-Análisis)* - Solo lectura para admins.
*   **Acción:** Asignar Score y Estado `PRE_ANALIZADO`.

### ⚖️ JUEZ / AUDITOR (Gestor de Errores)
*   **Input:** Bandeja de pendientes (`PRE_ANALIZADO`).
*   **Pantalla:** *Panel 2 (Mesa de Decisión)*.
*   **Acción:**
    *   `CONFIRMAR` -> Pasa a Operador.
    *   `FALSO POSITIVO` -> Pasa a Ajuste (Dev).
    *   `FALSO NEGATIVO` -> Pasa a Ajuste (Dev).

### 🎓 OPERADOR (Usuario Final)
*   **Input:** Feedback educativo.
*   **Pantalla:** *Panel 4 (Feedback)* y *Correo Electrónico*.
*   **Acción:** Leer, confirmar lectura ("Enterado"), mejorar próximo mensaje.

### 🧪 INGENIERO (Dev)
*   **Input:** Casos de Borde (FP/FN).
*   **Pantalla:** *Panel 3 (Errores de Sistema)*.
*   **Acción:** Ajustar Regex en `validador_mensajes.py`.

---

## 6. 📅 PLAN DE IMPLEMENTACIÓN (3 ETAPAS)

### ETAPA 1: HIGIENE Y SEGURIDAD (Inmediato)
1.  Eliminar archivos basura.
2.  Proteger escritura de DB (Locking).
3.  Implementar Paginación básica.

### ETAPA 2: CONSOLIDACIÓN OPERATIVA (Semana 1)
1.  Habilitar Panel 4 para Operadores reales (Login simple).
2.  Activar simulador de envío de email.
3.  Backup automático de logs.

### ETAPA 3: DESPLIEGUE FINAL (Semana 2)
1.  Dockerizar solución completa.
2.  Dashboard Gerencial con gráficas reales de tendencia.
3.  Migración a Base de Datos relacional (PostgreSQL) si el volumen supera 10k mensajes.

---

## ✅ CHECKLIST DE PRE-PUBLICACIÓN
- [ ] 🗑️ Root limpio de archivos viejos.
- [ ] 🔒 `SECRET_KEY` segura configurada.
- [ ] 📱 Interfaz Mobile-Friendly verificada.
- [ ] 💾 Mecanismo de Backup de `auditoria_logs.json` activo.
- [ ] 🚦 Semáforos de calidad visualizando datos reales.
- [ ] 🧪 Test de estrés (100 mensajes simultáneos) pasado.

**Firmado:**
*Ariel Szlapak - Lead Architect*
