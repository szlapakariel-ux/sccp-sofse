"""
Validador de Mensajes SOFSE - Sistema ROCA v3.0
Autor: Ariel - SOFSE Yunex/Constitución  
Fecha: Diciembre 2024

MEJORAS IMPLEMENTADAS (v3.0):
1. ✅ Sección INFORMACIÓN FALTANTE solo si hay faltantes
2. ✅ CANCELADO/SUSPENDIDO no marca tardanza
3. ✅ Estados detectados con espacios múltiples (regex flexible)
4. ✅ Eliminada sugerencia del guion
5. ✅ Detecta inconsistencia código vs contingencia
6. ✅ SERVICIO_GENERAL no muestra tiempo de respuesta
7. ✅ Mensaje sin referencia a Excel
8. ✅ Sin repetir mensaje original en ejemplo
9. ✅ Detecta "DEMORA" singular con cantidad
10. ✅ Advierte código 17 (excepcional)

CLASIFICACIÓN:
- COMPLETO: Mensaje perfecto (antes EXCELENTE)
- IMPORTANTE: Falta información obligatoria
- OBSERVACIONES: Problemas de formato/proceso
- SUGERENCIAS: Mejoras opcionales
"""

import pandas as pd
import json
import re
import glob
import os
import sys
import io

# Forzar UTF-8 en consola Windows para evitar error con emojis
# Forzar UTF-8 en consola Windows para evitar error con emojis
if sys.platform == 'win32':
    # Check if already wrapped or closed to avoid crash on reload
    try:
        if isinstance(sys.stdout, io.TextIOWrapper) and sys.stdout.encoding.lower() != 'utf-8':
             sys.stdout.reconfigure(encoding='utf-8')
        elif not isinstance(sys.stdout, io.TextIOWrapper):
             # Original logic but guarded
             sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
             sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass # Ignore errors here to prevent module crash

from datetime import datetime, timedelta

# Corrector ortográfico liviano (pyspellchecker)
try:
    from spellchecker import SpellChecker
    CORRECTOR_DISPONIBLE = True
    # Inicializar corrector (se puede mover a una variable global o lazy load)
    spell = SpellChecker(language='es')
except ImportError:
    CORRECTOR_DISPONIBLE = False
    spell = None

def cargar_config(linea="ROCA"):
    """Carga configuración específica de la línea"""
    try:
        # Normalizar nombre línea
        if not linea: linea = "ROCA"
        nombre_clean = linea.strip().lower().replace(' ', '_')
        if 'san_martin' in nombre_clean: nombre_clean = 'san_martin'
        
        # Buscar path relativo a este script
        base_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_path, "configs", f"config_{nombre_clean}.json")
        
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Fallback a ROCA si no existe (para compatibilidad)
            # print(f"⚠️ Config no encontrada para {linea}, usando ROCA por defecto")
            path_roca = os.path.join(base_path, "configs", "config_roca.json")
            if os.path.exists(path_roca):
                with open(path_roca, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"palabras_tecnicas": []}
            
    except Exception as e:
        print(f"❌ Error cargando config: {e}")
        return {"palabras_tecnicas": []}

# =================================================================
#                    MAPEOS DE ESTADOS
# =================================================================

MAP_ESTADOS_CODIGO = {
    '1': {
        'nombre': 'DEMORA',
        'patrones': [
            r'CIRCULA\s+CON\s+DEMORAS?(?:\s+DE)?',
            r'REGISTRA\s+DEMORAS?',
            # MEJORA #5: Variantes de demora de partida
            r'SE\s+ENCUENTRA\s+DEMORANDO',
            r'DEMORANDO\s+SU\s+PARTIDA',
            r'DEMORA(?:S)?\s+EN\s+(?:LA\s+)?PARTIDA',
            r'PARTIDA\s+DEMORADA'
        ]
    },
    '2': {
        'nombre': 'CANCELACIÓN',
        'patrones': [
            r'HA\s+SIDO\s+CANCELADO',
            r'FUE\s+CANCELADO',
            r'SE\s+CANCEL[OÓ]',
            r'SER[AÁ]\s+CANCELADO'
        ]
    },
    '2B': {
        'nombre': 'SUSPENSIÓN',
        'patrones': [
            r'HA\s+SIDO\s+SUSPENDIDO',
            r'FUE\s+SUSPENDIDO',
            r'SE\s+SUSPEND[EÍ]',
            r'SER[AÁ]\s+SUSPENDIDO',
            r'SUSPENDIDO\s+EN',
            r'SER[AÁ]\s+SUSPENDIOD'  # Detectar typo común
        ]
    },
    '3': {
        'nombre': 'RESTABLECIMIENTO',
        'patrones': [
            # MEJORA #5: Agregar estado RESTABLECIMIENTO
            r'SE\s+RESTABLECE',
            r'RESTABLECE\s+(?:EL\s+)?SERVICIO',
            r'SERVICIO\s+RESTABLECIDO'
        ]
    },
    '4': {
        'nombre': 'REDUCIDO',
        'patrones': [
            r'CIRCULA\s+REDUCIDO',
            r'SERVICIO\s+REDUCIDO',
            # MEJORA: Patrones adicionales reportados
            r'(?:ESQUEMA|CRONOGRAMA|DIAGRAMA)\s+(?:DE\s+)?(?:SERVICIO\s+)?REDUCIDO',
            r'REDUCIDO\s+(?:POR|EN)'
        ]
    },
    '5': {
        'nombre': 'CONDICIONAL',
        'patrones': [
            r'CIRCULA\s+(?:DE\s+FORMA\s+)?CONDICIONAL'
        ]
    },
    '6': {
        'nombre': 'INTERRUMPIDO',
        'patrones': [
            r'SE\s+ENCUENTRA\s+INTERRUMPIDO',
            r'EST[ÁA]\s+INTERRUMPIDO',
            r'INTERRUMPIDO\s+(?:ENTRE|EN)'
        ]
    },
    '1B': {
        'nombre': 'DEMORA_PARTIDA',
        'patrones': [
            r'(?:DEMORA|DEMORANDO)\s+(?:EN|SU)?\s+PARTIDA',
            r'DEMORANDO\s+EN\s+ESTACI[OÓ]N'
        ]
    },
    '7R': {
        'nombre': 'RECTIFICACION',
        'patrones': [
            r'SE\s+RECTIFICA',
            r'RECTIFICACI[OÓ]N'
        ]
    }
}

# MEJORA: Diccionario de Sinónimos para Contingencias
SINONIMOS_CONTINGENCIAS = {
    'PROBLEMAS TÉCNICOS': [
        'PROBLEMAS TECNICOS', 'FALLA TECNICA', 'DESPERFECTOS TECNICOS', 
        'INCONVENIENTES TECNICOS', 'TECNICOS', 'TECNICO'
    ],
    'PROBLEMAS OPERATIVOS': [
        'PROBLEMAS OPERATIVOS', 'FALLA OPERATIVA', 'INCONVENIENTES OPERATIVOS', 
        'OPERATIVOS', 'OPERATIVO', 'RAZONES OPERATIVAS', 'RAZON OPERATIVA', 
        'INCONVENIENTES EN LA LOC' # Caso reportado por usuario
    ],
    'OTRAS CONTINGENCIAS': [
        'OTRAS CONTINGENCIAS', 'OTRA CAUSA', 'CAUSA DESCONOCIDA'
    ],
    'ACCIDENTE EN PASO A NIVEL': [
        'ACCIDENTE', 'ACCIDENTE PAN', 'COLISION', 'EMBESTIDA', 'ACCIDENTE EN VÍA'
    ],
    'OBRA EN ZONA DE VÍAS': [
        'OBRA', 'OBRAS', 'TRABAJOS EN VIA', 'REPARACION DE VÍA'
    ],
    'MANIFESTACIÓN / PIQUETE': [
        'MANIFESTACION', 'PIQUETE', 'CORTE DE VIA', 'PROTESTA'
    ]
}

# Estados que no requieren validación de tiempo (o tienen lógica especial)
ESTADOS_SIN_TARDANZA = ['REDUCIDO', 'INTERRUMPIDO', 'CONDICIONAL', 'REANUDACIÓN']

# =================================================================
#                    CARGAR CONTINGENCIAS
# =================================================================

def cargar_contingencias(archivo_excel="Contingencias.xlsx"):
    """Carga matriz de contingencias desde Excel"""
    try:
        # Check if file exists to assume safe loading
        if not os.path.exists(archivo_excel):
            return None

        df = pd.read_excel(archivo_excel)
        
        # Normalizar nombres de columnas para evitar problemas de mayúsculas/espacios
        df.columns = [c.strip().replace(' ', '_') for c in df.columns]
        
        # Asegurar que código sea string con 2 dígitos
        if 'Codigo' in df.columns:
            df['Código'] = df['Codigo'].astype(str).str.zfill(2)
        elif 'Código' in df.columns:
            df['Código'] = df['Código'].astype(str).str.zfill(2)
            
        # ========================================================
        # PARCHE EN MEMORIA (Alinear Excel viejo con Imagen Nueva)
        # ========================================================
        # El usuario indicó que la imagen es la 'guía'.
        # El Excel local tiene códigos viejos (ej: 01=Técnicos),
        # así que los corregimos aquí para que la validación funcione.
        
        col_com = None
        if 'Forma_Comunicacion' in df.columns: col_com = 'Forma_Comunicacion'
        elif 'Formas_de_comunicación' in df.columns: col_com = 'Formas_de_comunicación'
        
        if col_com:
            # Forzar 03 = PROBLEMAS TÉCNICOS
            df.loc[df[col_com].str.strip().str.upper() == 'PROBLEMAS TÉCNICOS', 'Código'] = '03'
            
            # Forzar 05 = PROBLEMAS OPERATIVOS (si existe la fila, o si era Manifestación)
            # En Excel viejo: 05=Manifestación. En Nuevo 05=Operativos.
            # Buscamos si existe "PROBLEMAS OPERATIVOS"
            mask_op = df[col_com].str.strip().str.upper() == 'PROBLEMAS OPERATIVOS'
            if mask_op.any():
                df.loc[mask_op, 'Código'] = '05'
            else:
                # Si no existe, podríamos renombrar la 05 vieja o agregar nueva.
                # Por seguridad, buscamos la 05 vieja y la actualizamos
                df.loc[df['Código'] == '05', col_com] = 'PROBLEMAS OPERATIVOS'

        return df
    except Exception as e:
        print(f"❌ Error cargando contingencias: {e}")
        return None

def buscar_contingencia_con_sinonimos(contenido_upper, contingencias_df):
    """
    MEJORA #9: Busca contingencia en texto considerando sinónimos y estructura real
    Retorna: (codigo_contingencia, forma_comunicacion) o (None, None)
    """
    # 1. Búsqueda exacta en columna 'Forma_Comunicacion' (la que va al pasajero)
    col_comunicacion = None
    if 'Forma_Comunicacion' in contingencias_df.columns:
        col_comunicacion = 'Forma_Comunicacion'
    elif 'Formas_de_comunicación' in contingencias_df.columns:
        col_comunicacion = 'Formas_de_comunicación' # fallback por si acaso

    if col_comunicacion:
        for idx, row in contingencias_df.iterrows():
            forma = str(row[col_comunicacion]).upper()
            if forma and forma != 'NAN':
                # Regex flexible
                patron = re.escape(forma).replace(r'\ ', r'\s+')
                if re.search(patron, contenido_upper):
                    codigo = str(row['Código']).zfill(2)
                    return (codigo, forma)
    
    # 2. Búsqueda por sinónimos (si falla la exacta)
    # Actualizado según imagen del usuario:
    # 03 = PROBLEMAS TÉCNICOS
    # 05 = PROBLEMAS OPERATIVOS
    # 17 = OTRAS CONTINGENCIAS
    
    for forma_oficial, sinonimos in SINONIMOS_CONTINGENCIAS.items():
        for sinonimo in sinonimos:
            patron = re.escape(sinonimo).replace(r'\ ', r'\s+')
            if re.search(patron, contenido_upper):
                
                # Buscar el código que corresponde a esa forma oficial en el Excel
                if col_comunicacion:
                    match = contingencias_df[contingencias_df[col_comunicacion].str.upper() == forma_oficial]
                    if not match.empty:
                        codigo = str(match.iloc[0]['Código']).zfill(2)
                        return (codigo, sinonimo)
                
                # Fallback manual si no está en Excel (por seguridad)
                if forma_oficial == 'PROBLEMAS TÉCNICOS': return ('03', sinonimo)
                if forma_oficial == 'PROBLEMAS OPERATIVOS': return ('05', sinonimo)
                if forma_oficial == 'OTRAS CONTINGENCIAS': return ('17', sinonimo)

    return (None, None)

# =================================================================
#                    DETECCIÓN TIPO MENSAJE
# =================================================================

def detectar_tipo_mensaje(contenido):
    """
    Detecta si es TREN ESPECÍFICO, SERVICIO GENERAL o REANUDACIÓN
    
    TREN ESPECÍFICO: Habla de UN tren puntual con número
    SERVICIO GENERAL: Habla del estado de ramal/línea/servicio
    REANUDACIÓN: MEJORA #2 - Mensaje de restablecimiento de servicio
    """
    contenido_upper = contenido.upper()
    
    # MEJORA #2: Detectar reanudación/restablecimiento
    if re.search(r'SE\s+RESTABLECE|RESTABLECE\s+(?:EL\s+)?SERVICIO', contenido_upper):
        # Buscar si menciona ramal/línea
        # MEJORA #13: Permitir guiones en nombres de ramales (ej: Retiro-Cabred)
        match_servicio = re.search(
            r'(?:RAMAL|L[ÍI]NEA)\s+([A-ZÁÉÍÓÚÑ\s\-\.]+?)(?:\s+SE\s+|\s+RESTABLECE)',
            contenido_upper
        )
        if match_servicio:
            return {
                'tipo': 'REANUDACION',
                'nombre_servicio': match_servicio.group(1).strip()
            }
        else:
            return {'tipo': 'REANUDACION'}

    # MEJORA #15: Detectar Rectificación
    if re.search(r'SE\s+RECTIFICA|RECTIFICACI[OÓ]N', contenido_upper):
        return {'tipo': 'RECTIFICACION'}
    
    # Buscar número de tren
    # CORRECCIÓN DEFINITIVA: Regex que tolera "TREN N @T3432" sin usar replace que duplique palabras
    match_tren = re.search(
        r'(?:TREN\s+(?:N[°º]?\s*)?(?:@?T)?|@T)\s*(\d{3,4})',
        contenido_upper
    )
    
    # Si falla, intento de rescate (buscando cualquier número de 3-4 cifras después de la palabra TREN)
    if not match_tren:
         match_tren = re.search(r'TREN.*?(\d{3,4})', contenido_upper)

    # MEJORA: Detectar si usaron "SERVICIO 3328" en lugar de "TREN"
    usado_servicio_como_tren = False
    if not match_tren:
        match_servicio_numerico = re.search(r'SERVICIO\s+(?:N[°º]?\s*)?(\d{3,4})', contenido_upper)
        if match_servicio_numerico:
            match_tren = match_servicio_numerico
            usado_servicio_como_tren = True

    if match_tren:
        resultado = {
            'tipo': 'TREN_ESPECIFICO',
            'numero_tren': match_tren.group(1)
        }
        if usado_servicio_como_tren:
            # NO podemos agregar advertencias aquí porque esto devuelve un dict simple de tipo.
            # Debemos manejarlo después o marcarlo aquí.
            resultado['usado_servicio_como_tren'] = True
        return resultado
    
    # Buscar servicio/ramal/línea
    match_servicio = re.search(r'(RAMAL|SERVICIO|L[IÍ]NEA)\s+([A-ZÁÉÍÓÚÑ\s-]+?)(?=\s+(?:SE\s+|INTERRUMPIDO|REDUCIDO|CON\s+|DEMORAS|CANCELADO))', contenido_upper)
    
    if match_servicio:
        return {
            'tipo': 'SERVICIO_GENERAL',
            'nombre_servicio': match_servicio.group(1).strip()
        }
    
    return {
        'tipo': 'DESCONOCIDO'
    }

# =================================================================
#                    VALIDACIÓN CÓDIGO ESTRUCTURA
# =================================================================

def detectar_codigo_estructura(contenido):
    """
    Busca códigos tipo 3.1.A, 17.1.A, etc.
    Flexibilizado para no exigir que sea el primer caracter absoluto.
    """
    # Busca digitos.digitos.letra al principio del string (permitiendo basura antes)
    match = re.search(r'(?:^|^\W*)(\d{1,2})\.(\d{1,2})\.([A-Z])', contenido.strip())
    
    if match:
        return {
            'completo': f"{match.group(1)}.{match.group(2)}.{match.group(3)}",
            'X': match.group(1).zfill(2),  # Código contingencia (01-24)
            'Y': match.group(2),             # Estado (1-5)
            'Z': match.group(3)              # Ciclo vida (no validar)
        }
    return None

def validar_codigo_estructura(codigo_extraido, codigo_contingencia_detectado, estado_detectado):
    """
    Valida que el código de estructura coincida con contingencia y estado
    
    MEJORAS:
    - #5: Detecta inconsistencia código vs contingencia
    - #8: Acepta código 17 sin contingencia para estaciones compuestas
    """
    observaciones = []
    
    if not codigo_extraido:
        observaciones.append("❌ Falta código de estructura (ej: 3.1.A)")
        return observaciones
    
    # MEJORA #8: Código 17 sin contingencia es válido (estaciones compuestas)
    if codigo_extraido['X'] == '17' and not codigo_contingencia_detectado:
        # Código 17 no requiere contingencia explícita
        pass
    # Validar X (contingencia) para otros códigos
    elif codigo_contingencia_detectado and codigo_extraido['X'] != codigo_contingencia_detectado:
        obs = f"⚠️ Inconsistencia en código: Usaste {codigo_extraido['X']} pero la contingencia corresponde al código {codigo_contingencia_detectado}"
        observaciones.append(obs)
    
    # Validar Y (estado)
    estado_esperado = MAP_ESTADOS_CODIGO.get(codigo_extraido['Y'], {}).get('nombre', '')
    if estado_esperado and estado_detectado and estado_esperado != estado_detectado:
        # Normalizar para evitar falsos positivos (DEMORA vs DEMORA_PARTIDA si aplica)
        if not (estado_esperado == 'DEMORA' and estado_detectado == 'DEMORA_PARTIDA'):
             obs = f"⚠️ Inconsistencia en estado: Código indica {estado_esperado} pero el mensaje describe {estado_detectado}"
             observaciones.append(obs)
    
    return observaciones

# =================================================================
#                    VALIDACIÓN DE COMPONENTES
# =================================================================

def validar_componentes(mensaje, contingencias_df):
    """
    Valida los componentes del mensaje según tipo
    """
    global CORRECTOR_DISPONIBLE
    
    contenido = mensaje.get('contenido', '')
    
    # MEJORA #12: Normalizar espacios múltiples
    contenido = re.sub(r'\s+', ' ', contenido).strip()
    
    contenido_upper = contenido.upper()
    
    tipo_info = detectar_tipo_mensaje(contenido)
    tipo = tipo_info['tipo']
    
    componentes = {
        'tipo_mensaje': tipo,
        'A': None,  # TREN o SERVICIO
        'B': None,  # ESTADO (demora, cancelación, etc)
        'C': None,  # CONTINGENCIA
        'D': None,  # HORA (solo tren específico)
        'E': None,  # RECORRIDO (solo tren específico)
        'F': None,  # CÓDIGO estructura
        'estructura_valida': False,
        'ortografia_valida': True,
        'errores_ortografia': [],
        'advertencias_formato': []
    }
    
    # MEJORA: Advertencia si usó SERVICIO en lugar de TREN
    if tipo_info.get('usado_servicio_como_tren'):
        componentes['advertencias_formato'].append(
            "Terminología incorrecta: Usaste 'SERVICIO N°'. Para trenes específicos usa 'TREN N°'. IMPORTANTE: SIEMPRE SEGUIR EL PROCEDIMIENTO."
        )
    
    # Componente F: Código de estructura
    codigo_estructura = detectar_codigo_estructura(contenido)
    if codigo_estructura:
        if isinstance(codigo_estructura, dict): # Si devuelve dict
             componentes['F'] = codigo_estructura['completo']
        else:
             componentes['F'] = codigo_estructura
        # La estructura solo es válida si además reconocemos el tipo de mensaje
        if tipo != 'DESCONOCIDO':
            componentes['estructura_valida'] = True
        else:
            # Si el tipo es DESCONOCIDO, aunque tenga código, la estructura global no es válida
            componentes['estructura_valida'] = False
            componentes.setdefault('advertencias_formato', []).append(
                "Código detectado pero el mensaje no tiene formato reconocido (TREN o GENERAL)"
            )
    
    # Componente A: Número de tren o servicio
    if tipo == 'TREN_ESPECIFICO':
        if tipo_info.get('numero_tren'):
            componentes['A'] = tipo_info.get('numero_tren')
        else:
            # Fallback (por si acaso) con la regex robusta nueva
            match_tren = re.search(r'(?:TREN.*?|@T)\s*(\d{3,4})', contenido_upper)
            if match_tren:
                componentes['A'] = match_tren.group(1)
    elif tipo == 'SERVICIO_GENERAL':
        # MEJORA #13: Permitir guiones en servicio
        match_servicio = re.search(
            r'(?:SERVICIO|RAMAL|L[ÍI]NEA)\s+([A-ZÁÉÍÓÚÑ\s\-\.]+?)(?:\s+SE\s+|\s+CIRCULA|\s+HA\s+)',
            contenido_upper
        )
        if match_servicio:
            componentes['A'] = match_servicio.group(1).strip()
    
    # Componente B: Estado (MEJORA #3: regex flexible)
    estado_detectado = None
    usa_estructura_formal = False
    
    for cod_estado, info_estado in MAP_ESTADOS_CODIGO.items():
        for patron in info_estado['patrones']:
            if re.search(patron, contenido_upper):
                estado_detectado = info_estado['nombre']
                usa_estructura_formal = True
                componentes['B'] = {
                    'estado': estado_detectado,
                    'codigo': cod_estado,
                    'estructura_formal': True
                }
                break
        if estado_detectado:
            break
    
    # Si no encontró estado formal, buscar menciones informales
    if not estado_detectado:
        # Buscar "DEMORA" sin estructura formal
        if re.search(r'\bDEMORAS?\b', contenido_upper):
            estado_detectado = 'DEMORA'
            componentes['B'] = {
                'estado': estado_detectado,
                'codigo': '1',
                'estructura_formal': False
            }
        # Buscar "CANCELADO/A" sin estructura formal
        elif re.search(r'\bCANCELAD[OA]S?\b', contenido_upper):
            estado_detectado = 'CANCELACIÓN'
            componentes['B'] = {
                'estado': estado_detectado,
                'codigo': '2',
                'estructura_formal': False
            }
    
    # Si es DEMORA, buscar minutos (MEJORA #1: acepta MIN., MIN, singular DEMORA)
    # MEJORA #14: Robusteza ante typos numéricos (ej: "5_" o "10.")
    if estado_detectado in ['DEMORA', 'DEMORA_PARTIDA']:
        match_minutos = re.search(
            r'(?:DEMORAS?|REGISTRA|ESPERA)(?:[\s\w]*?)(?:DE\s*|DE_|OBSERVA\s+)?([_\-\.]?)\s*(\d+)\s*([_\-\.]?)\s*(?:MINUTOS?|MIN\.?)',
            contenido_upper
        )
        if match_minutos:
            prefix = match_minutos.group(1)
            minutos = match_minutos.group(2)
            suffix = match_minutos.group(3)
            
            if componentes['B']:
                componentes['B']['minutos'] = minutos
                
                # Si hay un caracter sucio (ej: 5_ o _7), sugerir corrección
                if prefix or suffix:
                   componentes.setdefault('advertencias_formato', []).append(
                       f"⚠️ Se detectó '{prefix}{minutos}{suffix}' en los minutos. Se sugiere escribir solo el número '{minutos}'."
                   )
    
    # Componente C: Contingencia (MEJORA #9: con sinónimos)
    codigo_contingencia = None
    forma_comunicacion = None
    
    if contingencias_df is not None:
        # MEJORA #9: Buscar con sinónimos
        codigo_contingencia, forma_comunicacion = buscar_contingencia_con_sinonimos(
            contenido_upper, contingencias_df
        )
        if codigo_contingencia:
            componentes['C'] = {
                'codigo': codigo_contingencia,
                'forma_comunicacion': forma_comunicacion
            }
    
    # Componente D y E: Lógica diferenciada por Tipo
    
    if tipo == 'TREN_ESPECIFICO':
        # --- D - HORA (Oficial: DE LAS XX:XX HS) ---
        match_hora_4dig = re.search(r'DE\s+LAS\s+(\d{2})(\d{2})\s*HS', contenido_upper)
        if match_hora_4dig:
            hour_str = match_hora_4dig.group(1)
            min_str = match_hora_4dig.group(2)
            componentes['D'] = f"{hour_str}:{min_str}"
            componentes.setdefault('advertencias_formato', []).append(
                "SUGERENCIA: Se recomienda usar 'DE LAS HH:MM HS' (con dos puntos) en lugar de sin separador. IMPORTANTE: SIEMPRE SEGUIR EL PROCEDIMIENTO."
            )
        else:
            # Patrón normal con separadores
            match_hora = re.search(r'DE\s+LAS\s+(\d{1,2})[\s:\.]+(\d{2})\s*HS', contenido_upper)
            if match_hora:
                hour_str = match_hora.group(1)
                min_str = match_hora.group(2)
                componentes['D'] = f"{hour_str}:{min_str}"
                
                # Detectar el separador usado
                texto_hora = match_hora.group(0)
                if ':' not in texto_hora:
                    componentes.setdefault('advertencias_formato', []).append(
                        f"SUGERENCIA: Se recomienda usar 'DE LAS HH:MM HS' (con dos puntos). IMPORTANTE: SIEMPRE SEGUIR EL PROCEDIMIENTO."
                    )
            else:
                # Intentar Flexible (DE LAS sin HS, A LAS, SALIDA...)
                match_hora_invertida = re.search(r'HS\.?\s*(\d{1,2})[\s:\.]*(\d{2})', contenido_upper)
                
                if match_hora_invertida:
                     componentes['D'] = f"{match_hora_invertida.group(1)}:{match_hora_invertida.group(2)}"
                     componentes.setdefault('advertencias_formato', []).append(
                         "Orden incorrecto: Escribiste 'HS Hora'. Lo correcto es 'DE LAS HH:MM HS'. IMPORTANTE: SIEMPRE SEGUIR EL PROCEDIMIENTO."
                     )
                else:
                    match_hora_flex = re.search(r'(?:(?:A|DE)?\s+)?LAS\s+(\d{1,2})[\s:\._]+(\d{2})', contenido_upper)
                    
                    if not match_hora_flex:
                        match_hora_flex = re.search(r'\b(\d{1,2})[\s:\._]+(\d{2})\s*HS', contenido_upper)

                    if match_hora_flex:
                         componentes['D'] = f"{match_hora_flex.group(1)}:{match_hora_flex.group(2)}"
                         if not re.search(r'DE\s+LAS', contenido_upper):
                             componentes.setdefault('advertencias_formato', []).append(
                                 "Falta preposición: Escribiste mal la hora. Lo correcto es 'DE LAS HH:MM HS'. IMPORTANTE: SIEMPRE SEGUIR EL PROCEDIMIENTO."
                             )

        # --- E - RECORRIDO (Oficial: DESDE [A] HACIA [B]) ---
        stop_words_recorrido = r'(?=\s+(?:HACIA|A\s+[A-Z]|CON\s+|CIRCULA|HA\s+|FUE|Y\s+|PARTIO|DETENIDO|\(|LLEGA))'
        
        match_origen = re.search(r'(?:PARTIENDO\s+(?:DE|DESDE)|DESDE|DE)\s+([A-ZÁÉÍÓÚÑ0-9\s\.]+?)' + stop_words_recorrido, contenido_upper)
        
        stop_words_destino = r'(?=\s+(?:CIRCULA|HA\s+|FUE|CON\s+|REGISTRA|SE\s+ENCUENTRA|POR\s+|O\s+TRAS|RESTABLECE|PARTIO|Y\s+|\(|EN\s+ESTACION|SE\s+|$))'
        match_destino = re.search(r'(?:HACIA|LLEGA\s+A|FINALIZA\s+EN|A)\s+([A-ZÁÉÍÓÚÑ0-9\s\.]+?)' + stop_words_destino, contenido_upper)
        
        # Lógica Flexible: Si no encuentra oficial, buscar variantes
        if not match_origen or not match_destino:
            # Variante 1: "ENTRE [A] Y [B]"
            match_entre = re.search(r'ENTRE\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.\(\)]+?)\s+Y\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.\(\)]+?)(?=\s+(?:CIRCULA|HA\s+SIDO|FUE|CON\s+DEMORA|$))', contenido_upper)
            if match_entre:
                componentes['E'] = {
                    'origen': match_entre.group(1).strip(),
                    'destino': match_entre.group(2).strip()
                }
                componentes.setdefault('advertencias_formato', []).append(
                    "Según Matriz de Mensajes: Usa 'DESDE [Origen] HACIA [Destino]'"
                )
                match_origen = True 
                match_destino = True
            
            # Variante 2: "DE [A] A [B]" (Solo si no encontró ENTRE)
            if not componentes.get('E'):
                match_de_a = re.search(r'(?:SALIENDO\s+|SALE\s+)?DE\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.\(\)]+?)\s+A\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s\.\(\)]+?)(?=\s+(?:CIRCULA|HA\s+SIDO|FUE|CON\s+DEMORA|$))', contenido_upper)
                if match_de_a:
                    componentes['E'] = {
                        'origen': match_de_a.group(1).strip(),
                        'destino': match_de_a.group(2).strip()
                    }
                    componentes.setdefault('advertencias_formato', []).append(
                        "Según Matriz de Mensajes: Usa 'HACIA [Estacion]' en lugar de 'A'"
                    )
        
        if (match_origen and match_destino) or componentes.get('E'):
            if not componentes.get('E'): # Si encontró oficial
                 componentes['E'] = {
                    'origen': match_origen.group(1).strip() if match_origen else None,
                    'destino': match_destino.group(1).strip() if match_destino else None
                }

    elif tipo == 'SERVICIO_GENERAL':
        # --- D - LUGAR (Contextual: "EN ...") ---
        match_lugar = re.search(r'\bEN\s+([A-ZÁÉÍÓÚÑ\s\.]+?)(?=\s+(?:DISCULPA|SEPA|\.|$))', contenido_upper)
        if match_lugar:
             lugar = match_lugar.group(1).strip()
             if lugar not in ["EL DIA", "LA TARDE", "LA NOCHE", "EL TRANSCURSO"]:
                componentes['D'] = lugar

        # --- E - DISCULPAS (Opcional) ---
        if "DISCULPA" in contenido_upper or "SEPA DISCULPAR" in contenido_upper:
            componentes['E'] = "Se piden disculpas"
            
    elif tipo == 'RECTIFICACION':
        match_tren = re.search(r'(?:TREN|SERVICIO|FORMACI[OÓ]N)\s+(?:N[°º]?\s*)?(\d+)', contenido_upper)
        if match_tren:
             componentes['A'] = match_tren.group(1)
        else:
             match_servicio = re.search(r'(?:RAMAL|L[ÍI]NEA)\s+([A-ZÁÉÍÓÚÑ\s\-\.]+)', contenido_upper)
             if match_servicio:
                 componentes['A'] = match_servicio.group(1).strip()
    
    # Validar ortografía con LanguageTool (si está disponible)
    errores_detectados = []
    config = cargar_config(mensaje.get('linea', 'ROCA'))
    palabras_tecnicas = set(word.upper() for word in config.get('palabras_tecnicas', []))

    if CORRECTOR_DISPONIBLE and spell:
        try:
            palabras = re.findall(r'\b[A-Za-záéíóúñÁÉÍÓÚÑ]+\b', contenido)
            desconocidas = spell.unknown(palabras)
            for word in desconocidas:
                word_upper = word.upper()
                if (word_upper in palabras_tecnicas or len(word) < 3 or 
                    word_upper in ['LSM', 'PK', 'KM', 'NRO', 'PDA', 'JCP', 'PC', 'S/E']):
                    continue
                sugerencia = spell.correction(word)
                if sugerencia and sugerencia.upper() != word_upper:
                    errores_detectados.append(f"{word} → {sugerencia}")
        except Exception:
            pass
    
    # Sistema de respaldo con regex
    if not CORRECTOR_DISPONIBLE:
        patrones_error = [
            (r'\bSUSPENDIOD\b', 'SUSPENDIDO'),
            (r'\bCIRUCLA\b', 'CIRCULA'),
            (r'\bCIRUCLAN\b', 'CIRCULAN'),
            (r'\bPARTEINEDO\b', 'PARTIENDO'),
            (r'\bPARTIDIENDO\b', 'PARTIENDO'),
            (r'\bMOOTIVO\b', 'MOTIVO'),
            (r'\bMOTIVIO\b', 'MOTIVO'),
            (r'\bHACIAA\b', 'HACIA'),
            (r'\bHAICIA\b', 'HACIA'),
            (r'\bREGISTRAA\b', 'REGISTRA'),
            (r'\bREGISTRAAD[OA]\b', 'REGISTRADO/A'),
        ]
        count_errors = 0
        for patron, correcto in patrones_error:
            if re.search(patron, contenido_upper):
                palabra_error = re.search(patron, contenido_upper).group()
                errores_detectados.append(f"{palabra_error} → {correcto}")
    
        if re.search(r'([A-Z])\1{2,}', contenido_upper):
            errores_detectados.append("Letras repetidas excesivamente")
    
    # 3. Detectar espacios múltiples
    if '  ' in contenido:
        espacios_multiples = len(re.findall(r'\s{2,}', contenido))
        if espacios_multiples > 2:
            errores_detectados.append(f"Espacios múltiples ({espacios_multiples} lugares)")
    
    # Aplicar errores detectados
    if errores_detectados:
        componentes['ortografia_valida'] = False
        componentes['errores_ortografia'].extend(errores_detectados)
    
    # Advertencia específica para @T
    if '@T' in contenido_upper:
        componentes.setdefault('advertencias_formato', []).append(
            "Formato no estándar: Se detectó el prefijo interno '@T'. P/ comunicación externa usar 'TREN N° ...'."
        )

    # Advertencia educativa: SUSPENDIDO vs REDUCIDO/LIMITADO
    if 'SUSPENDIDO' in contenido_upper:
         sugerencia = "⚠️ 'SUSPENDIDO' no es válido. "
         if componentes.get('tipo_mensaje') == 'TREN_ESPECIFICO':
             sugerencia += "Si el tren no completa recorrido, usar estructura: 'EL TREN N° [N] DESDE [A] HACIA [B] CIRCULA REDUCIDO ENTRE [A] Y [C] POR [MOTIVO]'."
         else:
             sugerencia += "Usar 'REDUCIDO' (menos trenes) o 'CANCELADO' (no corre)."
         componentes.setdefault('advertencias_formato', []).append(sugerencia)

    if 'advertencias_formato' in componentes:
        componentes['advertencias_formato'] = list(dict.fromkeys(componentes['advertencias_formato']))

    return componentes, codigo_estructura, codigo_contingencia, estado_detectado

# =================================================================
#                    VALIDACIÓN TIEMPO RESPUESTA
# =================================================================

def validar_tiempo_respuesta(mensaje, componentes):
    """
    Valida el tiempo de respuesta
    """
    tipo = componentes.get('tipo_mensaje')
    if tipo in ['SERVICIO_GENERAL', 'RECTIFICACION']:
        return None
        
    estado = componentes.get('B', {})
    if isinstance(estado, dict) and estado.get('estado') == 'DEMORA_PARTIDA':
         if not estado.get('minutos'):
             return None
    
    if isinstance(estado, dict):
        estado_nombre = estado.get('estado', '')
        if estado_nombre in ESTADOS_SIN_TARDANZA:
            return None
    
    hora_programada = componentes.get('D')
    if not hora_programada:
        return None
    
    es_cancelacion_o_suspension = isinstance(estado, dict) and estado.get('estado') in ['CANCELACIÓN', 'SUSPENSIÓN']
    minutos_demora = componentes.get('B', {}).get('minutos') if isinstance(componentes.get('B'), dict) else None
    
    if not es_cancelacion_o_suspension and not minutos_demora:
        return None
    
    try:
        fecha_mensaje = mensaje.get('fecha_hora', '')
        hora_envio = datetime.strptime(fecha_mensaje, "%d/%m/%Y %H:%M:%S")
        
        partes_hora = hora_programada.split(':')
        hora_prog = hora_envio.replace(
            hour=int(partes_hora[0]),
            minute=int(partes_hora[1]),
            second=0
        )
        
        if es_cancelacion_o_suspension:
            hora_referencia = hora_prog
        else:
            hora_referencia = hora_prog + timedelta(minutes=int(minutos_demora))
        
        tardanza_segundos = (hora_envio - hora_referencia).total_seconds()
        tardanza_minutos = tardanza_segundos / 60
        
        if es_cancelacion_o_suspension:
            if tardanza_minutos <= 10:
                clasificacion = "OPORTUNO"
                nivel = "ACEPTABLE"
            elif tardanza_minutos <= 20: 
                clasificacion = "ACEPTABLE"  
                nivel = "OBSERVACION"
            else:
                clasificacion = "CRITICO"
                nivel = "IMPORTANTE"
        else:
            if tardanza_minutos < -60:
                clasificacion = "ANTICIPADO"
                nivel = "EXCELENTE"
            elif tardanza_minutos < 0:
                clasificacion = "ANTICIPADO"
                nivel = "MUY_BUENO"
            elif tardanza_minutos <= 10:
                clasificacion = "OPORTUNO"
                nivel = "ACEPTABLE"
            elif tardanza_minutos <= 20:
                clasificacion = "ACEPTABLE"
                nivel = "OBSERVACION"
            else:
                clasificacion = "CRITICO"
                nivel = "IMPORTANTE"
        
        return {
            'tardanza_minutos': round(tardanza_minutos, 1),
            'clasificacion': clasificacion,
            'nivel': nivel,
            'hora_programada': hora_programada,
            'minutos_demora': minutos_demora if not es_cancelacion_o_suspension else 0,
            'hora_referencia': hora_referencia.strftime("%H:%M"),
            'hora_envio': hora_envio.strftime("%H:%M:%S"),
            'es_cancelacion': es_cancelacion_o_suspension
        }
    except Exception as e:
        return None

# =================================================================
#                    CLASIFICACIÓN FINAL
# =================================================================

def clasificar_mensaje(mensaje, componentes, codigo_estructura, codigo_contingencia, estado_detectado, timing):
    """
    Clasifica el mensaje en: COMPLETO, IMPORTANTE, OBSERVACIONES, SUGERENCIAS
    """
    clasificacion = {
        'IMPORTANTE': [],
        'OBSERVACIONES': [],
        'SUGERENCIAS': []
    }
    
    tipo = componentes.get('tipo_mensaje')
    
    if tipo == 'TREN_ESPECIFICO':
        if not componentes.get('A'):
            clasificacion['IMPORTANTE'].append("Falta número de tren")
        
        if not componentes.get('B'):
            clasificacion['IMPORTANTE'].append("Falta estado del servicio")
        elif isinstance(componentes['B'], dict):
            if not componentes['B'].get('estructura_formal', True):
                clasificacion['SUGERENCIAS'].append(
                    f"⚠️ El mensaje menciona '{componentes['B'].get('estado')}' pero no usa la estructura formal."
                )
            estado = componentes['B'].get('estado')
            tiene_minutos = componentes['B'].get('minutos')
            
            if estado == 'DEMORA' and not tiene_minutos:
                contenido_upper = mensaje.get('contenido', '').upper()
                es_demora_partida = re.search(r'DEMORANDO\s+(?:SU\s+)?PARTIDA|PARTIDA\s+DEMORADA', contenido_upper)
                
                if es_demora_partida:
                    clasificacion['OBSERVACIONES'].append(
                        "💡 Demora de partida: No indicaste minutos. Es válido, pero ayuda sumarlos."
                    )
                else:
                    clasificacion['IMPORTANTE'].append(
                        "Falta cantidad de minutos. Si aguarda salida, usar estructura 'DEMORANDO SU PARTIDA'."
                    )
            
            elif estado == 'REDUCIDO':
                contenido_upper = mensaje.get('contenido', '').upper()
                tiene_limite = re.search(r'(?:REDUCIDO|CORTO|LIMITADO)\s+(?:EN|A|HASTA)\s+[A-Z]', contenido_upper)
                if not tiene_limite:
                    clasificacion['IMPORTANTE'].append("Falta tramo reducido.")
        
        if not componentes.get('D'):
            clasificacion['IMPORTANTE'].append("Falta hora programada")
        
        recorrido = componentes.get('E')
        if not recorrido:
            clasificacion['IMPORTANTE'].append("Falta origen y destino")
        elif isinstance(recorrido, dict):
            if not recorrido.get('origen'):
                clasificacion['IMPORTANTE'].append("Falta estación origen")
            if not recorrido.get('destino'):
                clasificacion['IMPORTANTE'].append("Falta estación destino")

    elif tipo == 'SERVICIO_GENERAL':
        if not componentes.get('A'):
            clasificacion['IMPORTANTE'].append("Falta identificación del servicio")
        if not componentes.get('B'):
            clasificacion['IMPORTANTE'].append("Falta estado del servicio")
        elif isinstance(componentes['B'], dict):
            if not componentes['B'].get('estructura_formal', True):
                clasificacion['SUGERENCIAS'].append(
                    f"⚠️ El mensaje menciona '{componentes['B'].get('estado')}' pero no usa estructura formal."
                )
        
        servicio_detectado = componentes.get('A')
        if servicio_detectado and '-' in servicio_detectado:
            clasificacion['SUGERENCIAS'].append(
                f"💡 Uso de guiones en '{servicio_detectado}' es aceptable, pero se sugiere validar Matriz."
            )
        
        if hasattr(componentes, 'get') and not componentes.get('D'):
             causa = componentes.get('C', {}).get('codigo', '') if isinstance(componentes.get('C'), dict) else ''
             if causa in ['01', '02', '11', '12']:
                 clasificacion['SUGERENCIAS'].append("💡 Podría ser útil especificar el LUGAR")

    elif tipo == 'RECTIFICACION':
        if not componentes.get('A'):
             clasificacion['IMPORTANTE'].append("No se especifica qué tren o servicio se rectifica")
    
    if tipo != 'RECTIFICACION' and not componentes.get('C'):
        estado = componentes.get('B', {})
        estado_nombre = estado.get('estado', '') if isinstance(estado, dict) else ''
        codigo_X = codigo_estructura['X'] if codigo_estructura else None
        contenido_msg = mensaje.get('contenido', '').upper()
        menciona_formaciones = 'FORMACION' in contenido_msg
        
        if estado_nombre in ['CANCELACIÓN', 'SUSPENDIDO'] and codigo_X == '17':
            clasificacion['OBSERVACIONES'].append(
                "ℹ️ Código 17 sin motivo detallado. Si existe causa específica, usar código correspondiente"
            )
        elif menciona_formaciones:
            clasificacion['SUGERENCIAS'].append(
                "💡 Mensaje sobre formaciones sin causa específica. Si hay motivo, agregarlo"
            )
        else:
            clasificacion['IMPORTANTE'].append("Falta motivo de la contingencia")
    
    if not componentes.get('estructura_valida'):
        clasificacion['IMPORTANTE'].append("Falta código de estructura (ej: 3.1.A)")
    else:
        if codigo_estructura and codigo_contingencia:
            obs_codigo = validar_codigo_estructura(codigo_estructura, codigo_contingencia, estado_detectado)
            for obs in obs_codigo:
                if '❌' in obs:
                    clasificacion['IMPORTANTE'].append(obs)
                else:
                    clasificacion['OBSERVACIONES'].append(obs)
        if codigo_estructura and codigo_estructura['X'] == '17':
            clasificacion['OBSERVACIONES'].append("⚠️ Código 17 es excepcional. Verificar si existe código específico")
    
    if not componentes.get('ortografia_valida'):
        for error in componentes.get('errores_ortografia', []):
            clasificacion['OBSERVACIONES'].append(f"Ortografía: {error}")

    for advertencia in componentes.get('advertencias_formato', []):
         clasificacion['SUGERENCIAS'].append(f"💡 Formato: {advertencia}")
    
    if timing and timing.get('nivel') in ['OBSERVACION', 'IMPORTANTE']:
        tardanza = timing['tardanza_minutos']
        if abs(tardanza) > 15:
            clasificacion['OBSERVACIONES'].append(f"Notificación tardía: {abs(tardanza):.0f} min después de salida")
    
    if clasificacion['IMPORTANTE']:
        nivel_general = 'IMPORTANTE'
    elif clasificacion['OBSERVACIONES']:
        nivel_general = 'OBSERVACIONES'
    elif clasificacion['SUGERENCIAS']:
        nivel_general = 'SUGERENCIAS'
    else:
        nivel_general = 'COMPLETO'
        
    for key in clasificacion:
        clasificacion[key] = list(dict.fromkeys(clasificacion[key]))
    
    return clasificacion, nivel_general

# =================================================================
#                    GENERAR REPORTE
# =================================================================

def calcular_scores(componentes, timing, mensaje):
    """
    Calcula los 3 scores independientes
    """
    scores = {
        'componentes': {'clasificacion': '', 'detalles': []},
        'timing': {'clasificacion': '', 'detalles': []},
        'estructura': {'clasificacion': '', 'detalles': []}
    }
    
    # 1. Componentes
    componentes_puntos = 0
    if componentes.get('A'): componentes_puntos += 20
    else: scores['componentes']['detalles'].append("Falta número de tren")
    
    if componentes.get('B'): componentes_puntos += 20
    else: scores['componentes']['detalles'].append("Falta estado/demora")
    
    if componentes.get('C'): componentes_puntos += 15
    elif componentes.get('tipo_mensaje') == 'INFORMATIVO': componentes_puntos += 15
    else: scores['componentes']['detalles'].append("Falta causa específica")
    
    if componentes.get('D'): componentes_puntos += 15
    elif componentes.get('tipo_mensaje') == 'SERVICIO_GENERAL': componentes_puntos += 15
    else: scores['componentes']['detalles'].append("Falta horario")
    
    if componentes.get('E'):
        if isinstance(componentes['E'], dict):
            if componentes['E'].get('origen') and componentes['E'].get('destino'): componentes_puntos += 20
            else: scores['componentes']['detalles'].append("Falta origen y/o destino")
        elif componentes.get('tipo_mensaje') == 'SERVICIO_GENERAL': componentes_puntos += 20
    elif componentes.get('tipo_mensaje') == 'SERVICIO_GENERAL': componentes_puntos += 20
    else: scores['componentes']['detalles'].append("Falta origen y/o destino")
    
    if componentes.get('estructura_valida'): componentes_puntos += 10
    else: scores['componentes']['detalles'].append("Falta código formal")
    
    if componentes_puntos >= 90: scores['componentes']['clasificacion'] = 'COMPLETO'
    elif componentes_puntos >= 70: scores['componentes']['clasificacion'] = 'ACEPTABLE'
    else: scores['componentes']['clasificacion'] = 'INCOMPLETO'
    
    # 2. Timing
    if timing and timing.get('tardanza_minutos') is not None:
        tardanza = timing['tardanza_minutos']
        estado = componentes.get('B', {})
        if isinstance(estado, dict): estado_nombre = estado.get('estado', '').upper()
        else: estado_nombre = ''
        es_cancel = estado_nombre in ['CANCELACIÓN', 'SUSPENDIDO']
        
        if -5 <= tardanza <= 0:
            scores['timing']['clasificacion'] = 'EXCELENTE'
        elif tardanza < -5 and es_cancel:
            scores['timing']['clasificacion'] = 'EXCELENTE'
        elif 0 < tardanza <= 11:
            scores['timing']['clasificacion'] = 'BUENO'
        else:
            scores['timing']['clasificacion'] = 'DEFICIENTE'
    else:
        scores['timing']['clasificacion'] = 'N/A'
    
    # 3. Estructura
    estructura_puntos = 0
    num_errores = len(componentes.get('errores_ortografia', []))
    if num_errores == 0: estructura_puntos += 40
    elif num_errores == 1: estructura_puntos += 25
    elif num_errores <= 3: estructura_puntos += 15
    elif num_errores <= 5: estructura_puntos += 10
    
    if componentes.get('estructura_valida'): estructura_puntos += 30
    else: estructura_puntos += 10
    
    contenido = mensaje.get('contenido', '').upper()
    if len(contenido) > 50 and componentes.get('tipo_mensaje'): estructura_puntos += 30
    elif len(contenido) > 30: estructura_puntos += 20
    else: estructura_puntos += 10
    
    if estructura_puntos >= 95: scores['estructura']['clasificacion'] = 'IMPECABLE'
    elif estructura_puntos >= 75: scores['estructura']['clasificacion'] = 'CORRECTO'
    elif estructura_puntos >= 55: scores['estructura']['clasificacion'] = 'MEJORABLE'
    else: scores['estructura']['clasificacion'] = 'DEFICIENTE'
    
    return scores

def generar_reporte(mensaje, componentes, clasificacion, nivel_general, timing):
    scores = calcular_scores(componentes, timing, mensaje)
    return {
        'numero_mensaje': mensaje.get('numero_mensaje'),
        'operador': mensaje.get('operador'),
        'fecha_hora': mensaje.get('fecha_hora'),
        'linea': mensaje.get('linea'),
        'contenido': mensaje.get('contenido'),
        'tipo_mensaje': componentes.get('tipo_mensaje'),
        'componentes': componentes,
        'clasificacion': clasificacion,
        'nivel_general': nivel_general,
        'timing': timing,
        'scores': scores,
        'requiere_notificacion': nivel_general in ['IMPORTANTE', 'OBSERVACIONES']
    }

def validar_mensaje_ROCA(mensaje, contingencias_df):
    componentes, codigo_estructura, codigo_contingencia, estado_detectado = validar_componentes(
        mensaje, contingencias_df
    )
    timing = validar_tiempo_respuesta(mensaje, componentes)
    clasificacion, nivel_general = clasificar_mensaje(
        mensaje, componentes, codigo_estructura, codigo_contingencia, estado_detectado, timing
    )
    reporte = generar_reporte(mensaje, componentes, clasificacion, nivel_general, timing)
    return reporte

def validar_mensajes_desde_json(archivo_json=None, contingencias_df=None):
    if not archivo_json:
        archivos_json = glob.glob("mensajes_sofse_*.json")
        if not archivos_json: return []
        archivo_json = max(archivos_json, key=os.path.getmtime)
    
    print(f"📖 Leyendo: {archivo_json}")
    with open(archivo_json, 'r', encoding='utf-8') as f:
        mensajes = json.load(f)
    print(f"📊 Total mensajes: {len(mensajes)}")
    
    if contingencias_df is None: contingencias_df = cargar_contingencias()
    
    reportes = []
    for mensaje in mensajes:
        try:
            reporte = validar_mensaje_ROCA(mensaje, contingencias_df)
            reportes.append(reporte)
        except Exception as e:
            print(f"⚠️ Error validando #{mensaje.get('numero_mensaje', 'N/A')}: {e}")
    return reportes

_CONTINGENCIAS_CACHE = None

def procesar_mensaje(mensaje):
    """
    Wrapper para validar un solo mensaje desde una app externa.
    Maneja la carga y cacheo de contingencias automáticamente.
    """
    global _CONTINGENCIAS_CACHE
    if _CONTINGENCIAS_CACHE is None:
        _CONTINGENCIAS_CACHE = cargar_contingencias()
    return validar_mensaje_ROCA(mensaje, _CONTINGENCIAS_CACHE)

if __name__ == "__main__":
    print("="*80)
    print("🔍 VALIDADOR MENSAJES SOFSE - SISTEMA ROCA v3.0")
    print("="*80)
    contingencias_df = cargar_contingencias()
    if contingencias_df is None:
        print("❌ No se pudo cargar Contingencias.xlsx")
        exit(1)
    reportes = validar_mensajes_desde_json(contingencias_df=contingencias_df)
    print(f"\n{'='*80}")
    print(f"✅ Validación completada: {len(reportes)} mensajes procesados")
    print("="*80)
