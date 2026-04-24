#!/usr/bin/env python3
"""
Flashcard Reviewer — CSV-based study tool
CSV format: Question, Answer, Difficulty, Topic
"""

import csv
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from copy import deepcopy

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
    def __init__(self, parent, title: str, card: dict | None = None):
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.grab_set()

        pad = {"padx": 16, "pady": 6}

        def lbl(text):
            return tk.Label(self, text=text, bg=BG, fg=MUTED,
                            font=FONT_LABEL, anchor="w")

        # ── Question ──
        lbl("QUESTION").pack(fill="x", padx=16, pady=(16, 0))
        self.q_text = tk.Text(self, height=4, width=52,
                              bg=CARD_BG, fg=TEXT, insertbackground=TEXT,
                              font=("Georgia", 12), relief="flat",
                              padx=10, pady=8, wrap="word",
                              highlightthickness=1,
                              highlightbackground=CARD_BORDER,
                              highlightcolor=ACCENT)
        self.q_text.pack(padx=16, pady=6)

        # ── Answer ──
        lbl("ANSWER").pack(fill="x", padx=16, pady=(8, 0))
        self.a_text = tk.Text(self, height=5, width=52,
                              bg=CARD_BG, fg=TEXT, insertbackground=TEXT,
                              font=("Georgia", 12), relief="flat",
                              padx=10, pady=8, wrap="word",
                              highlightthickness=1,
                              highlightbackground=CARD_BORDER,
                              highlightcolor=ACCENT)
        self.a_text.pack(padx=16, pady=6)

        # ── Row: Difficulty + Topic ──
        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=16, pady=6)

        diff_frame = tk.Frame(row, bg=BG)
        diff_frame.pack(side="left", padx=(0, 20))
        lbl2 = tk.Label(diff_frame, text="DIFFICULTY", bg=BG, fg=MUTED, font=FONT_LABEL)
        lbl2.pack(anchor="w")
        self.diff_var = tk.StringVar(value="Medium")
        diff_menu = ttk.Combobox(diff_frame, textvariable=self.diff_var,
                                 values=DIFFICULTIES, state="readonly", width=12,
                                 font=FONT_LABEL)
        diff_menu.pack()

        topic_frame = tk.Frame(row, bg=BG)
        topic_frame.pack(side="left", fill="x", expand=True)
        lbl3 = tk.Label(topic_frame, text="TOPIC", bg=BG, fg=MUTED, font=FONT_LABEL)
        lbl3.pack(anchor="w")
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

        cancel_btn = tk.Button(btn_row, text="CANCEL", command=self.destroy,
                               bg=BTN_BG, fg=MUTED, font=FONT_BTN,
                               relief="flat", padx=16, pady=6, cursor="hand2",
                               activebackground=BTN_HOVER, activeforeground=TEXT,
                               bd=0)
        cancel_btn.pack(side="right", padx=(8, 0))

        save_btn = tk.Button(btn_row, text="SAVE", command=self._save,
                             bg=ACCENT, fg=WHITE, font=FONT_BTN,
                             relief="flat", padx=24, pady=6, cursor="hand2",
                             activebackground=ACCENT2, activeforeground=WHITE,
                             bd=0)
        save_btn.pack(side="right")

        # ── Prefill if editing ──
        if card:
            self.q_text.insert("1.0", card["Question"])
            self.a_text.insert("1.0", card["Answer"])
            self.diff_var.set(card.get("Difficulty", "Medium"))
            self.topic_entry.insert(0, card.get("Topic", ""))

        # Style combobox
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=CARD_BG,
                        background=CARD_BG,
                        foreground=TEXT,
                        selectbackground=ACCENT,
                        selectforeground=WHITE,
                        bordercolor=CARD_BORDER,
                        arrowcolor=ACCENT)

        self.q_text.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())

        # Center on parent
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(0,px)}+{max(0,py)}")

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
        self._unsaved: bool = False
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

        title_lbl = tk.Label(topbar, text="✦ FLASHCARD REVIEWER",
                              bg=BG, fg=ACCENT2, font=FONT_TITLE)
        title_lbl.pack(side="left")

        self.save_btn = tk.Button(topbar, text="💾  GUARDAR CSV",
                                   command=self._save_csv,
                                   bg=BTN_BG, fg=MUTED, font=FONT_BTN,
                                   relief="flat", padx=12, pady=4,
                                   cursor="hand2", bd=0,
                                   activebackground=BTN_HOVER, activeforeground=TEXT)
        self.save_btn.pack(side="right", padx=(8, 0))

        load_btn = tk.Button(topbar, text="📂  CARGAR CSV",
                              command=self._load_csv,
                              bg=ACCENT, fg=WHITE, font=FONT_BTN,
                              relief="flat", padx=12, pady=4,
                              cursor="hand2", bd=0,
                              activebackground=ACCENT2, activeforeground=WHITE)
        load_btn.pack(side="right")

        # ── Counter + topic row ──
        meta_row = tk.Frame(self, bg=BG)
        meta_row.pack(fill="x", padx=24, pady=(10, 0))

        self.counter_lbl = tk.Label(meta_row, text="", bg=BG, fg=MUTED, font=FONT_COUNTER)
        self.counter_lbl.pack(side="left")

        # ── Auto-show checkbox ──
        auto_cb = tk.Checkbutton(
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
        )
        auto_cb.pack(side="left", padx=(20, 0))

        self.diff_lbl = tk.Label(meta_row, text="", bg=BG, fg=WARNING, font=FONT_META)
        self.diff_lbl.pack(side="right", padx=(0, 4))

        self.topic_lbl = tk.Label(meta_row, text="", bg=BG, fg=MUTED, font=FONT_META)
        self.topic_lbl.pack(side="right", padx=(0, 16))

        # ── Progress bar ──
        self.progress_canvas = tk.Canvas(self, bg=BG, height=3,
                                          highlightthickness=0)
        self.progress_canvas.pack(fill="x", padx=24, pady=(6, 0))

        # ── Card ──
        self.card_frame = tk.Frame(self, bg=CARD_BG,
                                    highlightthickness=1,
                                    highlightbackground=CARD_BORDER)
        self.card_frame.pack(fill="both", expand=True, padx=24, pady=14)

        # Question section
        q_header = tk.Label(self.card_frame, text="PREGUNTA",
                             bg=CARD_BG, fg=MUTED, font=FONT_META, anchor="w")
        q_header.pack(fill="x", padx=20, pady=(20, 4))

        self.q_label = tk.Label(self.card_frame, text="",
                                 bg=CARD_BG, fg=TEXT, font=FONT_CARD_Q,
                                 wraplength=640, justify="left", anchor="w")
        self.q_label.pack(fill="x", padx=20, pady=(0, 16))

        # Divider
        self.divider = tk.Frame(self.card_frame, bg=CARD_BORDER, height=1)
        self.divider.pack(fill="x", padx=20, pady=0)

        # Answer section
        a_header = tk.Label(self.card_frame, text="RESPUESTA",
                             bg=CARD_BG, fg=MUTED, font=FONT_META, anchor="w")
        a_header.pack(fill="x", padx=20, pady=(12, 4))

        self.a_label = tk.Label(self.card_frame, text="",
                                 bg=CARD_BG, fg=SUCCESS, font=FONT_CARD_A,
                                 wraplength=640, justify="left", anchor="w")
        self.a_label.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Show/hide answer button
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
            b = tk.Button(parent, text=text, command=cmd,
                          bg=bg, fg=fg, font=FONT_BTN,
                          relief="flat", padx=12, pady=6,
                          cursor="hand2", bd=0,
                          activebackground=BTN_HOVER, activeforeground=TEXT)
            return b

        # Left nav
        nav_left = tk.Frame(toolbar, bg=BG)
        nav_left.pack(side="left")

        self.prev_btn = mk_btn(nav_left, "◀  ANTERIOR", lambda: self._navigate(-1))
        self.prev_btn.pack(side="left", padx=(0, 4))

        self.next_btn = mk_btn(nav_left, "SIGUIENTE  ▶", lambda: self._navigate(1))
        self.next_btn.pack(side="left")

        # Right actions
        nav_right = tk.Frame(toolbar, bg=BG)
        nav_right.pack(side="right")

        mk_btn(nav_right, "＋ ANTES",  self._add_before).pack(side="left", padx=(0, 4))
        mk_btn(nav_right, "＋ DESPUÉS", self._add_after).pack(side="left", padx=(0, 4))
        mk_btn(nav_right, "✎  EDITAR",  self._edit_current).pack(side="left", padx=(0, 4))
        mk_btn(nav_right, "✕  ELIMINAR", self._delete_current,
               fg=DANGER).pack(side="left")

    # ── Empty / Welcome state ──────────────────
    def _show_empty_state(self):
        self.q_label.config(text="Carga un CSV para empezar ✦")
        self.a_label.config(text="")
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

        card = self.cards[self.index]
        total = len(self.cards)
        n = self.index + 1

        self.counter_lbl.config(text=f"{n} / {total}")
        self.topic_lbl.config(text=card.get("Topic") or "Sin tema")

        diff = card.get("Difficulty", "Medium")
        self.diff_lbl.config(text=f"● {diff}",
                              fg=DIFF_COLORS.get(diff, WARNING))

        self.q_label.config(text=card["Question"])

        # Reset answer visibility (or auto-show if checkbox is on)
        if self.auto_show_var.get():
            self.answer_visible = True
            self.a_label.config(text=card["Answer"])
            self.toggle_btn.config(text="🙈  OCULTAR RESPUESTA  [Space]")
        else:
            self.answer_visible = False
            self.a_label.config(text="")
            self.toggle_btn.config(text="👁  VER RESPUESTA  [Space]")
        self.toggle_btn.pack(pady=(0, 12))

        # Nav button states
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
            self.progress_canvas.create_rectangle(
                0, 0, int(w * ratio), 3, fill=ACCENT, outline=""
            )

    # ── Interactions ───────────────────────────
    def _toggle_answer(self):
        if not self.cards:
            return
        self.answer_visible = not self.answer_visible
        if self.answer_visible:
            self.a_label.config(text=self.cards[self.index]["Answer"])
            self.toggle_btn.config(text="🙈  OCULTAR RESPUESTA  [Space]")
        else:
            self.a_label.config(text="")
            self.toggle_btn.config(text="👁  VER RESPUESTA  [Space]")

    def _navigate(self, delta: int):
        if not self.cards:
            return
        new_idx = self.index + delta
        if 0 <= new_idx < len(self.cards):
            self.index = new_idx
            self._render()

    def _edit_current(self):
        if not self.cards:
            return
        dlg = CardDialog(self, "Editar flashcard", deepcopy(self.cards[self.index]))
        self.wait_window(dlg)
        if dlg.result:
            self.cards[self.index] = dlg.result
            self._mark_unsaved()
            self._render()
            if self.answer_visible:
                self.a_label.config(text=dlg.result["Answer"])

    def _add_before(self):
        if not self.cards:
            self._add_new_empty()
            return
        dlg = CardDialog(self, "Nueva flashcard — insertar ANTES")
        self.wait_window(dlg)
        if dlg.result:
            self.cards.insert(self.index, dlg.result)
            self._mark_unsaved()
            self._render()

    def _add_after(self):
        dlg = CardDialog(self, "Nueva flashcard — insertar DESPUÉS")
        self.wait_window(dlg)
        if dlg.result:
            insert_at = self.index + 1 if self.cards else 0
            self.cards.insert(insert_at, dlg.result)
            self.index = insert_at
            self._mark_unsaved()
            self._render()

    def _add_new_empty(self):
        dlg = CardDialog(self, "Nueva flashcard")
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
        """When the checkbox changes, update the current card immediately."""
        if self.cards:
            card = self.cards[self.index]
            if self.auto_show_var.get():
                self.answer_visible = True
                self.a_label.config(text=card["Answer"])
                self.toggle_btn.config(text="🙈  OCULTAR RESPUESTA  [Space]")
            else:
                self.answer_visible = False
                self.a_label.config(text="")
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
        if self.cards:
            w = self.card_frame.winfo_width() - 40
            self.q_label.config(wraplength=max(200, w))
            self.a_label.config(wraplength=max(200, w))
        self._draw_progress(
            (self.index + 1) / len(self.cards) if self.cards else 0
        )


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = FlashcardApp()
    app.bind("<Configure>", app._on_resize)
    app.mainloop()