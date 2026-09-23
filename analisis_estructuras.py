"""
Análisis de estructuras del Lenguaje Genesis:
declaraciones, println, read, if, while y for.
Detección de identificadores duplicados en declaraciones.
"""


def analizar_estructuras(tokens, registrar_error):
    """
    Escanea la secuencia de tokens y devuelve filas para la tabla GUI.
    Las variables duplicadas las detecta también la tabla de símbolos en proyecto.py.
    """
    estructuras = []
    declarados = {}
    i = 0
    n = len(tokens)

    while i < n:
        t = tokens[i]

        if t.type in ('INT', 'BOOLEAN', 'STRING') and i + 1 < n and tokens[i + 1].type == 'ID':
            nombre = str(tokens[i + 1].value)
            linea = tokens[i + 1].lineno
            if nombre in declarados:
                registrar_error(
                    f"Identificador duplicado: '{nombre}' ya declarado (línea {declarados[nombre]})",
                    linea,
                    getattr(tokens[i + 1], 'lexpos', i),
                )
            else:
                declarados[nombre] = linea
            estructuras.append({
                'categoria': 'declaracion',
                'nombre': nombre,
                'parametros': str(t.value),
                'linea': linea,
                'ambito': 'global',
            })
            i += 2
            continue

        if t.type == 'PRINTLN':
            estructuras.append({
                'categoria': 'println',
                'nombre': 'println',
                'parametros': '(expresion)',
                'linea': t.lineno,
                'ambito': 'global',
            })
            i += 1
            continue

        if t.type == 'READ' and i + 1 < n and tokens[i + 1].type == 'ID':
            estructuras.append({
                'categoria': 'read',
                'nombre': str(tokens[i + 1].value),
                'parametros': 'read',
                'linea': tokens[i + 1].lineno,
                'ambito': 'global',
            })
            i += 2
            continue

        if t.type == 'IF':
            estructuras.append({
                'categoria': 'if',
                'nombre': 'if',
                'parametros': '(expresion)',
                'linea': t.lineno,
                'ambito': 'global',
            })
            i += 1
            continue

        if t.type == 'WHILE':
            estructuras.append({
                'categoria': 'while',
                'nombre': 'while',
                'parametros': '(expresion)',
                'linea': t.lineno,
                'ambito': 'global',
            })
            i += 1
            continue

        if t.type == 'FOR':
            estructuras.append({
                'categoria': 'for',
                'nombre': 'for',
                'parametros': '(id = expr; expr; id = expr)',
                'linea': t.lineno,
                'ambito': 'global',
            })
            i += 1
            continue

        i += 1

    return estructuras
