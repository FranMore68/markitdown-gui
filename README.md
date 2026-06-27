# MarkItDown GUI

Aplicación de escritorio para convertir documentos a formato Markdown.  
Basada en la librería [markitdown](https://github.com/microsoft/markitdown) de Microsoft.

## Descarga

👉 [Descargar la última versión para Windows](../../releases/latest)

Descarga el archivo `MarkItDown-Windows.zip`, extráelo y ejecuta `MarkItDown.exe`.  
No requiere instalar Python ni ninguna dependencia.

## Formatos soportados

| Formato | Extensiones |
|---|---|
| PDF | `.pdf` |
| Word | `.docx`, `.doc` |
| Excel | `.xlsx`, `.xls` |
| PowerPoint | `.pptx`, `.ppt` |
| Web | `.html`, `.htm` |
| Texto y datos | `.txt`, `.csv`, `.json`, `.xml` |
| E-book | `.epub` |
| Imágenes | `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff` |
| Jupyter Notebook | `.ipynb` |
| Outlook | `.msg` |
| Audio WAV | `.wav` *(requiere internet, usa Google Speech)* |
| Audio MP3/MP4 | `.mp3`, `.mp4` *(además requiere [ffmpeg](https://ffmpeg.org))* |
| YouTube URL | URL de YouTube *(requiere internet)* |

## Uso

1. Selecciona un archivo con **Browse…** o pega una URL de YouTube
2. Revisa la vista previa del Markdown generado
3. Ajusta el nombre y carpeta de salida si lo necesitas
4. Pulsa **Convert to Markdown**

## Nota sobre Windows SmartScreen

La primera vez que ejecutes la app, Windows puede mostrar un aviso de seguridad  
porque el ejecutable no tiene firma digital.  
Haz clic en **"Más información" → "Ejecutar de todas formas"** para continuar.

## Compilar desde el código fuente

Ver [HOWTO.md](HOWTO.md) para instrucciones de compilación en Windows, Mac y Linux.

## Licencia

MIT
