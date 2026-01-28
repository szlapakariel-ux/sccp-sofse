# 🧪 PROTOCOLO DE PRUEBAS DE CALIDAD (QA) - SCCP v3.1

Este documento define la lista de comprobación paso a paso para validar la estabilidad, seguridad y correctitud funcional del Sistema de Gobierno de Comunicaciones.

---

## 🟢 FASE 1: LÓGICA DEL MOTOR (validador_mensajes.py)
*Objetivo: Asegurar que el cerebro del sistema juzgue correctamente.*

- [ ] **Prueba de Sintaxis "Perfecta"**
    - [ ] Input: `3.1.A EL TREN 3344 DE LAS 14:00 HS DE RETIRO HACIA PILAR CIRCULA CON 10 MINUTOS DE DEMORA POR PROBLEMAS TECNICOS.`
    - [ ] Resultado Esperado: `CORRECTO` / `COMPLETO`.
- [ ] **Prueba de "Error Humano Común" (Guiones bajos)**
    - [ ] Input: `...CON DEMORAS DE_10 MINUTOS...`
    - [ ] Resultado Esperado: `INCORRECTO` o `OBSERVACION`. (El sistema debe detectar el caracter sucio).
- [ ] **Prueba de Coherencia de Contingencias**
    - [ ] Input: Usar código `17.1.A` pero escribir "POR PROBLEMAS TECNICOS" (Texto de cód 03).
    - [ ] Resultado Esperado: `OBSERVACION` (Alerta de inconsistencia Código vs Texto).
- [ ] **Prueba de Cancelación**
    - [ ] Input: `...HA SIDO CANCELADO...`
    - [ ] Resultado Esperado: `CORRECTO`. No debe pedir "minutos de demora".

## 🔵 FASE 2: FLUJO DE DATOS E INTEGRACIÓN
*Objetivo: Asegurar que los datos viajan sin corromperse entre capas.*

- [ ] **Importación de Lote Histórico**
    - [ ] Acción: Ejecutar `importar_datos_ui.py`.
    - [ ] Verificación: Abrir `auditoria_logs.json` y verificar que el campo `estado` sea `PRE_ANALIZADO`.
- [ ] **Persistencia de Decisión**
    - [ ] Acción: En Panel 2, tomar un mensaje y marcarlo como `CONFIRMAR`.
    - [ ] Verificación: Reiniciar el servidor y verificar que el mensaje NO volvió a aparecer en Panel 2 (estado persistente).

## 🟠 FASE 3: INTERFAZ Y EXPERIENCIA (UI/UX)
*Objetivo: Validar el diseño "Premium" y la usabilidad.*

- [ ] **Renderizado de Tarjetas**
    - [ ] Verificar que no se ve la tabla antigua HTML.
    - [ ] Verificar que los "Badges" de dictamen (Verde/Rojo) son visibles claramente.
- [ ] **Respuesta Móvil (Responsive)**
    - [ ] Achicar la ventana del navegador a tamaño celular.
    - [ ] Verificar que la Sidebar se comporte correctamente (o al menos no rompa el layout crítico).
- [ ] **Feedback Visual**
    - [ ] Al hacer clic en "Confirmar", ¿hay una transición o recarga suave?

## 🔴 FASE 4: SEGURIDAD Y ROLES (RBAC)
*Objetivo: Blindar el sistema de accesos no autorizados.*

- [ ] **Intento de Acceso Operador**
    - [ ] Login con `operador@sofse.gob.ar`.
    - [ ] Intentar acceder manualmente a `/auditoria/decision`.
    - [ ] Resultado Esperado: Redirección forzada a `/operador/feedback` o Error 403.
- [ ] **Intento de Acceso Anónimo**
    - [ ] Abrir ventana incógnito y entrar directo a `/auditoria/decision`.
    - [ ] Resultado Esperado: Redirección inmediata al Login.

## 🟣 FASE 5: CICLO COMPLETO (End-to-End)
*Objetivo: Simular un día de trabajo real.*

1.  **Ingesta:** Cargar un caso "sucio" nuevo en el JSON.
2.  **Auditoría:** Entrar como Gestor, ver el caso en Panel 2, marcarlo como "Falso Positivo".
3.  **Verificación Error:** Ir al Panel 3 y confirmar que el mensaje cayó ahí.
4.  **Verificación Operador:** Entrar como Operador y asegurar que ESE mensaje NO aparece en su bandeja (Panel 4).

---

### 📝 REGISTRO DE EJECUCIÓN
*Fecha: 28/01/2026*
*Tester: Ariel Szlapak*
*Versión: v3.1*

| ID Prueba | Estado | Observaciones |
|-----------|--------|---------------|
| QA-001    | ...    | ...           |
| ...       | ...    | ...           |
