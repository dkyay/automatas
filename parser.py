"""
Analizador sintáctico LL(1) por descenso recursivo.
Gramática del Lenguaje Genesis (G = {SI, NT, T, P}).
"""

from ast_nodes import (
    Programa,
    Declaracion,
    Asignacion,
    BinOp,
    Numero,
    Cadena,
    Identificador,
    Booleano,
    Condicional,
    Bucle,
    NodoError,
    Println,
    Read,
    ForStmt,
    Bloque,
    Parentesis,
)

TIPOS_TOKEN = frozenset({'INT', 'BOOLEAN', 'STRING'})

INICIO_DECL = TIPOS_TOKEN | frozenset({
    'PRINTLN', 'READ', 'WHILE', 'IF', 'FOR', 'ID',
})

OPERADORES = frozenset({'ARROBA', 'HASH', 'AMP', 'PIPE', 'RELACIONAL'})

OPERADORES_VALIDOS = frozenset({
    '@', '#', '&', '|', '==', '!=', '<', '>', '<=', '>=',
})

TERMINO_INICIO = frozenset({'ID', 'NUMERO', 'TRUE', 'FALSE'})

SINCRONIZACION = frozenset({'PUNTO_COMA', 'LLAVE_DER', 'FIN'})


class Parser:
    def __init__(self, tokens, tabla_simbolos_existente=None):
        self.tokens = list(tokens)
        self.pos = 0
        self.errores = []
        self.tabla = tabla_simbolos_existente

    def parsear(self):
        arbol = self.programa()
        return arbol, self.errores

    # --- Utilidades de tokens ---
    def _fin(self):
        return self.pos >= len(self.tokens)

    def _actual(self):
        if self._fin():
            return None
        return self.tokens[self.pos]

    def _actual_tipo(self):
        tok = self._actual()
        return tok.type if tok else None

    def _actual_valor(self):
        tok = self._actual()
        return tok.value if tok else None

    def _actual_linea(self):
        tok = self._actual()
        return tok.lineno if tok else 0

    def _lookahead(self, n=1):
        idx = self.pos + n
        if idx >= len(self.tokens):
            return None
        return self.tokens[idx]

    def _lookahead_tipo(self, n=1):
        tok = self._lookahead(n)
        return tok.type if tok else None

    def _avanzar(self):
        if not self._fin():
            self.pos += 1

    def _consumir(self, tipo):
        if self._actual_tipo() == tipo:
            tok = self._actual()
            self._avanzar()
            return tok
        return None

    def _consumir_tipos(self, *tipos):
        if self._actual_tipo() in tipos:
            tok = self._actual()
            self._avanzar()
            return tok
        return None

    def _coincide(self, tipo):
        return self._actual_tipo() == tipo

    def _coincide_tipos(self, *tipos):
        return self._actual_tipo() in tipos

    def _token_lexema(self, tok):
        if tok is None:
            return "EOF"
        return str(tok.value)

    def _agregar_error(self, mensaje):
        if mensaje not in self.errores:
            self.errores.append(mensaje)

    def _error_inesperado(self, esperado, tok=None):
        tok = tok or self._actual()
        if tok is None:
            self._agregar_error(
                f"Línea {self._actual_linea()}: fin de archivo inesperado — se esperaba {esperado}."
            )
            return
        self._agregar_error(
            f"Línea {tok.lineno}: token '{self._token_lexema(tok)}' inesperado — se esperaba {esperado}."
        )

    def _error_operando(self, tok=None):
        tok = tok or self._actual()
        if tok is None:
            self._agregar_error(
                f"Línea {self._actual_linea()}: fin de archivo inesperado — se esperaba un término, una cadena o '('."
            )
            return
        self._agregar_error(
            f"Línea {tok.lineno}: token '{self._token_lexema(tok)}' inesperado — se esperaba un término, una cadena o '('."
        )

    def _error_parentesis_no_cerrado(self, linea=None):
        linea = linea or self._actual_linea()
        self._agregar_error(f"Línea {linea}: paréntesis '(' no cerrado.")

    def _error_llave_no_cerrada(self, linea=None):
        linea = linea or self._actual_linea()
        self._agregar_error(f"Línea {linea}: llave '{{' no cerrada.")

    def _error_punto_y_coma(self, linea=None):
        linea = linea or self._actual_linea()
        self._agregar_error(f"Línea {linea}: se esperaba ';' después de la declaración.")

    def _error_expresion_incompleta(self, linea=None):
        linea = linea or self._actual_linea()
        self._agregar_error(f"Línea {linea}: expresión incompleta.")

    def _sincronizar(self):
        while not self._fin():
            t = self._actual_tipo()
            if t == 'PUNTO_COMA':
                self._avanzar()
                return
            if t in ('FIN', 'LLAVE_DER', 'PAR_DER'):
                return
            self._avanzar()

    def _sincronizar_decl(self):
        while not self._fin():
            t = self._actual_tipo()
            if t in SINCRONIZACION:
                if t == 'PUNTO_COMA':
                    self._avanzar()
                return
            if t in INICIO_DECL or t in ('FIN', 'INICIO'):
                return
            self._avanzar()

    def _expresion_vacia(self, nodo):
        return nodo is None or isinstance(nodo, NodoError)

    def _consultar_declarado(self, nombre, linea):
        if self.tabla is None:
            return
        if nombre not in self.tabla:
            self._agregar_error(
                f"Línea {linea}: identificador '{nombre}' usado sin declaración previa."
            )

    def _exigir_punto_y_coma(self, linea):
        if self._consumir('PUNTO_COMA'):
            return True
        self._error_punto_y_coma(linea)
        while not self._fin():
            t = self._actual_tipo()
            if t == 'PUNTO_COMA':
                self._avanzar()
                return False
            if t in ('FIN', 'LLAVE_DER') or t in INICIO_DECL:
                return False
            self._avanzar()
        return False

    def _bloque_llaves(self, linea):
        if not self._consumir('LLAVE_IZQ'):
            self._error_inesperado("'{'")
            self._sincronizar_decl()
            return Bloque([], '{', '}')
        sentencias = self.lista_decl()
        if not self._consumir('LLAVE_DER'):
            self._error_llave_no_cerrada(linea)
        return Bloque(sentencias, '{', '}')

    # --- Reglas gramaticales ---
    def programa(self):
        if not self._consumir('INICIO'):
            self._error_inesperado("'inicio'")

        sentencias = self.lista_decl()

        if not self._consumir('FIN'):
            self._error_inesperado("'fin'")

        self._reportar_tokens_sobrantes()
        return Programa(sentencias)

    def _reportar_tokens_sobrantes(self):
        while not self._fin():
            tok = self._actual()
            if tok.type == 'CARACTER_ILEGAL':
                self._agregar_error(
                    f"Línea {tok.lineno}: carácter ilegal '{tok.value}' fuera de la gramática."
                )
            else:
                self._error_inesperado("fin de programa", tok)
            self._avanzar()

    def lista_decl(self):
        sentencias = []
        while not self._fin():
            tipo = self._actual_tipo()
            if tipo in ('FIN', 'LLAVE_DER'):
                break
            if tipo == 'PUNTO_COMA':
                self._agregar_error(
                    f"Línea {self._actual_linea()}: ';' inesperado — se esperaba una declaración."
                )
                self._avanzar()
                continue
            linea = self._actual_linea()
            decl = self.decl()
            if decl is not None:
                sentencias.append(decl)
            self._exigir_punto_y_coma(linea)
        return sentencias

    def decl(self):
        if self._fin():
            return None

        tipo = self._actual_tipo()

        if tipo in TIPOS_TOKEN:
            return self.declaracion()

        if tipo == 'PRINTLN':
            return self.println_stmt()

        if tipo == 'READ':
            return self.read_stmt()

        if tipo == 'WHILE':
            return self.bucle()

        if tipo == 'IF':
            return self.condicional()

        if tipo == 'FOR':
            return self.for_stmt()

        if tipo == 'ID':
            return self.asignacion()

        tok = self._actual()
        if tok is not None and tok.type == 'CARACTER_ILEGAL':
            self._agregar_error(
                f"Línea {tok.lineno}: carácter ilegal '{tok.value}' fuera de la gramática."
            )
        else:
            self._error_inesperado("una declaración", tok)
        self._avanzar()
        self._sincronizar_decl()
        return NodoError("declaración inválida")

    def declaracion(self):
        tipo_tok = self._consumir_tipos(*TIPOS_TOKEN)
        if tipo_tok is None:
            self._error_inesperado("un tipo de dato (int, boolean o string)")
            self._sincronizar_decl()
            return NodoError("declaracion")

        id_tok = self._consumir('ID')
        if id_tok is None:
            self._error_inesperado("un identificador")
            self._sincronizar_decl()
            return NodoError("declaracion")

        return Declaracion(str(tipo_tok.value), str(id_tok.value))

    def asignacion(self):
        linea = self._actual_linea()
        id_tok = self._consumir('ID')
        if id_tok is None:
            self._error_inesperado("un identificador")
            self._sincronizar_decl()
            return NodoError("asignacion")

        self._consultar_declarado(id_tok.value, id_tok.lineno)

        if not self._consumir('ASIGNACION'):
            self._error_inesperado("'='")
            self._sincronizar_decl()
            return NodoError("asignacion")

        expresion = self.expresion()
        if self._expresion_vacia(expresion):
            self._error_expresion_incompleta(linea)

        return Asignacion(str(id_tok.value), expresion)

    def println_stmt(self):
        linea = self._actual_linea()
        if not self._consumir('PRINTLN'):
            return NodoError("println")
        expresion = self.expresion()
        if self._expresion_vacia(expresion):
            self._error_expresion_incompleta(linea)
        return Println(expresion)

    def read_stmt(self):
        if not self._consumir('READ'):
            return NodoError("read")
        id_tok = self._consumir('ID')
        if id_tok is None:
            self._error_inesperado("un identificador")
            self._sincronizar_decl()
            return NodoError("read")
        self._consultar_declarado(id_tok.value, id_tok.lineno)
        return Read(str(id_tok.value))

    def condicional(self):
        linea = self._actual_linea()
        if not self._consumir('IF'):
            return NodoError("if")

        if not self._consumir('PAR_IZQ'):
            self._error_inesperado("'('")
        condicion = self.expresion()
        if not self._consumir('PAR_DER'):
            self._error_parentesis_no_cerrado(linea)

        cuerpo = self._bloque_llaves(linea)
        elifs = self.else_if_opt()
        sino = self.else_opt()
        return Condicional(condicion, cuerpo, sino, elifs)

    def else_if_opt(self):
        elifs = []
        while self._coincide('ELSE') and self._lookahead_tipo(1) == 'IF':
            linea = self._actual_linea()
            self._avanzar()
            self._avanzar()
            if not self._consumir('PAR_IZQ'):
                self._error_inesperado("'('")
            cond = self.expresion()
            if not self._consumir('PAR_DER'):
                self._error_parentesis_no_cerrado(linea)
            cuerpo = self._bloque_llaves(linea)
            elifs.append((cond, cuerpo))
        return elifs

    def else_opt(self):
        if not self._coincide('ELSE'):
            return None
        linea = self._actual_linea()
        self._avanzar()
        return self._bloque_llaves(linea)

    def bucle(self):
        linea = self._actual_linea()
        if not self._consumir('WHILE'):
            return NodoError("while")

        if not self._consumir('PAR_IZQ'):
            self._error_inesperado("'('")
        condicion = self.expresion()
        if not self._consumir('PAR_DER'):
            self._error_parentesis_no_cerrado(linea)

        cuerpo = self._bloque_llaves(linea)
        return Bucle(condicion, cuerpo)

    def for_stmt(self):
        linea = self._actual_linea()
        if not self._consumir('FOR'):
            return NodoError("for")

        if not self._consumir('PAR_IZQ'):
            self._error_inesperado("'('")

        id_init = self._consumir('ID')
        if id_init is None:
            self._error_inesperado("un identificador")
            self._sincronizar_decl()
            return NodoError("for")
        self._consultar_declarado(id_init.value, id_init.lineno)

        if not self._consumir('ASIGNACION'):
            self._error_inesperado("'='")
        expr_init = self.expresion()

        if not self._consumir('PUNTO_COMA'):
            self._error_inesperado("';' en la cabecera del for")

        condicion = self.expresion()

        if not self._consumir('PUNTO_COMA'):
            self._error_inesperado("';' en la cabecera del for")

        id_incr = self._consumir('ID')
        if id_incr is None:
            self._error_inesperado("un identificador")
        else:
            self._consultar_declarado(id_incr.value, id_incr.lineno)

        if not self._consumir('ASIGNACION'):
            self._error_inesperado("'='")
        expr_incr = self.expresion()

        if not self._consumir('PAR_DER'):
            self._error_parentesis_no_cerrado(linea)

        cuerpo = self._bloque_llaves(linea)
        nombre_incr = str(id_incr.value) if id_incr is not None else "?"
        return ForStmt(
            str(id_init.value),
            expr_init,
            condicion,
            nombre_incr,
            expr_incr,
            cuerpo,
        )

    def expresion(self):
        tok = self._actual()
        if tok is None:
            self._error_operando()
            return NodoError("expresion")

        if tok.type == 'CADENA':
            self._avanzar()
            return Cadena(tok.value, tok.lineno)

        if tok.type in TERMINO_INICIO:
            return self.termino()

        if tok.type == 'PAR_IZQ':
            linea = tok.lineno
            self._avanzar()
            izquierda = self.expresion()
            op_tok = self._consumir_tipos(*OPERADORES)
            if op_tok is None:
                self._error_inesperado("un operador (@, #, &, |, ==, !=, <, >, <=, >=)")
                if not self._consumir('PAR_DER'):
                    self._error_parentesis_no_cerrado(linea)
                    self._sincronizar()
                return Parentesis(NodoError("operador"))
            op = str(op_tok.value)
            if op not in OPERADORES_VALIDOS:
                self._agregar_error(
                    f"Línea {op_tok.lineno}: operador '{op}' no reconocido."
                )
            derecha = self.expresion()
            if self._expresion_vacia(derecha):
                self._error_operando()
                derecha = NodoError("operando")
            if not self._consumir('PAR_DER'):
                self._error_parentesis_no_cerrado(linea)
                self._sincronizar()
            return Parentesis(BinOp(izquierda, op, derecha))

        self._error_operando(tok)
        self._avanzar()
        return NodoError("expresion")

    def termino(self):
        tok = self._actual()
        if tok is None:
            self._error_operando()
            return NodoError("termino")

        if tok.type == 'ID':
            self._avanzar()
            self._consultar_declarado(tok.value, tok.lineno)
            return Identificador(tok.value, tok.lineno)

        if tok.type == 'NUMERO':
            self._avanzar()
            return Numero(tok.value, tok.lineno)

        if tok.type in ('TRUE', 'FALSE'):
            self._avanzar()
            return Booleano(str(tok.value), tok.lineno)

        self._error_inesperado("un identificador, un número, true o false", tok)
        self._avanzar()
        return NodoError("termino")
