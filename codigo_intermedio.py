"""Generación de código intermedio (segmento de datos) del Lenguaje Genesis."""


def _tipo_de(tipo):
    """Normaliza el tipo guardado en la tabla de símbolos."""
    if isinstance(tipo, dict):
        tipo = tipo.get("tipo")
    if tipo == "boolean":
        return "bool"
    return tipo


def generar_codigo_intermedio(tabla):
    """
    Emite una directiva de datos por cada variable de la tabla.

    tabla es un diccionario {nombre: tipo}. El tipo puede ser el texto
    del lenguaje ("int", "boolean", "string", "bool") o la entrada
    completa de la tabla de símbolos.

    int            -> nombre DW ?
    bool/boolean   -> nombre DB ?
    string         -> nombre DB ?
    """
    codigo = []

    for nombre, tipo in tabla.items():
        tipo = _tipo_de(tipo)

        if tipo == "int":
            codigo.append(f"{nombre} DW ?")

        elif tipo == "bool":
            codigo.append(f"{nombre} DB ?")

        elif tipo == "string":
            codigo.append(f"{nombre} DB ?")

    if len(codigo) == 0:
        return "No hay variables para generar."

    return "\n".join(codigo)
