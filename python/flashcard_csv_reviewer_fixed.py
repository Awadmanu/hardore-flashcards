#!/usr/bin/env python3
"""
Flashcard CSV Reviewer - fixed version

Expected CSV header:
("Question","Answer","Difficulty","Topic")
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
        self.root.geometry("1000x760")

        self.cards = []
        self.index = 0
        self.current_path = None
        self.answer_visible = False

        self._build_ui()
        self._bind_shortcuts()
        self._load_initial_file()

    def _build_ui(self):
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        top = tk.Frame(self.root, padx=10, pady=10)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        tk.Button(top, text="Abrir CSV", command=self.open_csv, width=14).grid(row=0, column=0, padx=(0, 8))
        self.path_label = tk.Label(top, text="Ningún archivo cargado", anchor="w")
        self.path_label.grid(row=0, column=1, sticky="ew")

        main = tk.Frame(self.root, padx=10, pady=0)
        main.grid(row=1, column=0, sticky="nsew")
        main.columnconfigure(1, weight=1)
        main.rowconfigure(2, weight=1)
        main.rowconfigure(4, weight=1)

        self.status_label = tk.Label(main, text="Sin tarjetas", font=("Arial", 11, "bold"))
        self.status_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Label(main, text="Question").grid(row=1, column=0, sticky="nw", padx=(0, 10), pady=4)
        self.question_text = tk.Text(main, height=10, wrap="word", undo=True)
        self.question_text.grid(row=1, column=1, sticky="nsew", pady=4)

        tk.Label(main, text="Answer").grid(row=2, column=0, sticky="nw", padx=(0, 10), pady=4)
        answer_frame = tk.Frame(main)
        answer_frame.grid(row=2, column=1, sticky="nsew", pady=4)
        answer_frame.rowconfigure(0, weight=1)
        answer_frame.columnconfigure(0, weight=1)

        self.answer_text = tk.Text(answer_frame, height=12, wrap="word", undo=True)
        self.answer_text.grid(row=0, column=0, sticky="nsew")

        self.answer_mask = tk.Label(
            answer_frame,
            text="Respuesta oculta.\nPulsa 'Mostrar respuesta' para verla.",
            justify="center",
            bg="#f0f0f0",
            fg="#444",
            font=("Arial", 12, "italic")
        )
        self.answer_mask.grid(row=0, column=0, sticky="nsew")

        meta = tk.Frame(main)
        meta.grid(row=3, column=1, sticky="ew", pady=(12, 6))
        meta.columnconfigure(1, weight=1)
        meta.columnconfigure(3, weight=1)

        tk.Label(meta, text="Difficulty").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.difficulty_entry = tk.Entry(meta)
        self.difficulty_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12))

        tk.Label(meta, text="Topic").grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.topic_entry = tk.Entry(meta)
        self.topic_entry.grid(row=0, column=3, sticky="ew")

        controls = tk.Frame(self.root, padx=10, pady=10)
        controls.grid(row=2, column=0, sticky="ew")
        for i in range(10):
            controls.columnconfigure(i, weight=1)

        tk.Button(controls, text="<< Anterior", command=self.prev_card).grid(row=0, column=0, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Siguiente >>", command=self.next_card).grid(row=0, column=1, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Mostrar respuesta", command=self.show_answer).grid(row=0, column=2, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Ocultar respuesta", command=self.hide_answer).grid(row=0, column=3, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Guardar tarjeta", command=self.save_current_card).grid(row=0, column=4, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Insertar antes", command=lambda: self.insert_card("before")).grid(row=0, column=5, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Insertar después", command=lambda: self.insert_card("after")).grid(row=0, column=6, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Eliminar esta", command=self.delete_current_card).grid(row=0, column=7, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Guardar CSV", command=self.save_csv).grid(row=0, column=8, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Guardar como...", command=self.save_csv_as).grid(row=0, column=9, sticky="ew", padx=3, pady=3)

        help_frame = tk.Frame(self.root, padx=10, pady=(10))
        help_frame.grid(row=3, column=0, sticky="ew")
        help_text = (
            "Ahora sí se puede editar directamente. La app guarda en memoria al cambiar de tarjeta. "
            "Atajos: Ctrl+S guardar CSV, Ctrl+Shift+S guardar como, Ctrl+N insertar después, "
            "Ctrl+Backspace eliminar, flechas izquierda/derecha navegar."
        )
        tk.Label(help_frame, text=help_text, fg="gray30", justify="left", wraplength=960).pack(anchor="w")

    def _bind_shortcuts(self):
        self.root.bind("<Control-s>", lambda e: self.save_csv())
        self.root.bind("<Control-S>", lambda e: self.save_csv_as())
        self.root.bind("<Control-n>", lambda e: self.insert_card("after"))
        self.root.bind("<Control-BackSpace>", lambda e: self.delete_current_card())
        self.root.bind("<Left>", lambda e: self.prev_card())
        self.root.bind("<Right>", lambda e: self.next_card())

    def _load_initial_file(self):
        if len(sys.argv) > 1:
            path = sys.argv[1]
            try:
                self.load_csv(path)
                return
            except Exception as exc:
                messagebox.showerror("Error al abrir CSV", str(exc))
        self.open_csv()

    def open_csv(self):
        path = filedialog.askopenfilename(
            title="Selecciona un CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        self.load_csv(path)

    def load_csv(self, path):
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValueError("El CSV está vacío o no tiene cabecera.")
            normalized = [name.strip() for name in reader.fieldnames]
            if normalized != EXPECTED_FIELDS:
                raise ValueError(
                    "Cabecera no válida.\n\n"
                    f"Esperada: {EXPECTED_FIELDS}\n"
                    f"Encontrada: {normalized}"
                )

            self.cards = [{
                "Question": row.get("Question", ""),
                "Answer": row.get("Answer", ""),
                "Difficulty": row.get("Difficulty", ""),
                "Topic": row.get("Topic", ""),
            } for row in reader]

        if not self.cards:
            self.cards = [{"Question": "", "Answer": "", "Difficulty": "", "Topic": ""}]

        self.index = 0
        self.current_path = path
        self.path_label.config(text=path)
        self.answer_visible = False
        self.display_current_card()

    def _set_text(self, widget, content):
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content)

    def get_current_editor_data(self):
        return {
            "Question": self.question_text.get("1.0", tk.END).rstrip("\n"),
            "Answer": self.answer_text.get("1.0", tk.END).rstrip("\n"),
            "Difficulty": self.difficulty_entry.get(),
            "Topic": self.topic_entry.get(),
        }

    def save_in_memory(self):
        if self.cards:
            self.cards[self.index] = self.get_current_editor_data()

    def display_current_card(self):
        if not self.cards:
            return

        card = self.cards[self.index]
        self.status_label.config(text=f"Tarjeta {self.index + 1} de {len(self.cards)}")

        self._set_text(self.question_text, card["Question"])
        self._set_text(self.answer_text, card["Answer"])

        self.difficulty_entry.delete(0, tk.END)
        self.difficulty_entry.insert(0, card["Difficulty"])

        self.topic_entry.delete(0, tk.END)
        self.topic_entry.insert(0, card["Topic"])

        if self.answer_visible:
            self.answer_mask.grid_remove()
        else:
            self.answer_mask.grid()

    def show_answer(self):
        self.answer_visible = True
        self.answer_mask.grid_remove()

    def hide_answer(self):
        self.answer_visible = False
        self.answer_mask.grid()

    def save_current_card(self):
        self.save_in_memory()
        messagebox.showinfo("Guardado", "Tarjeta guardada en memoria.")

    def prev_card(self):
        if not self.cards:
            return
        self.save_in_memory()
        if self.index > 0:
            self.index -= 1
            self.answer_visible = False
            self.display_current_card()

    def next_card(self):
        if not self.cards:
            return
        self.save_in_memory()
        if self.index < len(self.cards) - 1:
            self.index += 1
            self.answer_visible = False
            self.display_current_card()

    def insert_card(self, position):
        self.save_in_memory()
        new_card = {"Question": "", "Answer": "", "Difficulty": "", "Topic": ""}

        if position == "before":
            self.cards.insert(self.index, new_card)
        else:
            self.cards.insert(self.index + 1, new_card)
            self.index += 1

        self.answer_visible = True
        self.display_current_card()
        self.question_text.focus_set()

    def delete_current_card(self):
        if not self.cards:
            return
        if not messagebox.askyesno("Confirmar borrado", "¿Seguro que quieres eliminar la flashcard actual?"):
            return

        del self.cards[self.index]
        if not self.cards:
            self.cards = [{"Question": "", "Answer": "", "Difficulty": "", "Topic": ""}]
            self.index = 0
        else:
            self.index = min(self.index, len(self.cards) - 1)

        self.answer_visible = False
        self.display_current_card()

    def _write_csv(self, path):
        self.save_in_memory()
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=EXPECTED_FIELDS)
            writer.writeheader()
            writer.writerows(self.cards)

    def save_csv(self):
        if not self.current_path:
            return self.save_csv_as()
        self._write_csv(self.current_path)
        messagebox.showinfo("CSV guardado", f"Archivo guardado en:\n{self.current_path}")

    def save_csv_as(self):
        path = filedialog.asksaveasfilename(
            title="Guardar CSV como",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        self._write_csv(path)
        self.current_path = path
        self.path_label.config(text=path)
        messagebox.showinfo("CSV guardado", f"Archivo guardado en:\n{path}")


def main():
    root = tk.Tk()
    FlashcardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
