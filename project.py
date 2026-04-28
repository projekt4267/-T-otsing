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
        query = """ #поиск из GraphQL
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
                "otsisona": quer,
                "valdkonnad": [],
                "asukohad": [],
                "kaugtoo": 0
            }
        }
        payload = { #запрос
            "operationName": "jobOfferSearch",
            "query": query,
            "variables": variables
        }

        try:
            response = requests.post(self.url, json=payload, headers=self.headers) #данные
            response.raise_for_status() #проверка статуса
            data = response.json() #переделка данных в понятную версию 

            if 'errors' in data: #проверка на ошибку
                print(f"Ошибка API: {data['errors']}")
                return []

            result = data['data']['jobOffersQuery'] #фильтрация 
            jobs = result['edges'] 
            total = result['pageInfo']['totalCount']
            print(f"Найдено {total} вакансий")
            return jobs

        except Exception as e: #проверка на ошибку
            print(f"Ошибка подключения: {e}")
            return []
    def tookassaFull(self, job_id): #полные данные
        query = """
        query jobofferquery($id: Int!) {
          publicJobOfferQuery(jobOfferId: $id) {
            nimetus # название 
            toopakkuja { 
              nimi #название работадателя
            }
            tookohaAndmed { #
              tootasuAlates #нач зп
              tootasuKuni #конечная зп
            }
            aadressid { #адрес
              aadressTekst
            }
          }
        }
        """

        payload = {
            "operationName": "jobofferquery",
            "query": query,
            "variables": {"id": job_id}
        }

        try:
            response = requests.post(self.url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            if 'errors' in data:
                return None

            return data['data']['publicJobOfferQuery']

        except Exception as e:
            return None
    def CV(self, quer):
        url = 'https://cv.ee/api/v1/vacancy-search-service/search'
        params = {
            'limit': 10,
            'offset': 0,
            'keywords[]': quer,
            'lang': 'ru'
        }
        result = []  # Список для сбора вакансий
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                vacancies = data.get('vacancies', [])
                
                if not vacancies:
                    print("На CV.ee ничего не найдено")
                    return [] 

                for v in vacancies:
                    item = {
                        'company': v.get('employerName'),     # Название фирмы 
                        'too':v.get('positionTitle'),
                        'salary_from': v.get('salaryFrom'),
                        'salary_to': v.get('salaryTo'),
                        'id': v.get('id')
                    }
                    result.append(item)
                
                return result 
            else:
                print(f"Ошибка CV.ee: {response.status_code}")
                return []

        except Exception as e:
            print(f"Ошибка в методе CV: {e}")
            return []

    def get_job(self, query):
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
