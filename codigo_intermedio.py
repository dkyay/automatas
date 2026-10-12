"""Código intermedio del Lenguaje Genesis, al estilo .DATA / .CODE."""

from ast_nodes import (
    Asignacion,
    BinOp,
    Bloque,
    Booleano,
    Bucle,
    Cadena,
    Condicional,
    Declaracion,
    ForStmt,
    Identificador,
    NodoError,
    Numero,
    Parentesis,
    Println,
    Programa,
    Read,
)

# Operadores aritméticos de Genesis y su instrucción.
# @ suma, # resta, & multiplicación, | división.
ARITMETICOS = {
    "@": "ADD",
    "#": "SUB",
    "&": "MUL",
    "|": "DIV",
}

# Salto que se toma cuando la comparación es falsa.
SALTO_SI_FALSO = {
    "==": "JNE",
    "!=": "JE",
    "<": "JGE",
    ">": "JLE",
    "<=": "JG",
    ">=": "JL",
}

DIRECTIVA = {
    "int": "DW",
    "bool": "DB",
    "boolean": "DB",
    "string": "DB",
    "float": "DD",
}


def _tipo_de(tipo):
    """Normaliza el tipo guardado en la tabla de símbolos."""
    if isinstance(tipo, dict):
        tipo = tipo.get("tipo")
    if tipo == "boolean":
        return "bool"
    return tipo


def _pares_tabla(tabla):
    if not isinstance(tabla, dict):
        return []
    pares = []
    for nombre, tipo in tabla.items():
        if isinstance(tipo, dict):
            tipo = tipo.get("tipo")
        if nombre:
            pares.append((str(nombre), tipo))
    return pares


def _desnudar(nodo):
    while isinstance(nodo, Parentesis):
        nodo = nodo.expresion
    return nodo


def _sentencias(cuerpo):
    if isinstance(cuerpo, Bloque):
        return cuerpo.sentencias
    if isinstance(cuerpo, Programa):
        return cuerpo.sentencias
    if isinstance(cuerpo, list):
        return cuerpo
    return []


def _es_simple(nodo):
    return isinstance(nodo, (Numero, Identificador, Booleano))


def _texto_simple(nodo):
    if isinstance(nodo, Numero):
        return str(nodo.valor)
    if isinstance(nodo, Identificador):
        return nodo.nombre
    if isinstance(nodo, Booleano):
        return "1" if str(nodo.valor) == "true" else "0"
    return "0"


def _texto_cadena(valor):
    texto = str(valor)
    if len(texto) >= 2 and texto[0] == '"' and texto[-1] == '"':
        texto = texto[1:-1]
    return texto


class Generador:
    def __init__(self, tabla):
        self.variables = _pares_tabla(tabla)
        self.tipos = {nombre: _tipo_de(tipo) for nombre, tipo in self.variables}
        self.codigo = []
        self.temporales = []
        self.mensajes = []
        self._texto_mensaje = {}
        self.usa_division = False
        self._n_temp = 0
        self._n_eti = 0

    def generar(self, arbol):
        self._recorrer(_sentencias(arbol))
        return self._armar()

    def _armar(self):
        grupos = []
        variables = []
        for nombre, tipo in self.variables:
            directiva = DIRECTIVA.get(tipo) or DIRECTIVA.get(_tipo_de(tipo))
            if directiva:
                variables.append(self._dato(nombre, directiva, "?"))
        if variables:
            grupos.append(variables)

        if self.temporales:
            grupos.append([
                self._dato(nombre, "DW", "?") for nombre in self.temporales
            ])

        extras = []
        if self.usa_division:
            extras.append(self._dato("COC", "DB", "0"))
            extras.append(self._dato("RESI", "DB", "0"))
        extras.extend(
            self._dato(etiqueta, "DB", f'"{texto} $",0AH,0DH')
            for etiqueta, texto in self.mensajes
        )
        if extras:
            grupos.append(extras)

        datos = "\n\n".join("\n".join(grupo) for grupo in grupos)
        instrucciones = "\n".join(self.codigo).rstrip()
        if datos:
            return f".DATA\n{datos}\n\n.CODE\n{instrucciones}"
        return f".DATA\n\n.CODE\n{instrucciones}"

    def _dato(self, nombre, directiva, valor):
        return f"{nombre:<8}{directiva:<8}{valor}"

    def _ins(self, mnem, operandos="", comentario=""):
        texto = f"{mnem:<8}{operandos}" if operandos else mnem
        if comentario:
            texto = f"{texto:<32}; {comentario}"
        self.codigo.append(texto.rstrip())

    def _etiqueta(self):
        self._n_eti += 1
        return f"L{self._n_eti}"

    def _temporal(self):
        self._n_temp += 1
        nombre = f"T{self._n_temp}"
        self.temporales.append(nombre)
        return nombre

    def _mensaje(self, valor):
        texto = _texto_cadena(valor)
        if texto in self._texto_mensaje:
            return self._texto_mensaje[texto]
        etiqueta = f"MSG{len(self.mensajes) + 1}"
        self.mensajes.append((etiqueta, texto))
        self._texto_mensaje[texto] = etiqueta
        return etiqueta

    def _marca(self, etiqueta):
        self.codigo.append(f"{etiqueta}:")

    def _recorrer(self, sentencias):
        for sentencia in sentencias:
            antes = len(self.codigo)
            self._sentencia(sentencia)
            if len(self.codigo) > antes:
                self.codigo.append("")
        while self.codigo and self.codigo[-1] == "":
            self.codigo.pop()

    def _sentencia(self, nodo):
        nodo = _desnudar(nodo)
        if nodo is None or isinstance(nodo, (NodoError, str)):
            return
        if isinstance(nodo, Declaracion):
            return
        if isinstance(nodo, Asignacion):
            self._asignacion(nodo)
        elif isinstance(nodo, Println):
            self._println(nodo)
        elif isinstance(nodo, Read):
            self._read(nodo)
        elif isinstance(nodo, Condicional):
            self._condicional(nodo)
        elif isinstance(nodo, Bucle):
            self._while(nodo)
        elif isinstance(nodo, ForStmt):
            self._for(nodo)
        elif isinstance(nodo, Bloque):
            self._recorrer(nodo.sentencias)
        elif isinstance(nodo, Programa):
            self._recorrer(nodo.sentencias)

    def _asignacion(self, nodo):
        expr = _desnudar(nodo.expresion)
        destino = nodo.identificador
        if isinstance(expr, Numero):
            self._ins("MOV", f"{destino}, {expr.valor}")
            return
        if isinstance(expr, Booleano):
            self._ins("MOV", f"{destino}, {_texto_simple(expr)}")
            return
        if isinstance(expr, Cadena):
            etiqueta = self._mensaje(expr.valor)
            self._ins("LEA", f"AX, {etiqueta}")
            self._ins("MOV", f"{destino}, AX")
            return
        self._evaluar(expr)
        self._ins("MOV", f"{destino}, AX")

    def _println(self, nodo):
        expr = _desnudar(nodo.expresion)
        if isinstance(expr, Cadena):
            etiqueta = self._mensaje(expr.valor)
            self._ins("MOV", "BX, 0001H", "Salida de un String")
            self._ins("LEA", f"DX, {etiqueta}")
            self._ins("MOV", "AH, 09H")
            self._ins("INT", "21H")
            return
        if isinstance(expr, Identificador) and self.tipos.get(expr.nombre) == "string":
            self._ins("MOV", "BX, 0001H", "Salida de un String")
            self._ins("LEA", f"DX, {expr.nombre}")
            self._ins("MOV", "AH, 09H")
            self._ins("INT", "21H")
            return
        if not isinstance(expr, Identificador):
            self._evaluar(expr)
            origen = "AL"
        else:
            origen = expr.nombre
        self._ins("MOV", "BX, 0001H")
        self._ins("MOV", f"DL, {origen}")
        self._ins("MOV", "AH, 02H")
        self._ins("INT", "21H")

    def _read(self, nodo):
        self._ins("MOV", "AH, 01H")
        self._ins("INT", "21H")
        self._ins("MOV", f"{nodo.identificador}, AL")

    def _condicional(self, nodo):
        fin = self._etiqueta()
        ramas = [(nodo.condicion, nodo.cuerpo)] + list(nodo.elifs)
        for indice, (condicion, cuerpo) in enumerate(ramas):
            hay_mas = indice < len(ramas) - 1 or nodo.sino is not None
            falso = self._etiqueta() if hay_mas else fin
            self._saltar_si_falso(condicion, falso)
            self._recorrer(_sentencias(cuerpo))
            if hay_mas:
                self._ins("JMP", fin)
                self._marca(falso)
        if nodo.sino is not None:
            self._recorrer(_sentencias(nodo.sino))
        self._marca(fin)

    def _while(self, nodo):
        inicio = self._etiqueta()
        fin = self._etiqueta()
        self._marca(inicio)
        self._saltar_si_falso(nodo.condicion, fin)
        self._recorrer(_sentencias(nodo.cuerpo))
        self._ins("JMP", inicio)
        self._marca(fin)

    def _for(self, nodo):
        self._asignacion(Asignacion(nodo.variable_init, nodo.expr_init))
        inicio = self._etiqueta()
        fin = self._etiqueta()
        self._marca(inicio)
        self._saltar_si_falso(nodo.condicion, fin)
        self._recorrer(_sentencias(nodo.cuerpo))
        self._asignacion(Asignacion(nodo.variable_incr, nodo.expr_incr))
        self._ins("JMP", inicio)
        self._marca(fin)

    def _saltar_si_falso(self, nodo, etiqueta):
        nodo = _desnudar(nodo)
        if isinstance(nodo, BinOp) and nodo.operador in SALTO_SI_FALSO:
            salto = self._comparar(nodo.izquierda, nodo.operador, nodo.derecha)
            self._ins(salto, etiqueta)
            return
        self._evaluar(nodo)
        self._ins("CMP", "AX, 0")
        self._ins("JE", etiqueta)

    def _comparar(self, izquierda, operador, derecha):
        derecha = _desnudar(derecha)
        if _es_simple(derecha):
            self._evaluar(izquierda)
            self._ins("CMP", f"AX, {_texto_simple(derecha)}")
        else:
            self._evaluar(derecha)
            temporal = self._temporal()
            self._ins("MOV", f"{temporal}, AX")
            self._evaluar(izquierda)
            self._ins("CMP", f"AX, {temporal}")
        return SALTO_SI_FALSO[operador]

    def _evaluar(self, nodo):
        """Deja el resultado de la expresión en AX."""
        nodo = _desnudar(nodo)
        if isinstance(nodo, Numero):
            self._ins("MOV", f"AX, {nodo.valor}")
            return
        if isinstance(nodo, Identificador):
            self._ins("MOV", f"AX, {nodo.nombre}")
            return
        if isinstance(nodo, Booleano):
            self._ins("MOV", f"AX, {_texto_simple(nodo)}")
            return
        if isinstance(nodo, Cadena):
            self._ins("LEA", f"AX, {self._mensaje(nodo.valor)}")
            return
        if isinstance(nodo, BinOp):
            if nodo.operador in SALTO_SI_FALSO:
                self._relacional(nodo)
            elif nodo.operador in ARITMETICOS:
                self._aritmetica(nodo)
            return
        self._ins("MOV", "AX, 0")

    def _relacional(self, nodo):
        verdadero = self._etiqueta()
        falso = self._etiqueta()
        salto = self._comparar(nodo.izquierda, nodo.operador, nodo.derecha)
        self._ins(salto, falso)
        self._ins("MOV", "AX, 1")
        self._ins("JMP", verdadero)
        self._marca(falso)
        self._ins("MOV", "AX, 0")
        self._marca(verdadero)

    def _aritmetica(self, nodo):
        operador = nodo.operador
        derecha = _desnudar(nodo.derecha)
        if operador == "&":
            temporal = self._preparar_operandos(nodo.izquierda, derecha)
            self._ins("MUL", self._operando_mul(derecha, temporal), "Resultado en EAX")
            return
        if operador == "|":
            self.usa_division = True
            temporal = self._preparar_operandos(nodo.izquierda, derecha)
            if temporal is None:
                self._ins("MOV", f"DX, {_texto_simple(derecha)}")
            else:
                self._ins("MOV", f"DX, {temporal}")
            self._ins("DIV", "DX", "Resultado AL=Coc AH=Resi")
            self._ins("MOV", "COC, AL")
            self._ins("MOV", "RESI, AH")
            self._ins("MOV", "AH, 0")
            return
        instruccion = ARITMETICOS[operador]
        if _es_simple(derecha):
            self._evaluar(nodo.izquierda)
            self._ins(instruccion, f"AX, {_texto_simple(derecha)}")
            return
        self._evaluar(derecha)
        temporal = self._temporal()
        self._ins("MOV", f"{temporal}, AX")
        self._evaluar(nodo.izquierda)
        self._ins(instruccion, f"AX, {temporal}")

    def _preparar_operandos(self, izquierda, derecha):
        """Deja el operando izquierdo en AX. El derecho complejo queda en un temporal."""
        derecha = _desnudar(derecha)
        if _es_simple(derecha):
            self._evaluar(izquierda)
            return None
        self._evaluar(derecha)
        temporal = self._temporal()
        self._ins("MOV", f"{temporal}, AX")
        self._evaluar(izquierda)
        return temporal

    def _operando_mul(self, derecha, temporal):
        derecha = _desnudar(derecha)
        if isinstance(derecha, Identificador):
            return derecha.nombre
        if isinstance(derecha, (Numero, Booleano)):
            self._ins("MOV", f"BX, {_texto_simple(derecha)}")
            return "BX"
        return temporal


def generar_codigo_intermedio(tabla, arbol=None):
    """
    Traduce el programa a representación intermedia .DATA / .CODE.

    int      -> nombre DW ?
    boolean  -> nombre DB ?
    string   -> nombre DB ?
    float    -> nombre DD ?

    Las asignaciones, las operaciones y println se emiten en .CODE.
    """
    generador = Generador(tabla)
    if arbol is None:
        if not generador.variables:
            return "No hay variables para generar."
        return generador._armar()
    return generador.generar(arbol)
