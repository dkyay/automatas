"""Nodos del árbol sintáctico abstracto (AST) — Lenguaje Genesis."""


def _prefijo(nivel):
    return "  " * nivel


def _conector(es_ultimo):
    return "└── " if es_ultimo else "├── "


def _continuacion(es_ultimo):
    return "    " if es_ultimo else "│   "


class Nodo:
    def imprimir(self, nivel=0) -> str:
        raise NotImplementedError

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        return self.imprimir()


def _normalizar_cuerpo(cuerpo):
    if isinstance(cuerpo, Bloque):
        return cuerpo
    return Bloque(cuerpo or [], None, None)


class Bloque(Nodo):
    def __init__(self, sentencias=None, apertura=None, cierre=None):
        self.sentencias = sentencias or []
        self.apertura = apertura
        self.cierre = cierre

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        lineas = []
        ext = prefijo + _continuacion(es_ultimo)
        if self.apertura:
            lineas.append(f"{prefijo}{_conector(False)}{self.apertura}")
            hijo_pref = ext
        else:
            hijo_pref = prefijo + _continuacion(es_ultimo)

        if not self.sentencias:
            lineas.append(f"{hijo_pref}{_conector(True)}(vacío)")
        else:
            for i, sent in enumerate(self.sentencias):
                ultima = i == len(self.sentencias) - 1 and not self.cierre
                if isinstance(sent, Nodo):
                    lineas.append(sent.imprimir_en(hijo_pref, ultima))
                else:
                    lineas.append(f"{hijo_pref}{_conector(ultima)}{sent}")

        if self.cierre:
            lineas.append(f"{prefijo}{_conector(True)}{self.cierre}")
        return "\n".join(lineas)

    def imprimir(self, nivel=0) -> str:
        return self.imprimir_en(_prefijo(nivel), True)


class Parentesis(Nodo):
    def __init__(self, expresion):
        self.expresion = expresion

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        lineas = [f"{prefijo}{_conector(False)}("]
        ext = prefijo + _continuacion(es_ultimo)
        if self.expresion is not None:
            lineas.append(self.expresion.imprimir_en(ext, False))
        lineas.append(f"{prefijo}{_conector(es_ultimo)})")
        return "\n".join(lineas)

    def imprimir(self, nivel=0) -> str:
        return self.imprimir_en(_prefijo(nivel), True)


class NodoError(Nodo):
    def __init__(self, descripcion="error"):
        self.descripcion = descripcion

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        return f"{prefijo}{_conector(es_ultimo)}[Error: {self.descripcion}]"

    def imprimir(self, nivel=0) -> str:
        return self.imprimir_en(_prefijo(nivel), True)


class Programa(Nodo):
    def __init__(self, sentencias=None):
        self.sentencias = sentencias or []

    def imprimir(self, nivel=0) -> str:
        lineas = [_prefijo(nivel) + "Programa"]
        base = _prefijo(nivel)
        hijos = ["inicio"] + list(self.sentencias) + ["fin"]
        for i, sent in enumerate(hijos):
            ultima = i == len(hijos) - 1
            pref = base + _continuacion(ultima)
            if isinstance(sent, Nodo):
                lineas.append(sent.imprimir_en(pref, ultima))
            else:
                lineas.append(pref + _conector(ultima) + str(sent))
        return "\n".join(lineas)

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        return self.imprimir()


class Declaracion(Nodo):
    def __init__(self, tipo, identificador):
        self.tipo = tipo
        self.identificador = identificador

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        lineas = [f"{prefijo}{_conector(es_ultimo)}Declaracion ({self.tipo})"]
        ext = prefijo + _continuacion(es_ultimo)
        lineas.append(f"{ext}{_conector(True)}Identificador: {self.identificador}")
        return "\n".join(lineas)

    def imprimir(self, nivel=0) -> str:
        return self.imprimir_en(_prefijo(nivel), True)


class Asignacion(Nodo):
    def __init__(self, identificador, expresion):
        self.identificador = identificador
        self.expresion = expresion

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        lineas = [f"{prefijo}{_conector(es_ultimo)}Asignacion"]
        ext = prefijo + _continuacion(es_ultimo)
        lineas.append(f"{ext}{_conector(False)}Identificador: {self.identificador}")
        if self.expresion is not None:
            lineas.append(self.expresion.imprimir_en(ext, True))
        return "\n".join(lineas)

    def imprimir(self, nivel=0) -> str:
        return self.imprimir_en(_prefijo(nivel), True)


class Println(Nodo):
    def __init__(self, expresion):
        self.expresion = expresion

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        lineas = [f"{prefijo}{_conector(es_ultimo)}Println"]
        ext = prefijo + _continuacion(es_ultimo)
        if self.expresion is not None:
            lineas.append(self.expresion.imprimir_en(ext, True))
        return "\n".join(lineas)

    def imprimir(self, nivel=0) -> str:
        return self.imprimir_en(_prefijo(nivel), True)


class Read(Nodo):
    def __init__(self, identificador):
        self.identificador = identificador

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        lineas = [f"{prefijo}{_conector(es_ultimo)}Read"]
        ext = prefijo + _continuacion(es_ultimo)
        lineas.append(f"{ext}{_conector(True)}Identificador: {self.identificador}")
        return "\n".join(lineas)

    def imprimir(self, nivel=0) -> str:
        return self.imprimir_en(_prefijo(nivel), True)


class BinOp(Nodo):
    def __init__(self, izquierda, operador, derecha):
        self.izquierda = izquierda
        self.operador = operador
        self.derecha = derecha

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        lineas = [f"{prefijo}{_conector(es_ultimo)}BinOp({self.operador})"]
        ext = prefijo + _continuacion(es_ultimo)
        if self.izquierda is not None:
            lineas.append(self.izquierda.imprimir_en(ext, False))
        if self.derecha is not None:
            lineas.append(self.derecha.imprimir_en(ext, True))
        return "\n".join(lineas)

    def imprimir(self, nivel=0) -> str:
        return self.imprimir_en(_prefijo(nivel), True)


class Numero(Nodo):
    def __init__(self, valor, linea=0):
        self.valor = valor
        self.linea = linea

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        return f"{prefijo}{_conector(es_ultimo)}Numero: {self.valor}"

    def imprimir(self, nivel=0) -> str:
        return self.imprimir_en(_prefijo(nivel), True)


class Cadena(Nodo):
    def __init__(self, valor, linea=0):
        self.valor = valor
        self.linea = linea

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        return f"{prefijo}{_conector(es_ultimo)}Cadena: {self.valor}"

    def imprimir(self, nivel=0) -> str:
        return self.imprimir_en(_prefijo(nivel), True)


class Identificador(Nodo):
    def __init__(self, nombre, linea=0):
        self.nombre = nombre
        self.linea = linea

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        return f"{prefijo}{_conector(es_ultimo)}Identificador: {self.nombre}"

    def imprimir(self, nivel=0) -> str:
        return self.imprimir_en(_prefijo(nivel), True)


class Booleano(Nodo):
    def __init__(self, valor, linea=0):
        self.valor = valor
        self.linea = linea

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        return f"{prefijo}{_conector(es_ultimo)}Booleano: {self.valor}"

    def imprimir(self, nivel=0) -> str:
        return self.imprimir_en(_prefijo(nivel), True)


class Condicional(Nodo):
    def __init__(self, condicion, cuerpo, sino=None, elifs=None):
        self.condicion = condicion
        self.cuerpo = cuerpo or []
        self.elifs = elifs or []
        self.sino = sino

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        tiene_else = self.sino is not None
        tiene_elif = len(self.elifs) > 0
        if tiene_else and tiene_elif:
            etiqueta = "Condicional (if / else if / else)"
        elif tiene_else:
            etiqueta = "Condicional (if-else)"
        elif tiene_elif:
            etiqueta = "Condicional (if / else if)"
        else:
            etiqueta = "Condicional (if)"
        lineas = [f"{prefijo}{_conector(es_ultimo)}{etiqueta}"]
        ext = prefijo + _continuacion(es_ultimo)
        lineas.append(f"{ext}{_conector(False)}Condicion:")
        if self.condicion is not None:
            if isinstance(self.condicion, Parentesis):
                lineas.append(self.condicion.imprimir_en(ext + "│   ", True))
            else:
                lineas.append(self.condicion.imprimir_en(ext + "│   ", True))
        lineas.append(f"{ext}{_conector(not self.elifs and not tiene_else)}Cuerpo:")
        cuerpo_pref = ext + _continuacion(not self.elifs and not tiene_else)
        lineas.extend(self._imprimir_bloque(self.cuerpo, cuerpo_pref))
        for idx, (cond_e, cuerpo_e) in enumerate(self.elifs):
            ultimo_elif = idx == len(self.elifs) - 1 and not tiene_else
            lineas.append(f"{ext}{_conector(ultimo_elif)}Else if:")
            elif_ext = ext + _continuacion(ultimo_elif)
            if cond_e is not None:
                lineas.append(cond_e.imprimir_en(elif_ext, False))
            lineas.extend(self._imprimir_bloque(cuerpo_e, elif_ext))
        if tiene_else:
            lineas.append(f"{ext}{_conector(True)}Else:")
            else_pref = ext + "    "
            lineas.extend(self._imprimir_bloque(self.sino, else_pref))
        return "\n".join(lineas)

    def _imprimir_bloque(self, cuerpo, prefijo):
        return [_normalizar_cuerpo(cuerpo).imprimir_en(prefijo, True)]

    def imprimir(self, nivel=0) -> str:
        return self.imprimir_en(_prefijo(nivel), True)


class Bucle(Nodo):
    def __init__(self, condicion, cuerpo):
        self.condicion = condicion
        self.cuerpo = cuerpo or []

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        lineas = [f"{prefijo}{_conector(es_ultimo)}Bucle (while)"]
        ext = prefijo + _continuacion(es_ultimo)
        lineas.append(f"{ext}{_conector(False)}Condicion:")
        if self.condicion is not None:
            lineas.append(self.condicion.imprimir_en(ext + "│   ", True))
        lineas.append(f"{ext}{_conector(True)}Cuerpo:")
        cuerpo_pref = ext + "    "
        lineas.extend(self._imprimir_bloque(self.cuerpo, cuerpo_pref))
        return "\n".join(lineas)

    def _imprimir_bloque(self, cuerpo, prefijo):
        return [_normalizar_cuerpo(cuerpo).imprimir_en(prefijo, True)]

    def imprimir(self, nivel=0) -> str:
        return self.imprimir_en(_prefijo(nivel), True)


class ForStmt(Nodo):
    def __init__(self, variable_init, expr_init, condicion, variable_incr, expr_incr, cuerpo):
        self.variable_init = variable_init
        self.expr_init = expr_init
        self.condicion = condicion
        self.variable_incr = variable_incr
        self.expr_incr = expr_incr
        self.cuerpo = cuerpo or []

    def imprimir_en(self, prefijo, es_ultimo=True) -> str:
        lineas = [f"{prefijo}{_conector(es_ultimo)}For"]
        ext = prefijo + _continuacion(es_ultimo)
        init = Asignacion(self.variable_init, self.expr_init)
        incr = Asignacion(self.variable_incr, self.expr_incr)
        lineas.append(f"{ext}{_conector(False)}Inicio:")
        lineas.append(init.imprimir_en(ext + "│   ", True))
        lineas.append(f"{ext}{_conector(False)}Condicion:")
        if self.condicion is not None:
            lineas.append(self.condicion.imprimir_en(ext + "│   ", True))
        lineas.append(f"{ext}{_conector(False)}Incremento:")
        lineas.append(incr.imprimir_en(ext + "│   ", True))
        lineas.append(f"{ext}{_conector(True)}Cuerpo:")
        cuerpo_pref = ext + "    "
        lineas.extend(_normalizar_cuerpo(self.cuerpo).imprimir_en(cuerpo_pref, True).split("\n"))
        return "\n".join(lineas)

    def imprimir(self, nivel=0) -> str:
        return self.imprimir_en(_prefijo(nivel), True)
