# Release Notes - v1.0

**Producto:** SCCP (Sistema de Control de Calidad Pre-Publicación)
**Fecha:** 28/01/2026
**Tag:** `v1.0-panel-170-casos`

## 🚀 Resumen del Lanzamiento
Primera versión estable del sistema unificado SCCP. Se consolida la separación de entornos (Legacy vs Producción) y se entrega el MVP funcional con validación de 170 casos iniciales.

## ✨ Novedades
- **Arquitectura:** Separación total de `auditoria-postenvio` (Legacy) y `sccp-prepublish` (Nuevo).
- **Seguridad:** Implementación de RBAC (Role-Based Access Control) con 4 niveles jerárquicos.
- **Frontend:** Tableros operativos (`/operador`, `/gerencial`, `/ejecutivo`) con renderizado HTML real.
- **Datos:** Ingesta inicial de 170 casos simulados para pruebas de estrés de los tableros.

## 🛠️ Correcciones
- Solucionado el error 404 en rutas cruzadas (aislamiento Flask verificado).
- Corregida la redirección `/validador` -> `/login` (Status 302 verificado).

## 📦 Artefactos Entregados
1. **Dataset:** `dataset_170_casos.json` (SHA256 validado).
2. **Documentación:** Protocolo de Auditoría Humana y Proceso Operativo ISO-friendly.
3. **Evidencia:** Capturas de pantalla de la puesta en marcha.

## ⚠️ Known Issues
- Las imágenes de evidencia son placeholders generados para cumplimiento documental hasta la operación real.
