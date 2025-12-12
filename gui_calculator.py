import tkinter as tk
from tkinter import ttk, messagebox
import json
import sys
import os

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

DATA_FILE = os.path.join(application_path, "salary_data.json")

# Значения по умолчанию для настроек
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
    """Безопасное получение значения из DoubleVar/IntVar.
    Если поле пустое, возвращает default."""
    try:
        return var.get()
    except tk.TclError:
        return default


class ProjectEditor(tk.Toplevel):
    """Окно редактирования проектов сотрудника"""

    def __init__(self, parent, project_data, callback):
        super().__init__(parent)
        self.title("Управление проектами")
        self.geometry("650x450")
        self.project_data = project_data if project_data else []
        self.callback = callback  # Функция обновления данных в главном окне
        self.rows = []

        # Заголовки
        tk.Label(self, text="Название проекта").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self, text="Бюджет ($)").grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self, text="Цели достигнуты?").grid(row=0, column=2, padx=5, pady=5)
        tk.Label(self, text="Действия").grid(row=0, column=3, padx=5, pady=5)

        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=1, column=0, columnspan=4, sticky="nsew")
        self.scrollbar.grid(row=1, column=4, sticky="ns")

        # Кнопки внизу
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=5, pady=10)
        tk.Button(btn_frame, text="Добавить проект", command=self.add_row).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Сохранить и закрыть", command=self.save_and_close, bg="#ddffdd").pack(side=tk.LEFT,
                                                                                                         padx=5)

        # Конфигурация сетки
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Загрузка существующих строк
        for proj in self.project_data:
            self.add_row(proj)

    def add_row(self, data=None):
        if data is None:
            data = {"name": "", "budget": 0.0, "success": False}

        row_idx = len(self.rows)

        name_var = tk.StringVar(value=data.get("name", ""))
        budget_var = tk.DoubleVar(value=data.get("budget", 0.0))
        success_var = tk.BooleanVar(value=data.get("success", False))

        # Виджеты
        e_name = ttk.Entry(self.scrollable_frame, textvariable=name_var, width=30)
        e_name.grid(row=row_idx, column=0, padx=5, pady=2)

        e_budget = ttk.Entry(self.scrollable_frame, textvariable=budget_var, width=15)
        e_budget.grid(row=row_idx, column=1, padx=5, pady=2)

        c_success = ttk.Checkbutton(self.scrollable_frame, variable=success_var)
        c_success.grid(row=row_idx, column=2, padx=5, pady=2)

        btn_del = tk.Button(self.scrollable_frame, text="X", bg="#ffcccc",
                            command=lambda idx=row_idx: self.delete_row(idx))
        btn_del.grid(row=row_idx, column=3, padx=5, pady=2)

        self.rows.append({
            "name": name_var,
            "budget": budget_var,
            "success": success_var,
            "widgets": [e_name, e_budget, c_success, btn_del]
        })

    def delete_row(self, index):
        # Удаляем виджеты визуально
        for w in self.rows[index]["widgets"]:
            w.destroy()
        # Помечаем строку как удаленную
        self.rows[index] = None

    def save_and_close(self):
        new_data = []
        for row in self.rows:
            if row is not None:
                # Используем safe_get для бюджета
                b = safe_get(row["budget"])
                new_data.append({
                    "name": row["name"].get(),
                    "budget": b,
                    "success": row["success"].get()
                })
        self.callback(new_data)
        self.destroy()


class EmployeeRow:
    """Класс, управляющий строкой одного сотрудника"""

    def __init__(self, parent_frame, app_ref, data=None, index=0):
        self.app = app_ref
        self.data = data if data else {}
        self.row_index = index + 1  # +1 для заголовка

        # --- Переменные данных ---
        self.var_name = tk.StringVar(value=self.data.get("name", ""))
        self.var_level = tk.StringVar(value=self.data.get("level", "Intern"))
        self.var_role = tk.StringVar(value=self.data.get("role", "SEO assistant"))
        self.var_base_cur = tk.DoubleVar(value=self.data.get("base_cur", 0.0))
        self.var_base_new = tk.DoubleVar(value=self.data.get("base_new", 0.0))
        self.var_content_base = tk.DoubleVar(value=self.data.get("content_base", 0.0))
        self.var_pages = tk.DoubleVar(value=self.data.get("pages", 0.0))
        self.var_rating = tk.DoubleVar(value=self.data.get("rating", 0.0))
        self.var_mentees = tk.IntVar(value=self.data.get("mentees", 0))
        self.projects = self.data.get("projects", [])  # Список словарей проектов

        # --- Создание виджетов ---
        # Кнопка удаления
        tk.Button(parent_frame, text="X", bg="#ffcccc", width=3, command=self.delete_me).grid(row=self.row_index,
                                                                                              column=0, padx=2, pady=2)

        # Кнопка проектов
        tk.Button(parent_frame, text="Проекты", command=self.open_projects).grid(row=self.row_index, column=1, padx=2,
                                                                                 pady=2)

        # Имя
        ttk.Entry(parent_frame, textvariable=self.var_name, width=15).grid(row=self.row_index, column=2, padx=2)

        # Уровень
        cb_level = ttk.Combobox(parent_frame, textvariable=self.var_level,
                                values=["Intern", "Junior", "Junior+", "Middle", "Middle+"], width=8, state="readonly")
        cb_level.grid(row=self.row_index, column=3, padx=2)
        cb_level.bind("<<ComboboxSelected>>", self.on_level_change)

        # Роль
        ttk.Combobox(parent_frame, textvariable=self.var_role,
                     values=["SEO copywriter", "SEO assistant", "SEO strategist", "R&D specialist"], width=15).grid(
            row=self.row_index, column=4, padx=2)

        # Текущая база
        ttk.Entry(parent_frame, textvariable=self.var_base_cur, width=10).grid(row=self.row_index, column=5, padx=2)

        # Новая база
        ttk.Entry(parent_frame, textvariable=self.var_base_new, width=10).grid(row=self.row_index, column=6, padx=2)

        # Контент база
        self.entry_content_base = ttk.Entry(parent_frame, textvariable=self.var_content_base, width=8)
        self.entry_content_base.grid(row=self.row_index, column=7, padx=2)

        # Страницы
        ttk.Entry(parent_frame, textvariable=self.var_pages, width=8).grid(row=self.row_index, column=8, padx=2)

        # Оценка
        ttk.Entry(parent_frame, textvariable=self.var_rating, width=6).grid(row=self.row_index, column=9, padx=2)

        # Наставничество (кол-во)
        ttk.Entry(parent_frame, textvariable=self.var_mentees, width=6).grid(row=self.row_index, column=10, padx=2)

        # --- Output Labels (вычисляемые поля) ---
        self.lbl_budget = tk.Label(parent_frame, text="0", bg="#f0f0f0", width=8)
        self.lbl_budget.grid(row=self.row_index, column=11, padx=2)

        self.lbl_bonus_content = tk.Label(parent_frame, text="0", bg="#e6f7ff", width=10)
        self.lbl_bonus_content.grid(row=self.row_index, column=12, padx=2)

        self.lbl_bonus_rating = tk.Label(parent_frame, text="0", bg="#e6f7ff", width=10)
        self.lbl_bonus_rating.grid(row=self.row_index, column=13, padx=2)

        self.lbl_bonus_mentor = tk.Label(parent_frame, text="0", bg="#e6f7ff", width=10)
        self.lbl_bonus_mentor.grid(row=self.row_index, column=14, padx=2)

        # Бонус за проекты (Мин / Реал / Макс)
        self.lbl_proj_min = tk.Label(parent_frame, text="0", bg="#fff0f0", width=8)
        self.lbl_proj_min.grid(row=self.row_index, column=15, padx=2)
        self.lbl_proj_real = tk.Label(parent_frame, text="0", bg="#fff0f0", width=8, font=("Arial", 9, "bold"))
        self.lbl_proj_real.grid(row=self.row_index, column=16, padx=2)
        self.lbl_proj_max = tk.Label(parent_frame, text="0", bg="#fff0f0", width=8)
        self.lbl_proj_max.grid(row=self.row_index, column=17, padx=2)

        # Общий бонус (Мин / Реал / Макс)
        self.lbl_total_bonus_min = tk.Label(parent_frame, text="0", bg="#f0fff0", width=8)
        self.lbl_total_bonus_min.grid(row=self.row_index, column=18, padx=2)
        self.lbl_total_bonus_real = tk.Label(parent_frame, text="0", bg="#f0fff0", width=8, font=("Arial", 9, "bold"))
        self.lbl_total_bonus_real.grid(row=self.row_index, column=19, padx=2)
        self.lbl_total_bonus_max = tk.Label(parent_frame, text="0", bg="#f0fff0", width=8)
        self.lbl_total_bonus_max.grid(row=self.row_index, column=20, padx=2)

        # ЗП ТЕКУЩАЯ (Мин / Реал / Макс)
        self.lbl_sal_cur_min = tk.Label(parent_frame, text="0", bg="#e8e8e8", width=9)
        self.lbl_sal_cur_min.grid(row=self.row_index, column=21, padx=2)
        self.lbl_sal_cur_real = tk.Label(parent_frame, text="0", bg="#e8e8e8", width=9, font=("Arial", 9, "bold"))
        self.lbl_sal_cur_real.grid(row=self.row_index, column=22, padx=2)
        self.lbl_sal_cur_max = tk.Label(parent_frame, text="0", bg="#e8e8e8", width=9)
        self.lbl_sal_cur_max.grid(row=self.row_index, column=23, padx=2)

        # ЗП НОВАЯ (Мин / Реал / Макс)
        self.lbl_sal_new_min = tk.Label(parent_frame, text="0", bg="#d9d9d9", width=9)
        self.lbl_sal_new_min.grid(row=self.row_index, column=24, padx=2)
        self.lbl_sal_new_real = tk.Label(parent_frame, text="0", bg="#d9d9d9", width=9, font=("Arial", 9, "bold"))
        self.lbl_sal_new_real.grid(row=self.row_index, column=25, padx=2)
        self.lbl_sal_new_max = tk.Label(parent_frame, text="0", bg="#d9d9d9", width=9)
        self.lbl_sal_new_max.grid(row=self.row_index, column=26, padx=2)

        # Трейсеры (отслеживание изменений)
        self.traces = []
        for var in [self.var_level, self.var_base_cur, self.var_base_new,
                    self.var_content_base, self.var_pages, self.var_rating, self.var_mentees]:
            self.traces.append(var.trace_add("write", lambda *args: self.calculate()))

        # Инициализация состояния UI
        self.on_level_change()
        self.calculate()

    def on_level_change(self, event=None):
        """Блокировка поля Контент-база для Middle"""
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
        """Расчет бонуса за контент на основе переданной базы"""
        lvl = self.var_level.get()

        # Для Middle бонуса нет
        if "Middle" in lvl:
            return 0.0

        # Используем safe_get, чтобы не крашилось на пустых полях
        pages = safe_get(self.var_pages)
        base_cnt = safe_get(self.var_content_base)

        if pages <= base_cnt:
            return 0.0

        extra_pages = pages - base_cnt

        # Получаем коэффициенты из глобальных настроек
        cfg = self.app.settings
        pct = 0.0

        if lvl in ["Intern", "Junior"]:
            pct = safe_get(cfg["pct_intern_junior"])
        elif lvl == "Junior+":
            pct = safe_get(cfg["pct_junior_plus"])

        bonus = extra_pages * (base_salary * (pct / 100.0))
        return bonus

    def calculate(self):
        cfg = self.app.settings

        # 1. Базовые значения (безопасно)
        base_cur = safe_get(self.var_base_cur)
        base_new = safe_get(self.var_base_new)

        # 2. Оценка менеджера
        rating = safe_get(self.var_rating)

        bonus_rating = 0.0
        # Безопасное получение настроек
        br_mid = safe_get(cfg["bonus_rating_mid"])
        br_high = safe_get(cfg["bonus_rating_high"])

        if 4.50 <= rating <= 4.99:
            bonus_rating = br_mid
        elif rating >= 5.00:
            bonus_rating = br_high

        # 3. Наставничество
        mentees = safe_get(self.var_mentees)
        b_mentor_val = safe_get(cfg["bonus_mentoring"])
        bonus_mentor = mentees * b_mentor_val

        # 4. Проекты
        total_budget = sum(p.get("budget", 0) for p in self.projects)

        c_fail = safe_get(cfg["coeff_fail"])
        c_succ = safe_get(cfg["coeff_success"])

        proj_bonus_min = total_budget * c_fail
        proj_bonus_max = total_budget * c_succ

        proj_bonus_real = 0.0
        for p in self.projects:
            bdg = p.get("budget", 0)
            is_ok = p.get("success", False)
            mult = c_succ if is_ok else c_fail
            proj_bonus_real += bdg * mult

        # 5. Контент бонус (Отображаем расчет по ТЕКУЩЕЙ базе в таблице)
        content_bonus_cur = self.get_content_bonus(base_cur)
        # Для расчета итоговой ЗП по новой базе, нужен пересчет
        content_bonus_new = self.get_content_bonus(base_new)

        # --- Обновление лейблов ---
        self.lbl_budget.config(text=f"${total_budget:,.0f}")
        self.lbl_bonus_content.config(text=f"{content_bonus_cur:,.0f}")
        self.lbl_bonus_rating.config(text=f"{bonus_rating:,.0f}")
        self.lbl_bonus_mentor.config(text=f"{bonus_mentor:,.0f}")

        self.lbl_proj_min.config(text=f"{proj_bonus_min:,.0f}")
        self.lbl_proj_real.config(text=f"{proj_bonus_real:,.0f}")
        self.lbl_proj_max.config(text=f"{proj_bonus_max:,.0f}")

        # ОБЩИЙ БОНУС
        def calc_total_bonus(proj_val, c_bonus):
            return c_bonus + bonus_rating + bonus_mentor + proj_val

        tb_min = calc_total_bonus(proj_bonus_min, content_bonus_cur)
        tb_real = calc_total_bonus(proj_bonus_real, content_bonus_cur)
        tb_max = calc_total_bonus(proj_bonus_max, content_bonus_cur)

        self.lbl_total_bonus_min.config(text=f"{tb_min:,.0f}")
        self.lbl_total_bonus_real.config(text=f"{tb_real:,.0f}")
        self.lbl_total_bonus_max.config(text=f"{tb_max:,.0f}")

        # ИТОГОВАЯ ЗП ТЕКУЩАЯ
        self.lbl_sal_cur_min.config(text=f"{base_cur + tb_min:,.0f}")
        self.lbl_sal_cur_real.config(text=f"{base_cur + tb_real:,.0f}")
        self.lbl_sal_cur_max.config(text=f"{base_cur + tb_max:,.0f}")

        # ИТОГОВАЯ ЗП НОВАЯ
        tb_min_new = calc_total_bonus(proj_bonus_min, content_bonus_new)
        tb_real_new = calc_total_bonus(proj_bonus_real, content_bonus_new)
        tb_max_new = calc_total_bonus(proj_bonus_max, content_bonus_new)

        self.lbl_sal_new_min.config(text=f"{base_new + tb_min_new:,.0f}")
        self.lbl_sal_new_real.config(text=f"{base_new + tb_real_new:,.0f}")
        self.lbl_sal_new_max.config(text=f"{base_new + tb_max_new:,.0f}")

    def delete_me(self):
        self.app.delete_employee(self)

    def to_dict(self):
        # Экспорт данных для сохранения (БЕЗОПАСНЫЙ)
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

        self.employees = []  # Список объектов EmployeeRow
        self.settings = {}  # Словарь DoubleVar

        # 1. Панель настроек
        self.create_settings_panel()

        # 2. Основная таблица (Canvas + Scrollbars)
        self.create_main_table()

        # 3. Кнопка добавления
        tk.Button(self.root, text="+ Добавить сотрудника", font=("Arial", 12, "bold"),
                  command=self.add_employee, bg="#e0ffe0", pady=10).pack(fill=tk.X, side=tk.BOTTOM)

        # 4. Загрузка данных
        self.load_data()

        # При закрытии сохраняем
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_settings_panel(self):
        frame = tk.LabelFrame(self.root, text="Глобальные настройки и коэффициенты", padx=10, pady=10)
        frame.pack(fill=tk.X, padx=10, pady=5)

        # Вспомогательная функция для создания инпутов
        def add_setting(key, label_text, row, col):
            tk.Label(frame, text=label_text).grid(row=row, column=col, sticky="e", padx=5)
            var = tk.DoubleVar(value=DEFAULT_SETTINGS[key])
            entry = ttk.Entry(frame, textvariable=var, width=10)
            entry.grid(row=row, column=col + 1, sticky="w", padx=5)
            # При изменении настроек пересчитываем всех сотрудников
            var.trace_add("write", lambda *args: self.recalc_all())
            self.settings[key] = var

        add_setting("coeff_fail", "Цели не достигнуты:", 0, 0)
        add_setting("coeff_success", "Цели достигнуты:", 0, 2)

        add_setting("pct_intern_junior", "% от базы за контент (Int/Jun):", 0, 4)
        add_setting("pct_junior_plus", "% от базы за контент (Jun+):", 0, 6)

        add_setting("bonus_rating_mid", "Бонус, оценка 4.5-4.99:", 1, 0)
        add_setting("bonus_rating_high", "Бонус, оценка 5.00:", 1, 2)
        add_setting("bonus_mentoring", "Бонус за наставничество (чел):", 1, 4)

    def create_main_table(self):
        # Контейнер для канваса и скроллов
        container = tk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Скроллбары
        vsb = ttk.Scrollbar(container, orient="vertical")
        hsb = ttk.Scrollbar(container, orient="horizontal")

        self.canvas = tk.Canvas(container, yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.config(command=self.canvas.yview)
        hsb.config(command=self.canvas.xview)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Фрейм внутри канваса
        self.table_frame = tk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.table_frame, anchor="nw")

        # Привязка событий для обновления скролла
        self.table_frame.bind("<Configure>", self.on_frame_configure)

        # Заголовки таблицы
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

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_employee(self, data=None):
        emp = EmployeeRow(self.table_frame, self, data, index=len(self.employees))
        self.employees.append(emp)

    def delete_employee(self, emp_obj):
        if messagebox.askyesno("Подтверждение", "Удалить сотрудника?"):
            self.employees.remove(emp_obj)
            self.refresh_table_ui()

    def refresh_table_ui(self):
        # Очистка фрейма
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        # Перерисовка заголовков
        self.create_main_table()
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

        # Сохраняем текущие данные
        current_data = [e.to_dict() for e in self.employees]
        self.employees = []

        # Создаем заново
        for d in current_data:
            self.add_employee(d)

    def recalc_all(self):
        for emp in self.employees:
            emp.calculate()

    def save_data(self):
        data = {
            "settings": {k: safe_get(v) for k, v in self.settings.items()},
            "employees": [e.to_dict() for e in self.employees]
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Загрузка настроек
            if "settings" in data:
                for k, v in data["settings"].items():
                    if k in self.settings:
                        self.settings[k].set(v)

            # Загрузка сотрудников
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