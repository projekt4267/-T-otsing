import requests
import csv
import customtkinter as ctk
from tkinter import ttk
import threading
import os
from PIL import Image
"""
класс saits нужен для поиска вакансий из töökassa и CV.ee, я использовал разные методы для получения данных с этих сайтов, так как у них разные API и структура данных.
Метод töökassa отправляет GraphQL запрос к API Tööukassa для получения списка вакансий по заданному запросу, а метод tookassaFull отправляет другой GraphQL запрос для получения полной информации о конкретной вакансии по ее ID.
Метод CVTown получает список городов с CV.ee для отображения их в читаемом виде, а метод CV отправляет GET запрос к API CV.ee для получения списка вакансий по заданному запросу.
Метод get_job_list объединяет результаты из обоих источников (Tööukassa и CV.ee) в единый список вакансий для отображения в интерфейсе приложения.
"""
class saits: # Класс для получения данных с сайтов Tööukassa и CV.ee
    def __init__(self): # Инициализация сессии и основных настроек
        self.headers = { # Заголовки для имитации браузера и корректной работы с API
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://www.tootukassa.ee",
            "Referer": "https://www.tootukassa.ee/et/toopakkumised"
        }
        self.url_tk = 'https://www.tootukassa.ee/web/graphql' # URL для Tööukassa
        self.towns = self.CVTown() # Получаем список городов для CV.ee, чтобы отображать их в читаемом виде

    def töökassa(self, quer): # Метод для получения списка вакансий с Tööukassa по заданному запросу
        query = """ # GraphQL päring Tööukassa tööpakkumiste otsimiseks
        query jobOfferSearch($first: Int, $cursor: Cursor, $searchInput: InputToopakkumineAvalikOtsingDTO) { # Parameetrid
          jobOffersQuery(first: $first, after: $cursor, searchInput: $searchInput) { # Tööpakkumiste päring lehejaotuse ja otsingukriteeriumidega
            edges { id } # Saame ainult töökohtade ID-d, ülejäänud andmeid küsime iga töökoha kohta eraldi
            pageInfo { totalCount } # Saame kasutajale kuvamiseks leitud töökohtade koguarvu
          }
        }
        """
        variables = { # Устанавливаем переменные для GraphQL запроса
            "first": 30, # Получаем первые 30 вакансий, можно увеличить при необходимости
            "searchInput": {"otsisona": quer, "valdkonnad": [], "asukohad": [], "kaugtoo": 0} # Параметры поиска
        } 
        payload = {"operationName": "jobOfferSearch", "query": query, "variables": variables} # Отправляем POST запрос к API Tööukassa и обрабатываем ответ, возвращая список вакансий (только ID)

        try:
            response = requests.post(self.url_tk, json=payload, headers=self.headers) # Отправляем POST запрос к API Tööukassa с заданными параметрами и заголовками
            data = response.json() #   Преобразуем ответ в JSON формат и извлекаем из него список вакансий
            return data.get('data', {}).get('jobOffersQuery', {}).get('edges', []) # Получаем список вакансий из ответа
        except: 
            return []

    def tookassaFull(self, job_id): # Метод для получения полной информации о вакансии с Tööukassa по ее ID
        query = """ # GraphQL-запрос для получения полной информации о вакансии в Тёкассе по её идентификатору.
        query jobofferquery($id: Int!) { # Параметр: Идентификатор задания, полученный на предыдущем шаге.
          publicJobOfferQuery(jobOfferId: $id) { # Запрос полной информации о вакансии на основании данного идентификатора.
            nimetus # Должность
            toopakkuja { nimi } #Информация о компании, предлагающей работу (название)
            tookohaAndmed { tootasuAlates tootasuKuni } # Информация о заработной плате: с и по
            aadressid { aadressTekst } # Töökohainfo (aadresse võib olla mitu, kuvame esimese)
          }
        }
        """
        payload = {"operationName": "jobofferquery", "query": query, "variables": {"id": job_id}} # Формируем тело запроса
        try: # Отправляем POST запрос к API Tööukassa
            response = requests.post(self.url_tk, json=payload, headers=self.headers) # Отправляем POST запрос к API Tööukassa
            return response.json().get('data', {}).get('publicJobOfferQuery') 
        except: 
            return None

    def CVTown(self): # Метод для получения списка городов с CV.ee
        url = 'https://cv.ee/api/v1/locations-service/list' # URL
        try: 
            response = requests.get(url, headers=self.headers) 
            if response.status_code == 200: 
                return {t['id']: t['name'] for t in response.json().get('towns', [])} # Получаем список городов из ответа
        except: pass 
        return {}

    def CV(self, quer): # Метод для получения списка вакансий с CV.ee по заданному запросу
        url = 'https://cv.ee/api/v1/vacancy-search-service/search' # URL 
        params = {'limit': 30, 'keywords[]': quer, 'lang': 'ru'} # Параметры для поиска вакансий с CV.ee
        result = [] # Список для хранения результатов поиска вакансий с CV.ee
        try: 
            response = requests.get(url, params=params, headers=self.headers) 
            if response.status_code == 200: 
                for v in response.json().get('vacancies', []): # Получаем список вакансий из ответа
                    result.append({ # Формируем словарь с информацией о каждой вакансии
                        'company': v.get('employerName'), # Название компании
                        'too': v.get('positionTitle'), # Название должности
                        'salary_from': v.get('salaryFrom'), # Зарплата от
                        'salary_to': v.get('salaryTo'), # Зарплата до
                        'id': f"https://cv.ee/et/vacancy/{v.get('id')}", # Ссылка на вакансию
                        'addresses': self.towns.get(v.get('townId'), "Ei ole märgitud") # Адрес работы
                    })
        except: pass # В случае ошибки возвращаем пустой список
        return result

    def get_job_list(self, query): # Метод для получения объединенного списка вакансий
        final_list = [] # Список для хранения 
        # Парсим Töötukassa
        tk_raw = self.töökassa(query) # Получаем список вакансий с Töötukassa
        for item in tk_raw: # Проходим по каждому элементу
            detail = self.tookassaFull(item['id']) # Получаем полную информацию о вакансии с Tööukassa по ее ID
            if detail:
                addr = detail.get("aadressid", [{}])[0].get("aadressTekst") if detail.get("aadressid") else "Ei ole märgitud"  # Получаем адрес работы из данных вакансии
                final_list.append({ 
                    'company': detail.get("toopakkuja", {}).get("nimi", "Teadmata"), # Название компании
                    'too': detail.get('nimetus', 'Pealkirjata'), # Название должности
                    'salary_from': detail.get("tookohaAndmed", {}).get("tootasuAlates"), # Зарплата от
                    'salary_to': detail.get("tookohaAndmed", {}).get("tootasuKuni"), # Зарплата до
                    'id': f"https://www.tootukassa.ee/et/toopakkumised/{item['id']}", # Ссылка на вакансию
                    'addresses': addr # Адрес работы
                })

        # Добавляем CV.ee
        final_list.extend(self.CV(query))# Получаем список вакансий с CV.ee
        return final_list # Возвращаем объединенный список
"""
класс JobSearchApp нужен для создания графического интерфейса приложения с помощью библиотеки customtkinter, который позволяет пользователю вводить запрос для поиска вакансий,
отображать результаты в виде таблицы и применять фильтры по зарплате и городу для удобного просмотра вакансий,
а также открывать детали вакансии в новом окне при двойном клике на строку таблицы
"""
class JobSearchApp(ctk.CTk): # Класс для создания графического интерфейса
    def __init__(self, backend=None): # Инициализация приложения
        super().__init__() # Инициализация базового класса CTk для создания окна приложения
        self.backend = backend # Сохранение экземпляра бэкенда 
        self.all_jobs = [] # Список для хранения всех вакансий
        self.title("Job Search Estonia")
        self.geometry("1100x700") # Установка размера 
        current_dir = os.path.dirname(os.path.abspath(__file__)) # Получение текущей директории
        image_path = os.path.join(current_dir, "Background_JobFinder.png") # Формирование пути к изображению
        bg_image_pil = Image.open(image_path) # Загрузка изображения для фона
        bg_image = ctk.CTkImage(light_image=bg_image_pil, # Создание объекта CTkImage
                         dark_image=bg_image_pil, 
                         size=(1100, 700))
        image = os.path.join(current_dir, "Icon_JobFinder.ico")
        self.iconbitmap(image) # Установка иконки для окна приложения
        ctk.set_appearance_mode("dark") # Установка темного режима для интерфейса приложения
        bg_label = ctk.CTkLabel(self, image=bg_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1) # Растягиваем на все окно
        style=ttk.Style()
        style.theme_use("default") # Установка темы "default"
        style.configure("Treeview", background="#4a4a4a", foreground="white", fieldbackground="#2b2b2b", rowheight=30,borderwidth=5) # Настройка стиля для виджета Treeview

       
        ctk.set_default_color_theme("green") # Установка зеленой цветовой темы
        self._build_ui()# Вызов метода для создания интерфейса приложения
       

        self.tree.bind("<Double-1>", self._on_double_click)# Связывание события двойного клика

    def _build_ui(self): # Метод для создания интерфейса приложения
        self.grid_columnconfigure(0, weight=1) # Настройка сетки для размещения элементов интерфейса
        self.grid_rowconfigure(2, weight=1) # Настройка сетки 

        top = ctk.CTkFrame(self, height=80)# Создание верхней панели
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
       
        self.search_var = ctk.StringVar() # Создание переменной для хранения 
        self.search_entry = ctk.CTkEntry(top, textvariable=self.search_var, placeholder_text="Ametikoht...", width=400) 
        self.search_entry.pack(side="left", padx=20, pady=20) 
       
        self.search_btn = ctk.CTkButton(top, text="Leida", command=self._start_search) # Создание кнопки для запуска поиска вакансий
        self.search_btn.pack(side="left", padx=10) 

        # 2. Панель фильтров
        filter_bar = ctk.CTkFrame(self) # Создание панели для размещения элементов управления фильтрами
        filter_bar.grid(row=1, column=0, sticky="ew", padx=10)
       
        self.salary_from_var = ctk.StringVar() # Создание переменной для хранения значения
        ctk.CTkLabel(filter_bar, text="palk:").pack(side="left", padx=5) 
        ctk.CTkEntry(filter_bar, textvariable=self.salary_from_var, width=80).pack(side="left", padx=5)

        self.city_var = ctk.StringVar() # Создание переменной для хранения значения
        ctk.CTkLabel(filter_bar, text="Linn:").pack(side="left", padx=5) 
        ctk.CTkEntry(filter_bar, textvariable=self.city_var, width=120).pack(side="left", padx=5) 

        ctk.CTkButton(filter_bar, text="Filter", width=100, command=self._apply_filters).pack(side="left", padx=20) # Создание кнопки для применения фильтров

        # 3. Таблица
        t_frame = ctk.CTkFrame(self) # Создание фрейма для размещения таблицы
        t_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10) 
       
        cols = ("Töö", "Ettevõte", "Linn", "Palk", "link") # Определение столбцов для таблицы
        self.tree = ttk.Treeview(t_frame, columns=cols, show="headings")# Создание виджета Treeview для отображения таблицы
        for col in cols: self.tree.heading(col, text=col.capitalize()) # Установка заголовков для каждого столбца в таблице
        self.tree.pack(expand=True, fill="both") # Размещение виджета
        style = ttk.Style() 
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#4a4a4a", foreground="white") 

    

        # Подсказка для пользователя
        ctk.CTkLabel(self, text="* Klõpsake tööpakkumisel kaks korda, et see avada ja link kopeerida", text_color="gray", fg_color="transparent").grid(row=7, column=0, pady=5)
        ctk.CTkButton(self,text="Salvesta CSV-failina", command=self._save_csv).grid(row=4, column=0, pady=10) 
        ctk.CTkButton(self,text ="Salvesta TXT-failina", command=self._save_txt).grid(row=5, column=0, pady=10) 

    def _on_double_click(self, event):
        item = self.tree.selection()
        if not item:
            return
        values = self.tree.item(item[0], "values")
        link = values[4]  # берём ссылку
        if link:
            os.startfile(link)  # открывает сайт

    def _start_search(self): # Метод для запуска процесса поиска вакансий
        query = self.search_var.get() # Получаем значение запроса из поля для ввода
        if not query: return # Если запрос пустой, просто возвращаемся из метода
        self.search_btn.configure(state="disabled") # Отключаем кнопку поиска
        threading.Thread(target=self._fetch, args=(query,), daemon=True).start() # Запускаем новый поток для получения данных о вакансиях с бэкенда

    def _fetch(self, query): # Метод для получения данных о вакансиях с бэкенда
        if self.backend:
            # Получаем список из бэкенда (saits)
            self.all_jobs = self.backend.get_job_list(query) # Получаем список вакансий
        self.after(0, self._on_done)  # После получения данных о вакансиях вызываем метод _on_done для обновления интерфейса

    def _on_done(self): # Метод для обработки завершения получения данных о вакансиях
        self.search_btn.configure(state="normal")
        self._apply_filters()

    def _apply_filters(self): # Метод для применения фильтров
        self.tree.delete(*self.tree.get_children())
        city_f = self.city_var.get().lower()
        sal_f = int(self.salary_from_var.get()) if self.salary_from_var.get().isdigit() else 0

        for j in self.all_jobs: # Проходим по каждому элементу в списке всех вакансий
            addr = (j.get('addresses') or "").lower()
            sal_to = j.get('salary_to') or j.get('salary_from') or 0
           
            if city_f in addr and (not sal_f or (sal_to and sal_to >= sal_f)): # Проверяем, соответствует ли город вакансии заданному фильтру по городу
                salary_str = f"{j.get('salary_from') or 0} - {j.get('salary_to') or ''}"
                self.tree.insert("", "end", values=(j['too'], j['company'], j['addresses'], salary_str, j['id']))
    def _save_csv(self): 
        # Получаем все ID строк из таблицы
        items = self.tree.get_children()
        if not items:
            return 

        with open("vacancies.csv", "w", newline="", encoding="utf-16") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(["Ametikoht", "Ettevõte", "Linn", "Palk", "Link"])
           
            for item_id in items:
                row_values = self.tree.item(item_id)['values']
                writer.writerow(row_values)
       
        os.startfile("vacancies.csv")

    def _save_txt(self): 
        items = self.tree.get_children()
        if not items:
            return

        with open("vacancies.txt", "w", encoding="utf-8") as f:
            for item_id in items:
                v = self.tree.item(item_id)['values']
                info = (
                    f"Ametikoht: {v[0]}\n"
                    f"Ettevõte: {v[1]}\n"
                    f"Linn: {v[2]}\n"
                    f"Palk: {v[3]}\n"
                    f"Link: {v[4]}\n"
                    f"{'-'*40}\n"
                )
                f.write(info)
       
        os.startfile("vacancies.txt")

if __name__ == "__main__": # Точка входа в приложение
    backend_instance = saits()
    app = JobSearchApp(backend=backend_instance)
    app.mainloop()
