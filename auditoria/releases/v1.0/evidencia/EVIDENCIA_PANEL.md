# Evidencia del Panel de Control (v1.0)

**Nota de Auditoría:** Este documento consagra la evidencia técnica disponible al momento del Release v1.0.

## 1. Capturas de Pantalla (Interfaz Gráfica)
Debido a restricciones de entorno de ejecución (servidor headless), la captura visual directa no está disponible en este ciclo de auditoría.

- **Pantalla de Login** → **[PENDIENTE DE CARGA MANUAL]**
- **Validador (Form)** → **[PENDIENTE DE CARGA MANUAL]**
- **Tableros** → **[PENDIENTE DE CARGA MANUAL]**

*Acción requerida: El operador humano deberá adjuntar las capturas en la ruta `auditoria/releases/v1.0/evidencia/img/` tras la validación en navegador.*

## 2. Evidencia Técnica Reproducible (HTTP Probes)
Para garantizar la trazabilidad inalterable del despliegue, se adjunta el reporte técnico de endpoints generado automáticamente.

> **Archivo Fuente:** [http_probe_results.json](./http_probe_results.json)  
> **Resumen:** [http_probe_results.md](./http_probe_results.md)

### Resumen de Hallazgos
1. **MVP Activo:** Endpoint `/login` responde 200 OK con contenido HTML (verificado por Hash/Length).
2. **Seguridad:** Endpoints internos (`/validador`) rechazan conexión sin sesión (302/403).
3. **Aislamiento:** Entorno Legacy responde 404 a solicitudes del nuevo sistema.

---
**Firma Digital:** Script `probe_endpoints.ps1` - SHA256 [Hash del script]
