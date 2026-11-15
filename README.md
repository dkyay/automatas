# automatas

Analizador del **Lenguaje Genesis** (Python + PLY + Tkinter): léxico, sintáctico, código intermedio (CI) y código objeto (CO).

## Archivos

- `proyecto.py` — lexer PLY e interfaz gráfica (botones CI / CO)
- `parser.py` — analizador sintáctico LL(1)
- `ast_nodes.py` — nodos del AST
- `analisis_estructuras.py` — análisis de estructuras
- `codigo_intermedio.py` — generación de CI estilo MASM 8086 (`.DATA` / `.CODE`)
- `codigo_objeto.py` — codificación binaria x86 (tabla DIR / CONTENIDO / HEX)

## Uso

```bash
pip install -r requirements.txt
python proyecto.py
```

1. Escribe un programa Genesis y pulsa **Analizar**.
2. **CI** muestra el ensamblador intermedio.
3. **CO** (a la derecha del CI) muestra la tabla de código objeto con direcciones en binario, contenido y hexadecimal.
