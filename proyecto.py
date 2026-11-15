import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import ply.lex as lex
from parser import Parser
from codigo_intermedio import generar_codigo_intermedio
from codigo_objeto import generar_filas_objeto

# ==========================================
# 1. DEFINICIÓN DEL ANALIZADOR LÉXICO
#     Lenguaje Genesis
# ==========================================

reservadas = {
    'inicio': 'INICIO',
    'fin': 'FIN',
    'int': 'INT',
    'boolean': 'BOOLEAN',
    'string': 'STRING',
    'true': 'TRUE',
    'false': 'FALSE',
    'println': 'PRINTLN',
    'read': 'READ',
    'while': 'WHILE',
    'if': 'IF',
    'else': 'ELSE',
    'for': 'FOR',
}

TIPOS_DATO = {'INT', 'BOOLEAN', 'STRING'}

# Etiquetas cortas como en la interfaz Genesis (PR, TD, PYC, …).
ETIQUETA_TOKEN = {
    'INICIO': 'PR', 'FIN': 'PR', 'WHILE': 'PR', 'IF': 'PR', 'ELSE': 'PR',
    'FOR': 'PR', 'TRUE': 'PR', 'FALSE': 'PR', 'READ': 'PR', 'PRINTLN': 'PRINTLN',
    'INT': 'TD', 'BOOLEAN': 'TD', 'STRING': 'TD',
    'ID': 'ID', 'NUMERO': 'NUM', 'CADENA': 'CAD',
    'ASIGNACION': 'ASIGN', 'PUNTO_COMA': 'PYC',
    'ARROBA': 'OP_ARIT', 'HASH': 'OP_ARIT', 'AMP': 'OP_ARIT', 'PIPE': 'OP_ARIT',
    'RELACIONAL': 'OP_REL',
    'PAR_IZQ': 'PAR_IZQ', 'PAR_DER': 'PAR_DER',
    'LLAVE_IZQ': 'LLAVE_IZQ', 'LLAVE_DER': 'LLAVE_DER',
    'CARACTER_ILEGAL': 'ERR',
}

tokens = [
    'ID', 'NUMERO', 'CADENA',
    'ARROBA', 'HASH', 'AMP', 'PIPE',
    'RELACIONAL', 'ASIGNACION',
    'PAR_IZQ', 'PAR_DER', 'LLAVE_IZQ', 'LLAVE_DER', 'PUNTO_COMA',
    'CARACTER_ILEGAL',
] + list(reservadas.values())

t_ignore = ' \t'

lista_errores = []
tabla_simbolos_memoria = []


def registrar_error(mensaje, linea, posicion):
    lista_errores.append((mensaje, linea, posicion))


def t_COMMENT_LINE(t):
    r'//.*'
    pass


t_RELACIONAL = r'>=|<=|==|!=|>|<'
t_ASIGNACION = r'='
t_ARROBA = r'@'
t_HASH = r'\#'
t_AMP = r'&'
t_PIPE = r'\|'
t_PAR_IZQ = r'\('
t_PAR_DER = r'\)'
t_LLAVE_IZQ = r'\{'
t_LLAVE_DER = r'\}'
t_PUNTO_COMA = r';'


def t_NUMERO_MALFORMADO(t):
    r'\d+\.[\d.]*'
    registrar_error('Número mal formado', t.lexer.lineno, t.lexpos)


def t_ID_INVALIDO(t):
    r'\d+[a-zA-Z][a-zA-Z0-9]*'
    registrar_error(
        'Identificador inválido: no puede iniciar con número',
        t.lexer.lineno,
        t.lexpos,
    )


def t_CADENA(t):
    r'"[^"\n]*"'
    return t


def t_CADENA_SIN_CERRAR(t):
    r'"[^"\n]*'
    registrar_error('Cadena no cerrada', t.lexer.lineno, t.lexpos)


def t_NUMERO(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_ID(t):
    r'[A-Za-z][A-Za-z0-9]*'
    t.type = reservadas.get(t.value, 'ID')
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_CARACTER_ILEGAL(t):
    r'[^\x00-\x7F]'
    ch = t.value[0]
    registrar_error(f"Carácter ilegal '{ch}'", t.lexer.lineno, t.lexpos)
    t.type = 'CARACTER_ILEGAL'
    t.value = ch
    return t


def t_error(t):
    ch = t.value[0]
    registrar_error(f"Carácter ilegal '{ch}'", t.lexer.lineno, t.lexpos)
    t.lexer.skip(1)


lexer = lex.lex()


# ==========================================
# 2. LÓGICA DE LA INTERFAZ
# ==========================================

EJEMPLO = """inicio
int x;
int y;
int res;
x = 5;
y = 3;
res = (x @ y);
println(res);
fin
"""

ultimo_arbol = None
ultimos_errores_sint = []
ultimo_ci = ""
lista_tokens_actual = []


def _reiniciar_estado_simbolos():
    return {
        'tipo_pendiente': None,
        'id_declaracion': None,
        'entrada_actual': None,
        'esperando_valor': False,
    }


def _texto_ambito(profundidad):
    if profundidad > 0:
        return f"Bloque (nivel {profundidad})"
    return "Global"


def _buscar_simbolo(nombre):
    for entrada in reversed(tabla_simbolos_memoria):
        if entrada['nombre'] == nombre:
            return entrada
    return None


def _tabla_simbolos_para_parser():
    vista = {}
    for entrada in tabla_simbolos_memoria:
        nombre = entrada['nombre']
        if nombre not in vista:
            vista[nombre] = entrada
    return vista


def _tabla_para_codigo_intermedio():
    vista = {}
    for entrada in tabla_simbolos_memoria:
        nombre = entrada['nombre']
        if nombre not in vista:
            vista[nombre] = entrada['tipo']
    return vista


def _set_text(widget, texto, editable=False):
    widget.config(state="normal")
    widget.delete("1.0", "end")
    widget.insert("end", texto)
    if not editable:
        widget.config(state="disabled")


def _mostrar_codigo_intermedio(texto):
    global ultimo_ci
    ultimo_ci = texto or ""
    _set_text(widget_ci, ultimo_ci)


def _mostrar_codigo_objeto(texto_ci_o_mensaje):
    for item in tabla_objeto.get_children():
        tabla_objeto.delete(item)

    if (
        not texto_ci_o_mensaje
        or not texto_ci_o_mensaje.strip()
        or texto_ci_o_mensaje.strip().startswith("No se puede")
        or texto_ci_o_mensaje.strip().startswith("No hay código")
    ):
        msg = (texto_ci_o_mensaje or "Genera primero el CI.").strip()
        tabla_objeto.insert("", tk.END, values=("", msg, ""))
        return

    for seccion, direccion, contenido, hex_txt in generar_filas_objeto(texto_ci_o_mensaje):
        if seccion and not direccion and not contenido and not hex_txt:
            tabla_objeto.insert("", tk.END, values=(f"── {seccion} ──", "", ""))
        else:
            tabla_objeto.insert("", tk.END, values=(direccion, contenido, hex_txt))


def _lexico_y_simbolos(codigo_fuente):
    """Recorre el lexer: construye tokens, tabla de símbolos y errores léxicos."""
    global lista_tokens_actual

    lista_errores.clear()
    tabla_simbolos_memoria.clear()
    lista_tokens_actual = []
    lexer.lineno = 1
    lexer.input(codigo_fuente)

    contador_id = 1
    contador_posicion = 1
    estado = _reiniciar_estado_simbolos()
    profundidad_llaves = 0
    nombres_declarados = {}
    lineas_tokens = []

    def reiniciar_declaracion():
        estado['tipo_pendiente'] = None
        estado['id_declaracion'] = None
        estado['entrada_actual'] = None
        estado['esperando_valor'] = False

    while True:
        tok = lexer.token()
        if not tok:
            break

        lista_tokens_actual.append(tok)
        etiqueta = ETIQUETA_TOKEN.get(tok.type, tok.type)
        lineas_tokens.append(f"{etiqueta}, {tok.value}")

        if tok.type == 'LLAVE_IZQ':
            profundidad_llaves += 1
        elif tok.type == 'LLAVE_DER':
            profundidad_llaves = max(0, profundidad_llaves - 1)

        if tok.type in TIPOS_DATO:
            reiniciar_declaracion()
            estado['tipo_pendiente'] = tok.value

        elif tok.type == 'ID':
            if estado['tipo_pendiente'] is not None:
                if tok.value in nombres_declarados:
                    registrar_error(
                        f"Identificador duplicado: '{tok.value}' ya declarado "
                        f"(línea {nombres_declarados[tok.value]})",
                        tok.lineno,
                        tok.lexpos,
                    )
                else:
                    nombres_declarados[tok.value] = tok.lineno

                entrada = {
                    'id_int': contador_id,
                    'nombre': tok.value,
                    'tipo': estado['tipo_pendiente'],
                    'valor': 'null',
                    'posicion': contador_posicion,
                    'linea_declaracion': tok.lineno,
                    'ambito': _texto_ambito(profundidad_llaves),
                }
                tabla_simbolos_memoria.append(entrada)
                contador_id += 1
                contador_posicion += 1
                estado['entrada_actual'] = entrada
                estado['id_declaracion'] = tok.value
                estado['tipo_pendiente'] = None
            else:
                estado['id_declaracion'] = tok.value
                estado['entrada_actual'] = _buscar_simbolo(tok.value)
                estado['tipo_pendiente'] = None
                estado['esperando_valor'] = False

        elif tok.type == 'ASIGNACION':
            if estado['id_declaracion'] is not None:
                estado['esperando_valor'] = True
            else:
                reiniciar_declaracion()

        elif tok.type in ('NUMERO', 'CADENA', 'TRUE', 'FALSE'):
            if estado['esperando_valor'] and estado['entrada_actual'] is not None:
                estado['entrada_actual']['valor'] = tok.value
                reiniciar_declaracion()
            else:
                reiniciar_declaracion()

        elif tok.type == 'PUNTO_COMA':
            reiniciar_declaracion()
        else:
            reiniciar_declaracion()

    return "\n".join(lineas_tokens)


def accion_tokens():
    """Botón Tokens: análisis léxico → panel Tokens."""
    codigo = cuadro_programa.get("1.0", tk.END)
    texto = _lexico_y_simbolos(codigo)
    _set_text(widget_tokens, texto)
    _set_text(widget_sintaxis, "")
    _mostrar_codigo_intermedio("")
    _mostrar_codigo_objeto("")


def accion_parsear():
    """Botón Parsear: léxico + sintaxis → panel Sintaxis."""
    global ultimo_arbol, ultimos_errores_sint

    codigo = cuadro_programa.get("1.0", tk.END)
    texto_tok = _lexico_y_simbolos(codigo)
    _set_text(widget_tokens, texto_tok)

    if lista_tokens_actual:
        parser = Parser(
            tokens=lista_tokens_actual,
            tabla_simbolos_existente=_tabla_simbolos_para_parser(),
        )
        arbol, errores_sint = parser.parsear()
        texto_arbol = arbol.imprimir() if arbol else "No se pudo construir el árbol."
    else:
        arbol = None
        errores_sint = []
        texto_arbol = "Programa\n  ├── inicio\n  └── fin"

    ultimo_arbol = arbol
    ultimos_errores_sint = list(errores_sint)

    if errores_sint:
        texto_arbol += "\n\n--- Errores sintácticos ---\n" + "\n".join(errores_sint)
    _set_text(widget_sintaxis, texto_arbol)


def accion_semantico():
    """Botón Semántico: muestra tabla de símbolos / chequeos."""
    accion_parsear()

    lineas = ["Tabla de símbolos", "─" * 40]
    if not tabla_simbolos_memoria:
        lineas.append("(vacía)")
    else:
        lineas.append(f"{'ID':<4} {'Nombre':<12} {'Tipo':<10} {'Valor':<12} {'Ámbito'}")
        for d in tabla_simbolos_memoria:
            lineas.append(
                f"{d['id_int']:<4} {d['nombre']:<12} {d['tipo']:<10} "
                f"{str(d['valor']):<12} {d.get('ambito', 'Global')}"
            )

    if lista_errores:
        lineas.append("")
        lineas.append("Errores léxicos / semánticos")
        lineas.append("─" * 40)
        for mensaje, linea, pos in lista_errores:
            lineas.append(f"L{linea}:{pos}  {mensaje}")
    elif not ultimos_errores_sint:
        lineas.append("")
        lineas.append("✓ Sin errores semánticos detectados.")

    # Semántico se muestra en Sintaxis (panel de análisis) manteniendo el layout.
    actual = widget_sintaxis.get("1.0", "end-1c")
    _set_text(widget_sintaxis, actual.rstrip() + "\n\n" + "\n".join(lineas))


def accion_ejemplo():
    _set_text(cuadro_programa, EJEMPLO, editable=True)
    _set_text(widget_tokens, "")
    _set_text(widget_sintaxis, "")
    _mostrar_codigo_intermedio("")
    _mostrar_codigo_objeto("")


def accion_limpiar():
    global ultimo_arbol, ultimos_errores_sint, ultimo_ci, lista_tokens_actual
    ultimo_arbol = None
    ultimos_errores_sint = []
    ultimo_ci = ""
    lista_tokens_actual = []
    lista_errores.clear()
    tabla_simbolos_memoria.clear()
    _set_text(cuadro_programa, "", editable=True)
    _set_text(widget_tokens, "")
    _set_text(widget_sintaxis, "")
    _mostrar_codigo_intermedio("")
    _mostrar_codigo_objeto("")


def generar_y_mostrar_ci():
    global ultimo_arbol, ultimos_errores_sint

    if ultimo_arbol is None and not tabla_simbolos_memoria:
        accion_parsear()

    if ultimos_errores_sint:
        _mostrar_codigo_intermedio(
            "No se puede generar CI mientras haya errores sintácticos.\n"
            "Corrige el programa y vuelve a Parsear."
        )
        _mostrar_codigo_objeto("")
        return

    texto = generar_codigo_intermedio(
        _tabla_para_codigo_intermedio(),
        ultimo_arbol,
    )
    _mostrar_codigo_intermedio(texto)


def generar_y_mostrar_co():
    global ultimo_ci

    if not ultimo_ci.strip() or ultimo_arbol is None:
        generar_y_mostrar_ci()

    if ultimos_errores_sint:
        _mostrar_codigo_objeto(
            "No se puede generar CO mientras haya errores sintácticos."
        )
        return

    _mostrar_codigo_objeto(ultimo_ci)


# ==========================================
# 3. VENTANA — interfaz Genesis (layout nuevo)
# ==========================================

BG = "#dce3ea"
ventana = tk.Tk()
ventana.title("Genesis")
ventana.geometry("1180x720")
ventana.configure(bg=BG)

raiz = tk.Frame(ventana, bg=BG, padx=10, pady=8)
raiz.pack(expand=True, fill="both")

# --- Cabecera: título + botones ---
cabecera = tk.Frame(raiz, bg=BG)
cabecera.pack(fill="x", pady=(0, 6))

tk.Label(
    cabecera, text="Genesis", bg=BG, font=("Arial", 18, "bold"),
).pack(side="left", padx=(4, 0))

frame_botones = tk.Frame(cabecera, bg=BG)
frame_botones.pack(side="right")

estilo_btn = {"font": ("Arial", 11), "width": 10, "relief": "raised", "bd": 1}
tk.Button(frame_botones, text="Tokens", command=accion_tokens, **estilo_btn).pack(
    side="left", padx=3,
)
tk.Button(frame_botones, text="Parsear", command=accion_parsear, **estilo_btn).pack(
    side="left", padx=3,
)
tk.Button(frame_botones, text="Semántico", command=accion_semantico, **estilo_btn).pack(
    side="left", padx=3,
)
tk.Button(
    frame_botones, text="Ejemplo", command=accion_ejemplo,
    bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), width=10, relief="raised", bd=1,
).pack(side="left", padx=3)
tk.Button(frame_botones, text="Limpiar", command=accion_limpiar, **estilo_btn).pack(
    side="left", padx=3,
)

# --- Fila superior: Programa | Tokens | Sintaxis ---
fila_sup = tk.Frame(raiz, bg=BG)
fila_sup.pack(expand=True, fill="both")
fila_sup.columnconfigure(0, weight=1, uniform="sup")
fila_sup.columnconfigure(1, weight=1, uniform="sup")
fila_sup.columnconfigure(2, weight=1, uniform="sup")
fila_sup.rowconfigure(1, weight=1)

tk.Label(fila_sup, text="Programa", bg=BG, font=("Arial", 11, "bold")).grid(
    row=0, column=0, sticky="w",
)
tk.Label(fila_sup, text="Tokens", bg=BG, font=("Arial", 11, "bold")).grid(
    row=0, column=1, sticky="w",
)
tk.Label(fila_sup, text="Sintaxis", bg=BG, font=("Arial", 11, "bold")).grid(
    row=0, column=2, sticky="w",
)

cuadro_programa = scrolledtext.ScrolledText(
    fila_sup, font=("Courier New", 11), wrap="none", height=14,
)
cuadro_programa.grid(row=1, column=0, sticky="nsew", padx=(0, 4), pady=(2, 6))

widget_tokens = scrolledtext.ScrolledText(
    fila_sup, font=("Courier New", 10), wrap="none", height=14, state="disabled",
)
widget_tokens.grid(row=1, column=1, sticky="nsew", padx=4, pady=(2, 6))

widget_sintaxis = scrolledtext.ScrolledText(
    fila_sup, font=("Courier New", 10), wrap="none", height=14, state="disabled",
)
widget_sintaxis.grid(row=1, column=2, sticky="nsew", padx=(4, 0), pady=(2, 6))

# --- Fila inferior: CI (izq) | CO (der, espacio bajo Sintaxis) ---
fila_inf = tk.Frame(raiz, bg=BG)
fila_inf.pack(expand=True, fill="both")
fila_inf.columnconfigure(0, weight=1, uniform="inf")
fila_inf.columnconfigure(1, weight=1, uniform="inf")
fila_inf.rowconfigure(1, weight=1)

btn_ci = tk.Button(
    fila_inf, text="CI", bg="#2196F3", fg="white",
    font=("Arial", 11, "bold"), width=6, command=generar_y_mostrar_ci,
)
btn_ci.grid(row=0, column=0, sticky="w", pady=(0, 2))

btn_co = tk.Button(
    fila_inf, text="CO", bg="#9C27B0", fg="white",
    font=("Arial", 11, "bold"), width=6, command=generar_y_mostrar_co,
)
btn_co.grid(row=0, column=1, sticky="w", pady=(0, 2))

widget_ci = scrolledtext.ScrolledText(
    fila_inf, font=("Courier New", 10), wrap="none", height=14, state="disabled",
)
widget_ci.grid(row=1, column=0, sticky="nsew", padx=(0, 4))

# Panel CO: tabla DIR / CONTENIDO / HEX (como el pizarrón)
frame_co = tk.Frame(fila_inf, bg=BG)
frame_co.grid(row=1, column=1, sticky="nsew", padx=(4, 0))
frame_co.rowconfigure(0, weight=1)
frame_co.columnconfigure(0, weight=1)

columnas_co = ("DIR", "CONTENIDO", "HEX")
tabla_objeto = ttk.Treeview(frame_co, columns=columnas_co, show="headings", height=12)
tabla_objeto.heading("DIR", text="DIR")
tabla_objeto.heading("CONTENIDO", text="CONTENIDO")
tabla_objeto.heading("HEX", text="HEX")
tabla_objeto.column("DIR", width=140, minwidth=100, anchor="w", stretch=False)
tabla_objeto.column("CONTENIDO", width=220, minwidth=120, anchor="w", stretch=True)
tabla_objeto.column("HEX", width=140, minwidth=100, anchor="w", stretch=False)

scroll_co_y = ttk.Scrollbar(frame_co, orient="vertical", command=tabla_objeto.yview)
scroll_co_x = ttk.Scrollbar(frame_co, orient="horizontal", command=tabla_objeto.xview)
tabla_objeto.configure(yscrollcommand=scroll_co_y.set, xscrollcommand=scroll_co_x.set)
tabla_objeto.grid(row=0, column=0, sticky="nsew")
scroll_co_y.grid(row=0, column=1, sticky="ns")
scroll_co_x.grid(row=1, column=0, sticky="ew")

if __name__ == "__main__":
    ventana.mainloop()
