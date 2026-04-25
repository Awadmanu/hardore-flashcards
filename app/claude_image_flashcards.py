#!/usr/bin/env python3
"""
Flashcard Reviewer — CSV-based study tool
CSV format: Question, Answer, Difficulty, Topic

Images: Ctrl+V en el editor pega imágenes del portapapeles.
        Se guardan como PNG en {csv}_media/ y se referencian
        como [[img:archivo.png]] en los campos Question/Answer.
"""

import csv
import sys
import os
import re
import uuid
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from copy import deepcopy

# ── DPI awareness (Windows) ───────────────────
# Sin esto Windows escala la ventana borrosa en pantallas HiDPI.
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()   # Fallback Win7+
        except Exception:
            pass

try:
    from PIL import Image, ImageTk, ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ─────────────────────────────────────────────
#  Palette
# ─────────────────────────────────────────────
BG          = "#0f0f13"
CARD_BG     = "#1a1a24"
CARD_BORDER = "#2e2e42"
ACCENT      = "#7c6af7"
ACCENT2     = "#a78bfa"
SUCCESS     = "#34d399"
DANGER      = "#f87171"
WARNING     = "#fbbf24"
TEXT        = "#e8e6ff"
MUTED       = "#6b6888"
BTN_BG      = "#252535"
BTN_HOVER   = "#2e2e46"
WHITE       = "#ffffff"

DIFFICULTIES = ["Basic", "Intermediate", "Difficult"]
DIFF_COLORS  = {"Basic": SUCCESS, "Intermediate": WARNING, "Difficult": DANGER}

FONT_TITLE   = ("Georgia", 13, "bold")
FONT_CARD_Q  = ("Georgia", 18, "bold")
FONT_CARD_A  = ("Georgia", 14)
FONT_META    = ("Courier New", 10)
FONT_BTN     = ("Courier New", 10, "bold")
FONT_COUNTER = ("Courier New", 11)
FONT_LABEL   = ("Courier New", 10)

# ─────────────────────────────────────────────
#  Image tag helpers
# ─────────────────────────────────────────────
IMG_TAG_RE = re.compile(r'\[\[img:([^\]]+)\]\]')


def parse_rich(text: str) -> list:
    """Split text into ('text', str) | ('img', filename) chunks."""
    result, last = [], 0
    for m in IMG_TAG_RE.finditer(text):
        if m.start() > last:
            result.append(('text', text[last:m.start()]))
        result.append(('img', m.group(1)))
        last = m.end()
    if last < len(text):
        result.append(('text', text[last:]))
    return result or [('text', text)]


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def load_csv(path: str) -> list[dict]:
    cards = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cards.append({
                "Question":   row.get("Question", "").strip(),
                "Answer":     row.get("Answer", "").strip(),
                "Difficulty": row.get("Difficulty", "Intermediate").strip(),
                "Topic":      row.get("Topic", "").strip(),
            })
    return cards


def save_csv(path: str, cards: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Question", "Answer", "Difficulty", "Topic"])
        writer.writeheader()
        writer.writerows(cards)


# ─────────────────────────────────────────────
#  Edit / Add dialog
# ─────────────────────────────────────────────
class CardDialog(tk.Toplevel):
    def __init__(self, parent, title: str, card: dict | None = None,
                 media_dir: str | None = None, prefill_topic: str = ""):
        super().__init__(parent)
        self.result = None
        self.media_dir = media_dir
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        pad = {"padx": 16, "pady": 6}

        def field_header(label_text, widget_ref_fn):
            """Label a la izquierda; botón de pegar imagen a la derecha."""
            hdr = tk.Frame(self, bg=BG)
            hdr.pack(fill="x", padx=16, pady=(14, 0))
            tk.Label(hdr, text=label_text, bg=BG, fg=MUTED,
                     font=FONT_LABEL, anchor="w").pack(side="left")
            if PIL_AVAILABLE:
                tk.Button(
                    hdr, text="📋 Pegar imagen  [Ctrl+V]",
                    command=lambda: self._paste_image(widget_ref_fn()),
                    bg=BTN_BG, fg=MUTED, font=FONT_LABEL,
                    relief="flat", padx=8, pady=2, cursor="hand2", bd=0,
                    activebackground=BTN_HOVER, activeforeground=ACCENT2,
                ).pack(side="right")

        # ── Question ──
        self.q_text = tk.Text(self, height=4, width=52,
                              bg=CARD_BG, fg=TEXT, insertbackground=TEXT,
                              font=("Georgia", 12), relief="flat",
                              padx=10, pady=8, wrap="word",
                              highlightthickness=1,
                              highlightbackground=CARD_BORDER,
                              highlightcolor=ACCENT)
        field_header("QUESTION", lambda: self.q_text)
        self.q_text.pack(padx=16, pady=6)

        # ── Answer ──
        self.a_text = tk.Text(self, height=5, width=52,
                              bg=CARD_BG, fg=TEXT, insertbackground=TEXT,
                              font=("Georgia", 12), relief="flat",
                              padx=10, pady=8, wrap="word",
                              highlightthickness=1,
                              highlightbackground=CARD_BORDER,
                              highlightcolor=ACCENT)
        field_header("ANSWER", lambda: self.a_text)
        self.a_text.pack(padx=16, pady=6)

        # Ctrl/Cmd+V → imagen si procede, texto normal si no
        if PIL_AVAILABLE:
            for w in (self.q_text, self.a_text):
                w.bind("<Control-v>", lambda e, _w=w: self._on_paste(e, _w))
                w.bind("<Command-v>", lambda e, _w=w: self._on_paste(e, _w))

        # ── Row: Difficulty + Topic ──
        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=16, pady=6)

        diff_frame = tk.Frame(row, bg=BG)
        diff_frame.pack(side="left", padx=(0, 20))
        tk.Label(diff_frame, text="DIFFICULTY", bg=BG, fg=MUTED, font=FONT_LABEL).pack(anchor="w")
        self.diff_var = tk.StringVar(value="Intermediate")
        ttk.Combobox(diff_frame, textvariable=self.diff_var,
                     values=DIFFICULTIES, state="readonly", width=12,
                     font=FONT_LABEL).pack()

        topic_frame = tk.Frame(row, bg=BG)
        topic_frame.pack(side="left", fill="x", expand=True)
        tk.Label(topic_frame, text="TOPIC", bg=BG, fg=MUTED, font=FONT_LABEL).pack(anchor="w")
        self.topic_entry = tk.Entry(topic_frame, bg=CARD_BG, fg=TEXT,
                                    insertbackground=TEXT, font=("Georgia", 12),
                                    relief="flat", width=28,
                                    highlightthickness=1,
                                    highlightbackground=CARD_BORDER,
                                    highlightcolor=ACCENT)
        self.topic_entry.pack(fill="x")

        # ── Buttons ──
        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(fill="x", padx=16, pady=(12, 16))

        tk.Button(btn_row, text="CANCEL", command=self.destroy,
                  bg=BTN_BG, fg=MUTED, font=FONT_BTN,
                  relief="flat", padx=16, pady=6, cursor="hand2",
                  activebackground=BTN_HOVER, activeforeground=TEXT,
                  bd=0).pack(side="right", padx=(8, 0))

        tk.Button(btn_row, text="SAVE", command=self._save,
                  bg=ACCENT, fg=WHITE, font=FONT_BTN,
                  relief="flat", padx=24, pady=6, cursor="hand2",
                  activebackground=ACCENT2, activeforeground=WHITE,
                  bd=0).pack(side="right")

        # ── Prefill ──
        if card:
            self.q_text.insert("1.0", card["Question"])
            self.a_text.insert("1.0", card["Answer"])
            self.diff_var.set(card.get("Difficulty", "Intermediate"))
            self.topic_entry.insert(0, card.get("Topic", ""))
        elif prefill_topic:
            self.topic_entry.insert(0, prefill_topic)

        # Style combobox
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=CARD_BG, background=CARD_BG,
                        foreground=TEXT, selectbackground=ACCENT,
                        selectforeground=WHITE, bordercolor=CARD_BORDER,
                        arrowcolor=ACCENT)

        self.q_text.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())

        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(0,px)}+{max(0,py)}")

    # ── Image paste ────────────────────────────
    def _on_paste(self, event, widget):
        """Si el portapapeles tiene imagen la pega; si no, deja el comportamiento normal."""
        if self._paste_image(widget):
            return "break"

    def _paste_image(self, widget) -> bool:
        """Guarda la imagen del portapapeles en media_dir e inserta el tag [[img:...]]."""
        if not PIL_AVAILABLE:
            return False
        if not self.media_dir:
            messagebox.showwarning(
                "Sin CSV guardado",
                "Para pegar imágenes primero guarda el CSV.\n"
                "Las imágenes se almacenan junto al archivo CSV.",
                parent=self,
            )
            return False
        try:
            clip = ImageGrab.grabclipboard()
            if clip is None:
                return False
            # En algunos sistemas grabclipboard() devuelve lista de rutas
            if isinstance(clip, list):
                for p in clip:
                    if os.path.isfile(p):
                        try:
                            clip = Image.open(p)
                            break
                        except Exception:
                            continue
                else:
                    return False
            if not isinstance(clip, Image.Image):
                return False
            os.makedirs(self.media_dir, exist_ok=True)
            fname = f"{uuid.uuid4().hex[:12]}.png"
            clip.save(os.path.join(self.media_dir, fname))
            widget.insert("insert", f"[[img:{fname}]]")
            return True
        except Exception as exc:
            messagebox.showerror("Error al pegar imagen", str(exc), parent=self)
            return False

    def _save(self):
        q = self.q_text.get("1.0", "end").strip()
        a = self.a_text.get("1.0", "end").strip()
        if not q:
            messagebox.showwarning("Campo vacío", "La pregunta no puede estar vacía.", parent=self)
            return
        self.result = {
            "Question":   q,
            "Answer":     a,
            "Difficulty": self.diff_var.get(),
            "Topic":      self.topic_entry.get().strip(),
        }
        self.destroy()


# ─────────────────────────────────────────────
#  Main application
# ─────────────────────────────────────────────
class FlashcardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Flashcard Reviewer")
        self.configure(bg=BG)
        self.minsize(640, 520)
        self.geometry("740x580")

        self.cards: list[dict] = []
        self.index: int = 0
        self.answer_visible: bool = False
        self.csv_path: str | None = None
        self._media_dir: str | None = None
        self._unsaved: bool = False
        self._photo_refs: list = []          # evita que GC destruya PhotoImages
        self.auto_show_var = tk.BooleanVar(value=False)

        self._build_ui()
        self._show_empty_state()
        self.bind("<Left>",  lambda e: self._navigate(-1))
        self.bind("<Right>", lambda e: self._navigate(1))
        self.bind("<space>", lambda e: self._toggle_answer())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI Construction ────────────────────────
    def _build_ui(self):
        # ── Top bar ──
        topbar = tk.Frame(self, bg=BG, pady=0)
        topbar.pack(fill="x", padx=24, pady=(18, 0))

        tk.Label(topbar, text="✦ FLASHCARD REVIEWER",
                 bg=BG, fg=ACCENT2, font=FONT_TITLE).pack(side="left")

        self.save_btn = tk.Button(topbar, text="💾  GUARDAR CSV",
                                   command=self._save_csv,
                                   bg=BTN_BG, fg=MUTED, font=FONT_BTN,
                                   relief="flat", padx=12, pady=4,
                                   cursor="hand2", bd=0,
                                   activebackground=BTN_HOVER, activeforeground=TEXT)
        self.save_btn.pack(side="right", padx=(8, 0))

        tk.Button(topbar, text="📂  CARGAR CSV",
                  command=self._load_csv,
                  bg=ACCENT, fg=WHITE, font=FONT_BTN,
                  relief="flat", padx=12, pady=4,
                  cursor="hand2", bd=0,
                  activebackground=ACCENT2, activeforeground=WHITE).pack(side="right")

        # ── Counter + checkbox + topic row ──
        meta_row = tk.Frame(self, bg=BG)
        meta_row.pack(fill="x", padx=24, pady=(10, 0))

        self.counter_lbl = tk.Label(meta_row, text="", bg=BG, fg=MUTED, font=FONT_COUNTER)
        self.counter_lbl.pack(side="left")

        # Auto-show checkbox
        tk.Checkbutton(
            meta_row,
            text="Mostrar respuesta automáticamente",
            variable=self.auto_show_var,
            command=self._on_auto_show_toggle,
            bg=BG, fg=MUTED,
            selectcolor=BTN_BG,
            activebackground=BG,
            activeforeground=ACCENT2,
            font=FONT_META,
            cursor="hand2",
            relief="flat", bd=0,
        ).pack(side="left", padx=(20, 0))

        self.diff_lbl = tk.Label(meta_row, text="", bg=BG, fg=WARNING, font=FONT_META)
        self.diff_lbl.pack(side="right", padx=(0, 4))

        self.topic_lbl = tk.Label(meta_row, text="", bg=BG, fg=MUTED, font=FONT_META)
        self.topic_lbl.pack(side="right", padx=(0, 16))

        # ── Progress bar ──
        self.progress_canvas = tk.Canvas(self, bg=BG, height=3, highlightthickness=0)
        self.progress_canvas.pack(fill="x", padx=24, pady=(6, 0))

        # ── Card ──
        self.card_frame = tk.Frame(self, bg=CARD_BG,
                                    highlightthickness=1,
                                    highlightbackground=CARD_BORDER)
        self.card_frame.pack(fill="both", expand=True, padx=24, pady=14)

        # Question
        tk.Label(self.card_frame, text="PREGUNTA",
                 bg=CARD_BG, fg=MUTED, font=FONT_META, anchor="w"
                 ).pack(fill="x", padx=20, pady=(20, 4))

        self.q_display = tk.Text(
            self.card_frame,
            bg=CARD_BG, fg=TEXT,
            font=FONT_CARD_Q,
            relief="flat", bd=0, highlightthickness=0,
            wrap="word", cursor="arrow",
            padx=0, pady=0, spacing1=2, spacing2=4,
            height=4, state="disabled",
        )
        self.q_display.pack(fill="x", padx=20, pady=(0, 12))

        # Divider
        tk.Frame(self.card_frame, bg=CARD_BORDER, height=1).pack(fill="x", padx=20)

        # Answer
        tk.Label(self.card_frame, text="RESPUESTA",
                 bg=CARD_BG, fg=MUTED, font=FONT_META, anchor="w"
                 ).pack(fill="x", padx=20, pady=(12, 4))

        self.a_display = tk.Text(
            self.card_frame,
            bg=CARD_BG, fg=SUCCESS,
            font=FONT_CARD_A,
            relief="flat", bd=0, highlightthickness=0,
            wrap="word", cursor="arrow",
            padx=0, pady=0, spacing1=2, spacing2=4,
            height=5, state="disabled",
        )
        self.a_display.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        # Toggle button
        self.toggle_btn = tk.Button(self.card_frame, text="👁  VER RESPUESTA  [Space]",
                                     command=self._toggle_answer,
                                     bg=CARD_BG, fg=ACCENT2, font=FONT_BTN,
                                     relief="flat", pady=4, cursor="hand2", bd=0,
                                     activebackground=CARD_BG, activeforeground=ACCENT)
        self.toggle_btn.pack(pady=(0, 12))

        # ── Bottom toolbar ──
        toolbar = tk.Frame(self, bg=BG)
        toolbar.pack(fill="x", padx=24, pady=(0, 18))

        def mk_btn(parent, text, cmd, fg=TEXT, bg=BTN_BG):
            return tk.Button(parent, text=text, command=cmd,
                             bg=bg, fg=fg, font=FONT_BTN,
                             relief="flat", padx=12, pady=6,
                             cursor="hand2", bd=0,
                             activebackground=BTN_HOVER, activeforeground=TEXT)

        nav_left = tk.Frame(toolbar, bg=BG)
        nav_left.pack(side="left")
        self.prev_btn = mk_btn(nav_left, "◀  ANTERIOR", lambda: self._navigate(-1))
        self.prev_btn.pack(side="left", padx=(0, 4))
        self.next_btn = mk_btn(nav_left, "SIGUIENTE  ▶", lambda: self._navigate(1))
        self.next_btn.pack(side="left")

        nav_right = tk.Frame(toolbar, bg=BG)
        nav_right.pack(side="right")
        mk_btn(nav_right, "＋ ANTES",   self._add_before).pack(side="left", padx=(0, 4))
        mk_btn(nav_right, "＋ DESPUÉS", self._add_after).pack(side="left", padx=(0, 4))
        mk_btn(nav_right, "✎  EDITAR",  self._edit_current).pack(side="left", padx=(0, 4))
        mk_btn(nav_right, "✕  ELIMINAR", self._delete_current, fg=DANGER).pack(side="left")

    # ── Rich content rendering ─────────────────
    def _media_dir_for(self, csv_path: str) -> str:
        return os.path.splitext(csv_path)[0] + "_media"

    def _render_rich(self, widget: tk.Text, content: str, base_color: str):
        """Inserta texto e imágenes ([[img:...]]) en un widget tk.Text de solo lectura."""
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.tag_configure("txt", foreground=base_color, font=widget["font"])

        for kind, data in parse_rich(content):
            if kind == "text":
                widget.insert("end", data, "txt")
            else:  # "img"
                if not (PIL_AVAILABLE and self._media_dir):
                    widget.insert("end", f" [imagen: {data}] ", "txt")
                    continue
                img_path = os.path.join(self._media_dir, data)
                if not os.path.exists(img_path):
                    widget.insert("end", f" [imagen no encontrada: {data}] ", "txt")
                    continue
                try:
                    pil_img = Image.open(img_path)
                    max_w = max(200, widget.winfo_width() - 40)
                    if pil_img.width > max_w:
                        ratio = max_w / pil_img.width
                        pil_img = pil_img.resize(
                            (max_w, int(pil_img.height * ratio)), Image.Resampling.LANCZOS
                        )
                    photo = ImageTk.PhotoImage(pil_img)
                    self._photo_refs.append(photo)
                    widget.insert("end", "\n", "txt")
                    widget.image_create("end", image=photo, padx=0, pady=6)
                    widget.insert("end", "\n", "txt")
                except Exception as exc:
                    widget.insert("end", f" [error al cargar imagen: {exc}] ", "txt")

        widget.config(state="disabled")

    # ── Empty / Welcome state ──────────────────
    def _show_empty_state(self):
        self._render_rich(self.q_display, "Carga un CSV para empezar ✦", TEXT)
        self._render_rich(self.a_display, "", SUCCESS)
        self.counter_lbl.config(text="")
        self.topic_lbl.config(text="")
        self.diff_lbl.config(text="")
        self.toggle_btn.pack_forget()
        self._draw_progress(0)

    # ── CSV I/O ────────────────────────────────
    def _load_csv(self):
        if self._unsaved:
            if not messagebox.askyesno("Cambios sin guardar",
                                       "Tienes cambios sin guardar. ¿Continuar?"):
                return
        path = filedialog.askopenfilename(
            title="Abrir CSV de flashcards",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            cards = load_csv(path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el CSV:\n{e}")
            return
        if not cards:
            messagebox.showinfo("Vacío", "El CSV no contiene ninguna tarjeta.")
            return
        self.cards = cards
        self.csv_path = path
        self._media_dir = self._media_dir_for(path)
        self.index = 0
        self._unsaved = False
        self._render()
        self.title(f"Flashcard Reviewer — {os.path.basename(path)}")

    def _save_csv(self):
        if not self.cards:
            return
        path = self.csv_path or filedialog.asksaveasfilename(
            title="Guardar CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return
        try:
            save_csv(path, self.cards)
            self.csv_path = path
            self._media_dir = self._media_dir_for(path)
            self._unsaved = False
            self.save_btn.config(fg=MUTED)
            self.title(f"Flashcard Reviewer — {os.path.basename(path)}")
            messagebox.showinfo("Guardado", f"CSV guardado en:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    # ── Rendering ──────────────────────────────
    def _render(self):
        if not self.cards:
            self._show_empty_state()
            return

        self._photo_refs.clear()
        card = self.cards[self.index]
        total = len(self.cards)
        n = self.index + 1

        self.counter_lbl.config(text=f"{n} / {total}")
        self.topic_lbl.config(text=card.get("Topic") or "Sin tema")

        diff = card.get("Difficulty", "Intermediate")
        self.diff_lbl.config(text=f"● {diff}", fg=DIFF_COLORS.get(diff, WARNING))

        self._render_rich(self.q_display, card["Question"], TEXT)

        # Respuesta: auto-show o hidden según checkbox
        if self.auto_show_var.get():
            self.answer_visible = True
            self._render_rich(self.a_display, card["Answer"], SUCCESS)
            self.toggle_btn.config(text="🙈  OCULTAR RESPUESTA  [Space]")
        else:
            self.answer_visible = False
            self._render_rich(self.a_display, "", SUCCESS)
            self.toggle_btn.config(text="👁  VER RESPUESTA  [Space]")
        self.toggle_btn.pack(pady=(0, 12))

        self.prev_btn.config(state="normal" if self.index > 0 else "disabled",
                              fg=TEXT if self.index > 0 else MUTED)
        self.next_btn.config(state="normal" if self.index < total - 1 else "disabled",
                              fg=TEXT if self.index < total - 1 else MUTED)

        self._draw_progress(n / total)

    def _draw_progress(self, ratio: float):
        self.progress_canvas.update_idletasks()
        w = self.progress_canvas.winfo_width() or 600
        self.progress_canvas.delete("all")
        self.progress_canvas.create_rectangle(0, 0, w, 3, fill=CARD_BORDER, outline="")
        if ratio > 0:
            self.progress_canvas.create_rectangle(0, 0, int(w * ratio), 3,
                                                   fill=ACCENT, outline="")

    # ── Interactions ───────────────────────────
    def _toggle_answer(self):
        if not self.cards:
            return
        self.answer_visible = not self.answer_visible
        if self.answer_visible:
            self._render_rich(self.a_display, self.cards[self.index]["Answer"], SUCCESS)
            self.toggle_btn.config(text="🙈  OCULTAR RESPUESTA  [Space]")
        else:
            self._render_rich(self.a_display, "", SUCCESS)
            self.toggle_btn.config(text="👁  VER RESPUESTA  [Space]")

    def _navigate(self, delta: int):
        if not self.cards:
            return
        new_idx = self.index + delta
        if 0 <= new_idx < len(self.cards):
            self.index = new_idx
            self._render()

    def _current_topic(self) -> str:
        return self.cards[self.index].get("Topic", "") if self.cards else ""

    def _edit_current(self):
        if not self.cards:
            return
        dlg = CardDialog(self, "Editar flashcard", deepcopy(self.cards[self.index]),
                         media_dir=self._media_dir)
        self.wait_window(dlg)
        if dlg.result:
            self.cards[self.index] = dlg.result
            self._mark_unsaved()
            self._render()

    def _add_before(self):
        if not self.cards:
            self._add_new_empty()
            return
        dlg = CardDialog(self, "Nueva flashcard — insertar ANTES",
                         media_dir=self._media_dir,
                         prefill_topic=self._current_topic())
        self.wait_window(dlg)
        if dlg.result:
            self.cards.insert(self.index, dlg.result)
            self._mark_unsaved()
            self._render()

    def _add_after(self):
        dlg = CardDialog(self, "Nueva flashcard — insertar DESPUÉS",
                         media_dir=self._media_dir,
                         prefill_topic=self._current_topic())
        self.wait_window(dlg)
        if dlg.result:
            insert_at = self.index + 1 if self.cards else 0
            self.cards.insert(insert_at, dlg.result)
            self.index = insert_at
            self._mark_unsaved()
            self._render()

    def _add_new_empty(self):
        dlg = CardDialog(self, "Nueva flashcard", media_dir=self._media_dir)
        self.wait_window(dlg)
        if dlg.result:
            self.cards.append(dlg.result)
            self.index = len(self.cards) - 1
            self._mark_unsaved()
            self._render()

    def _delete_current(self):
        if not self.cards:
            return
        card = self.cards[self.index]
        preview = card["Question"][:60] + ("…" if len(card["Question"]) > 60 else "")
        if not messagebox.askyesno("Eliminar tarjeta", f"¿Eliminar esta flashcard?\n\n{preview}"):
            return
        self.cards.pop(self.index)
        if self.index >= len(self.cards):
            self.index = max(0, len(self.cards) - 1)
        self._mark_unsaved()
        self._render()

    def _on_auto_show_toggle(self):
        """Actualiza la tarjeta actual al momento de cambiar el checkbox."""
        if self.cards:
            card = self.cards[self.index]
            if self.auto_show_var.get():
                self.answer_visible = True
                self._render_rich(self.a_display, card["Answer"], SUCCESS)
                self.toggle_btn.config(text="🙈  OCULTAR RESPUESTA  [Space]")
            else:
                self.answer_visible = False
                self._render_rich(self.a_display, "", SUCCESS)
                self.toggle_btn.config(text="👁  VER RESPUESTA  [Space]")

    def _mark_unsaved(self):
        self._unsaved = True
        self.save_btn.config(fg=WARNING)

    def _on_close(self):
        if self._unsaved:
            resp = messagebox.askyesnocancel(
                "Cambios sin guardar",
                "Tienes cambios sin guardar. ¿Guardar antes de salir?"
            )
            if resp is None:
                return
            if resp:
                self._save_csv()
        self.destroy()

    def _on_resize(self, event=None):
        self._draw_progress(
            (self.index + 1) / len(self.cards) if self.cards else 0
        )


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    if not PIL_AVAILABLE:
        _root = tk.Tk()
        _root.withdraw()
        messagebox.showwarning(
            "Pillow no instalado",
            "Para soporte de imágenes instala Pillow:\n\n"
            "    pip install Pillow\n\n"
            "La app funciona con normalidad, pero sin imágenes."
        )
        _root.destroy()
    app = FlashcardApp()
    app.bind("<Configure>", app._on_resize)
    app.mainloop()