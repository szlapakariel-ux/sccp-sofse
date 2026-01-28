# Reporte Técnico de Pruebas HTTP

**Fecha:** 01/28/2026 00:30:51

| Nombre | URL | Método | Status | Length | Location/Hash |
|---|---|---|---|---|---|
| Login | https://sccp-prepublish.onrender.com/login | GET | **200** | 1620 | SHA256: 45435960... |
| Validador (No Auth) | https://sccp-prepublish.onrender.com/validador | HEAD | **500** | 0 |  |
| Tablero Operador (No Auth) | https://sccp-prepublish.onrender.com/tablero/operador | HEAD | **500** | 0 |  |
| Legacy Root | https://auditoria-postenvio.onrender.com/ | HEAD | **200** | 0 |  |
| Legacy Insolation Check | https://auditoria-postenvio.onrender.com/tablero/operador | HEAD | **404** | 0 |  |

