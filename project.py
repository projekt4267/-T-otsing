import requests
import csv
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
                    'addresses':adress #адрес, который мы получили из данных о вакансии и сохранили в переменной adress, которая будет использоваться для вывода информации о городе, где находится работа. Если адрес не был найден, то значение будет None.
                }
                )
    
        for i in jobsC: #проходим по каждой вакансии в списке вакансий, полученных с сайта CV.ee
    
            spisok.append({ #добавляем каждую вакансию из списка вакансий с сайта CV.ee в список spisok, который содержит объединенные результаты вакансий с обоих сайтов. Мы добавляем каждую вакансию в список spisok в виде словаря, который содержит информацию о компании, названии работы, зарплате и ссылке на вакансию.
                'company':i['company'], #название компании, которая предлагает работу, получаемое из данных о вакансии с сайта CV.ee, используя ключ 'company' для доступа к названию компании. Если ключ 'company' отсутствует, возвращаем пустую строку.
                'too':i['too'], #название работы, получаемое из данных о вакансии с сайта CV.ee, используя ключ 'too' для доступа к названию работы. Если ключ 'too' отсутствует, возвращаем пустую строку.
                'salary_from':i['salary_from'], #начальная зарплата, получаемая из данных о вакансии с сайта CV.ee, используя ключ 'salary_from' для доступа к начальной зарплате. Если ключ 'salary_from' отсутствует, возвращаем None.
                'salary_to':i['salary_to'], #конечная зарплата, получаемая из данных о вакансии с сайта CV.ee, используя ключ 'salary_to' для доступа к конечной зарплате. Если ключ 'salary_to' отсутствует, возвращаем None.
                'id':f"https://cv.ee/et/vacancy/{i['id']}", #ссылка на вакансию, формируемая с помощью айди вакансии, полученного из списка вакансий с сайта CV.ee, который мы обрабатываем в текущей итерации цикла. Мы используем f-строку для форматирования ссылки, вставляя айди вакансии в нужное место в URL.
                'addresses':i['addresses'] #адрес, который мы получили из данных о вакансии с сайта CV.ee. Если адрес не был найден, то значение будет None.
            })
        
        for i in spisok:
            print(f"Работа: {i['too']}   Фирма: {i['company']}  Город: {i['addresses']}  ЗП: {i['salary_from']}-{i['salary_to']} Ссылка: {i['id']}") #выводим информацию о каждой вакансии из списка spisok в удобном формате, который включает название работы, название компании, город, где находится работа, диапазон зарплаты и ссылку на вакансию. Мы используем f-строку для форматирования вывода, вставляя соответствующие значения из каждого словаря вакансии в нужные места в строке вывода.
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
