# automatas

Analizador léxico y sintáctico del **Lenguaje Genesis** (Python + PLY + Tkinter), con generación de **Código Intermedio (CI)** y **Código Objeto (CO)**.

## Archivos

- `proyecto.py` — interfaz Genesis (Tokens / Parsear / Semántico / Ejemplo / Limpiar + CI | CO)
- `parser.py` — analizador sintáctico LL(1)
- `ast_nodes.py` — nodos del AST
- `analisis_estructuras.py` — análisis de estructuras
- `codigo_intermedio.py` — generación de CI (.DATA / .CODE)
- `codigo_objeto.py` — codificación binaria 8086 → tabla DIR / CONTENIDO / HEX
- `tareas/` — entregables (PDF de codificación binaria y diapositivas CI/CO)

## Uso

```bash
pip install -r requirements.txt
python proyecto.py
```

Si clonaste otra rama y ves la interfaz vieja, cambia a esta:

```bash
git fetch origin
git checkout cursor/tareas-entregables-c630
git pull
python proyecto.py
```
