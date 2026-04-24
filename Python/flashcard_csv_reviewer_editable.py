#!/usr/bin/env python3
"""
Flashcard CSV Reviewer - editable version

CSV header required:
Question,Answer,Difficulty,Topic
"""

import csv
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

EXPECTED_FIELDS = ["Question", "Answer", "Difficulty", "Topic"]


class FlashcardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flashcard CSV Reviewer")
        self.root.geometry("1150x760")
        self.root.minsize(900, 600)

        self.cards = []
        self.index = 0
        self.current_path = None
        self.answer_shown = False

        self.build_ui()
        self.bind_shortcuts()
        self.load_initial()

    def build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        top = tk.Frame(self.root, padx=10, pady=10)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        tk.Button(top, text="Abrir CSV", command=self.open_csv, width=14).grid(row=0, column=0, padx=(0, 10))
        self.path_label = tk.Label(top, text="Ningún archivo cargado", anchor="w")
        self.path_label.grid(row=0, column=1, sticky="ew")

        self.status_label = tk.Label(top, text="Sin tarjetas", font=("Arial", 11, "bold"))
        self.status_label.grid(row=0, column=2, padx=(10, 0))

        main = tk.Frame(self.root, padx=10, pady=10)
        main.grid(row=1, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        # Left panel: review
        review = tk.LabelFrame(main, text="Vista de repaso", padx=10, pady=10)
        review.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        review.columnconfigure(0, weight=1)
        review.rowconfigure(1, weight=1)
        review.rowconfigure(3, weight=1)

        tk.Label(review, text="Question", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.review_question = tk.Text(review, wrap="word", height=12, state="disabled", bg="#f8f8f8")
        self.review_question.grid(row=1, column=0, sticky="nsew", pady=(0, 12))

        answer_header = tk.Frame(review)
        answer_header.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        answer_header.columnconfigure(0, weight=1)

        tk.Label(answer_header, text="Answer", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        tk.Button(answer_header, text="Mostrar/Ocultar", command=self.toggle_answer).grid(row=0, column=1, sticky="e")

        self.review_answer = tk.Text(review, wrap="word", height=12, state="disabled", bg="#f8f8f8")
        self.review_answer.grid(row=3, column=0, sticky="nsew")

        # Right panel: editor
        editor = tk.LabelFrame(main, text="Editor de la tarjeta actual", padx=10, pady=10)
        editor.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        editor.columnconfigure(0, weight=1)
        editor.rowconfigure(1, weight=1)
        editor.rowconfigure(3, weight=1)

        tk.Label(editor, text="Question", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.edit_question = tk.Text(
            editor,
            wrap="word",
            height=10,
            undo=True,
            insertbackground="black",
            bg="white",
            fg="black",
            relief="solid",
            borderwidth=1
        )
        self.edit_question.grid(row=1, column=0, sticky="nsew", pady=(0, 12))

        tk.Label(editor, text="Answer", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=(0, 6))
        self.edit_answer = tk.Text(
            editor,
            wrap="word",
            height=10,
            undo=True,
            insertbackground="black",
            bg="white",
            fg="black",
            relief="solid",
            borderwidth=1
        )
        self.edit_answer.grid(row=3, column=0, sticky="nsew", pady=(0, 12))

        meta = tk.Frame(editor)
        meta.grid(row=4, column=0, sticky="ew")
        meta.columnconfigure(1, weight=1)
        meta.columnconfigure(3, weight=1)

        tk.Label(meta, text="Difficulty").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.edit_difficulty = tk.Entry(meta, relief="solid", borderwidth=1)
        self.edit_difficulty.grid(row=0, column=1, sticky="ew", padx=(0, 12))

        tk.Label(meta, text="Topic").grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.edit_topic = tk.Entry(meta, relief="solid", borderwidth=1)
        self.edit_topic.grid(row=0, column=3, sticky="ew")

        buttons = tk.Frame(self.root, padx=10, pady=10)
        buttons.grid(row=2, column=0, sticky="ew")
        for i in range(9):
            buttons.columnconfigure(i, weight=1)

        tk.Button(buttons, text="<< Anterior", command=self.prev_card).grid(row=0, column=0, sticky="ew", padx=3, pady=3)
        tk.Button(buttons, text="Siguiente >>", command=self.next_card).grid(row=0, column=1, sticky="ew", padx=3, pady=3)
        tk.Button(buttons, text="Aplicar cambios", command=self.apply_changes).grid(row=0, column=2, sticky="ew", padx=3, pady=3)
        tk.Button(buttons, text="Insertar antes", command=lambda: self.insert_card("before")).grid(row=0, column=3, sticky="ew", padx=3, pady=3)
        tk.Button(buttons, text="Insertar después", command=lambda: self.insert_card("after")).grid(row=0, column=4, sticky="ew", padx=3, pady=3)
        tk.Button(buttons, text="Eliminar actual", command=self.delete_current).grid(row=0, column=5, sticky="ew", padx=3, pady=3)
        tk.Button(buttons, text="Guardar CSV", command=self.save_csv).grid(row=0, column=6, sticky="ew", padx=3, pady=3)
        tk.Button(buttons, text="Guardar como...", command=self.save_csv_as).grid(row=0, column=7, sticky="ew", padx=3, pady=3)
        tk.Button(buttons, text="Nueva vacía al final", command=self.append_card).grid(row=0, column=8, sticky="ew", padx=3, pady=3)

        hint = (
            "A la izquierda ves la tarjeta en modo repaso. A la derecha la editas en cajas normales. "
            "Pulsa 'Aplicar cambios' para refrescar la vista, aunque al navegar también se guarda en memoria."
        )
        tk.Label(self.root, text=hint, fg="gray30", padx=10, pady=0, wraplength=1100, justify="left").grid(row=3, column=0, sticky="w")

    def bind_shortcuts(self):
        self.root.bind("<Control-s>", lambda e: self.save_csv())
        self.root.bind("<Control-S>", lambda e: self.save_csv_as())
        self.root.bind("<Control-Return>", lambda e: self.apply_changes())
        self.root.bind("<Left>", lambda e: self.prev_card())
        self.root.bind("<Right>", lambda e: self.next_card())

    def load_initial(self):
        if len(sys.argv) > 1:
            try:
                self.load_csv(sys.argv[1])
                return
            except Exception as exc:
                messagebox.showerror("Error al abrir CSV", str(exc))
        self.open_csv()

    def open_csv(self):
        path = filedialog.askopenfilename(
            title="Selecciona un CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if path:
            self.load_csv(path)

    def load_csv(self, path):
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValueError("El CSV está vacío o no tiene cabecera.")

            headers = [h.strip() for h in reader.fieldnames]
            if headers != EXPECTED_FIELDS:
                raise ValueError(
                    "Cabecera no válida.\n"
                    f"Esperada: {EXPECTED_FIELDS}\n"
                    f"Encontrada: {headers}"
                )

            self.cards = []
            for row in reader:
                self.cards.append({
                    "Question": row.get("Question", ""),
                    "Answer": row.get("Answer", ""),
                    "Difficulty": row.get("Difficulty", ""),
                    "Topic": row.get("Topic", "")
                })

        if not self.cards:
            self.cards = [self.empty_card()]

        self.index = 0
        self.current_path = path
        self.path_label.config(text=path)
        self.answer_shown = False
        self.load_card_into_editor()
        self.refresh_review()

        # cursor real, sin teatro
        self.edit_question.focus_set()
        self.edit_question.mark_set("insert", "1.0")

    def empty_card(self):
        return {"Question": "", "Answer": "", "Difficulty": "", "Topic": ""}

    def set_text(self, widget, text):
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)

    def set_readonly_text(self, widget, text):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.config(state="disabled")

    def get_editor_data(self):
        return {
            "Question": self.edit_question.get("1.0", tk.END).rstrip("\n"),
            "Answer": self.edit_answer.get("1.0", tk.END).rstrip("\n"),
            "Difficulty": self.edit_difficulty.get(),
            "Topic": self.edit_topic.get()
        }

    def save_current_in_memory(self):
        if self.cards:
            self.cards[self.index] = self.get_editor_data()

    def load_card_into_editor(self):
        if not self.cards:
            return
        card = self.cards[self.index]
        self.set_text(self.edit_question, card["Question"])
        self.set_text(self.edit_answer, card["Answer"])

        self.edit_difficulty.delete(0, tk.END)
        self.edit_difficulty.insert(0, card["Difficulty"])

        self.edit_topic.delete(0, tk.END)
        self.edit_topic.insert(0, card["Topic"])

        self.status_label.config(text=f"Tarjeta {self.index + 1} de {len(self.cards)}")

    def refresh_review(self):
        if not self.cards:
            return
        card = self.cards[self.index]
        self.set_readonly_text(self.review_question, card["Question"])
        if self.answer_shown:
            self.set_readonly_text(self.review_answer, card["Answer"])
        else:
            self.set_readonly_text(self.review_answer, "[Respuesta oculta]")

    def apply_changes(self):
        self.save_current_in_memory()
        self.refresh_review()
        messagebox.showinfo("Aplicado", "Cambios aplicados a la tarjeta actual.")

    def toggle_answer(self):
        self.answer_shown = not self.answer_shown
        self.refresh_review()

    def goto_card(self, new_index):
        self.save_current_in_memory()
        self.index = new_index
        self.answer_shown = False
        self.load_card_into_editor()
        self.refresh_review()
        self.edit_question.focus_set()
        self.edit_question.mark_set("insert", "1.0")

    def prev_card(self):
        if self.cards and self.index > 0:
            self.goto_card(self.index - 1)

    def next_card(self):
        if self.cards and self.index < len(self.cards) - 1:
            self.goto_card(self.index + 1)

    def insert_card(self, where):
        self.save_current_in_memory()
        new_card = self.empty_card()
        if where == "before":
            self.cards.insert(self.index, new_card)
        else:
            self.cards.insert(self.index + 1, new_card)
            self.index += 1
        self.answer_shown = True
        self.load_card_into_editor()
        self.refresh_review()
        self.edit_question.focus_set()
        self.edit_question.mark_set("insert", "1.0")

    def append_card(self):
        self.save_current_in_memory()
        self.cards.append(self.empty_card())
        self.index = len(self.cards) - 1
        self.answer_shown = True
        self.load_card_into_editor()
        self.refresh_review()
        self.edit_question.focus_set()
        self.edit_question.mark_set("insert", "1.0")

    def delete_current(self):
        if not self.cards:
            return
        if not messagebox.askyesno("Confirmar borrado", "¿Eliminar la flashcard actual?"):
            return

        del self.cards[self.index]
        if not self.cards:
            self.cards = [self.empty_card()]
            self.index = 0
        else:
            self.index = min(self.index, len(self.cards) - 1)

        self.answer_shown = False
        self.load_card_into_editor()
        self.refresh_review()

    def write_csv(self, path):
        self.save_current_in_memory()
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=EXPECTED_FIELDS)
            writer.writeheader()
            writer.writerows(self.cards)

    def save_csv(self):
        if not self.current_path:
            self.save_csv_as()
            return
        self.write_csv(self.current_path)
        messagebox.showinfo("Guardado", f"CSV guardado en:\n{self.current_path}")

    def save_csv_as(self):
        path = filedialog.asksaveasfilename(
            title="Guardar CSV como",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        self.write_csv(path)
        self.current_path = path
        self.path_label.config(text=path)
        messagebox.showinfo("Guardado", f"CSV guardado en:\n{path}")


def main():
    root = tk.Tk()
    FlashcardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
