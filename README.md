# automatas

Analizador léxico y sintáctico del **Lenguaje Genesis** (Python + PLY + Tkinter).

## Archivos

- `proyecto.py` — lexer PLY e interfaz gráfica
- `parser.py` — analizador sintáctico LL(1)
- `ast_nodes.py` — nodos del AST
- `analisis_estructuras.py` — análisis de estructuras
- `codigo_intermedio.py` — código intermedio a partir de la tabla de símbolos

## Código intermedio

Tras el análisis, la pestaña **Código Intermedio** muestra una directiva por variable:

- `int` → `nombre DW ?`
- `boolean` → `nombre DB ?`
- `string` → `nombre DB ?`

Si no hay variables, el texto es `No hay variables para generar.`

## Uso

```bash
pip install -r requirements.txt
python proyecto.py
```
