import requests
from bs4 import BeautifulSoup
import fake_useragent
import time
import json
import concurrent.futures
#https://www.youtube.com/watch?v=0_xwepyuV1E 6:53

"""
По сути, мне сейчас узко направленный скрипт на hh.ru - следует обобщить,
Либо сделать отдельные скрипты для разных сайтов и уже между ними переключаться
Я думаю в данном случае будет лучше исполнить именно многопроцессорность запросов.

Сделать скрипты для напила всех заявок с разных сайтов.
Сделать скрипт, что будет запускать всех их и обрабатывать нужные данные

Потом полученные json обрабатывать в csv формат.

"""

def get_links(text):
    ua = fake_useragent.UserAgent()
    data = requests.get(
        url="https://krasnoyarsk.hh.ru/search/vacancy?L_save_area=true&text={text}&excluded_text=&salary=&currency_code=RUR&experience=doesNotMatter&order_by=relevance&search_period=0&items_on_page=50&page={page}",
        headers={"user-agent": ua.ff}
    )
    soup = BeautifulSoup(data.content, 'lxml')
    try:
        page_count = int(soup.find("div", attrs={"class":"pager"}).find_all("span", recursive=False)[-1].find("a").find("span").text)
    except:
        page_count = 0
    for page in range(page_count):
        try:
            data = requests.get(
                url="https://krasnoyarsk.hh.ru/search/vacancy?L_save_area=true&text={text}&excluded_text=&salary=&currency_code=RUR&experience=doesNotMatter&order_by=relevance&search_period=0&items_on_page=50&page={page}",
                headers={"user-agent": ua.random}
            )
            if data.status_code == 200:
                soup = BeautifulSoup(data.content, "lxml")
                for i in soup.find("div", attrs={"data-qa":"vacancy-serp__results"}).find_all("div", attrs={"class":"serp-item"}):
                    #Находятся все ссылки в блоке, после чего они все приписываются в лист. Из него
                    #берётся первая ссылка, что ссылат на работу, а не на компанию
                    yield f'{i.find_all("a", "bloko-link")[0].attrs["href"].split("?")[0]}'
        except Exception as e:
            print(f"{e}")
        time.sleep(0.1)
    print(page_count)
def get_resume(link):
    ua = fake_useragent.UserAgent()
    data = requests.get(
        url=link,
        headers={"user-agent": ua.random}
    )
    if data.status_code != 200:
        return
    soup = BeautifulSoup(data.content, "lxml")

    #Название вакансии, описание вакансии, зп, регион, работодатель
    #Требования, опыт работы, график работы ,

    try:
        name = soup.find(attrs={"data-qa":"vacancy-title"}).text
    except:
        name =""
    try:
        about = soup.find(attrs={"class":"g-user-content"}).find("p").text
    except:
        about = ""
    try:
        salary = soup.find(attrs={"data-qa":"vacancy-salary-compensation-type-net"}).text.replace("\u2009","").replace("\xa0", " ")
    except:
        salary =""
    try:
        region = soup.find("p", attrs={"data-qa":"vacancy-view-location"}).text
    except:
        region = ""
    try:
        exp = soup.find(attrs={"data-qa":"vacancy-experience"}).text.replace("\u2009","").replace("\xa0", " ")
    except:
        exp = ""
    resume = {
        "name":name,
        "salary":salary,
        "link":link,
        "exp": exp
    }
    return resume

links = get_links("BI-analytic")
data = []
def put_resume_to_work(link):
    data.append(get_resume(link))

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(put_resume_to_work, links)


with open("data.json","w",encoding="utf-8") as f:
    json.dump(data,f,indent=4,ensure_ascii=False)

