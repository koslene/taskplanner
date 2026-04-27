import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from uuid import uuid4

DATA_FILE = "tasks.json"


def safe_load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        return []


def safe_save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def valid_date(date_text):
    if not date_text.strip():
        return True
    try:
        datetime.strptime(date_text.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


class TaskPlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mācību uzdevumu plānotājs")
        self.root.geometry("1120x680")
        self.root.minsize(980, 620)

        self.tasks = safe_load_tasks()
        self.selected_task_id = None

        self._build_ui()
        self.refresh_tree()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        title = tk.Label(
            self.root,
            text="Mācību uzdevumu plānotājs",
            font=("Segoe UI", 20, "bold")
        )
        title.pack(pady=10)

        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        left = ttk.LabelFrame(main, text="Uzdevuma ievade", padding=10)
        left.pack(side="left", fill="y", padx=(0, 10))

        right = ttk.Frame(main)
        right.pack(side="right", fill="both", expand=True)

        # Form fields
        self.title_var = tk.StringVar()
        self.desc_var = tk.StringVar()
        self.due_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.priority_var = tk.StringVar(value="2")
        self.status_var = tk.StringVar(value="Nav sākts")

        ttk.Label(left, text="Nosaukums:").grid(row=0, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(left, textvariable=self.title_var, width=30).grid(row=1, column=0, sticky="we", pady=(0, 8))

        ttk.Label(left, text="Apraksts:").grid(row=2, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(left, textvariable=self.desc_var, width=30).grid(row=3, column=0, sticky="we", pady=(0, 8))

        ttk.Label(left, text="Termiņš (YYYY-MM-DD):").grid(row=4, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(left, textvariable=self.due_var, width=30).grid(row=5, column=0, sticky="we", pady=(0, 8))

        ttk.Label(left, text="Kategorija:").grid(row=6, column=0, sticky="w", pady=(0, 4))
        ttk.Entry(left, textvariable=self.category_var, width=30).grid(row=7, column=0, sticky="we", pady=(0, 8))

        ttk.Label(left, text="Prioritāte:").grid(row=8, column=0, sticky="w", pady=(0, 4))
        ttk.Combobox(
            left,
            textvariable=self.priority_var,
            values=["1", "2", "3"],
            state="readonly",
            width=27
        ).grid(row=9, column=0, sticky="we", pady=(0, 8))

        ttk.Label(left, text="Statuss:").grid(row=10, column=0, sticky="w", pady=(0, 4))
        ttk.Combobox(
            left,
            textvariable=self.status_var,
            values=["Nav sākts", "Procesā", "Pabeigts"],
            state="readonly",
            width=27
        ).grid(row=11, column=0, sticky="we", pady=(0, 12))

        btn_frame = ttk.Frame(left)
        btn_frame.grid(row=12, column=0, sticky="we")

        ttk.Button(btn_frame, text="Pievienot", command=self.add_task).grid(row=0, column=0, padx=2, pady=2, sticky="we")
        ttk.Button(btn_frame, text="Atjaunināt", command=self.update_task).grid(row=0, column=1, padx=2, pady=2, sticky="we")
        ttk.Button(btn_frame, text="Dzēst", command=self.delete_task).grid(row=1, column=0, padx=2, pady=2, sticky="we")
        ttk.Button(btn_frame, text="Notīrīt laukus", command=self.clear_form).grid(row=1, column=1, padx=2, pady=2, sticky="we")
        ttk.Button(btn_frame, text="Pārslēgt statusu", command=self.toggle_status).grid(
            row=2, column=0, columnspan=2, padx=2, pady=(8, 2), sticky="we"
        )

        # Search and filter
        topbar = ttk.LabelFrame(right, text="Meklēšana un filtrs", padding=10)
        topbar.pack(fill="x", pady=(0, 10))

        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="Visi")

        ttk.Label(topbar, text="Meklēt:").grid(row=0, column=0, sticky="w")
        ttk.Entry(topbar, textvariable=self.search_var, width=30).grid(row=0, column=1, padx=6, sticky="we")
        ttk.Label(topbar, text="Statuss:").grid(row=0, column=2, sticky="w")
        ttk.Combobox(
            topbar,
            textvariable=self.filter_var,
            values=["Visi", "Nav sākts", "Procesā", "Pabeigts"],
            state="readonly",
            width=16
        ).grid(row=0, column=3, padx=6)

        ttk.Button(topbar, text="Filtrēt", command=self.refresh_tree).grid(row=0, column=4, padx=4)
        ttk.Button(topbar, text="Notīrīt", command=self.clear_filters).grid(row=0, column=5, padx=4)

        topbar.columnconfigure(1, weight=1)

        # Treeview
        table_frame = ttk.Frame(right)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "title", "due", "priority", "category", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        headings = {
            "id": "ID",
            "title": "Nosaukums",
            "due": "Termiņš",
            "priority": "Prioritāte",
            "category": "Kategorija",
            "status": "Statuss"
        }

        widths = {
            "id": 90,
            "title": 240,
            "due": 120,
            "priority": 90,
            "category": 140,
            "status": 120
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Stats
        self.stats_var = tk.StringVar(value="Kopā: 0 | Pabeigti: 0 | Aktīvi: 0")
        ttk.Label(right, textvariable=self.stats_var, font=("Segoe UI", 11, "bold")).pack(pady=10, anchor="w")

    def get_form_data(self):
        title = self.title_var.get().strip()
        desc = self.desc_var.get().strip()
        due = self.due_var.get().strip()
        category = self.category_var.get().strip()
        priority = self.priority_var.get().strip()
        status = self.status_var.get().strip()

        if not title:
            messagebox.showerror("Kļūda", "Nosaukums nevar būt tukšs.")
            return None

        if not valid_date(due):
            messagebox.showerror("Kļūda", "Termiņam jābūt formātā YYYY-MM-DD.")
            return None

        if priority not in {"1", "2", "3"}:
            messagebox.showerror("Kļūda", "Prioritātei jābūt 1, 2 vai 3.")
            return None

        if status not in {"Nav sākts", "Procesā", "Pabeigts"}:
            messagebox.showerror("Kļūda", "Nederīgs statuss.")
            return None

        return {
            "id": uuid4().hex[:8],
            "title": title,
            "description": desc,
            "due_date": due,
            "category": category,
            "priority": int(priority),
            "status": status
        }

    def add_task(self):
        data = self.get_form_data()
        if data is None:
            return

        self.tasks.append(data)
        safe_save_tasks(self.tasks)
        self.refresh_tree()
        self.clear_form()
        messagebox.showinfo("Pievienots", "Uzdevums veiksmīgi pievienots.")

    def update_task(self):
        if not self.selected_task_id:
            messagebox.showwarning("Uzmanību", "Vispirms izvēlies uzdevumu tabulā.")
            return

        title = self.title_var.get().strip()
        desc = self.desc_var.get().strip()
        due = self.due_var.get().strip()
        category = self.category_var.get().strip()
        priority = self.priority_var.get().strip()
        status = self.status_var.get().strip()

        if not title:
            messagebox.showerror("Kļūda", "Nosaukums nevar būt tukšs.")
            return
        if not valid_date(due):
            messagebox.showerror("Kļūda", "Termiņam jābūt formātā YYYY-MM-DD.")
            return

        for task in self.tasks:
            if task["id"] == self.selected_task_id:
                task["title"] = title
                task["description"] = desc
                task["due_date"] = due
                task["category"] = category
                task["priority"] = int(priority)
                task["status"] = status
                break

        safe_save_tasks(self.tasks)
        self.refresh_tree()
        messagebox.showinfo("Atjaunināts", "Uzdevums veiksmīgi atjaunināts.")

    def delete_task(self):
        if not self.selected_task_id:
            messagebox.showwarning("Uzmanību", "Vispirms izvēlies uzdevumu tabulā.")
            return

        confirm = messagebox.askyesno("Apstiprinājums", "Vai tiešām dzēst izvēlēto uzdevumu?")
        if not confirm:
            return

        self.tasks = [t for t in self.tasks if t["id"] != self.selected_task_id]
        safe_save_tasks(self.tasks)
        self.selected_task_id = None
        self.refresh_tree()
        self.clear_form()
        messagebox.showinfo("Dzēsts", "Uzdevums ir dzēsts.")

    def toggle_status(self):
        if not self.selected_task_id:
            messagebox.showwarning("Uzmanību", "Vispirms izvēlies uzdevumu tabulā.")
            return

        for task in self.tasks:
            if task["id"] == self.selected_task_id:
                if task["status"] == "Pabeigts":
                    task["status"] = "Nav sākts"
                elif task["status"] == "Nav sākts":
                    task["status"] = "Procesā"
                else:
                    task["status"] = "Pabeigts"
                self.status_var.set(task["status"])
                break

        safe_save_tasks(self.tasks)
        self.refresh_tree()

    def clear_form(self):
        self.selected_task_id = None
        self.title_var.set("")
        self.desc_var.set("")
        self.due_var.set("")
        self.category_var.set("")
        self.priority_var.set("2")
        self.status_var.set("Nav sākts")
        self.tree.selection_remove(self.tree.selection())

    def clear_filters(self):
        self.search_var.set("")
        self.filter_var.set("Visi")
        self.refresh_tree()

    def on_select(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        values = item["values"]
        if not values:
            return

        task_id = values[0]
        self.selected_task_id = task_id

        for task in self.tasks:
            if task["id"] == task_id:
                self.title_var.set(task.get("title", ""))
                self.desc_var.set(task.get("description", ""))
                self.due_var.set(task.get("due_date", ""))
                self.category_var.set(task.get("category", ""))
                self.priority_var.set(str(task.get("priority", 2)))
                self.status_var.set(task.get("status", "Nav sākts"))
                break

    def refresh_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        query = self.search_var.get().strip().lower()
        selected_status = self.filter_var.get().strip()

        filtered = []
        for task in self.tasks:
            haystack = " ".join([
                str(task.get("title", "")),
                str(task.get("description", "")),
                str(task.get("category", "")),
                str(task.get("status", ""))
            ]).lower()

            if query and query not in haystack:
                continue

            if selected_status != "Visi" and task.get("status") != selected_status:
                continue

            filtered.append(task)

        def sort_key(t):
            due = t.get("due_date", "")
            if due:
                try:
                    return datetime.strptime(due, "%Y-%m-%d")
                except ValueError:
                    pass
            return datetime.max

        filtered.sort(key=sort_key)

        for task in filtered:
            self.tree.insert(
                "",
                "end",
                values=(
                    task.get("id", ""),
                    task.get("title", ""),
                    task.get("due_date", ""),
                    task.get("priority", 2),
                    task.get("category", ""),
                    task.get("status", "")
                )
            )

        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t.get("status") == "Pabeigts")
        active = total - done
        self.stats_var.set(f"Kopā: {total} | Pabeigti: {done} | Aktīvi: {active}")

    def on_close(self):
        safe_save_tasks(self.tasks)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TaskPlannerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()