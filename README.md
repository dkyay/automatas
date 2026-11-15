# automatas — Genesis

Compilador del **Lenguaje Genesis** (Python + PLY + Tkinter): léxico, sintáctico, semántico, código intermedio (CI) y código objeto (CO).

## Interfaz

Layout principal (ventana `Genesis`):

```
[Genesis]          [Tokens] [Parsear] [Semántico] [Ejemplo] [Limpiar]
[ Programa ]       [ Tokens ]       [ Sintaxis ]
[ CI ]             [ CO ]
[ ensamblador ]    [ DIR | CONTENIDO | HEX ]
```

El panel **CO** ocupa el espacio a la derecha del CI (debajo de Sintaxis).

## Archivos

- `proyecto.py` — interfaz Genesis + lexer
- `parser.py` — analizador sintáctico LL(1)
- `ast_nodes.py` — nodos del AST
- `analisis_estructuras.py` — análisis de estructuras
- `codigo_intermedio.py` — CI estilo MASM 8086
- `codigo_objeto.py` — codificación binaria x86 (DIR / CONTENIDO / HEX)

## Uso

```bash
pip install -r requirements.txt
python proyecto.py
```

1. **Ejemplo** carga un programa de muestra.
2. **Tokens** / **Parsear** / **Semántico** llenan los paneles superiores.
3. **CI** genera el ensamblador intermedio.
4. **CO** genera la tabla de código objeto a la derecha.
