# automatas

Analizador léxico y sintáctico del **Lenguaje Genesis** (Python + PLY + Tkinter).

## Archivos

- `proyecto.py` — lexer PLY e interfaz gráfica
- `parser.py` — analizador sintáctico LL(1)
- `ast_nodes.py` — nodos del AST
- `analisis_estructuras.py` — análisis de estructuras
- `codigo_intermedio.py` — código intermedio a partir de la tabla de símbolos

## Código intermedio

Tras el análisis, la pestaña **Código Intermedio** traduce el programa a representación intermedia `.DATA` / `.CODE`.

Datos:

- `int` → `nombre DW ?`
- `boolean` → `nombre DB ?`
- `string` → `nombre DB ?`
- una cadena de `println` → `MSGn DB "texto $",0AH,0DH`
- una división → `COC DB 0` y `RESI DB 0`

Operadores en `.CODE`:

- `@` suma → `ADD`
- `#` resta → `SUB`
- `&` multiplicación → `MUL` (resultado en EAX)
- `|` división → `DIV` (cociente en `AL`/`COC`, residuo en `AH`/`RESI`)
- `println` de una cadena → función `09H` de la interrupción `21H`
- `println` de un número → función `02H` de la interrupción `21H`

Si no hay programa ni variables, el texto es `No hay variables para generar.`

## Uso

```bash
pip install -r requirements.txt
python proyecto.py
```
