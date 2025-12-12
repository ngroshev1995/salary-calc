import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys

# --- НАСТРОЙКА ПУТЕЙ (Для Windows и Mac) ---
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

DATA_FILE = os.path.join(application_path, "salary_data.json")

# --- КОНСТАНТЫ ---
DEFAULT_SETTINGS = {
    "coeff_fail": 0.18,
    "coeff_success": 0.25,
    "pct_intern_junior": 1.5,
    "pct_junior_plus": 0.3,
    "bonus_rating_mid": 1250,  # 4.50 - 4.99
    "bonus_rating_high": 2500,  # 5.00
    "bonus_mentoring": 2500
}


def safe_get(var, default=0.0):
    """Безопасное получение значения из DoubleVar/IntVar."""
    try:
        val = var.get()
        if val == "": return default
        return val
    except tk.TclError:
        return default


class ProjectEditor(tk.Toplevel):
    """Окно редактирования проектов"""

    def __init__(self, parent, project_data, callback):
        super().__init__(parent)
        self.title("Управление проектами")
        self.geometry("650x450")
        self.project_data = project_data if project_data else []
        self.callback = callback
        self.rows = []

        tk.Label(self, text="Название проекта").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self, text="Бюджет ($)").grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self, text="Цели достигнуты?").grid(row=0, column=2, padx=5, pady=5)
        tk.Label(self, text="Действия").grid(row=0, column=3, padx=5, pady=5)

        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=1, column=0, columnspan=4, sticky="nsew")
        self.scrollbar.grid(row=1, column=4, sticky="ns")

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=5, pady=10)
        tk.Button(btn_frame, text="Добавить проект", command=self.add_row).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Сохранить и закрыть", command=self.save_and_close, bg="#ddffdd").pack(side=tk.LEFT,
                                                                                                         padx=5)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        for proj in self.project_data:
            self.add_row(proj)

    def add_row(self, data=None):
        if data is None: data = {"name": "", "budget": 0.0, "success": False}
        row_idx = len(self.rows)
        name_var = tk.StringVar(value=data.get("name", ""))
        budget_var = tk.DoubleVar(value=data.get("budget", 0.0))
        success_var = tk.BooleanVar(value=data.get("success", False))

        e_name = ttk.Entry(self.scrollable_frame, textvariable=name_var, width=30)
        e_name.grid(row=row_idx, column=0, padx=5, pady=2)
        e_budget = ttk.Entry(self.scrollable_frame, textvariable=budget_var, width=15)
        e_budget.grid(row=row_idx, column=1, padx=5, pady=2)
        c_success = ttk.Checkbutton(self.scrollable_frame, variable=success_var)
        c_success.grid(row=row_idx, column=2, padx=5, pady=2)
        btn_del = tk.Button(self.scrollable_frame, text="X", bg="#ffcccc",
                            command=lambda idx=row_idx: self.delete_row(idx))
        btn_del.grid(row=row_idx, column=3, padx=5, pady=2)

        self.rows.append({"name": name_var, "budget": budget_var, "success": success_var,
                          "widgets": [e_name, e_budget, c_success, btn_del]})

    def delete_row(self, index):
        for w in self.rows[index]["widgets"]: w.destroy()
        self.rows[index] = None

    def save_and_close(self):
        new_data = []
        for row in self.rows:
            if row is not None:
                new_data.append({
                    "name": row["name"].get(),
                    "budget": safe_get(row["budget"]),
                    "success": row["success"].get()
                })
        self.callback(new_data)
        self.destroy()


class EmployeeRow:
    """Строка сотрудника"""

    def __init__(self, parent_frame, app_ref, data=None, index=0):
        self.app = app_ref
        self.data = data if data else {}
        self.row_index = index + 1

        # Данные ввода
        self.var_name = tk.StringVar(value=self.data.get("name", ""))
        self.var_level = tk.StringVar(value=self.data.get("level", "Intern"))
        self.var_role = tk.StringVar(value=self.data.get("role", "SEO assistant"))
        self.var_base_cur = tk.DoubleVar(value=self.data.get("base_cur", 0.0))
        self.var_base_new = tk.DoubleVar(value=self.data.get("base_new", 0.0))
        self.var_content_base = tk.DoubleVar(value=self.data.get("content_base", 0.0))
        self.var_pages = tk.DoubleVar(value=self.data.get("pages", 0.0))
        self.var_rating = tk.DoubleVar(value=self.data.get("rating", 0.0))
        self.var_mentees = tk.IntVar(value=self.data.get("mentees", 0))
        self.projects = self.data.get("projects", [])

        # Переменные для хранения результатов
        self.res_budget = 0.0
        self.res_cnt_bonus = 0.0
        self.res_rtg_bonus = 0.0
        self.res_mnt_bonus = 0.0
        self.res_p_min = 0.0
        self.res_p_real = 0.0
        self.res_p_max = 0.0
        self.res_tb_min = 0.0
        self.res_tb_real = 0.0
        self.res_tb_max = 0.0
        self.res_sc_min = 0.0
        self.res_sc_real = 0.0
        self.res_sc_max = 0.0
        self.res_sn_min = 0.0
        self.res_sn_real = 0.0
        self.res_sn_max = 0.0

        # Виджеты ввода
        tk.Button(parent_frame, text="X", bg="#ffcccc", width=3, command=self.delete_me).grid(row=self.row_index,
                                                                                              column=0, padx=2, pady=2)
        tk.Button(parent_frame, text="Проекты", command=self.open_projects).grid(row=self.row_index, column=1, padx=2,
                                                                                 pady=2)
        ttk.Entry(parent_frame, textvariable=self.var_name, width=15).grid(row=self.row_index, column=2, padx=2)

        cb_level = ttk.Combobox(parent_frame, textvariable=self.var_level,
                                values=["Intern", "Junior", "Junior+", "Middle", "Middle+"], width=8, state="readonly")
        cb_level.grid(row=self.row_index, column=3, padx=2)
        cb_level.bind("<<ComboboxSelected>>", self.on_level_change)

        ttk.Combobox(parent_frame, textvariable=self.var_role,
                     values=["SEO copywriter", "SEO assistant", "SEO strategist", "R&D specialist"], width=15).grid(
            row=self.row_index, column=4, padx=2)
        ttk.Entry(parent_frame, textvariable=self.var_base_cur, width=10).grid(row=self.row_index, column=5, padx=2)
        ttk.Entry(parent_frame, textvariable=self.var_base_new, width=10).grid(row=self.row_index, column=6, padx=2)

        self.entry_content_base = ttk.Entry(parent_frame, textvariable=self.var_content_base, width=8)
        self.entry_content_base.grid(row=self.row_index, column=7, padx=2)

        ttk.Entry(parent_frame, textvariable=self.var_pages, width=8).grid(row=self.row_index, column=8, padx=2)
        ttk.Entry(parent_frame, textvariable=self.var_rating, width=6).grid(row=self.row_index, column=9, padx=2)
        ttk.Entry(parent_frame, textvariable=self.var_mentees, width=6).grid(row=self.row_index, column=10, padx=2)

        # Лейблы результатов
        self.lbl_budget = tk.Label(parent_frame, text="0", bg="#f0f0f0", width=8)
        self.lbl_budget.grid(row=self.row_index, column=11, padx=2)
        self.lbl_bonus_content = tk.Label(parent_frame, text="0", bg="#e6f7ff", width=10)
        self.lbl_bonus_content.grid(row=self.row_index, column=12, padx=2)
        self.lbl_bonus_rating = tk.Label(parent_frame, text="0", bg="#e6f7ff", width=10)
        self.lbl_bonus_rating.grid(row=self.row_index, column=13, padx=2)
        self.lbl_bonus_mentor = tk.Label(parent_frame, text="0", bg="#e6f7ff", width=10)
        self.lbl_bonus_mentor.grid(row=self.row_index, column=14, padx=2)

        self.lbl_proj_min = tk.Label(parent_frame, text="0", bg="#fff0f0", width=8)
        self.lbl_proj_min.grid(row=self.row_index, column=15, padx=2)
        self.lbl_proj_real = tk.Label(parent_frame, text="0", bg="#fff0f0", width=8, font=("Arial", 9, "bold"))
        self.lbl_proj_real.grid(row=self.row_index, column=16, padx=2)
        self.lbl_proj_max = tk.Label(parent_frame, text="0", bg="#fff0f0", width=8)
        self.lbl_proj_max.grid(row=self.row_index, column=17, padx=2)

        self.lbl_total_bonus_min = tk.Label(parent_frame, text="0", bg="#f0fff0", width=8)
        self.lbl_total_bonus_min.grid(row=self.row_index, column=18, padx=2)
        self.lbl_total_bonus_real = tk.Label(parent_frame, text="0", bg="#f0fff0", width=8, font=("Arial", 9, "bold"))
        self.lbl_total_bonus_real.grid(row=self.row_index, column=19, padx=2)
        self.lbl_total_bonus_max = tk.Label(parent_frame, text="0", bg="#f0fff0", width=8)
        self.lbl_total_bonus_max.grid(row=self.row_index, column=20, padx=2)

        self.lbl_sal_cur_min = tk.Label(parent_frame, text="0", bg="#e8e8e8", width=9)
        self.lbl_sal_cur_min.grid(row=self.row_index, column=21, padx=2)
        self.lbl_sal_cur_real = tk.Label(parent_frame, text="0", bg="#e8e8e8", width=9, font=("Arial", 9, "bold"))
        self.lbl_sal_cur_real.grid(row=self.row_index, column=22, padx=2)
        self.lbl_sal_cur_max = tk.Label(parent_frame, text="0", bg="#e8e8e8", width=9)
        self.lbl_sal_cur_max.grid(row=self.row_index, column=23, padx=2)

        self.lbl_sal_new_min = tk.Label(parent_frame, text="0", bg="#d9d9d9", width=9)
        self.lbl_sal_new_min.grid(row=self.row_index, column=24, padx=2)
        self.lbl_sal_new_real = tk.Label(parent_frame, text="0", bg="#d9d9d9", width=9, font=("Arial", 9, "bold"))
        self.lbl_sal_new_real.grid(row=self.row_index, column=25, padx=2)
        self.lbl_sal_new_max = tk.Label(parent_frame, text="0", bg="#d9d9d9", width=9)
        self.lbl_sal_new_max.grid(row=self.row_index, column=26, padx=2)

        self.traces = []
        for var in [self.var_level, self.var_base_cur, self.var_base_new, self.var_content_base, self.var_pages,
                    self.var_rating, self.var_mentees]:
            self.traces.append(var.trace_add("write", lambda *args: self.calculate()))

        self.on_level_change()
        self.calculate()

    def on_level_change(self, event=None):
        lvl = self.var_level.get()
        if "Middle" in lvl:
            self.entry_content_base.config(state="disabled")
        else:
            self.entry_content_base.config(state="normal")
        self.calculate()

    def open_projects(self):
        ProjectEditor(self.app.root, self.projects, self.update_projects)

    def update_projects(self, new_projects):
        self.projects = new_projects
        self.calculate()
        self.app.save_data()

    def get_content_bonus(self, base_salary):
        lvl = self.var_level.get()
        if "Middle" in lvl: return 0.0
        pages = safe_get(self.var_pages)
        base_cnt = safe_get(self.var_content_base)
        if pages <= base_cnt: return 0.0

        cfg = self.app.settings
        pct = 0.0
        if lvl in ["Intern", "Junior"]:
            pct = safe_get(cfg["pct_intern_junior"])
        elif lvl == "Junior+":
            pct = safe_get(cfg["pct_junior_plus"])
        return (pages - base_cnt) * (base_salary * (pct / 100.0))

    def calculate(self):
        cfg = self.app.settings
        base_cur = safe_get(self.var_base_cur)
        base_new = safe_get(self.var_base_new)
        rating = safe_get(self.var_rating)

        bonus_rating = 0.0
        if 4.50 <= rating <= 4.99:
            bonus_rating = safe_get(cfg["bonus_rating_mid"])
        elif rating >= 5.00:
            bonus_rating = safe_get(cfg["bonus_rating_high"])

        mentees = safe_get(self.var_mentees)
        bonus_mentor = mentees * safe_get(cfg["bonus_mentoring"])

        total_budget = sum(p.get("budget", 0) for p in self.projects)
        c_fail = safe_get(cfg["coeff_fail"])
        c_succ = safe_get(cfg["coeff_success"])

        proj_min = total_budget * c_fail
        proj_max = total_budget * c_succ
        proj_real = 0.0
        for p in self.projects:
            proj_real += p.get("budget", 0) * (c_succ if p.get("success", False) else c_fail)

        content_bonus_cur = self.get_content_bonus(base_cur)
        content_bonus_new = self.get_content_bonus(base_new)

        # Сохранение результатов в переменные
        self.res_budget = total_budget
        self.res_cnt_bonus = content_bonus_cur
        self.res_rtg_bonus = bonus_rating
        self.res_mnt_bonus = bonus_mentor
        self.res_p_min = proj_min
        self.res_p_real = proj_real
        self.res_p_max = proj_max

        self.res_tb_min = content_bonus_cur + bonus_rating + bonus_mentor + proj_min
        self.res_tb_real = content_bonus_cur + bonus_rating + bonus_mentor + proj_real
        self.res_tb_max = content_bonus_cur + bonus_rating + bonus_mentor + proj_max

        self.res_sc_min = base_cur + self.res_tb_min
        self.res_sc_real = base_cur + self.res_tb_real
        self.res_sc_max = base_cur + self.res_tb_max

        # Для новой базы пересчитываем бонус
        tb_min_new = content_bonus_new + bonus_rating + bonus_mentor + proj_min
        tb_real_new = content_bonus_new + bonus_rating + bonus_mentor + proj_real
        tb_max_new = content_bonus_new + bonus_rating + bonus_mentor + proj_max

        self.res_sn_min = base_new + tb_min_new
        self.res_sn_real = base_new + tb_real_new
        self.res_sn_max = base_new + tb_max_new

        # Обновление UI
        self.lbl_budget.config(text=f"${self.res_budget:,.0f}")
        self.lbl_bonus_content.config(text=f"{self.res_cnt_bonus:,.0f}")
        self.lbl_bonus_rating.config(text=f"{self.res_rtg_bonus:,.0f}")
        self.lbl_bonus_mentor.config(text=f"{self.res_mnt_bonus:,.0f}")

        self.lbl_proj_min.config(text=f"{self.res_p_min:,.0f}")
        self.lbl_proj_real.config(text=f"{self.res_p_real:,.0f}")
        self.lbl_proj_max.config(text=f"{self.res_p_max:,.0f}")

        self.lbl_total_bonus_min.config(text=f"{self.res_tb_min:,.0f}")
        self.lbl_total_bonus_real.config(text=f"{self.res_tb_real:,.0f}")
        self.lbl_total_bonus_max.config(text=f"{self.res_tb_max:,.0f}")

        self.lbl_sal_cur_min.config(text=f"{self.res_sc_min:,.0f}")
        self.lbl_sal_cur_real.config(text=f"{self.res_sc_real:,.0f}")
        self.lbl_sal_cur_max.config(text=f"{self.res_sc_max:,.0f}")

        self.lbl_sal_new_min.config(text=f"{self.res_sn_min:,.0f}")
        self.lbl_sal_new_real.config(text=f"{self.res_sn_real:,.0f}")
        self.lbl_sal_new_max.config(text=f"{self.res_sn_max:,.0f}")

        # Дергаем пересчет итогов в приложении
        self.app.update_totals_trigger()

    def delete_me(self):
        self.app.delete_employee(self)

    def to_dict(self):
        return {
            "name": self.var_name.get(),
            "level": self.var_level.get(),
            "role": self.var_role.get(),
            "base_cur": safe_get(self.var_base_cur),
            "base_new": safe_get(self.var_base_new),
            "content_base": safe_get(self.var_content_base),
            "pages": safe_get(self.var_pages),
            "rating": safe_get(self.var_rating),
            "mentees": safe_get(self.var_mentees),
            "projects": self.projects
        }


class SalaryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Калькулятор Зарплат и Бонусов")
        self.root.geometry("1400x800")
        self.employees = []
        self.settings = {}
        self.total_labels = {}

        self.create_settings_panel()
        self.create_main_table()

        tk.Button(self.root, text="+ Добавить сотрудника", font=("Arial", 12, "bold"),
                  command=self.add_employee, bg="#e0ffe0", pady=10).pack(fill=tk.X, side=tk.BOTTOM)

        self.load_data()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_settings_panel(self):
        frame = tk.LabelFrame(self.root, text="Глобальные настройки и коэффициенты", padx=10, pady=10)
        frame.pack(fill=tk.X, padx=10, pady=5)

        def add_setting(key, label_text, row, col):
            tk.Label(frame, text=label_text).grid(row=row, column=col, sticky="e", padx=5)
            var = tk.DoubleVar(value=DEFAULT_SETTINGS[key])
            entry = ttk.Entry(frame, textvariable=var, width=10)
            entry.grid(row=row, column=col + 1, sticky="w", padx=5)
            var.trace_add("write", lambda *args: self.recalc_all())
            self.settings[key] = var

        add_setting("coeff_fail", "Цели достигнуты:", 0, 0)
        add_setting("coeff_success", "Цели не достигнуты:", 0, 2)
        add_setting("pct_intern_junior", "% от базы за экстра контент (Int/Jun):", 0, 4)
        add_setting("pct_junior_plus", "% от базы за экстра контент (Jun+):", 0, 6)
        add_setting("bonus_rating_mid", "Бонус, оценка 4.5-4.99:", 1, 0)
        add_setting("bonus_rating_high", "Бонус, оценка 5.00:", 1, 2)
        add_setting("bonus_mentoring", "Бонус за наставничество (чел):", 1, 4)

    def create_main_table(self):
        container = tk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        vsb = ttk.Scrollbar(container, orient="vertical")
        hsb = ttk.Scrollbar(container, orient="horizontal")
        self.canvas = tk.Canvas(container, yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.config(command=self.canvas.yview)
        hsb.config(command=self.canvas.xview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.table_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.table_frame, anchor="nw")
        self.table_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.draw_headers()
        # draw_total_row вызывается только после добавления сотрудников

    def draw_headers(self):
        headers = [
            "Удал", "Проекты", "ФИО", "Уровень", "Роль",
            "Тек. База", "Нов. База", "Конт. План", "Стр. Факт",
            "Оценка", "Наставник", "Бюджет ($)", "Конт. Бон",
            "Рейт. Бон", "Наст. Бон",
            "П. Мин", "П. Реал", "П. Макс",
            "Бон. Мин", "Бон. Реал", "Бон. Макс",
            "ЗП Тек Мин", "ЗП Тек Реал", "ЗП Тек Макс",
            "ЗП Нов Мин", "ЗП Нов Реал", "ЗП Нов Макс"
        ]
        for i, h in enumerate(headers):
            lbl = tk.Label(self.table_frame, text=h, font=("Arial", 9, "bold"), bg="#ddd", relief="raised", padx=5)
            lbl.grid(row=0, column=i, sticky="nsew", ipady=5)

    def draw_total_row(self):
        # Удаляем старые лейблы итогов
        for widget in self.total_labels.values():
            widget.destroy()
        self.total_labels = {}

        # Рассчитываем номер строки: кол-во сотрудников + 1 (так как есть заголовок)
        # +1 чтобы быть ПОД последним сотрудником
        row_idx = len(self.employees) + 1

        # Рисуем
        t_title = tk.Label(self.table_frame, text="ИТОГО:", font=("Arial", 10, "bold"), bg="#444", fg="white")
        t_title.grid(row=row_idx, column=0, columnspan=11, sticky="nsew", padx=2, pady=5)
        self.total_labels['title'] = t_title

        cols = range(11, 27)
        for c in cols:
            lbl = tk.Label(self.table_frame, text="0", font=("Arial", 9, "bold"), bg="#444", fg="white")
            lbl.grid(row=row_idx, column=c, sticky="nsew", padx=2, pady=5)
            self.total_labels[c] = lbl

        self.recalc_totals()

    def add_employee(self, data=None):
        emp = EmployeeRow(self.table_frame, self, data, index=len(self.employees))
        self.employees.append(emp)
        # После добавления сотрудника перерисовываем строку итогов ниже
        self.draw_total_row()

    def delete_employee(self, emp_obj):
        if messagebox.askyesno("Подтверждение", "Удалить сотрудника?"):
            self.employees.remove(emp_obj)
            self.refresh_table_ui()

    def refresh_table_ui(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        self.total_labels = {}
        self.draw_headers()

        current_data = [e.to_dict() for e in self.employees]
        self.employees = []
        for d in current_data:
            self.add_employee(d)  # внутри вызывается draw_total_row

    def recalc_all(self):
        for emp in self.employees:
            emp.calculate()

    def update_totals_trigger(self):
        self.recalc_totals()

    def recalc_totals(self):
        if not self.total_labels: return

        sums = {i: 0.0 for i in range(11, 27)}

        for emp in self.employees:
            sums[11] += emp.res_budget
            sums[12] += emp.res_cnt_bonus
            sums[13] += emp.res_rtg_bonus
            sums[14] += emp.res_mnt_bonus
            sums[15] += emp.res_p_min
            sums[16] += emp.res_p_real
            sums[17] += emp.res_p_max
            sums[18] += emp.res_tb_min
            sums[19] += emp.res_tb_real
            sums[20] += emp.res_tb_max
            sums[21] += emp.res_sc_min
            sums[22] += emp.res_sc_real
            sums[23] += emp.res_sc_max
            sums[24] += emp.res_sn_min
            sums[25] += emp.res_sn_real
            sums[26] += emp.res_sn_max

        for col, val in sums.items():
            if col in self.total_labels:
                prefix = "$" if col == 11 else ""
                self.total_labels[col].config(text=f"{prefix}{val:,.0f}")

    def save_data(self):
        data = {
            "settings": {k: safe_get(v) for k, v in self.settings.items()},
            "employees": [e.to_dict() for e in self.employees]
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_data(self):
        if not os.path.exists(DATA_FILE): return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "settings" in data:
                for k, v in data["settings"].items():
                    if k in self.settings: self.settings[k].set(v)
            if "employees" in data:
                for emp_data in data["employees"]:
                    self.add_employee(emp_data)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")

    def on_close(self):
        self.save_data()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SalaryApp(root)
    root.mainloop()