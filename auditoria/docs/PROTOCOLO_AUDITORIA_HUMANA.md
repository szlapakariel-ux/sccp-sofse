# Protocolo de Auditoría Humana

**Objetivo:** Estandarizar el criterio de validación en `/tablero/operador`.

## Checklist de Validación

### 1. Integridad del Mensaje
- [ ] ¿El mensaje incluye Línea y Ramal?
- [ ] ¿Se especifica la estación o tramo afectado?
- [ ] ¿Hay una estimación de tiempo o acción a tomar?

### 2. Tono y Estilo
- [ ] ¿Cumple con el tono institucional (Neutro/Informativo)?
- [ ] ¿Evita palabras prohibidas ("Lamentamos", "Disculpas", etc.)?
- [ ] ¿La ortografía y gramática son impecables?

### 3. Matriz Medio-Mensaje
- [ ] ¿El canal utilizado es correcto para la severidad del evento?
  - *Demora < 10min* -> App/Web (No Push)
  - *Interrupción Total* -> Todos los canales

## Criterio de Decisión

| Situación | Acción en Sistema |
|-----------|-------------------|
| Mensaje cumple 100% | **APROBAR** |
| Mensaje tiene error menor (tilde, espacio) | **APROBAR CON OBS.** |
| Mensaje tiene error de fondo (tono, dato falso) | **RECHAZAR** |
| Sistema marcó "Error" pero el mensaje está bien | **MARCAR FALSO POSITIVO** (No enviar a operador) |

## Registro de Incidencia
Todo rechazo debe ir acompañado de una selección tipificada en el campo `Motivo`. **No usar "Otros" salvo emergencia.**
