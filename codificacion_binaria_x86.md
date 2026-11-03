# Codificación Binaria x86 (Generación de Código)

**Alumno:** Beltran Salazar Norberto Rafael  
**No. control:** 23170707  
**Horario:** 1:00 – 2:00

---

## Objetivo

Comprender la estructura de bajo nivel de las instrucciones en lenguaje ensamblador Intel x86 de **16 bits (8086/MASM)** y su representación exacta en código máquina (binario/hexadecimal), simulando el proceso que realiza el backend de un compilador en la fase de **generación de código**.

**Base:** Gramática BNF del Lenguaje Genesis y generador de código intermedio (`codigo_intermedio.py`), que emite instrucciones 8086/MASM con registros de 16 bits (`AX`, `BX`, `DX`, etc.) para:

- asignaciones (`MOV`, `LEA`)
- operaciones aritméticas (`ADD`, `SUB`, `MUL`, `DIV`)
- comparaciones (`CMP`)
- saltos (`JMP`, `JE`, `JNE`, …)
- servicios DOS (`INT 21h`)
- manipulación de pila (`PUSH`, `POP`)

---

## Notas previas (formato Intel 8086)

| Concepto | Significado |
|---|---|
| **Opcode** | Byte(s) que identifican la operación |
| **ModR/M** | Byte opcional: `MOD` (2 bits) + `REG` (3 bits) + `R/M` (3 bits) |
| **Little Endian** | Los valores de 16 bits se almacenan con el byte menos significativo primero |
| **rel8** | Desplazamiento relativo de 1 byte (complemento a dos) respecto al siguiente IP |
| **moffs16** | Dirección de memoria directa de 16 bits (sin ModR/M en formas `A1`/`A3`) |

**Codificación de registros (campo REG / R/M):**

| Registro | Código |
|---|---|
| AX | 000 |
| CX | 001 |
| DX | 010 |
| BX | 011 |
| SP | 100 |
| BP | 101 |
| SI | 110 |
| DI | 111 |

---

## 1. MOV — carga de memoria al acumulador (asignación / lectura de variable)

- **Instrucción:** `MOV AX, [num]`
- **Uso en la gramática:** cargar el valor de una variable (`int`) al acumulador para evaluarla.
- **Código máquina (Hex):** `A1 00 00`
- **Binario:** `10100001 00000000 00000000`
- **Desglose:**
  - `A1`: opcode optimizado de Intel exclusivo para mover una **palabra de 16 bits** desde una dirección de memoria directa hacia el acumulador **AX**.
  - `00 00`: dirección de memoria (offset `0x0000`) en formato Little Endian.
  - **No requiere** byte ModR/M.

---

## 2. MOV — inmediato hacia el acumulador (asignación de literal)

- **Instrucción:** `MOV AX, 0x0005`
- **Uso en la gramática:** `MOV AX, <número>` al evaluar literales enteros.
- **Código máquina (Hex):** `B8 05 00`
- **Binario:** `10111000 00000101 00000000`
- **Desglose:**
  - `B8`: opcode `B8 + rw`, donde `rw = 000` selecciona **AX**. Los 5 bits altos (`10111`) indican “MOV inmediato → registro de 16 bits”.
  - `05 00`: valor inmediato `0x0005` en Little Endian (2 bytes, modo 16 bits).

---

## 3. MOV — inmediato de 8 bits hacia AH (preparar servicio DOS)

- **Instrucción:** `MOV AH, 09h`
- **Uso en la gramática:** seleccionar el servicio DOS 09h (imprimir cadena) antes de `INT 21h`.
- **Código máquina (Hex):** `B4 09`
- **Binario:** `10110100 00001001`
- **Desglose:**
  - `B4`: opcode `B0 + rb`. El código de registro de **AH** es `100`, por lo que `B0 + 4 = B4`.
  - `09`: inmediato de 8 bits (número de servicio DOS).

---

## 4. MOV — almacenar acumulador en memoria (asignación)

- **Instrucción:** `MOV [total], AX`
- **Uso en la gramática:** guardar el resultado de una expresión en una variable (`MOV destino, AX`).
- **Código máquina (Hex):** `A3 04 00` *(offset de ejemplo `0x0004` para `total`)*
- **Binario:** `10100011 00000100 00000000`
- **Desglose:**
  - `A3`: opcode optimizado para mover **AX** hacia una dirección de memoria directa (`moffs16`).
  - `04 00`: offset `0x0004` en Little Endian.
  - **No requiere** ModR/M.

---

## 5. LEA — carga de dirección efectiva

- **Instrucción:** `LEA DX, [total]`
- **Uso en la gramática:** obtener la dirección de un mensaje (`MSG`) o cadena para imprimir con el servicio 09h.
- **Código máquina (Hex):** `8D 16 04 00`
- **Binario:** `10001101 00010110 00000100 00000000`
- **Desglose:**
  - `8D`: opcode de **LEA** (Load Effective Address) hacia un registro de 16 bits.
  - `16` = `00 | 010 | 110` (ModR/M):
    - `MOD = 00` y `R/M = 110` → desplazamiento directo de 16 bits.
    - `REG = 010` → registro destino **DX**.
  - `04 00`: dirección de memoria (offset `0x0004`) en Little Endian.

---

## 6. ADD — suma de memoria al acumulador (`@`)

- **Instrucción:** `ADD AX, [num2]`
- **Uso en la gramática:** operador aritmético `@` (suma) del Lenguaje Genesis.
- **Código máquina (Hex):** `03 06 02 00`
- **Binario:** `00000011 00000110 00000010 00000000`
- **Desglose:**
  - `03`: opcode **ADD** registro ← r/m de 16 bits (`ADD r16, r/m16`).
  - `06` = `00 | 000 | 110` (ModR/M):
    - `MOD = 00` y `R/M = 110` → memoria directa de 16 bits.
    - `REG = 000` → destino **AX**.
  - `02 00`: dirección de memoria (offset `0x0002`) en Little Endian.

---

## 7. SUB — resta de memoria al acumulador (`#`)

- **Instrucción:** `SUB AX, [num2]`
- **Uso en la gramática:** operador aritmético `#` (resta).
- **Código máquina (Hex):** `2B 06 02 00`
- **Binario:** `00101011 00000110 00000010 00000000`
- **Desglose:**
  - `2B`: opcode **SUB** registro ← r/m de 16 bits (`SUB r16, r/m16`).
  - `06` = `00 | 000 | 110` (ModR/M): misma forma que en ADD; `REG = 000` selecciona **AX**.
  - `02 00`: offset `0x0002` en Little Endian.

---

## 8. CMP — comparación (condiciones `if` / `while` / `for`)

- **Instrucción:** `CMP AX, 0x0000`
- **Uso en la gramática:** tras evaluar una condición, se compara el acumulador (o se emite `CMP AX, <operando>`) antes del salto condicional.
- **Código máquina (Hex):** `3D 00 00`
- **Binario:** `00111101 00000000 00000000`
- **Desglose:**
  - `3D`: opcode optimizado **CMP AX, imm16** (compara el acumulador con un inmediato de 16 bits y actualiza las banderas `ZF`, `SF`, `CF`, `OF`).
  - `00 00`: inmediato `0` en Little Endian.
  - **No requiere** ModR/M.

**Variante con memoria** (cuando el operando derecho es variable):

- **Instrucción:** `CMP AX, [T1]`
- **Hex:** `3B 06 06 00` *(offset de ejemplo `0x0006`)*
- **Desglose:**
  - `3B`: opcode `CMP r16, r/m16`.
  - `06` = `00 | 000 | 110`: memoria directa; `REG = AX`.
  - `06 00`: offset del temporal/variable.

---

## 9. PUSH — guardar registro en la pila

- **Instrucción:** `PUSH AX`
- **Uso:** preservar el acumulador (contexto de llamada / salvaguarda de registros).
- **Código máquina (Hex):** `50`
- **Binario:** `01010000`
- **Desglose:**
  - `50`: opcode de 1 byte `50 + rw`.
  - Bits `01010` = operación **PUSH** de registro de 16 bits.
  - Bits `000` = registro **AX**.

---

## 10. POP — recuperar registro desde la pila

- **Instrucción:** `POP AX`
- **Uso:** restaurar el valor previamente guardado con `PUSH`.
- **Código máquina (Hex):** `58`
- **Binario:** `01011000`
- **Desglose:**
  - `58`: opcode de 1 byte `58 + rw`.
  - Bits `01011` = operación **POP** de registro de 16 bits.
  - Bits `000` = registro **AX**.

---

## 11. JMP — salto incondicional (bucles / fin de `if`)

- **Instrucción:** `JMP WHILE_1` *(ejemplo `rel8 = -20`)*
- **Uso en la gramática:** cerrar un `while`/`for` volviendo a la etiqueta de inicio, o saltar al final de un `if`.
- **Código máquina (Hex):** `EB EC`
- **Binario:** `11101011 11101100`
- **Desglose:**
  - `EB`: opcode de salto incondicional **corto** (`JMP rel8`).
  - `EC`: desplazamiento relativo de 1 byte en complemento a dos (`-20` decimal = `0xEC`), que retrocede el puntero de instrucción (`IP`) al inicio del bucle.
  - **No usa** ModR/M.

---

## 12. JE / JNE — saltos condicionales (comparaciones)

### 12.1 JE (saltar si igual / cero) — usado cuando la condición `!=` es falsa, o al comparar con 0

- **Instrucción:** `JE L2` *(ejemplo `rel8 = +10`)*
- **Código máquina (Hex):** `74 0A`
- **Binario:** `01110100 00001010`
- **Desglose:**
  - `74`: opcode **JE/JZ** (salta si `ZF = 1`).
  - `0A`: desplazamiento relativo `+10` bytes.
  - Depende de las banderas dejadas por un `CMP` previo.

### 12.2 JNE (saltar si distinto) — usado cuando la condición `==` es falsa

- **Instrucción:** `JNE L2` *(ejemplo `rel8 = +8`)*
- **Código máquina (Hex):** `75 08`
- **Binario:** `01110101 00001000`
- **Desglose:**
  - `75`: opcode **JNE/JNZ** (salta si `ZF = 0`).
  - `08`: desplazamiento relativo `+8`.

**Tabla de saltos que emite el generador según el operador relacional:**

| Operador Genesis | Si la condición es **falsa**, salta con |
|---|---|
| `==` | `JNE` |
| `!=` | `JE` |
| `<`  | `JGE` (`7D`) |
| `>`  | `JLE` (`7E`) |
| `<=` | `JG`  (`7F`) |
| `>=` | `JL`  (`7C`) |

---

## 13. INT — servicio de salida / entrada DOS

- **Instrucción:** `INT 21h`
- **Uso en la gramática:** `println` (servicios `02h` / `09h`) y `read` (servicio `01h`), tras cargar `AH` con el número de función.
- **Código máquina (Hex):** `CD 21`
- **Binario:** `11001101 00100001`
- **Desglose:**
  - `CD`: opcode de interrupción por software con inmediato de un byte (`INT imm8`).
  - `21`: número de interrupción **21h** de DOS; el registro **AH** selecciona el servicio concreto (impresión, lectura o terminación).

---

## Resumen del conjunto analizado

| # | Ensamblador | Hex | Rol en el compilador |
|---|---|---|---|
| 1 | `MOV AX, [num]` | `A1 00 00` | Leer variable |
| 2 | `MOV AX, 5` | `B8 05 00` | Literal → AX |
| 3 | `MOV AH, 09h` | `B4 09` | Preparar DOS |
| 4 | `MOV [total], AX` | `A3 04 00` | Guardar resultado |
| 5 | `LEA DX, [total]` | `8D 16 04 00` | Dirección de cadena |
| 6 | `ADD AX, [num2]` | `03 06 02 00` | Operador `@` |
| 7 | `SUB AX, [num2]` | `2B 06 02 00` | Operador `#` |
| 8 | `CMP AX, 0` | `3D 00 00` | Comparación |
| 9 | `PUSH AX` | `50` | Apilar registro |
| 10 | `POP AX` | `58` | Desapilar registro |
| 11 | `JMP rel8` | `EB EC` | Salto incondicional |
| 12 | `JE` / `JNE` | `74` / `75` | Saltos por condición |
| 13 | `INT 21h` | `CD 21` | I/O DOS |

Estas representaciones son exactamente los bytes que un ensamblador (o el backend de generación de código) escribiría en el archivo objeto / ejecutable para cada instrucción emitida a partir del código intermedio de la gramática.
