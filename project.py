import requests
import csv
import customtkinter as ctk
from tkinter import ttk
import threading

# ── Подключи свой модуль ──────────────────────
# from saits import saits
# ─────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class JobSearchApp(ctk.CTk):
    """
    GUI-приложение для поиска вакансий.

    Подключается к классу saits и отображает результаты
    в таблице с фильтрацией по зарплате и городу.

    Usage:
        app = JobSearchApp(backend=saits())
        app.mainloop()
    """

    def __init__(self, backend=None):
        """
        Initialize the application window.

        Args:
            backend: экземпляр класса saits. Если None,
                     используются тестовые данные.
        """
        super().__init__()

        self.backend = backend
        self.all_jobs: list = []  # все найденные вакансии (до фильтрации)

        self.title("Поиск вакансий")
        self.geometry("1100x700")
        self.minsize(800, 550)

        self._build_ui()

    # ──────────────────────────────────────────
    #  Построение интерфейса
    # ──────────────────────────────────────────

    def _build_ui(self):
        """Build and arrange all UI widgets."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_top_bar()
        self._build_filter_bar()
        self._build_table()
        self._build_status_bar()

    def _build_top_bar(self):
        """Build the top search bar."""
        top = ctk.CTkFrame(self, corner_radius=0, fg_color="#1a1a1a")
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top, text="  Поиск вакансий",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=15)

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            top,
            textvariable=self.search_var,
            placeholder_text="Введите должность, например: kokk, programmeerija...",
            height=40,
            font=ctk.CTkFont(size=13),
            corner_radius=8,
        )
        self.search_entry.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        self.search_entry.bind("<Return>", lambda e: self._start_search())

        self.search_btn = ctk.CTkButton(
            top, text="Найти", width=110, height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8,
            command=self._start_search,
        )
        self.search_btn.grid(row=0, column=2, padx=(0, 20), pady=15)

    def _build_filter_bar(self):
        """Build the filter controls bar."""
        bar = ctk.CTkFrame(self, corner_radius=0, fg_color="#141414")
        bar.grid(row=1, column=0, sticky="ew")
        bar.grid_columnconfigure(6, weight=1)

        label_font = ctk.CTkFont(size=11)
        entry_width = 100

        # ── ЗП от ──
        ctk.CTkLabel(bar, text="ЗП от:", font=label_font, text_color="#aaa").grid(
            row=0, column=0, padx=(16, 4), pady=10)
        self.salary_from_var = ctk.StringVar()
        ctk.CTkEntry(bar, textvariable=self.salary_from_var,
                     placeholder_text="0", width=entry_width, height=32,
                     corner_radius=6).grid(row=0, column=1, padx=4, pady=10)

        # ── ЗП до ──
        ctk.CTkLabel(bar, text="до:", font=label_font, text_color="#aaa").grid(
            row=0, column=2, padx=4, pady=10)
        self.salary_to_var = ctk.StringVar()
        ctk.CTkEntry(bar, textvariable=self.salary_to_var,
                     placeholder_text="без лимита", width=entry_width, height=32,
                     corner_radius=6).grid(row=0, column=3, padx=4, pady=10)

        # ── Город ──
        ctk.CTkLabel(bar, text="Город:", font=label_font, text_color="#aaa").grid(
            row=0, column=4, padx=(16, 4), pady=10)
        self.city_var = ctk.StringVar()
        ctk.CTkEntry(bar, textvariable=self.city_var,
                     placeholder_text="Tallinn, Tartu...", width=140, height=32,
                     corner_radius=6).grid(row=0, column=5, padx=4, pady=10)

        # ── Кнопка фильтра ──
        ctk.CTkButton(
            bar, text="Применить фильтр", height=32, width=160,
            font=ctk.CTkFont(size=12),
            corner_radius=6,
            command=self._apply_filters,
        ).grid(row=0, column=6, padx=12, pady=10, sticky="w")

        # ── Сброс ──
        ctk.CTkButton(
            bar, text="Сброс", height=32, width=80,
            font=ctk.CTkFont(size=12),
            fg_color="transparent", border_width=1,
            corner_radius=6,
            command=self._reset_filters,
        ).grid(row=0, column=7, padx=(0, 16), pady=10)

    def _build_table(self):
        """Build the results table with scrollbars."""
        frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#0f0f0f")
        frame.grid(row=2, column=0, sticky="nsew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Jobs.Treeview",
                        background="#181818",
                        foreground="#e0e0e0",
                        fieldbackground="#181818",
                        rowheight=30,
                        font=("Consolas", 10))
        style.configure("Jobs.Treeview.Heading",
                        background="#222222",
                        foreground="#6fcf00",
                        font=("Consolas", 10, "bold"),
                        relief="flat")
        style.map("Jobs.Treeview",
                  background=[("selected", "#2a5500")],
                  foreground=[("selected", "#ffffff")])

        columns = ("too", "company", "city", "salary", "link")
        self.tree = ttk.Treeview(frame, columns=columns,
                                 show="headings", style="Jobs.Treeview")

        self.tree.heading("too",     text="Должность")
        self.tree.heading("company", text="Компания")
        self.tree.heading("city",    text="Город")
        self.tree.heading("salary",  text="Зарплата (€)")
        self.tree.heading("link",    text="Ссылка")

        self.tree.column("too",     width=250, minwidth=150)
        self.tree.column("company", width=200, minwidth=120)
        self.tree.column("city",    width=120, minwidth=80)
        self.tree.column("salary",  width=130, minwidth=90)
        self.tree.column("link",    width=350, minwidth=200)

        vsb = ttk.Scrollbar(frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.tag_configure("odd",  background="#181818")
        self.tree.tag_configure("even", background="#1f1f1f")

    def _build_status_bar(self):
        """Build the bottom status bar."""
        bar = ctk.CTkFrame(self, corner_radius=0, fg_color="#111111", height=28)
        bar.grid(row=3, column=0, sticky="ew")
        bar.grid_propagate(False)

        self.status_var = ctk.StringVar(value="Введите запрос и нажмите «Найти»")
        ctk.CTkLabel(bar, textvariable=self.status_var,
                     font=ctk.CTkFont(size=11),
                     text_color="#777777").pack(side="left", padx=12)

        self.progress = ctk.CTkProgressBar(bar, width=160, height=8,
                                           corner_radius=4)
        self.progress.pack(side="right", padx=12, pady=8)
        self.progress.set(0)

    # ──────────────────────────────────────────
    #  Логика поиска
    # ──────────────────────────────────────────

    def _start_search(self):
        """Start job search in a background thread."""
        query = self.search_var.get().strip()
        if not query:
            self._set_status("Введите ключевое слово")
            return

        self.search_btn.configure(state="disabled", text="Поиск...")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self._set_status(f"Ищем вакансии: «{query}»...")
        self._clear_table()

        thread = threading.Thread(target=self._fetch_jobs, args=(query,), daemon=True)
        thread.start()

    def _fetch_jobs(self, query: str):
        """
        Fetch jobs from backend in a separate thread.

        Args:
            query: ключевое слово для поиска
        """
        try:
            if self.backend:
                jobs = self._collect_jobs(query)
            else:
                jobs = self._demo_jobs(query)

            self.all_jobs = jobs
            self.after(0, self._on_results_ready)

        except Exception as e:
            self.after(0, lambda: self._set_status(f"Ошибка: {e}"))
            self.after(0, self._search_done)

    def _collect_jobs(self, query: str) -> list:
        """
        Collect and merge jobs from both sites via backend.

        Args:
            query: ключевое слово для поиска

        Returns:
            List of job dicts with keys:
            too, company, addresses, salary_from, salary_to, id
        """
        jobs_tk = self.backend.töökassa(query)
        jobs_cv = self.backend.CV(query)
        spisok = []

        for job in jobs_tk:
            detail = self.backend.tookassaFull(job["id"])
            if not detail:
                continue
            addresses = detail.get("aadressid", [])
            adress = addresses[0].get("aadressTekst") if addresses else None
            company = detail.get("toopakkuja", {}).get("nimi")
            if not any(item["company"] == company for item in spisok):
                spisok.append({
                    "company":     company,
                    "too":         detail.get("nimetus", ""),
                    "salary_from": detail.get("tookohaAndmed", {}).get("tootasuAlates"),
                    "salary_to":   detail.get("tookohaAndmed", {}).get("tootasuKuni"),
                    "id":          f"https://www.tootukassa.ee/et/toopakkumised/{job['id']}",
                    "addresses":   adress,
                })

        for i in jobs_cv:
            spisok.append({
                "company":     i["company"],
                "too":         i["too"],
                "salary_from": i["salary_from"],
                "salary_to":   i["salary_to"],
                "id":          f"https://cv.ee/et/vacancy/{i['id']}",
                "addresses":   i["addresses"],
            })

        return spisok

    # ──────────────────────────────────────────
    #  Таблица и фильтры
    # ──────────────────────────────────────────

    def _on_results_ready(self):
        """Called in main thread when search results are available."""
        self._search_done()
        self._apply_filters()

    def _apply_filters(self):
        """Filter self.all_jobs and redraw the table."""
        sal_from = self._parse_int(self.salary_from_var.get())
        sal_to   = self._parse_int(self.salary_to_var.get())
        city     = self.city_var.get().strip().lower()

        filtered = []
        for job in self.all_jobs:
            sf = job.get("salary_from") or 0
            st = job.get("salary_to")   or sf

            if sal_from and st < sal_from:
                continue
            if sal_to and sf > sal_to:
                continue

            addr = (job.get("addresses") or "").lower()
            if city and city not in addr:
                continue

            filtered.append(job)

        self._fill_table(filtered)
        self._set_status(f"Показано: {len(filtered)} из {len(self.all_jobs)} вакансий")

    def _reset_filters(self):
        """Clear all filter fields and show all results."""
        self.salary_from_var.set("")
        self.salary_to_var.set("")
        self.city_var.set("")
        self._fill_table(self.all_jobs)
        self._set_status(f"Показано: {len(self.all_jobs)} вакансий")

    def _fill_table(self, jobs: list):
        """
        Populate the treeview with job data.

        Args:
            jobs: список словарей с данными вакансий
        """
        self._clear_table()
        for idx, j in enumerate(jobs):
            sal_f = j.get("salary_from")
            sal_t = j.get("salary_to")
            if sal_f and sal_t:
                salary = f"{sal_f} – {sal_t}"
            elif sal_f:
                salary = f"от {sal_f}"
            elif sal_t:
                salary = f"до {sal_t}"
            else:
                salary = "не указана"

            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", "end", tags=(tag,), values=(
                j.get("too")       or "—",
                j.get("company")   or "—",
                j.get("addresses") or "—",
                salary,
                j.get("id")        or "—",
            ))

    def _clear_table(self):
        """Remove all rows from the treeview."""
        for row in self.tree.get_children():
            self.tree.delete(row)

    def _search_done(self):
        """Re-enable search button and stop progress bar."""
        self.search_btn.configure(state="normal", text="Найти")
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(1)

    # ──────────────────────────────────────────
    #  Утилиты
    # ──────────────────────────────────────────

    def _set_status(self, text: str):
        """Update the status bar label."""
        self.status_var.set(text)

    @staticmethod
    def _parse_int(value: str):
        """
        Safely parse a string to int.

        Args:
            value: строка для преобразования

        Returns:
            int или None если строка пустая / не число
        """
        try:
            return int(value.strip())
        except (ValueError, AttributeError):
            return None

    # ──────────────────────────────────────────
    #  Тестовые данные (без бекенда)
    # ──────────────────────────────────────────

    @staticmethod
    def _demo_jobs(query: str) -> list:
        """Return sample jobs for UI testing without backend."""
        return [
            {"too": f"{query.capitalize()} старший",   "company": "Acme OÜ",   "addresses": "Tallinn", "salary_from": 1800, "salary_to": 2500, "id": "https://cv.ee"},
            {"too": f"{query.capitalize()} младший",   "company": "Beta AS",    "addresses": "Tartu",   "salary_from": 1200, "salary_to": 1600, "id": "https://cv.ee"},
            {"too": f"{query.capitalize()} специалист","company": "Gamma OÜ",   "addresses": "Pärnu",   "salary_from": 1500, "salary_to": 2000, "id": "https://tootukassa.ee"},
            {"too": f"Старший {query}",                "company": "Delta Corp", "addresses": "Tallinn", "salary_from": 2200, "salary_to": None,  "id": "https://tootukassa.ee"},
            {"too": f"Помощник {query}а",              "company": "Epsilon OÜ", "addresses": "Narva",   "salary_from": None, "salary_to": None,  "id": "https://cv.ee"},
        ]


# ──────────────────────────────────────────────
#  Запуск
# ──────────────────────────────────────────────

if __name__ == "__main__":
    # from saits import saits
    # backend = saits()
    backend = None  # убери None и раскомментируй строки выше

    app = JobSearchApp(backend=backend)
    app.mainloop()
class saits: #Класс где будет происходить поиск вакансий
    def __init__(self):
        self.headers = { #нужен чтобы сайт не понял что это робот, в селф чтобы не писать кучу раз
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://www.tootukassa.ee",
            "Referer": "https://www.tootukassa.ee/et/toopakkumised"
        }
        self.towns = self.CVTown() #получаем список городов при инициализации класса, чтобы использовать его для получения информации о городе по айди вакансии на CV.ee в функции CV
    def töökassa(self,quer): # функция для поиска айди для тоокааса
        self.url = 'https://www.tootukassa.ee/web/graphql'
        query = """ #поиск из GraphQL # поиск по ключевому слову, количество страниц и тд
        query jobOfferSearch($first: Int, $cursor: Cursor, $searchInput: InputToopakkumineAvalikOtsingDTO) {
          jobOffersQuery(first: $first, after: $cursor, searchInput: $searchInput) {
            edges {
              id #узнать айпи
            }
            pageInfo {
              totalCount #общее количество
            }
          }
        }
        """
        variables = { #фильтрации поиска
            "first": 10,
            "searchInput": {
                "otsisona": quer, #ключевое слово
                "valdkonnad": [], #профессия
                "asukohad": [], #место
                "kaugtoo": 0 #удаленная работа или нет
            }
        }
        payload = { #запрос
            "operationName": "jobOfferSearch", #название запроса
            "query": query, #сам запрос
            "variables": variables #переменные для запроса
        }

        try:
            response = requests.post(self.url, json=payload, headers=self.headers) #отправляем запрос
            response.raise_for_status() #проверка на статус ответа
            data = response.json() #получаем данные в формате json 

            if 'errors' in data: #проверка на ошибку
                print(f"Ошибка API: {data['errors']}") #если есть ошибка, выводим ее и возвращаем пустой список
                return [] #возвращаем пустой список в случае ошибки

            result = data['data']['jobOffersQuery'] #получаем результат из данных
            jobs = result['edges']  #список вакансий, который мы будем возвращать
            total = result['pageInfo']['totalCount'] #общее количество вакансий, найденных по запросу
            return jobs #возвращаем список вакансий

        except Exception as e: #проверка на ошибку
            print(f"Ошибка подключения: {e}")
            return []
    def tookassaFull(self, job_id): #полные данные
        query = """ #
        query jobofferquery($id: Int!) { #поиск по айди
          publicJobOfferQuery(jobOfferId: $id) {
            nimetus # название 
            toopakkuja {  #информация о работадателе
              nimi #название работадателя
              tutvustus #info
            }
            tookohaAndmed { #информация о зарплате
              tootasuAlates #нач зп
              tootasuKuni #конечная зп
            }
            aadressid { #адрес
              aadressTekst #текст адреса
            }
          }
        }
        """

        payload = { #запрос
            "operationName": "jobofferquery", #название запроса
            "query": query, 
            "variables": {"id": job_id} #переменные для запроса, в данном случае это айди вакансии, который мы получили на предыдущем этапе поиска
        }

        try: 
            response = requests.post(self.url, json=payload, headers=self.headers) #отправляем запрос
            response.raise_for_status()#проверка на статус ответа
            data = response.json()#получаем данные в формате json

            if 'errors' in data: #проверка на ошибку в данных
                return None

            return data['data']['publicJobOfferQuery'] #возвращаем полные данные о вакансии, которые мы получили из ответа

        except Exception as e: #проверка на ошибку при подключении или обработке данных
            return None
    def CVTown(self): #получение информации о городе по айди вакансии на CV.ee
        url = 'https://cv.ee/api/v1/locations-service/list' #внутренний API CV.ee для получения списка городов
        try:
            response = requests.get(url, headers=self.headers) #отправляем GET запрос к API CV.ee для получения списка городов с указанными заголовками
            if response.status_code == 200:
                data = response.json()
                return {t['id']: t['name'] for t in data.get('towns', [])}
        except Exception as e:
            print(f"Ошибка подключения к CV.ee для получения городов: {e}")
        return {}        
    def CV(self, quer): #поиск вакансий на CV.ee
        url ='https://cv.ee/api/v1/vacancy-search-service/search' #внутренний API CV.ee для поиска вакансий
        params = { #параметры запроса для поиска вакансий на CV.ee
            'limit': 10, #сколько вакансий показать
            'offset': 0, 
            'keywords[]': quer, #ключевое слово для поиска вакансий
            'lang': 'ru' #язык интерфейса, в данном случае русский
        }
        result = []  # Список для сбора вакансий
        
        try:
            response = requests.get(url, params=params, headers=self.headers) #отправляем GET запрос к API CV.ee с указанными параметрами и заголовками
            if response.status_code == 200: #проверяем статус ответа, если он 200, значит запрос успешный
                data = response.json() #получаем данные в формате json из ответа
                vacancies = data.get('vacancies', []) #получаем список вакансий из данных, если ключ 'vacancies' отсутствует, возвращаем пустой список
                
                if not vacancies:
                    print("На CV.ee ничего не найдено")
                    return [] 

                for v in vacancies: #проходим по каждой вакансии в списке вакансий, полученных из ответа
                    town_id = v.get('townId') #получаем айди города из данных о вакансии, используя ключ 'townId' для доступа к информации о городе. Если ключ 'townId' отсутствует, возвращаем None.
                    town_name = self.towns.get(town_id, "Не указан")
                    item = { #создаем словарь для каждой вакансии, который будет содержать информацию о компании, названии работы, зарплате и ссылке на вакансию
                        'company': v.get('employerName'),     # Название фирмы 
                        'too':v.get('positionTitle'), #название работы
                        'salary_from': v.get('salaryFrom'), #начальная зп
                        'salary_to': v.get('salaryTo'), #конечная зп
                        'id': v.get('id'),#айди для ссылки
                        'addresses': town_name #получаем информацию о городе по айди вакансии, используя функцию CVTown, которая принимает айди вакансии и возвращает название города, где находится работа. Мы передаем айди вакансии, полученный из данных о вакансии, в функцию CVTown для получения информации о городе.
                    }
                    result.append(item)
                
                return result #возвращаем список вакансий, который мы собрали из ответа
            else:
                print(f"Ошибка CV.ee: {response.status_code}")
                return []

        except Exception as e:
            print(f"Ошибка в методе CV: {e}")
            return []

    def get_job(self, query): #главная функция для получения вакансий по ключевому слову, которая объединяет результаты с обоих сайтов и выводит их в удобном формате
        jobs = self.töökassa(query) #получаем список вакансий с сайта TööKassa по ключевому слову, используя функцию töökassa
        jobsC=self.CV(query) #получаем список вакансий с сайта CV.ee по ключевому слову, используя функцию CV
        spisok=[] #создаем пустой список, который будет содержать объединенные результаты вакансий с обоих сайтов, чтобы избежать дублирования и вывести их в удобном формат
        for job in jobs: #проходим по каждой вакансии в списке вакансий, полученных с сайта TööKassa

            detail = self.tookassaFull(job["id"]) #получаем полные данные о вакансии, используя функцию tookassaFull, которая принимает айди вакансии и возвращает подробную информацию о ней, такую как название работы, название компании, зарплата и адрес
            if not detail: #если по какой-то причине не удалось получить полные данные о вакансии,
                continue
            addresses = detail.get("aadressid", []) #получаем список адресов из данных о вакансии, если ключ 'aadressid' отсутствует, возвращаем пустой список
            adress=None
            if addresses: #если список адресов не пустой, берем текст первого адреса из списка и сохраняем его в переменную adress, которая будет использоваться для вывода информации о городе, где находится работа
                adress=addresses[0].get("aadressTekst")
            if not any(item['company'] == detail.get("toopakkuja", {}).get("nimi") for item in spisok): #проверяем, есть ли уже в списке spisok вакансия от той же компании, что и текущая вакансия, которую мы обрабатываем. Если в списке spisok уже есть вакансия от той же компании, то мы не добавляем текущую вакансию в список spisok, чтобы избежать дублирования вакансий от одной и той же компании. Если в списке spisok нет вакансии от той же компании, то мы добавляем текущую вакансию в список spisok.
                spisok.append({ #список
                    'company':detail.get("toopakkuja", {}).get("nimi"), #название компании, которая предлагает работу, получаемое из данных о вакансии, используя ключ 'toopakkuja' для доступа к информации о компании и ключ 'nimi' для получения названия компании. Если ключ 'toopakkuja' или 'nimi' отсутствует, возвращаем пустую строку.
                    'too':detail.get('nimetus',{}), #название работы, получаемое из данных о вакансии, используя ключ 'nimetus' для доступа к названию работы. Если ключ 'nimetus' отсутствует, возвращаем пустую строку.
                    'salary_from':detail.get("tookohaAndmed", {}).get("tootasuAlates"), #начальная зарплата, получаемая из данных о вакансии, используя ключ 'tookohaAndmed' для доступа к информации о зарплате и ключ 'tootasuAlates' для получения начальной зарплаты. Если ключ 'tookohaAndmed' или 'tootasuAlates' отсутствует, возвращаем None.
                    'salary_to':detail.get("tookohaAndmed", {}).get("tootasuKuni"), #конечная зарплата, получаемая из данных о вакансии, используя ключ 'tookohaAndmed' для доступа к информации о зарплате и ключ 'tootasuKuni' для получения конечной зарплаты. Если ключ 'tookohaAndmed' или 'tootasuKuni' отсутствует, возвращаем None.
                    'id':f"https://www.tootukassa.ee/et/toopakkumised/{job['id']}", #ссылка на вакансию, формируемая с помощью айди вакансии, полученного из списка вакансий с сайта TööKassa, который мы обрабатываем в текущей итерации цикла. Мы используем f-строку для форматирования ссылки, вставляя айди вакансии в нужное место в URL.
                    'addresses':adress, #адрес, который мы получили из данных о вакансии и сохранили в переменной adress, которая будет использоваться для вывода информации о городе, где находится работа. Если адрес не был найден, то значение будет None.
                    'info':detail.get('toopakkuja',{}).get('tutvustus')
                }
                )
    
        for i in jobsC: #проходим по каждой вакансии в списке вакансий, полученных с сайта CV.ee
    
            spisok.append({ #добавляем каждую вакансию из списка вакансий с сайта CV.ee в список spisok, который содержит объединенные результаты вакансий с обоих сайтов. Мы добавляем каждую вакансию в список spisok в виде словаря, который содержит информацию о компании, названии работы, зарплате и ссылке на вакансию.
                'company':i['company'], #название компании, которая предлагает работу, получаемое из данных о вакансии с сайта CV.ee, используя ключ 'company' для доступа к названию компании. Если ключ 'company' отсутствует, возвращаем пустую строку.
                'too':i['too'], #название работы, получаемое из данных о вакансии с сайта CV.ee, используя ключ 'too' для доступа к названию работы. Если ключ 'too' отсутствует, возвращаем пустую строку.
                'salary_from':i['salary_from'], #начальная зарплата, получаемая из данных о вакансии с сайта CV.ee, используя ключ 'salary_from' для доступа к начальной зарплате. Если ключ 'salary_from' отсутствует, возвращаем None.
                'salary_to':i['salary_to'], #конечная зарплата, получаемая из данных о вакансии с сайта CV.ee, используя ключ 'salary_to' для доступа к конечной зарплате. Если ключ 'salary_to' отсутствует, возвращаем None.
                'id':f"https://cv.ee/et/vacancy/{i['id']}", #ссылка на вакансию, формируемая с помощью айди вакансии, полученного из списка вакансий с сайта CV.ee, который мы обрабатываем в текущей итерации цикла. Мы используем f-строку для форматирования ссылки, вставляя айди вакансии в нужное место в URL.
                'addresses':i['addresses'], #адрес, который мы получили из данных о вакансии с сайта CV.ee. Если адрес не был найден, то значение будет None.
                'info':None
            })
        
        for i in spisok:
            print(f"Работа: {i['too']}   Фирма: {i['company']}  Город: {i['addresses']}  ЗП: {i['salary_from']}-{i['salary_to']} Ссылка: {i['id']}  Информация: {i['info']}" ) #выводим информацию о каждой вакансии из списка spisok в удобном формате, который включает название работы, название компании, город, где находится работа, диапазон зарплаты и ссылку на вакансию. Мы используем f-строку для форматирования вывода, вставляя соответствующие значения из каждого словаря вакансии в нужные места в строке вывода.
        if spisok:
            self.save_to_csv(spisok)
            self.save_to_txt(spisok)
    
    def save_to_csv(self,jobs):
        with open('jobs.csv', 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
            writer.writeheader()
            writer.writerows(jobs)
    def save_to_txt(self,jobs):
        with open('jobs.txt', 'w', encoding='utf-8') as f:
            for j in jobs:
                f.write(f"Töö: {j['too']} | Ettevõte: {j['company']} | linn: {j['addresses']} | palk: {j['salary_from']}-{j['salary_to']} | link: {j['id']}\n")

test = saits()
test.get_job('kokk') #здесь можно изменить ключевое слово для поиска вакансий, например 'kokk' для поиска вакансий повара, 'programmeerija' для поиска вакансий программиста и т.д.
