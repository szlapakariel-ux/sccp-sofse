# SCCP - Proceso Operativo Estándar (v1.0)

**Autoridad:** Arquitectura Lógica SOFSE  
**Fecha:** 28/01/2026  
**Versión:** 1.0  

## 1. Definición y Alcance
El Sistema de Control de Calidad Pre-Publicación (SCCP) es una herramienta de **auditoría post-envío no obstructiva**. Su objetivo es garantizar que la comunicación operativa cumpla la normativa institucional sin detener el flujo de información crítico.

## 2. Roles y Responsabilidades

### 2.1 Mesa de Usuario (Operador)
- **Función:** Generar y emitir el mensaje operativo a los pasajeros.
- **Responsabilidad:** Precisión del dato (hora, ramal, estación).
- **Límite:** No realiza auditoría de estilo ni define normas.

### 2.2 Sistema Automático (Pre-Análisis)
- **Función:** Scrapear y comparar el mensaje contra la Matriz Medio-Mensaje.
- **Responsabilidad:** Detectar patrones de desvío conocidos.
- **Límite:** No toma decisiones. Emite un "dictamen propuesto" al auditor.

### 2.3 Auditor Humano (Decision Maker)
- **Función:** Validar o rectificar el dictamen del sistema.
- **Responsabilidad:** Es el único autorizado para calificar un mensaje como "Error".
- **Límite:** Audita al sistema, no persigue al operador.

## 3. Flujo Operativo (Happy Path)
1. Operador envía mensaje.
2. Sistema captura y analiza.
3. Auditor recibe el caso en `/tablero/operador`.
4. Auditor confirma dictamen del sistema:
   - Si es **Correcto**: el feedback fluye al Dashboard de Operadores.
   - Si es **Incorrecto (Divergencia)**: Se activa protocolo de Ajuste de Reglas.

## 4. Gestión de Divergencias (Falsos Positivos/Negativos)
Si el Auditor no está de acuerdo con el Sistema:
1. **Acción Inmediata:** Se marca la divergencia en el registro.
2. **Consecuencia:** NO se notifica al Operador (para evitar confusión).
3. **Resolución:** El caso pasa a `ajuste_reglas` para refinar la Matriz.

## 5. Principio Rector
> "El sistema no aprende solo. El operador no paga por los bugs del sistema. El auditor es la verdad final."
