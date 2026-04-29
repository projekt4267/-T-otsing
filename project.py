import requests

class saits: #Класс где будет происходить поиск вакансий
    def __init__(self):
        self.headers = { #нужен чтобы сайт не понял что это робот, в селф чтобы не писать кучу раз
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://www.tootukassa.ee",
            "Referer": "https://www.tootukassa.ee/et/toopakkumised"
        }
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
    def CV(self, quer): #поиск вакансий на CV.ee
        url = 'https://cv.ee/api/v1/vacancy-search-service/search' #внутренний API CV.ee для поиска вакансий
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
                    item = { #создаем словарь для каждой вакансии, который будет содержать информацию о компании, названии работы, зарплате и ссылке на вакансию
                        'company': v.get('employerName'),     # Название фирмы 
                        'too':v.get('positionTitle'), #название работы
                        'salary_from': v.get('salaryFrom'), #начальная зп
                        'salary_to': v.get('salaryTo'), #конечная зп
                        'id': v.get('id')#айди для ссылки
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
        jobs = self.töökassa(query)
        jobsC=self.CV(query)
        spisok=[]
        for job in jobs:

            detail = self.tookassaFull(job["id"])
            if not detail:
                continue
            addresses = detail.get("aadressid", [])
            adress=None
            if addresses:
                adress=addresses[0].get("aadressTekst")
            if not any(item['company'] == detail.get("toopakkuja", {}).get("nimi") for item in spisok):
                spisok.append({ #список
                    'company':detail.get("toopakkuja", {}).get("nimi"),
                    'too':detail.get('nimetus',{}),
                    'salary_from':detail.get("tookohaAndmed", {}).get("tootasuAlates"),
                    'salary_to':detail.get("tookohaAndmed", {}).get("tootasuKuni"),
                    'id':f"https://www.tootukassa.ee/et/toopakkumised/{job['id']}",
                    'addresses':adress
                }
                )
            
        for i in jobsC:
            spisok.append({
                'company':i['company'],
                'too':i['too'],
                'salary_from':i['salary_from'],
                'salary_to':i['salary_to'],
                'id':f"https://cv.ee/et/vacancy/{i['id']}",
                'addresses':None
            })
        for i in spisok:
            print(f"Работа: {i['too']}   Фирма: {i['company']}  Город: {i['addresses']}  ЗП: {i['salary_from']}-{i['salary_to']} Ссылка: {i['id']}")

test = saits()
test.get_job('kokk')
