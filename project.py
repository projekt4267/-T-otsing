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

    def get_job(self, query):
        jobs = self.töökassa(query)

        for job in jobs:

            detail = self.tookassaFull(job["id"])
            if not detail:
                continue

            company = detail.get("toopakkuja", {}).get("nimi") #получение имени работадателя
            salary_from = detail.get("tookohaAndmed", {}).get("tootasuAlates")
            salary_to = detail.get("tookohaAndmed", {}).get("tootasuKuni")
            addresses = detail.get("aadressid", [])
            adress=None
            if addresses:
                adress=addresses[0].get("aadressTekst")
            spisok=[]
            spisok.append({ #список
                'company':company,
                'salary_from':salary_from,
                'salary_to':salary_to,
                'addresses':adress
            }
            )
            for i in spisok:
                print(f"{i['company']},{i['addresses']}, {i['salary_from']}-{i['salary_to']}")

test = saits()
test.get_job('ehitaja')
