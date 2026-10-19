# automatas

Analizador léxico, sintáctico y generador de **código intermedio (CI)** del
**Lenguaje Genesis** (Python + PLY + Tkinter).

## Archivos

- `proyecto.py` — lexer PLY e interfaz gráfica (botones Analizar y CI)
- `parser.py` — analizador sintáctico LL(1)
- `ast_nodes.py` — nodos del AST
- `analisis_estructuras.py` — análisis de estructuras
- `codigo_intermedio.py` — traducción a ensamblador intermedio (.DATA / .CODE)

## Uso

```bash
pip install -r requirements.txt
python proyecto.py
```

1. Escribe un programa Genesis en el editor.
2. Pulsa **Analizar** para lexemas, símbolos, AST y errores.
3. Pulsa **CI** para generar el código intermedio y verlo en la pestaña **CI**.
