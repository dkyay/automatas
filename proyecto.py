import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import ply.lex as lex
from codigo_intermedio import generar_codigo_intermedio
from parser import Parser

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


# Operadores compuestos antes de los de un carácter.
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
# 2. LÓGICA DE LA INTERFAZ GRÁFICA
# ==========================================

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
    """Diccionario de solo lectura para el parser (primera declaración por nombre)."""
    vista = {}
    for entrada in tabla_simbolos_memoria:
        nombre = entrada['nombre']
        if nombre not in vista:
            vista[nombre] = entrada
    return vista


def _tabla_para_codigo_intermedio():
    """Diccionario {nombre: tipo} en orden de declaración."""
    vista = {}
    for entrada in tabla_simbolos_memoria:
        nombre = entrada['nombre']
        if nombre not in vista:
            vista[nombre] = entrada['tipo']
    return vista


def _mostrar_codigo_intermedio(texto):
    widget_codigo.config(state="normal")
    widget_codigo.delete("1.0", "end")
    widget_codigo.insert("end", texto)
    widget_codigo.config(state="disabled")


def ejecutar_analisis():
    try:
        _ejecutar_analisis_interno()
    except Exception as exc:
        widget_errores_sint.config(state="normal")
        widget_errores_sint.delete("1.0", "end")
        widget_errores_sint.insert(
            "end",
            f"Error interno del analizador:\n{exc}\n",
            "error",
        )
        widget_errores_sint.config(state="disabled")


def _ejecutar_analisis_interno():
    lista_errores.clear()
    tabla_simbolos_memoria.clear()
    lexer.lineno = 1

    for item in tabla_lexemas.get_children():
        tabla_lexemas.delete(item)
    for item in tabla_errores.get_children():
        tabla_errores.delete(item)
    for item in tabla_simbolos.get_children():
        tabla_simbolos.delete(item)
    _mostrar_codigo_intermedio("")

    codigo_fuente = cuadro_texto.get("1.0", tk.END)
    lexer.input(codigo_fuente)

    lista_tokens = []

    contador_id = 1
    contador_posicion = 1
    estado = _reiniciar_estado_simbolos()
    profundidad_llaves = 0
    nombres_declarados = {}

    def reiniciar_declaracion():
        estado['tipo_pendiente'] = None
        estado['id_declaracion'] = None
        estado['entrada_actual'] = None
        estado['esperando_valor'] = False

    while True:
        tok = lexer.token()
        if not tok:
            break

        lista_tokens.append(tok)
        tabla_lexemas.insert("", tk.END, values=(tok.value, tok.type, tok.lineno))

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
                        f"Identificador duplicado: '{tok.value}' ya declarado (línea {nombres_declarados[tok.value]})",
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

    for datos in tabla_simbolos_memoria:
        tabla_simbolos.insert("", tk.END, values=(
            datos['id_int'],
            datos['nombre'],
            datos['tipo'],
            datos['valor'],
            datos['posicion'],
            datos.get('ambito', 'Global'),
        ))

    if len(lista_errores) == 0:
        tabla_errores.insert("", tk.END, values=("Ninguno", "-", "Análisis Limpio"))
    else:
        for error in lista_errores:
            tabla_errores.insert("", tk.END, values=(error[0], error[1], error[2]))

    arbol = None
    if lista_tokens:
        parser = Parser(
            tokens=lista_tokens,
            tabla_simbolos_existente=_tabla_simbolos_para_parser(),
        )
        arbol, errores_sint = parser.parsear()
        texto_arbol = arbol.imprimir() if arbol else "No se pudo construir el árbol."
    else:
        errores_sint = []
        texto_arbol = "Programa\n  ├── inicio\n  └── fin"

    widget_arbol.config(state="normal")
    widget_arbol.delete("1.0", "end")
    widget_arbol.insert("end", texto_arbol)
    widget_arbol.config(state="disabled")

    widget_errores_sint.config(state="normal")
    widget_errores_sint.delete("1.0", "end")
    if errores_sint:
        for err in errores_sint:
            widget_errores_sint.insert("end", err + "\n", "error")
    else:
        widget_errores_sint.insert("end", "✓ Sin errores sintácticos.")
    widget_errores_sint.config(state="disabled")

    _mostrar_codigo_intermedio(
        generar_codigo_intermedio(_tabla_para_codigo_intermedio(), arbol)
    )


# ==========================================
# 3. VENTANA (TKINTER)
# ==========================================

ventana = tk.Tk()
ventana.title("Lenguaje Genesis — Análisis y Código Intermedio")
ventana.geometry("750x820")

contenedor = tk.Frame(ventana, padx=20, pady=20)
contenedor.pack(expand=True, fill="both")

titulo = tk.Label(contenedor, text="Analizador Léxico, Sintáctico y Código Intermedio — Genesis")
titulo.config(font=("Arial", 16, "bold"))
titulo.pack(side="top", anchor="n", pady=(0, 20))

lbl_editor = tk.Label(contenedor, text="1. Ingresa el código fuente:", font=("Arial", 12, "bold"))
lbl_editor.pack(anchor="w")

cuadro_texto = tk.Text(contenedor, height=10, width=80, font=("Courier", 11))
cuadro_texto.pack(pady=5)

btn_analizar = tk.Button(
    contenedor,
    text="Analizar",
    bg="#4CAF50",
    fg="white",
    font=("Arial", 12, "bold"),
    command=ejecutar_analisis,
)
btn_analizar.pack(pady=15)

lbl_resultados = tk.Label(contenedor, text="2. Resultados del Análisis:", font=("Arial", 12, "bold"))
lbl_resultados.pack(anchor="w", pady=(10, 5))

pestanas = ttk.Notebook(contenedor)
pestanas.pack(expand=True, fill="both")

frame_lexemas = ttk.Frame(pestanas)
pestanas.add(frame_lexemas, text="Zona de Lexemas")
columnas_lex = ("Lexema", "Componente Léxico (Token)", "Línea")
tabla_lexemas = ttk.Treeview(frame_lexemas, columns=columnas_lex, show="headings")
for col in columnas_lex:
    tabla_lexemas.heading(col, text=col)
tabla_lexemas.pack(expand=True, fill="both")

frame_errores = ttk.Frame(pestanas)
pestanas.add(frame_errores, text="Zona de Errores")
columnas_err = ("Error Encontrado", "Línea", "Posición de Memoria")
tabla_errores = ttk.Treeview(frame_errores, columns=columnas_err, show="headings")
for col in columnas_err:
    tabla_errores.heading(col, text=col)
tabla_errores.pack(expand=True, fill="both")

frame_simbolos = ttk.Frame(pestanas)
pestanas.add(frame_simbolos, text="Tabla de Símbolos")

columnas_sim = ("ID Interno", "Identificador", "Tipo", "Valor", "Posición", "Ámbito")
tabla_simbolos = ttk.Treeview(frame_simbolos, columns=columnas_sim, show="headings")

for col in columnas_sim:
    tabla_simbolos.heading(col, text=col)
    tabla_simbolos.column(col, width=130, anchor="center")

tabla_simbolos.pack(expand=True, fill="both")

frame_ast = ttk.Frame(pestanas)
pestanas.add(frame_ast, text="Árbol Sintáctico")
widget_arbol = scrolledtext.ScrolledText(
    frame_ast,
    height=12,
    font=("Courier New", 10),
    wrap="none",
    state="disabled",
)
widget_arbol.pack(expand=True, fill="both")

frame_err_sint = ttk.Frame(pestanas)
pestanas.add(frame_err_sint, text="Errores Sintácticos")
widget_errores_sint = scrolledtext.ScrolledText(
    frame_err_sint,
    height=8,
    font=("Courier New", 10),
    wrap="word",
    state="disabled",
)
widget_errores_sint.tag_config("error", foreground="red")
widget_errores_sint.pack(expand=True, fill="both")

frame_codigo = ttk.Frame(pestanas)
pestanas.add(frame_codigo, text="Código Intermedio")
widget_codigo = scrolledtext.ScrolledText(
    frame_codigo,
    height=12,
    font=("Courier New", 11),
    wrap="none",
    state="disabled",
)
widget_codigo.pack(expand=True, fill="both")

if __name__ == "__main__":
    ventana.mainloop()
