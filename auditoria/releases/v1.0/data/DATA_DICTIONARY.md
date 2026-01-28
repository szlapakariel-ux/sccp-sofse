# Diccionario de Datos - Release v1.0

## Archivo: dataset_170_casos.json

Este conjunto de datos contiene el registro histórico de las primeras 170 validaciones realizadas por el sistema SCCP unificado.

### Estructura del Objeto

| Campo | Tipo | Descripción | Valores Ejemplo |
|-------|------|-------------|-----------------|
| `id` | String | Identificador único del mensaje auditado. | `MSG-1001` |
| `timestamp` | DATETIME | Fecha y hora del procesamiento (YYYY-MM-DD HH:MM). | `2026-01-27 10:15` |
| `linea` | String | Línea ferroviaria emisora del mensaje. | `Sarmiento`, `Mitre`, `Roca` |
| `estado` | String | Dictamen final del auditor. | `APROBADO`, `RECHAZADO` |
| `motivo` | String | Justificación del rechazo (si aplica). | `Tono incorrecto`, `Falta horario` |
| `auditor` | String | Identificador del auditor responsable. | `HUMANO_SYS_01` |

### Notas de Calidad
- Integridad verificada vía SHA256.
- Fuente: Logs de auditoria/app_sccp.py (Simulación MVP 170 casos).
