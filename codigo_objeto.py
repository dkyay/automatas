"""Código Objeto (CO) del Lenguaje Genesis — codificación binaria 8086/MASM 16 bits.

A partir del código intermedio (.DATA / .CODE) produce una tabla:

    DIR                 CONTENIDO                         HEX
    ─── DATOS ───
    ─── CÓDIGO ───

según las modalidades de direccionamiento Intel (opcode + ModR/M +
desplazamientos / inmediatos en Little Endian).
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Tablas Intel 8086
# ---------------------------------------------------------------------------

REG16 = {"AX": 0, "CX": 1, "DX": 2, "BX": 3, "SP": 4, "BP": 5, "SI": 6, "DI": 7}
REG8 = {"AL": 0, "CL": 1, "DL": 2, "BL": 3, "AH": 4, "CH": 5, "DH": 6, "BH": 7}

# Opcode base de saltos cortos (rel8).
SALTOS = {
    "JO": 0x70, "JNO": 0x71, "JB": 0x72, "JNAE": 0x72, "JAE": 0x73, "JNB": 0x73,
    "JE": 0x74, "JZ": 0x74, "JNE": 0x75, "JNZ": 0x75, "JBE": 0x76, "JNA": 0x76,
    "JA": 0x77, "JNBE": 0x77, "JS": 0x78, "JNS": 0x79, "JP": 0x7A, "JPE": 0x7A,
    "JNP": 0x7B, "JPO": 0x7B, "JL": 0x7C, "JNGE": 0x7C, "JGE": 0x7D, "JNL": 0x7D,
    "JLE": 0x7E, "JNG": 0x7E, "JG": 0x7F, "JNLE": 0x7F,
}

# Instrucciones de 1 byte con operando implícito.
IMPLICITAS = {
    "CLC": 0xF8, "STC": 0xF9, "CLI": 0xFA, "STI": 0xFB, "CLD": 0xFC, "STD": 0xFD,
    "NOP": 0x90, "HLT": 0xF4, "CBW": 0x98, "CWD": 0x99, "WAIT": 0x9B,
    "PUSHF": 0x9C, "POPF": 0x9D, "SAHF": 0x9E, "LAHF": 0x9F,
    "RET": 0xC3, "RETF": 0xCB, "IRET": 0xCF,
}

# Grupo /digit para ALU con inmediato (81 /x, 80 /x, 83 /x).
ALU_DIGITO = {
    "ADD": 0, "OR": 1, "ADC": 2, "SBB": 3,
    "AND": 4, "SUB": 5, "XOR": 6, "CMP": 7,
}

# Opcode r16 ← r/m16  (03, 0B, 13, …)
ALU_R_RM16 = {
    "ADD": 0x03, "OR": 0x0B, "ADC": 0x13, "SBB": 0x1B,
    "AND": 0x23, "SUB": 0x2B, "XOR": 0x33, "CMP": 0x3B,
}

# Opcode AL/AX ← imm (04/05, …)
ALU_AX_IMM16 = {
    "ADD": 0x05, "OR": 0x0D, "ADC": 0x15, "SBB": 0x1D,
    "AND": 0x25, "SUB": 0x2D, "XOR": 0x35, "CMP": 0x3D,
}

ALU_AL_IMM8 = {
    "ADD": 0x04, "OR": 0x0C, "ADC": 0x14, "SBB": 0x1C,
    "AND": 0x24, "SUB": 0x2C, "XOR": 0x34, "CMP": 0x3C,
}


# ---------------------------------------------------------------------------
# Utilidades de formato
# ---------------------------------------------------------------------------

def _bytes_a_binario(bs: List[int]) -> str:
    return " ".join(f"{b:08b}"[:4] + " " + f"{b:08b}"[4:] for b in bs)


def _bytes_a_hex(bs: List[int]) -> str:
    return " ".join(f"{b:02X}" for b in bs)


def _dir_binaria(addr: int) -> str:
    """Dirección de 16 bits como 4 grupos de 4 bits."""
    bits = f"{addr & 0xFFFF:016b}"
    return " ".join(bits[i:i + 4] for i in range(0, 16, 4))


def _parse_imm(texto: str) -> Optional[int]:
    t = texto.strip().upper().replace("H", "")
    if not t:
        return None
    try:
        if texto.strip().upper().endswith("H") or any(c in t for c in "ABCDEF"):
            return int(t, 16) & 0xFFFF
        return int(t, 10) & 0xFFFF
    except ValueError:
        return None


def _imm16_le(valor: int) -> List[int]:
    v = valor & 0xFFFF
    return [v & 0xFF, (v >> 8) & 0xFF]


def _imm8(valor: int) -> List[int]:
    return [valor & 0xFF]


def _modrm(mod: int, reg: int, rm: int) -> int:
    return ((mod & 3) << 6) | ((reg & 7) << 3) | (rm & 7)


def _es_registro(op: str) -> bool:
    return op.upper() in REG16 or op.upper() in REG8


def _ancho_reg(op: str) -> int:
    u = op.upper()
    if u in REG16:
        return 16
    if u in REG8:
        return 8
    return 0


# ---------------------------------------------------------------------------
# Parser ligero del CI
# ---------------------------------------------------------------------------

_RE_DATO = re.compile(
    r"^([A-Za-z_][\w]*)\s+(DW|DB|DD)\s+(.+)$",
    re.IGNORECASE,
)
_RE_ETIQUETA = re.compile(r"^([A-Za-z_][\w]*)\s*:\s*$")
_RE_INS = re.compile(
    r"^([A-Za-z]+)\s*(.*?)(?:\s*;.*)?$"
)


def _limpiar_operando(op: str) -> str:
    return op.strip().strip("[]")


def _partir_operandos(resto: str) -> List[str]:
    if not resto.strip():
        return []
    # Quitar comentario residual.
    resto = resto.split(";")[0].strip()
    partes = [p.strip() for p in resto.split(",")]
    return [p for p in partes if p]


class GeneradorObjeto:
    def __init__(self):
        self.simbolos: Dict[str, int] = {}  # nombre → offset en DATOS
        self.tamanos: Dict[str, int] = {}   # nombre → tamaño en bytes
        self.filas_datos: List[Tuple[int, str, str]] = []
        self.filas_codigo: List[Tuple[int, List[int]]] = []
        self.etiquetas: Dict[str, int] = {}
        self._pendientes_salto: List[Tuple[int, int, str]] = []  # (idx_fila, addr_byte_rel, etiqueta)
        self.ip = 0

    # ---- .DATA ----
    def _agregar_dato(self, nombre: str, directiva: str, valor: str) -> None:
        directiva = directiva.upper()
        tam = {"DB": 1, "DW": 2, "DD": 4}.get(directiva, 2)
        offset = sum(self.tamanos.values())
        self.simbolos[nombre] = offset
        self.tamanos[nombre] = tam

        # Contenido: reservado (?) → vacío; número → little endian.
        valor = valor.strip().strip('"')
        if valor == "?" or valor.startswith('"') or "," in valor:
            contenido_bin = ""
            contenido_hex = ""
            etiqueta = f"{nombre} {directiva} {valor}"[:40]
            self.filas_datos.append((offset, etiqueta, contenido_hex))
            # Solo marcamos la dirección; no emitimos bytes de código.
            return

        imm = _parse_imm(valor)
        if imm is None:
            self.filas_datos.append((offset, f"{nombre} {directiva}", ""))
            return
        if tam == 1:
            bs = _imm8(imm)
        elif tam == 2:
            bs = _imm16_le(imm)
        else:
            bs = _imm16_le(imm) + [0, 0]
        self.filas_datos.append((offset, _bytes_a_binario(bs), _bytes_a_hex(bs)))

    # ---- Emisión de bytes de código ----
    def _emitir(self, bs: List[int]) -> None:
        if not bs:
            return
        self.filas_codigo.append((self.ip, list(bs)))
        self.ip += len(bs)

    def _offset_simbolo(self, nombre: str) -> int:
        return self.simbolos.get(nombre, 0)

    def _es_memoria(self, op: str) -> bool:
        u = op.upper()
        if u in REG16 or u in REG8:
            return False
        if _parse_imm(op) is not None and not any(c.isalpha() for c in op.replace("H", "").replace("h", "")):
            # puro inmediato numérico
            return False
        # identificador / [ident] → memoria (variable del .DATA)
        return True

    def _codificar_mem_directa(self, reg_field: int) -> List[int]:
        """ModR/M + disp16 para memoria directa (mod=00, r/m=110)."""
        return [_modrm(0b00, reg_field, 0b110)]

    # ---- Codificación de instrucciones ----
    def _codificar(self, mnem: str, ops: List[str]) -> Optional[List[int]]:
        m = mnem.upper()

        if m in IMPLICITAS and not ops:
            return [IMPLICITAS[m]]

        # INC / DEC registro 16 bits (un byte): 40+rw / 48+rw
        if m in ("INC", "DEC") and len(ops) == 1 and ops[0].upper() in REG16:
            base = 0x40 if m == "INC" else 0x48
            return [base + REG16[ops[0].upper()]]

        # PUSH / POP registro 16 bits
        if m == "PUSH" and len(ops) == 1 and ops[0].upper() in REG16:
            return [0x50 + REG16[ops[0].upper()]]
        if m == "POP" and len(ops) == 1 and ops[0].upper() in REG16:
            return [0x58 + REG16[ops[0].upper()]]

        # INT imm8
        if m == "INT" and len(ops) == 1:
            n = _parse_imm(ops[0])
            if n is not None:
                return [0xCD, n & 0xFF]

        # JMP / Jcc etiqueta  (rel8; se parchea después)
        if m == "JMP" and len(ops) == 1 and _parse_imm(ops[0]) is None:
            # Emitimos EB 00 y anotamos parche
            self._pendientes_salto.append((len(self.filas_codigo), self.ip + 1, ops[0]))
            return [0xEB, 0x00]
        if m in SALTOS and len(ops) == 1:
            self._pendientes_salto.append((len(self.filas_codigo), self.ip + 1, ops[0]))
            return [SALTOS[m], 0x00]

        # LEA r16, mem
        if m == "LEA" and len(ops) == 2 and ops[0].upper() in REG16:
            dest = REG16[ops[0].upper()]
            nombre = _limpiar_operando(ops[1])
            off = self._offset_simbolo(nombre)
            return [0x8D, _modrm(0b00, dest, 0b110)] + _imm16_le(off)

        # MOV
        if m == "MOV" and len(ops) == 2:
            return self._codificar_mov(ops[0], ops[1])

        # ALU: ADD/SUB/CMP/AND/OR/XOR/ADC/SBB
        if m in ALU_DIGITO and len(ops) == 2:
            return self._codificar_alu(m, ops[0], ops[1])

        # MUL / DIV / IDIV r/m16  → F7 /4, /6, /7
        if m in ("MUL", "DIV", "IDIV") and len(ops) == 1:
            digito = {"MUL": 4, "DIV": 6, "IDIV": 7}[m]
            op = ops[0]
            if op.upper() in REG16:
                return [0xF7, _modrm(0b11, digito, REG16[op.upper()])]
            nombre = _limpiar_operando(op)
            off = self._offset_simbolo(nombre)
            return [0xF7, _modrm(0b00, digito, 0b110)] + _imm16_le(off)

        return None

    def _codificar_mov(self, dest: str, src: str) -> Optional[List[int]]:
        du, su = dest.upper(), src.upper()

        # MOV r16, imm16  → B8+rw iw
        if du in REG16:
            imm = _parse_imm(src)
            if imm is not None:
                return [0xB8 + REG16[du]] + _imm16_le(imm)
            # MOV r8, imm8 → B0+rb ib
        if du in REG8:
            imm = _parse_imm(src)
            if imm is not None:
                return [0xB0 + REG8[du]] + _imm8(imm)

        # MOV AX, moffs16 → A1
        if du == "AX" and self._es_memoria(src):
            off = self._offset_simbolo(_limpiar_operando(src))
            return [0xA1] + _imm16_le(off)
        # MOV AL, moffs8 → A0
        if du == "AL" and self._es_memoria(src):
            off = self._offset_simbolo(_limpiar_operando(src))
            return [0xA0] + _imm16_le(off)
        # MOV moffs16, AX → A3
        if su == "AX" and self._es_memoria(dest):
            off = self._offset_simbolo(_limpiar_operando(dest))
            return [0xA3] + _imm16_le(off)
        # MOV moffs8, AL → A2
        if su == "AL" and self._es_memoria(dest):
            off = self._offset_simbolo(_limpiar_operando(dest))
            return [0xA2] + _imm16_le(off)

        # MOV r/m16, imm16 → C7 /0
        if self._es_memoria(dest):
            imm = _parse_imm(src)
            if imm is not None:
                off = self._offset_simbolo(_limpiar_operando(dest))
                return [0xC7, _modrm(0b00, 0, 0b110)] + _imm16_le(off) + _imm16_le(imm)
            # MOV mem, r16 → 89 /r
            if su in REG16:
                off = self._offset_simbolo(_limpiar_operando(dest))
                return [0x89, _modrm(0b00, REG16[su], 0b110)] + _imm16_le(off)
            # MOV mem, r8 → 88 /r
            if su in REG8:
                off = self._offset_simbolo(_limpiar_operando(dest))
                return [0x88, _modrm(0b00, REG8[su], 0b110)] + _imm16_le(off)

        # MOV r16, r/m16 → 8B /r
        if du in REG16 and self._es_memoria(src):
            off = self._offset_simbolo(_limpiar_operando(src))
            return [0x8B, _modrm(0b00, REG16[du], 0b110)] + _imm16_le(off)
        # MOV r8, r/m8 → 8A /r
        if du in REG8 and self._es_memoria(src):
            off = self._offset_simbolo(_limpiar_operando(src))
            return [0x8A, _modrm(0b00, REG8[du], 0b110)] + _imm16_le(off)

        # MOV r16, r16 → 89 /r  (destino en r/m, fuente en reg)  como en la diapositiva MOV AX,CX = 89 C8
        if du in REG16 and su in REG16:
            return [0x89, _modrm(0b11, REG16[su], REG16[du])]
        # MOV r8, r8 → 88 /r
        if du in REG8 and su in REG8:
            return [0x88, _modrm(0b11, REG8[su], REG8[du])]

        # MOV r/m8, imm8 → C6 /0 (mem)
        if du in REG8:
            pass  # ya cubierto con B0+rb
        return None

    def _codificar_alu(self, mnem: str, dest: str, src: str) -> Optional[List[int]]:
        du, su = dest.upper(), src.upper()
        digito = ALU_DIGITO[mnem]

        # ALU AX, imm16 → opcode optimizado
        if du == "AX":
            imm = _parse_imm(src)
            if imm is not None:
                return [ALU_AX_IMM16[mnem]] + _imm16_le(imm)
        if du == "AL":
            imm = _parse_imm(src)
            if imm is not None:
                return [ALU_AL_IMM8[mnem]] + _imm8(imm)

        # ALU r16, imm16 → 81 /dig iw
        if du in REG16:
            imm = _parse_imm(src)
            if imm is not None:
                return [0x81, _modrm(0b11, digito, REG16[du])] + _imm16_le(imm)
            # ALU r16, r/m16
            if self._es_memoria(src):
                off = self._offset_simbolo(_limpiar_operando(src))
                return [ALU_R_RM16[mnem], _modrm(0b00, REG16[du], 0b110)] + _imm16_le(off)
            if su in REG16:
                # ALU r16, r16  (destino r/m, fuente reg) usando forma 01/09/…  → opcode = ALU_R_RM16 - 2
                return [ALU_R_RM16[mnem] - 2, _modrm(0b11, REG16[su], REG16[du])]

        # ALU r8, imm8 → 80 /dig ib
        if du in REG8:
            imm = _parse_imm(src)
            if imm is not None:
                return [0x80, _modrm(0b11, digito, REG8[du])] + _imm8(imm)

        # ALU mem, imm → 81 /dig (DW) o 80 (DB)
        if self._es_memoria(dest):
            imm = _parse_imm(src)
            off = self._offset_simbolo(_limpiar_operando(dest))
            if imm is not None:
                return [0x81, _modrm(0b00, digito, 0b110)] + _imm16_le(off) + _imm16_le(imm)
            if su in REG16:
                return [ALU_R_RM16[mnem] - 2, _modrm(0b00, REG16[su], 0b110)] + _imm16_le(off)

        return None

    def _parchear_saltos(self) -> None:
        for idx_fila, addr_rel, etiqueta in self._pendientes_salto:
            destino = self.etiquetas.get(etiqueta)
            if destino is None:
                # Buscar sin distinguir mayúsculas
                for k, v in self.etiquetas.items():
                    if k.upper() == etiqueta.upper():
                        destino = v
                        break
            if destino is None:
                continue
            # rel8 = destino - (IP después de la instrucción) = destino - (addr_rel + 1)
            rel = (destino - (addr_rel + 1)) & 0xFF
            addr_ins, bs = self.filas_codigo[idx_fila]
            bs = list(bs)
            # El byte de desplazamiento es el segundo (índice 1)
            if len(bs) >= 2:
                bs[1] = rel
                self.filas_codigo[idx_fila] = (addr_ins, bs)

    def generar_desde_ci(self, texto_ci: str) -> str:
        """Parsea el texto CI y devuelve la tabla CO formateada."""
        self.__init__()
        seccion = None  # 'data' | 'code'

        for cruda in texto_ci.splitlines():
            linea = cruda.strip()
            if not linea or linea.startswith(";"):
                continue
            up = linea.upper()

            if up.startswith(".DATA"):
                seccion = "data"
                continue
            if up.startswith(".CODE"):
                seccion = "code"
                continue
            if up.startswith(".MODEL") or up.startswith(".STACK") or up.startswith(".486"):
                continue
            if up.startswith("TITLE") or up.startswith("MAIN ") or up == "END":
                continue
            if up in (".STARTUP", ".EXIT") or up.endswith("ENDP"):
                continue

            # Etiqueta
            m_eti = _RE_ETIQUETA.match(linea)
            if m_eti:
                self.etiquetas[m_eti.group(1)] = self.ip
                continue
            # Etiqueta pegada a instrucción: L1: MOV AX, 0
            if ":" in linea and not linea.upper().startswith("MAIN"):
                partes = linea.split(":", 1)
                nombre_eti = partes[0].strip()
                if nombre_eti and re.match(r"^[A-Za-z_][\w]*$", nombre_eti):
                    self.etiquetas[nombre_eti] = self.ip
                    linea = partes[1].strip()
                    if not linea:
                        continue

            if seccion == "data":
                m = _RE_DATO.match(linea)
                if m:
                    self._agregar_dato(m.group(1), m.group(2), m.group(3))
                continue

            if seccion == "code":
                m = _RE_INS.match(linea)
                if not m:
                    continue
                mnem = m.group(1)
                ops = _partir_operandos(m.group(2) or "")
                # Registrar etiqueta si el mnemónico parece etiqueta suelta (ya cubierto)
                bs = self._codificar(mnem, ops)
                if bs is not None:
                    self._emitir(bs)
                else:
                    # Instrucción no reconocida: fila de comentario
                    self.filas_codigo.append((self.ip, []))
                    # No avanzamos IP; guardamos marcador textual vía lista auxiliar
                    # Mejor: emitir NOP comentado — omitimos silenciosamente no reconocidas.
                    self.filas_codigo.pop()

        self._parchear_saltos()
        return self._formatear()

    def _formatear(self) -> str:
        col_dir = 19
        col_cont = 42
        lineas = []
        encabezado = f"{'DIR':<{col_dir}} {'CONTENIDO':<{col_cont}} HEX"
        lineas.append(encabezado)
        lineas.append("─" * len(encabezado))
        lineas.append("DATOS")
        if not self.filas_datos:
            lineas.append(f"{_dir_binaria(0):<{col_dir}} {'':<{col_cont}}")
        else:
            for offset, contenido, hex_txt in self.filas_datos:
                # Si contenido es etiqueta textual (variable), mostrar vacío en CONTENIDO binario
                if contenido and not contenido[0].isdigit():
                    # Variable reservada: DIR + nombre en CONTENIDO, HEX vacío
                    lineas.append(
                        f"{_dir_binaria(offset):<{col_dir}} {contenido:<{col_cont}} {hex_txt}"
                    )
                else:
                    lineas.append(
                        f"{_dir_binaria(offset):<{col_dir}} {contenido:<{col_cont}} {hex_txt}"
                    )

        lineas.append("")
        lineas.append("CÓDIGO")
        if not self.filas_codigo:
            lineas.append("(sin instrucciones)")
        else:
            for addr, bs in self.filas_codigo:
                if not bs:
                    continue
                lineas.append(
                    f"{_dir_binaria(addr):<{col_dir}} "
                    f"{_bytes_a_binario(bs):<{col_cont}} "
                    f"{_bytes_a_hex(bs)}"
                )
        return "\n".join(lineas)


def generar_codigo_objeto(texto_ci: str) -> str:
    """API pública: CI (texto) → tabla CO (texto)."""
    if not texto_ci or not texto_ci.strip():
        return "No hay código intermedio. Genera primero el CI."
    if "No se puede generar" in texto_ci:
        return texto_ci
    return GeneradorObjeto().generar_desde_ci(texto_ci)
