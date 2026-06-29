# MarkItDown GUI — Guía completa

Aplicación de escritorio para convertir documentos a formato Markdown usando la librería
[markitdown](https://github.com/microsoft/markitdown) de Microsoft.

---

## Archivos del proyecto

```
markitdown/
├── gui_app.py          ← la aplicación (único archivo a mantener)
├── requirements.txt    ← dependencias pip
├── MarkItDown.spec     ← configuración de PyInstaller para generar ejecutable
├── markdown.icns       ← icono para Mac (.app)
├── markdown.ico        ← icono para Windows (.exe)
├── markdown.png        ← icono fuente (usado también en Linux)
├── HOWTO.md            ← este archivo
├── dist/               ← ejecutables generados (no subir al repo)
└── build/              ← carpeta temporal de PyInstaller (ignorar)
```

**Archivos necesarios para compilar:** `gui_app.py`, `requirements.txt`, `MarkItDown.spec`, `markdown.icns`, `markdown.ico`, `markdown.png`, `HOWTO.md`
El mismo `MarkItDown.spec` genera el ejecutable en Windows (`.exe`), Linux (binario) y Mac (`.app`).

---

## Formatos de archivo soportados

PDF, Word (docx/doc), Excel (xlsx/xls), PowerPoint (pptx/ppt),
HTML, CSV, JSON, TXT, EPUB, imágenes (PNG/JPG/etc.), Jupyter notebooks (.ipynb),
Outlook (.msg)

---

## Opción A — Ejecutar desde Python (Windows y Mac)

### Requisitos previos
- Python 3.10 o superior con tkinter incluido
  - Windows: descarga de https://python.org (tkinter incluido por defecto)
  - Mac: `brew install python-tk` o usar el instalador de python.org

### Windows — Instalación de dependencias (una sola vez)
```bash
pip install -r requirements.txt
```

### Lanzar la app (Windows)
```bash
python gui_app.py
```

### Mac — Instalación de dependencias (una sola vez)

En Mac con Python de Homebrew, `pip` está protegido y hay que usar un entorno virtual:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Lanzar la app (Mac)

Cada vez que abras una terminal nueva, activa primero el entorno virtual:
```bash
source venv/bin/activate
python3 gui_app.py
```

---

## Opción B — Crear ejecutable sin Python

### Windows → genera `MarkItDown.exe`

```bash
pip install -r requirements.txt
pip install pyinstaller
python -m PyInstaller MarkItDown.spec
```

El ejecutable queda en `dist/MarkItDown.exe` (~93 MB).
Se puede copiar a cualquier Windows 10/11 de 64 bits y hacer doble clic.

---

### Linux → genera `MarkItDown` (binario ELF)

#### 1. Instalar Python con tkinter

Ubuntu / Debian:
```bash
sudo apt install python3-tk python3-pip
```
Fedora:
```bash
sudo dnf install python3-tkinter python3-pip
```
Arch:
```bash
sudo pacman -S tk python-pip
```

#### 2. Instalar dependencias
```bash
pip3 install -r requirements.txt
pip3 install pyinstaller
```

#### 3. Compilar
```bash
python3 -m PyInstaller MarkItDown.spec
```

El resultado aparece en `dist/MarkItDown` (sin extensión).
Para lanzarlo:
```bash
./dist/MarkItDown
```
O haz doble clic desde el gestor de archivos (puede que necesites marcar el archivo como ejecutable: clic derecho → Propiedades → Permisos → "Permitir ejecutar").

> **Nota de compatibilidad:** el binario generado funciona en distribuciones con la misma versión de glibc o superior a la del equipo de compilación. Para mayor compatibilidad, compila en Ubuntu LTS (22.04 / 24.04).

---

### Mac → genera `MarkItDown.app`

**Importante:** PyInstaller genera ejecutables para el SO donde se ejecuta.
El `.exe` de Windows NO funciona en Mac, y el `.app` de Mac NO funciona en Windows.
Hay que compilar en cada plataforma por separado.

#### 1. Instalar Python con tkinter

Usando Homebrew (recomendado):
```bash
brew install python-tk
```
O descargando el instalador oficial de https://python.org (incluye tkinter).

#### 2. Crear entorno virtual e instalar dependencias

En Mac, `pip` está protegido por el sistema y requiere un entorno virtual:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
```

#### 3. Compilar
```bash
python -m PyInstaller MarkItDown.spec
```

El resultado aparece en `dist/MarkItDown.app` (~28 MB).

#### 4. Si Mac bloquea la app (Gatekeeper)
La primera vez que abras la app, Mac puede mostrar "no se puede abrir porque es de un desarrollador no identificado".
Para solucionarlo, abre Terminal y ejecuta:
```bash
xattr -cr dist/MarkItDown.app
```
Luego haz doble clic en el `.app` normalmente.
O ve a Ajustes del sistema → Privacidad y seguridad → y haz clic en "Abrir igualmente".

> **Nota:** la carpeta `venv/` solo es necesaria para compilar. El `.app` generado funciona en cualquier Mac sin Python instalado.

---

## Qué hace el fix de encoding

Los PDFs de DocuSign (y otros) a veces tienen el texto codificado de forma que
pdfminer lo extrae con los acentos rotos (`Ã³` en vez de `ó`, `â¬` en vez de `€`).

La app aplica automáticamente dos correcciones:
1. **Fix de encoding** (`_fix_text`): convierte los caracteres rotos a UTF-8 correcto.
2. **Limpieza de marcas de agua** (`_clean_text`): elimina las letras sueltas que DocuSign
   incrusta como marca de agua en el PDF (aparecen como líneas con una sola letra: I, N, P…).

---

## Notas técnicas

- La conversión y la vista previa se ejecutan en hilos secundarios para no bloquear la UI.
- El archivo de salida se guarda en UTF-8.
- Si el archivo de destino ya existe, la app pregunta antes de sobreescribirlo.
- El botón "Convert to Markdown" se desactiva durante la conversión para evitar dobles clics.
