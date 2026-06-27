"""
MarkItDown GUI — local desktop converter
Converts documents to Markdown using the markitdown library.
"""

import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# ---------------------------------------------------------------------------
# Locate markitdown — installed package takes priority, then local source
# ---------------------------------------------------------------------------
_local_src = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "packages", "markitdown", "src")
if os.path.isdir(_local_src) and _local_src not in sys.path:
    sys.path.insert(0, _local_src)

try:
    from markitdown import MarkItDown
    _MARKITDOWN_OK = True
except ImportError:
    _MARKITDOWN_OK = False

try:
    import ftfy as _ftfy
    _FTFY_OK = True
except ImportError:
    _FTFY_OK = False

def _fix_text(t: str) -> str:
    """Fix UTF-8-decoded-as-Latin-1 mojibake by processing the text in latin-1-safe chunks."""
    if _FTFY_OK:
        fixed = _ftfy.fix_text(t)
        # ftfy may leave some sequences unfixed in mixed content; run manual pass too
        t = fixed

    # Character-by-character chunk approach: collect runs that can round-trip
    # through latin-1, then re-decode as utf-8 to recover the original chars.
    out, chunk = [], []
    def flush():
        if not chunk:
            return
        s = "".join(chunk)
        try:
            out.append(s.encode("latin-1").decode("utf-8"))
        except (UnicodeEncodeError, UnicodeDecodeError):
            out.append(s)
        chunk.clear()

    for ch in t:
        try:
            ch.encode("latin-1")
            chunk.append(ch)
        except UnicodeEncodeError:
            flush()
            out.append(ch)
    flush()
    return "".join(out)

import re as _re

def _clean_text(t: str) -> str:
    """Remove PDF watermark artifacts: lines containing only a single uppercase letter."""
    lines = t.splitlines()
    cleaned = [ln for ln in lines if not _re.fullmatch(r"\s*[A-Z]\s*", ln)]
    return "\n".join(cleaned)

# ---------------------------------------------------------------------------
# ffmpeg detection (needed for MP3/MP4/M4A/etc.)
# ---------------------------------------------------------------------------
_FFMPEG_EXTENSIONS = {'.mp3', '.mp4', '.m4a', '.ogg', '.flac', '.aac', '.wma', '.mov'}

def _ffmpeg_available() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=4)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


# ---------------------------------------------------------------------------
# Supported file types for the open dialog
# ---------------------------------------------------------------------------
_FILETYPES = [
    ("All supported",
     "*.pdf *.docx *.doc *.xlsx *.xls *.pptx *.ppt "
     "*.html *.htm *.csv *.json *.xml *.txt *.epub "
     "*.ipynb *.png *.jpg *.jpeg *.gif *.bmp *.tiff *.msg"),
    ("PDF",          "*.pdf"),
    ("Word",         "*.docx *.doc"),
    ("Excel",        "*.xlsx *.xls"),
    ("PowerPoint",   "*.pptx *.ppt"),
    ("Web / HTML",   "*.html *.htm"),
    ("Text / Data",  "*.txt *.csv *.json *.xml"),
    ("Notebook",     "*.ipynb"),
    ("E-book",       "*.epub"),
    ("Images",       "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
    ("Outlook msg",  "*.msg"),
    ("All files",    "*.*"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_theme(root: tk.Tk) -> None:
    """Pick the best available ttk theme for the current platform."""
    available = ttk.Style().theme_names()
    for name in ("vista", "aqua", "clam", "alt"):
        if name in available:
            ttk.Style().theme_use(name)
            break

    s = ttk.Style()
    s.configure("Status.TLabel",
                 foreground="#555555",
                 font=("", 9))


def _safe_after(widget, fn, *args):
    """Call fn(*args) on the Tk main thread, ignoring destroyed widgets."""
    try:
        widget.after(0, fn, *args)
    except tk.TclError:
        pass


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("MarkItDown — Convert to Markdown")
        self.root.geometry("940x700")
        self.root.minsize(700, 560)

        _apply_theme(root)

        self._input_path   = tk.StringVar()
        self._input_url    = tk.StringVar()
        self._input_mode   = tk.StringVar(value="file")   # "file" | "url"
        self._output_file  = tk.StringVar()
        self._output_dir   = tk.StringVar()
        self._status_text  = tk.StringVar(value="Ready — select an input file or enter a URL.")

        self._converting = False

        self._build_ui()

        if not _MARKITDOWN_OK:
            self._set_status(
                "WARNING: markitdown not found. "
                "Install it with: pip install markitdown",
                color="#cc4400",
            )

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = self.root

        # ---- top: input (file OR url) ----
        frm_in = ttk.LabelFrame(root, text=" Input ", padding=(10, 6))
        frm_in.pack(fill="x", padx=14, pady=(14, 4))

        # Mode selector row
        frm_mode = ttk.Frame(frm_in)
        frm_mode.pack(fill="x", pady=(0, 6))
        ttk.Radiobutton(
            frm_mode, text="File", variable=self._input_mode,
            value="file", command=self._on_mode_change,
        ).pack(side="left", padx=(0, 20))
        ttk.Radiobutton(
            frm_mode, text="YouTube / URL", variable=self._input_mode,
            value="url", command=self._on_mode_change,
        ).pack(side="left")

        # File picker row
        self._frm_file = ttk.Frame(frm_in)
        self._frm_file.pack(fill="x")
        self._entry_input = ttk.Entry(
            self._frm_file, textvariable=self._input_path, font=("", 10))
        self._entry_input.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(
            self._frm_file, text="Browse…", command=self._browse_input, width=10,
        ).pack(side="right")

        # URL entry row (hidden until URL mode selected)
        self._frm_url = ttk.Frame(frm_in)
        ttk.Label(self._frm_url, text="URL:", width=5, anchor="w").pack(side="left")
        self._entry_url = ttk.Entry(
            self._frm_url, textvariable=self._input_url, font=("", 10))
        self._entry_url.pack(side="left", fill="x", expand=True, padx=(4, 8))
        ttk.Button(
            self._frm_url, text="Preview", command=self._preview_url, width=10,
        ).pack(side="right")

        # ---- bottom bar: status + convert button ----
        # Packed BEFORE the preview so it always stays visible when the window is small.
        frm_bottom = ttk.Frame(root, padding=(14, 6, 14, 12))
        frm_bottom.pack(side="bottom", fill="x")

        self._status_lbl = ttk.Label(
            frm_bottom, textvariable=self._status_text, style="Status.TLabel")
        self._status_lbl.pack(side="left", fill="x", expand=True)

        self._btn_convert = tk.Button(
            frm_bottom, text="Convert to Markdown",
            command=self._convert,
            font=("", 11, "bold"),
            padx=18, pady=6,
            relief="raised", cursor="hand2")
        self._btn_convert.pack(side="right")

        tk.Button(
            frm_bottom, text="Clear",
            command=self._clear,
            font=("", 10),
            padx=10, pady=6,
            relief="raised", cursor="hand2",
            foreground="#555555",
        ).pack(side="right", padx=(0, 8))

        # ---- output — also packed before preview (anchored to bottom) ----
        frm_out = ttk.LabelFrame(root, text=" Output ", padding=(10, 8))
        frm_out.pack(side="bottom", fill="x", padx=14, pady=4)

        # Row 1 — output file name
        row_file = ttk.Frame(frm_out)
        row_file.pack(fill="x", pady=(0, 6))
        ttk.Label(row_file, text="File name:", width=12, anchor="w").pack(side="left")
        ttk.Entry(row_file, textvariable=self._output_file,
                  font=("", 10)).pack(side="left", fill="x", expand=True, padx=(4, 8))
        ttk.Button(row_file, text="Save as…", width=10,
                   command=self._browse_output_file).pack(side="right")

        # Row 2 — output folder
        row_dir = ttk.Frame(frm_out)
        row_dir.pack(fill="x")
        ttk.Label(row_dir, text="Folder:", width=12, anchor="w").pack(side="left")
        ttk.Entry(row_dir, textvariable=self._output_dir,
                  font=("", 10)).pack(side="left", fill="x", expand=True, padx=(4, 8))
        ttk.Button(row_dir, text="Browse…", width=10,
                   command=self._browse_output_dir).pack(side="right")

        # ---- preview — packed last so it fills whatever space remains ----
        frm_prev = ttk.LabelFrame(root, text=" Preview (converted Markdown) ", padding=(10, 6))
        frm_prev.pack(fill="both", expand=True, padx=14, pady=4)

        self._preview = scrolledtext.ScrolledText(
            frm_prev, wrap="word",
            font=("Consolas", 10),
            relief="flat",
            state="disabled",
            background="#fafafa",
        )
        self._preview.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Mode switch
    # ------------------------------------------------------------------

    def _on_mode_change(self) -> None:
        if self._input_mode.get() == "file":
            self._frm_url.pack_forget()
            self._frm_file.pack(fill="x")
        else:
            self._frm_file.pack_forget()
            self._frm_url.pack(fill="x")
            self._entry_url.focus_set()

    # ------------------------------------------------------------------
    # Browse actions
    # ------------------------------------------------------------------

    def _browse_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Select a file to convert",
            filetypes=_FILETYPES,
        )
        if not path:
            return

        self._input_path.set(path)

        # Derive defaults for output
        folder = os.path.dirname(path)
        stem   = os.path.splitext(os.path.basename(path))[0]
        self._output_dir.set(folder)
        self._output_file.set(stem + ".md")

        # Warn if the file needs ffmpeg and it is not installed
        ext = os.path.splitext(path)[1].lower()
        if ext in _FFMPEG_EXTENSIONS and not _ffmpeg_available():
            messagebox.showwarning(
                "ffmpeg no encontrado",
                f"Los archivos {ext.upper()} requieren ffmpeg para convertir el audio.\n\n"
                "Instálalo y vuelve a intentarlo:\n\n"
                "  Windows:   winget install ffmpeg\n"
                "  Mac:       brew install ffmpeg\n\n"
                "Los archivos WAV funcionan sin ffmpeg.",
            )
            return

        self._load_preview(path)

    def _browse_output_file(self) -> None:
        initial_dir  = self._output_dir.get()  or os.path.expanduser("~")
        initial_file = self._output_file.get() or "output.md"
        path = filedialog.asksaveasfilename(
            title="Save Markdown file as…",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("All files", "*.*")],
        )
        if not path:
            return
        self._output_dir.set(os.path.dirname(path))
        self._output_file.set(os.path.basename(path))

    def _browse_output_dir(self) -> None:
        folder = filedialog.askdirectory(
            title="Select output folder",
            initialdir=self._output_dir.get() or os.path.expanduser("~"),
        )
        if folder:
            self._output_dir.set(folder)

    def _preview_url(self) -> None:
        url = self._input_url.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please enter a YouTube or web URL.")
            return
        # Derive a sensible default output filename from the URL
        video_id_match = _re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
        stem = video_id_match.group(1) if video_id_match else "url_output"
        if not self._output_file.get():
            self._output_file.set(stem + ".md")
        if not self._output_dir.get():
            self._output_dir.set(os.path.expanduser("~"))
        self._load_preview(url)

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def _load_preview(self, path: str) -> None:
        self._set_preview_text("Loading preview…")
        self._set_status("Loading preview…")

        def worker():
            if not _MARKITDOWN_OK:
                _safe_after(self.root, self._set_preview_text,
                            "(markitdown not installed — cannot generate preview)")
                return
            try:
                md     = MarkItDown()
                result = md.convert(path)
                text   = _clean_text(_fix_text(result.text_content or "(empty result)"))
            except Exception as exc:
                text = f"(Preview error)\n\n{exc}"
            _safe_after(self.root, self._set_preview_text, text)
            _safe_after(self.root, self._set_status, "Preview ready.")

        threading.Thread(target=worker, daemon=True).start()

    def _set_preview_text(self, text: str) -> None:
        self._preview.config(state="normal")
        self._preview.delete("1.0", "end")
        self._preview.insert("end", text)
        self._preview.config(state="disabled")

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def _convert(self) -> None:
        if self._converting:
            return

        mode = self._input_mode.get()

        if mode == "url":
            input_src = self._input_url.get().strip()
            if not input_src:
                messagebox.showwarning("No URL",
                                       "Please enter a YouTube or web URL first.")
                return
            # Default output dir to home folder for URLs
            fallback_dir = os.path.expanduser("~")
            fallback_file = "url_output.md"
        else:
            input_src = self._input_path.get().strip()
            if not input_src:
                messagebox.showwarning("No file selected",
                                       "Please select an input file first.")
                return
            if not os.path.isfile(input_src):
                messagebox.showerror("File not found",
                                     f"Input file not found:\n{input_src}")
                return
            fallback_dir  = os.path.dirname(input_src)
            fallback_file = os.path.splitext(os.path.basename(input_src))[0] + ".md"
            # Check ffmpeg for audio formats that require it
            ext = os.path.splitext(input_src)[1].lower()
            if ext in _FFMPEG_EXTENSIONS and not _ffmpeg_available():
                messagebox.showwarning(
                    "ffmpeg no encontrado",
                    f"Los archivos {ext.upper()} requieren ffmpeg.\n\n"
                    "  Windows:   winget install ffmpeg\n"
                    "  Mac:       brew install ffmpeg\n\n"
                    "Los archivos WAV funcionan sin ffmpeg.",
                )
                return

        if not _MARKITDOWN_OK:
            messagebox.showerror(
                "markitdown not installed",
                "Run this command and restart the app:\n\n  pip install markitdown",
            )
            return

        out_dir  = self._output_dir.get().strip()  or fallback_dir
        out_file = self._output_file.get().strip()  or fallback_file

        output_path = os.path.join(out_dir, out_file)

        # Ask before overwriting
        if os.path.exists(output_path):
            if not messagebox.askyesno(
                "File exists",
                f"This file already exists:\n{output_path}\n\nOverwrite it?",
            ):
                return

        self._converting = True
        self._btn_convert.config(state="disabled")
        self._set_status("Converting…")

        def worker():
            try:
                md     = MarkItDown()
                result = md.convert(input_src)   # accepts both file paths and URLs
                os.makedirs(out_dir, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as fh:
                    fh.write(_clean_text(_fix_text(result.text_content)))
                _safe_after(self.root, self._on_success, output_path)
            except Exception as exc:
                _safe_after(self.root, self._on_error, str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_success(self, output_path: str) -> None:
        self._converting = False
        self._btn_convert.config(state="normal")
        self._set_status(f"Saved: {output_path}")
        messagebox.showinfo("Conversion complete",
                            f"File saved successfully:\n\n{output_path}")

    def _on_error(self, error: str) -> None:
        self._converting = False
        self._btn_convert.config(state="normal")
        self._set_status("Conversion failed.")
        messagebox.showerror("Conversion error",
                             f"An error occurred during conversion:\n\n{error}")

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _clear(self) -> None:
        self._input_path.set("")
        self._input_url.set("")
        self._output_file.set("")
        self._output_dir.set("")
        self._set_preview_text("")
        self._set_status("Ready — select an input file or enter a URL.")

    def _set_status(self, msg: str, color: str = "#555555") -> None:
        self._status_text.set(msg)
        try:
            self._status_lbl.config(foreground=color)
        except tk.TclError:
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    root = tk.Tk()

    # HiDPI awareness on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    try:
        root.tk.call("tk", "scaling", 1.4)
    except tk.TclError:
        pass

    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
