#!/usr/bin/env python3
"""
Flashcard CSV Reviewer

Expected CSV header:
("Question","Answer","Difficulty","Topic")

Features:
- Load a CSV from command line or file picker
- Review cards one by one
- Reveal/hide answer
- Edit current card
- Insert a new card before or after current
- Delete current card
- Save back to CSV or Save As
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
        self.root.geometry("980x720")

        self.cards = []
        self.index = 0
        self.current_path = None
        self.answer_visible = False

        self._build_ui()
        self._load_initial_file()

    def _build_ui(self):
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Top bar
        top = tk.Frame(self.root, padx=10, pady=10)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        tk.Button(top, text="Abrir CSV", command=self.open_csv, width=14).grid(row=0, column=0, padx=(0, 8))
        self.path_label = tk.Label(top, text="Ningún archivo cargado", anchor="w")
        self.path_label.grid(row=0, column=1, sticky="ew")

        # Main content
        main = tk.Frame(self.root, padx=10, pady=0)
        main.grid(row=1, column=0, sticky="nsew")
        main.rowconfigure(3, weight=1)
        main.columnconfigure(1, weight=1)

        self.status_label = tk.Label(main, text="Sin tarjetas", font=("Arial", 11, "bold"))
        self.status_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Label(main, text="Question").grid(row=1, column=0, sticky="nw", pady=4, padx=(0, 8))
        self.question_text = tk.Text(main, height=8, wrap="word", undo=True)
        self.question_text.grid(row=1, column=1, sticky="nsew", pady=4)

        tk.Label(main, text="Answer").grid(row=2, column=0, sticky="nw", pady=4, padx=(0, 8))
        self.answer_text = tk.Text(main, height=10, wrap="word", undo=True)
        self.answer_text.grid(row=2, column=1, sticky="nsew", pady=4)

        meta = tk.Frame(main)
        meta.grid(row=4, column=1, sticky="ew", pady=(12, 6))
        meta.columnconfigure(1, weight=1)
        meta.columnconfigure(3, weight=1)

        tk.Label(meta, text="Difficulty").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.difficulty_entry = tk.Entry(meta)
        self.difficulty_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12))

        tk.Label(meta, text="Topic").grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.topic_entry = tk.Entry(meta)
        self.topic_entry.grid(row=0, column=3, sticky="ew")

        # Buttons
        controls = tk.Frame(self.root, padx=10, pady=10)
        controls.grid(row=2, column=0, sticky="ew")
        for i in range(9):
            controls.columnconfigure(i, weight=1)

        tk.Button(controls, text="<< Anterior", command=self.prev_card).grid(row=0, column=0, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Siguiente >>", command=self.next_card).grid(row=0, column=1, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Mostrar/Ocultar respuesta", command=self.toggle_answer).grid(row=0, column=2, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Guardar cambios de esta", command=self.save_current_card).grid(row=0, column=3, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Insertar antes", command=lambda: self.insert_card("before")).grid(row=0, column=4, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Insertar después", command=lambda: self.insert_card("after")).grid(row=0, column=5, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Eliminar esta", command=self.delete_current_card).grid(row=0, column=6, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Guardar CSV", command=self.save_csv).grid(row=0, column=7, sticky="ew", padx=3, pady=3)
        tk.Button(controls, text="Guardar como...", command=self.save_csv_as).grid(row=0, column=8, sticky="ew", padx=3, pady=3)

        help_frame = tk.Frame(self.root, padx=10, pady=10)
        help_frame.grid(row=3, column=0, sticky="ew")
        help_text = (
            "Consejo: edita los campos y pulsa 'Guardar cambios de esta' antes de cambiar de tarjeta. "
            "La respuesta empieza oculta para simular repaso."
        )
        tk.Label(help_frame, text=help_text, fg="gray30", justify="left", wraplength=940).pack(anchor="w")

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
        try:
            self.load_csv(path)
        except Exception as exc:
            messagebox.showerror("Error al abrir CSV", str(exc))

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

            cards = []
            for row in reader:
                cards.append({
                    "Question": row.get("Question", ""),
                    "Answer": row.get("Answer", ""),
                    "Difficulty": row.get("Difficulty", ""),
                    "Topic": row.get("Topic", ""),
                })

        self.cards = cards if cards else [{
            "Question": "",
            "Answer": "",
            "Difficulty": "",
            "Topic": "",
        }]
        self.index = 0
        self.current_path = path
        self.path_label.config(text=path)
        self.answer_visible = False
        self.display_current_card()

    def display_current_card(self):
        if not self.cards:
            self.status_label.config(text="Sin tarjetas")
            self._set_text(self.question_text, "")
            self._set_text(self.answer_text, "")
            self.difficulty_entry.delete(0, tk.END)
            self.topic_entry.delete(0, tk.END)
            return

        card = self.cards[self.index]
        total = len(self.cards)
        self.status_label.config(text=f"Tarjeta {self.index + 1} de {total}")

        self._set_text(self.question_text, card["Question"])
        if self.answer_visible:
            self._set_text(self.answer_text, card["Answer"])
            self.answer_text.config(state="normal")
        else:
            self._set_text(self.answer_text, "Respuesta oculta. Pulsa 'Mostrar/Ocultar respuesta'.")
            self.answer_text.config(state="disabled")

        self.difficulty_entry.delete(0, tk.END)
        self.difficulty_entry.insert(0, card["Difficulty"])

        self.topic_entry.delete(0, tk.END)
        self.topic_entry.insert(0, card["Topic"])

    def _set_text(self, widget, content):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content)

    def _get_editor_data(self):
        answer = self.answer_text.get("1.0", tk.END).rstrip("\n")
        if not self.answer_visible and answer == "Respuesta oculta. Pulsa 'Mostrar/Ocultar respuesta'.":
            answer = self.cards[self.index]["Answer"] if self.cards else ""
        return {
            "Question": self.question_text.get("1.0", tk.END).rstrip("\n"),
            "Answer": answer,
            "Difficulty": self.difficulty_entry.get(),
            "Topic": self.topic_entry.get(),
        }

    def save_current_card(self):
        if not self.cards:
            return
        self.cards[self.index] = self._get_editor_data()
        messagebox.showinfo("Guardado", "Cambios guardados en memoria para esta flashcard.")

    def toggle_answer(self):
        if not self.cards:
            return
        if not self.answer_visible:
            current_data = self._get_editor_data()
            self.cards[self.index]["Question"] = current_data["Question"]
            self.cards[self.index]["Difficulty"] = current_data["Difficulty"]
            self.cards[self.index]["Topic"] = current_data["Topic"]
        else:
            current_answer = self.answer_text.get("1.0", tk.END).rstrip("\n")
            self.cards[self.index]["Answer"] = current_answer
        self.answer_visible = not self.answer_visible
        self.display_current_card()

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

    def save_in_memory(self):
        if not self.cards:
            return
        self.cards[self.index] = self._get_editor_data()

    def insert_card(self, position):
        if not self.cards:
            self.cards = [{"Question": "", "Answer": "", "Difficulty": "", "Topic": ""}]
            self.index = 0
            self.answer_visible = False
            self.display_current_card()
            return

        self.save_in_memory()
        new_card = {
            "Question": "",
            "Answer": "",
            "Difficulty": "",
            "Topic": "",
        }
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

    def save_csv(self):
        if not self.current_path:
            return self.save_csv_as()
        self.save_in_memory()
        self._write_csv(self.current_path)
        messagebox.showinfo("CSV guardado", f"Archivo guardado en:\n{self.current_path}")

    def save_csv_as(self):
        if not self.cards:
            messagebox.showwarning("Nada que guardar", "No hay tarjetas cargadas.")
            return
        path = filedialog.asksaveasfilename(
            title="Guardar CSV como",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        self.save_in_memory()
        self._write_csv(path)
        self.current_path = path
        self.path_label.config(text=path)
        messagebox.showinfo("CSV guardado", f"Archivo guardado en:\n{path}")

    def _write_csv(self, path):
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=EXPECTED_FIELDS, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(self.cards)


def main():
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
