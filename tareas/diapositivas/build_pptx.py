#!/usr/bin/env python3
"""Genera diapositivas CI/CO en PPTX (diseño azul Cormorant/Inter)."""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT = ROOT / "Genesis_CI_CO.pptx"

# 16:9
W, H = Inches(13.333), Inches(7.5)

BLUE = RGBColor(0x2E, 0x6E, 0xED)
INK = RGBColor(0x14, 0x1F, 0x38)
MUTED = RGBColor(0x7A, 0x84, 0x94)
PANEL = RGBColor(0xF0, 0xF3, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
DARK = RGBColor(0x0B, 0x12, 0x20)
CODE_BG = RGBColor(0x0F, 0x17, 0x2A)
CODE_FG = RGBColor(0xE2, 0xE8, 0xF0)
LINE = RGBColor(0xE2, 0xE7, 0xF0)


def _set_run_font(run, size=18, bold=False, color=INK, name="Calibri"):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = name
    # Try serif for titles via eastAsia/ascii
    rPr = run._r.get_or_add_rPr()
    for tag in ("latin", "ea", "cs"):
        el = rPr.find(qn(f"a:{tag}"))
        if el is None:
            el = rPr.makeelement(qn(f"a:{tag}"), {})
            rPr.append(el)
        el.set("typeface", name)


def add_bar(slide, x=Inches(0.7), y=Inches(0.55)):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, Inches(0.75), Pt(5))
    shape.fill.solid()
    shape.fill.fore_color.rgb = BLUE
    shape.line.fill.background()
    return shape


def set_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_text(slide, left, top, width, height, text, size=18, bold=False, color=INK, name="Calibri", align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    _set_run_font(run, size=size, bold=bold, color=color, name=name)
    return box


def add_title(slide, text, dark=False):
    add_bar(slide)
    add_text(
        slide, Inches(0.7), Inches(0.75), Inches(12), Inches(0.9),
        text, size=36, bold=True, color=WHITE if dark else INK, name="Georgia",
    )


def add_eyebrow(slide, text, dark=False):
    add_text(
        slide, Inches(0.7), Inches(1.55), Inches(12), Inches(0.35),
        text.upper(), size=12, bold=True, color=RGBColor(0x94, 0xA3, 0xB8) if dark else MUTED, name="Calibri",
    )


def add_panel(slide, left, top, width, height, color=PANEL):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def add_accent_strip(slide, left, top, height, color=BLUE, width=Pt(4)):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def add_code_block(slide, left, top, width, height, lines):
    add_panel(slide, left, top, width, height, CODE_BG)
    box = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.35), height - Inches(0.25))
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        run = p.add_run()
        run.text = line
        _set_run_font(run, size=11, color=CODE_FG, name="Consolas")
        p.space_after = Pt(2)
    return box


def add_table(slide, left, top, width, rows, col_widths=None):
    n_rows = len(rows)
    n_cols = len(rows[0])
    table_shape = slide.shapes.add_table(n_rows, n_cols, left, top, width, Inches(0.38 * n_rows))
    table = table_shape.table
    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = w
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = table.cell(r, c)
            cell.text = str(val)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            for p in cell.text_frame.paragraphs:
                for run in p.runs:
                    if r == 0:
                        _set_run_font(run, size=11, bold=True, color=WHITE, name="Calibri")
                    else:
                        _set_run_font(run, size=12, color=INK, name="Consolas")
            # fill
            fill = cell.fill
            fill.solid()
            if r == 0:
                fill.fore_color.rgb = INK
            elif r % 2 == 0:
                fill.fore_color.rgb = PANEL
            else:
                fill.fore_color.rgb = WHITE
    return table_shape


def add_bullets(slide, left, top, width, items, size=18):
    box = slide.shapes.add_textbox(left, top, width, Inches(0.45 * len(items) + 0.2))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        # blue square via prefix
        run = p.add_run()
        run.text = "    " + item
        _set_run_font(run, size=size, color=INK, name="Calibri")
        p.space_after = Pt(10)
    # overlay blue squares
    for i in range(len(items)):
        sq = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            left, top + Inches(0.08) + Inches(0.42 * i),
            Pt(9), Pt(9),
        )
        sq.fill.solid()
        sq.fill.fore_color.rgb = BLUE
        sq.line.fill.background()
    return box


def add_chips(slide, left, top, labels):
    x = left
    for label in labels:
        # estimate width
        w = Inches(0.12 * len(label) + 0.35)
        chip = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, top, w, Inches(0.34))
        chip.fill.solid()
        chip.fill.fore_color.rgb = RGBColor(0xE8, 0xEE, 0xFC)
        chip.line.color.rgb = RGBColor(0xC9, 0xD7, 0xF8)
        tf = chip.text_frame
        tf.word_wrap = False
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = label
        _set_run_font(run, size=11, bold=True, color=BLUE, name="Calibri")
        x += w + Inches(0.12)


def blank(prs):
    layout = prs.slide_layouts[6]  # blank
    return prs.slides.add_slide(layout)


def build():
    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H

    # 1 Portada
    s = blank(prs)
    set_bg(s, DARK)
    add_bar(s)
    add_text(s, Inches(0.7), Inches(2.2), Inches(11), Inches(1.6),
             "Código Intermedio\ny Código Objeto", size=48, bold=True, color=WHITE, name="Georgia")
    add_text(s, Inches(0.7), Inches(4.0), Inches(11), Inches(0.4),
             "Generación por plantillas · Intel x86 16 bits (8086/MASM)", size=16, color=MUTED)
    add_text(s, Inches(0.7), Inches(4.7), Inches(11), Inches(0.4),
             "Beltrán Salazar Norberto Rafael", size=20, color=MUTED, name="Georgia")

    # 2 Plantillas
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "Generación de código por plantillas")
    add_eyebrow(s, "Diseño · Flujo de datos")
    add_bullets(s, Inches(0.7), Inches(2.0), Inches(12), [
        "Recorrido del arreglo de tokens / AST",
        "Mapeo de instrucciones (como int x) a bloques de Código Intermedio",
    ])
    add_text(s, Inches(0.7), Inches(3.1), Inches(12), Inches(0.4),
             "Estructura del Código Intermedio", size=20, bold=True, color=INK, name="Georgia")
    add_accent_strip(s, Inches(0.7), Inches(3.55), Inches(1.35))
    add_panel(s, Inches(0.7), Inches(3.55), Inches(4.2), Inches(1.35))
    add_text(s, Inches(0.95), Inches(3.7), Inches(3.8), Inches(1.1),
             "int x;\nint y;", size=16, color=INK, name="Consolas")
    add_accent_strip(s, Inches(0.7), Inches(5.15), Inches(1.1))
    add_panel(s, Inches(0.7), Inches(5.15), Inches(4.2), Inches(1.1))
    add_text(s, Inches(0.95), Inches(5.3), Inches(3.8), Inches(0.8),
             "x = (x + y);", size=16, color=INK, name="Consolas")
    add_table(s, Inches(5.3), Inches(3.55), Inches(7.2), [
        ["Nombre", "Op", "Arg"],
        ["x", "DW", "?"],
        ["y", "DW", "?"],
    ], [Inches(2.4), Inches(2.4), Inches(2.4)])
    add_table(s, Inches(5.3), Inches(5.0), Inches(7.2), [
        ["Nombre", "Op", "Arg"],
        ["", "MOV", "AX, x"],
        ["", "MOV", "BX, y"],
        ["", "ADD", "AX, BX"],
        ["", "MOV", "x, AX"],
    ], [Inches(2.4), Inches(2.4), Inches(2.4)])

    # 3 Generación CI
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "Generación de CI")
    add_eyebrow(s, "Plantilla para declaraciones")
    add_accent_strip(s, Inches(0.7), Inches(2.1), Inches(2.4))
    add_panel(s, Inches(0.7), Inches(2.1), Inches(5.5), Inches(2.4))
    add_text(s, Inches(1.0), Inches(2.25), Inches(5), Inches(0.4),
             "Plantilla", size=20, bold=True, color=INK, name="Georgia")
    add_text(s, Inches(1.0), Inches(2.8), Inches(5), Inches(1.4),
             "TIPODATO VAR;\n↓\nVAR  DW / DD / DB  ?", size=16, color=INK, name="Consolas")
    add_chips(s, Inches(0.7), Inches(4.8), ["int → DW", "bool → DB", "float → DD", "string → DB"])
    add_code_block(s, Inches(6.6), Inches(2.1), Inches(6.0), Inches(4.4), [
        "# codigo_intermedio.py",
        "DIRECTIVA = {",
        '    "int": "DW",',
        '    "bool": "DB",',
        '    "string": "DB",',
        '    "float": "DD",',
        "}",
        "",
        "def _armar(self):",
        "    for nombre, tipo in self.variables:",
        "        directiva = DIRECTIVA.get(tipo)",
        "        if directiva:",
        '            self._dato(nombre, directiva, "?")',
        "    # →  x       DW      ?",
    ])

    # 4 Captura CI
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "CI generado en la interfaz")
    add_eyebrow(s, "Ejemplo en Genesis")
    img_ci = ASSETS / "shot-ci.jpg"
    img_full = ASSETS / "shot-full-ui.jpg"
    if img_ci.exists():
        s.shapes.add_picture(str(img_ci), Inches(0.5), Inches(2.05), width=Inches(6.0))
    if img_full.exists():
        s.shapes.add_picture(str(img_full), Inches(6.7), Inches(2.05), width=Inches(6.1))
    add_text(s, Inches(0.5), Inches(6.85), Inches(6), Inches(0.3),
             "PANEL CI — .DATA / .CODE", size=10, bold=True, color=MUTED)
    add_text(s, Inches(6.7), Inches(6.85), Inches(6), Inches(0.3),
             "PROGRAMA → TOKENS → SINTAXIS → CI | CO", size=10, bold=True, color=MUTED)

    # 5 Dos pasadas
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "Generación de CO")
    add_eyebrow(s, "Arquitectura de dos pasadas")
    add_accent_strip(s, Inches(0.7), Inches(2.15), Inches(1.0))
    add_panel(s, Inches(0.7), Inches(2.15), Inches(11.8), Inches(1.0))
    add_text(s, Inches(1.0), Inches(2.4), Inches(11), Inches(0.5),
             "Arquitectura de dos pasadas: recorremos la tabla del CI dos veces.", size=18, color=INK)
    add_bullets(s, Inches(0.7), Inches(3.5), Inches(12), [
        "1ª pasada. Calcular tamaños y direcciones de las etiquetas.",
        "2ª pasada. Generar código binario final con los saltos y referencias.",
    ], size=20)
    add_chips(s, Inches(0.7), Inches(5.0), ["DIR · CONTENIDO · HEX", "8086 / MASM 16 bits", "Little Endian"])

    # 6 Pasada 1
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "Direcciones y etiquetas")
    add_eyebrow(s, "Generación de CO · Pasada 1")
    add_code_block(s, Inches(0.7), Inches(2.1), Inches(11.9), Inches(4.6), [
        "# Idea de la 1ª pasada — en Genesis: GeneradorObjeto",
        "for linea in tabla_ci:",
        "    if linea.nombre and not linea.op:          # etiqueta",
        "        etiquetas[linea.nombre] = dir_temp",
        "        continue",
        "    if linea.op in directivas_ignoradas:",
        "        continue",
        "",
        "    info = codificar_instruccion(linea, …, solo_tam=True)",
        "    instrucciones_filtradas.append({",
        '        "linea": linea, "dir": dir_temp, "bytes": info.bytes,',
        "    })",
        "    dir_temp += info.bytes",
    ])

    # 7 Pasada 2
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "Binario, hex e instrucción")
    add_eyebrow(s, "Generación de CO · Pasada 2")
    add_code_block(s, Inches(0.7), Inches(2.1), Inches(11.9), Inches(4.6), [
        "# 2ª pasada — emite DIR / CONTENIDO / HEX",
        "for item in instrucciones_filtradas:",
        "    info = codificar_instruccion(item.linea, …, solo_tam=False)",
        "    codigo_co.append({",
        '        "dir": formatear_binario(item.dir, 16),',
        '        "contenido": formatear_binario(info.bin),',
        '        "hex": bin_a_hex(info.bin),',
        '        "referencia": f"{item.linea.op} {item.linea.arg}",',
        "    })",
        "",
        "# En Genesis: generar_filas_objeto(texto_ci)",
        "# → filas (sección, dir, contenido, hex) para la GUI",
    ])

    # 8 MOV REG REG
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "Generación de MOV REG, REG")
    add_eyebrow(s, "Ejemplo de Código CO")
    add_code_block(s, Inches(0.7), Inches(2.1), Inches(6.4), Inches(4.5), [
        "# codigo_objeto.py",
        "if dest in REG16 and src in REG16:",
        "    opcode = 0b10001001   # 89h",
        "    modrm  = 0b11 << 6 | REG16[src] << 3 | REG16[dest]",
        "    return [opcode, modrm]",
        "",
        "# Ejemplo: MOV AX, CX",
        "#   dest=AX=000  src=CX=001",
        "#   ModR/M = 11 001 000 = C8",
        "#   → 89 C8",
    ])
    add_text(s, Inches(7.4), Inches(2.1), Inches(5.2), Inches(0.4),
             "REG_BITS (registros 16 bits)", size=18, bold=True, color=INK, name="Georgia")
    regs = [("AX", "000"), ("CX", "001"), ("DX", "010"), ("BX", "011"),
            ("SP", "100"), ("BP", "101"), ("SI", "110"), ("DI", "111")]
    for i, (name, bits) in enumerate(regs):
        col, row = i % 4, i // 4
        x = Inches(7.4) + Inches(1.35 * col)
        y = Inches(2.65) + Inches(1.05 * row)
        add_panel(s, x, y, Inches(1.25), Inches(0.9))
        add_text(s, x, y + Inches(0.15), Inches(1.25), Inches(0.35),
                 name, size=16, bold=True, color=INK, name="Consolas", align=PP_ALIGN.CENTER)
        add_text(s, x, y + Inches(0.48), Inches(1.25), Inches(0.3),
                 bits, size=12, color=MUTED, name="Consolas", align=PP_ALIGN.CENTER)
    add_chips(s, Inches(7.4), Inches(5.0), ["opcode 89h", "mod = 11 (reg-reg)", "MOV AX, CX → 89 C8"])

    # 9 Captura CO
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "Tabla CO en la interfaz")
    add_eyebrow(s, "Ejemplo en Genesis")
    img_co = ASSETS / "shot-co.jpg"
    if img_co.exists():
        s.shapes.add_picture(str(img_co), Inches(0.5), Inches(2.05), width=Inches(6.0))
    if img_full.exists():
        s.shapes.add_picture(str(img_full), Inches(6.7), Inches(2.05), width=Inches(6.1))
    add_text(s, Inches(0.5), Inches(6.85), Inches(6), Inches(0.3),
             "CO — DIR · CONTENIDO · HEX", size=10, bold=True, color=MUTED)
    add_text(s, Inches(6.7), Inches(6.85), Inches(6), Inches(0.3),
             "EJEMPLO: X=5, Y=3, RES=(X+Y)", size=10, bold=True, color=MUTED)

    # 10 Del programa al CO
    s = blank(prs)
    set_bg(s, WHITE)
    add_title(s, "Del programa al CO")
    add_eyebrow(s, "Del ejemplo Genesis")
    add_accent_strip(s, Inches(0.7), Inches(2.1), Inches(2.3))
    add_panel(s, Inches(0.7), Inches(2.1), Inches(5.3), Inches(2.3))
    add_text(s, Inches(0.95), Inches(2.25), Inches(4.9), Inches(2.0),
             "inicio\nint x; int y; int res;\nx = 5; y = 3;\nres = (x + y);\nprintln res;\nfin",
             size=14, color=INK, name="Consolas")
    add_table(s, Inches(0.7), Inches(4.6), Inches(5.3), [
        ["CI (.CODE)"],
        ["MOV x, 5"],
        ["MOV y, 3"],
        ["MOV AX, x"],
        ["ADD AX, y"],
        ["MOV res, AX"],
    ], [Inches(5.3)])
    add_table(s, Inches(6.4), Inches(2.1), Inches(6.2), [
        ["DIR", "HEX", "Ref"],
        ["0000", "C7 06 00 00 05 00", "MOV x, 5"],
        ["0006", "C7 06 02 00 03 00", "MOV y, 3"],
        ["000C", "A1 00 00", "MOV AX, x"],
        ["000F", "03 06 02 00", "ADD AX, y"],
        ["0013", "A3 04 00", "MOV res, AX"],
    ], [Inches(1.2), Inches(2.8), Inches(2.2)])

    # 11 Fin
    s = blank(prs)
    set_bg(s, DARK)
    add_bar(s)
    add_text(s, Inches(0.7), Inches(2.6), Inches(11), Inches(1.0),
             "Fin de la especificación", size=44, bold=True, color=WHITE, name="Georgia")
    add_text(s, Inches(0.7), Inches(3.8), Inches(11), Inches(0.4),
             "Código Intermedio · Código Objeto · Plantillas · 8086", size=16, color=MUTED)
    add_text(s, Inches(0.7), Inches(4.5), Inches(11), Inches(0.4),
             "Beltrán Salazar Norberto Rafael", size=20, color=MUTED, name="Georgia")

    prs.save(OUT)
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
