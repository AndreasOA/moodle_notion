from selenium import webdriver
from selenium import *
import requests
import json
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from time import sleep
import re

month_dict = {
    "January": "01",
    "February": "02",
    "March": "03",
    "April": "04",
    "May": "05",
    "June": "06",
    "July": "07",
    "August": "08",
    "September": "09",
    "October": "10",
    "November": "11",
    "December": "12"
}


class MoodleReader:
    def __init__(self, username, password, telegram_api,
                 telegram_chat, phone, token, databaseId,
                 debug = True, notify_user = False) -> None:
        options = webdriver.ChromeOptions() 
        options.add_argument("user-data-dir=/Users/ao/Library/Application Support/Google/Chrome") #Path to your chrome profile
        options.add_argument("--no-proxy-server")
        options.add_argument("--disable-extensions")
        options.add_argument("disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(r'chromedriver', chrome_options=options)
        self.username = username
        self.password = password
        self.debug = debug
        self.notify_user = notify_user
        self.token = token
        self.databaseId = databaseId
        self.URL = f"https://api.telegram.org/bot{telegram_api}/sendMessage?chat_id={telegram_chat}&text="
        ########################        # Start
        self.driver.get('https://moodle.jku.at/jku/my/')
        #self.driver.maximize_window()



    def login(self) -> None:
        try:
            self.driver.get('https://moodle.jku.at/jku/login/index.php')
            sleep(5)
            email_input = self.driver.find_element_by_id('username')
            email_input.send_keys(self.username)
            pw_input = self.driver.find_element_by_id('password')
            pw_input.send_keys(self.password)
            self.driver.find_element_by_name('_eventId_proceed').click()
        except NoSuchElementException:
            print('already logged in')


    def getDeadlines(self) -> list:
        try:
            self.driver.get('https://moodle.jku.at/jku/my/')
            sleep(5)
            page_switch_parent = self.driver.find_element_by_class_name('columnleft')
            page_switches = page_switch_parent.find_elements_by_class_name('page-item')
            disabled_button = page_switch_parent.find_elements_by_class_name('disabled')[-1]
            while page_switches[1] != disabled_button:
                page_switches[1].click()
                try:
                    disabled_button = page_switch_parent.find_element_by_class_name('disabled')
                except NoSuchElementException:
                    print('Currently no disabled Button')
                sleep(0.3)
            event_parent = self.driver.find_element_by_class_name('tab-content')
            events = event_parent.find_elements_by_class_name('event-name-container')
            event_list = []
            for event in events:
                event_data = event.find_element_by_tag_name('a')
                if self.debug:
                    print(event_data.get_attribute('aria-label'))
                event_list.append(event_data.get_attribute('aria-label'))

            return event_list
        except NoSuchElementException:
            print('No events')
    

    def filterDeadlines(self, data: list) -> list:
        events_filtered = []
        for event in data:
            if "zoom" not in event.lower() and "sessions" not in event.lower():
                if " VL " in  event or " VO " in  event or " UE " in  event or " KV " in  event:
                    rest, date = event.split(', 2023S ist ')
                    date = date.replace(' fällig', '')
                    date, time = date.split(', ')
                    day, month, year = date.split(' ')
                    day = day.replace('.', '')
                    day = '0' + day if len(day) == 1 else day
                    month = month_dict[month]
                    date = f'{year}-{month}-{day}'
                    opts = [', VL ', ', VO ', ', UE ', ', KV ']
                    for opt in opts:
                        try:
                            title, course = rest.split(opt)
                            title = title.replace('Aktivität ', '')
                            try:
                                title = title.split(' (')[0]
                            except:
                                pass
                            try:
                                title = title.split(' ist')[0]
                            except:
                                pass
                            course = 'UE ' + course
                            break
                        except:
                            print('not that mode')
                    
                    course, teacher = course.split(', ')
                    if course + "///" + date not in events_filtered:
                        events_filtered.append([title, course, date])

        return events_filtered
    

    def readNotionDb(self) -> dict:
        headers = {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        readUrl = f"https://api.notion.com/v1/databases/{self.databaseId}/query"
        res = requests.request("POST", readUrl, headers=headers)
        data = res.json()

        return data


    def filterUploadData(self, notionData: dict, moodleData) -> list:
        notionData = notionData['results']
        event_names = []
        foundMatchingEvent = False
        for title, course, date in moodleData:
            foundMatchingEvent = False
            for event in notionData:
                try:
                    eventName = event['properties']['Name']['title'][0]['text']['content']
                    dueDate = event['properties']['Due']['date']['start']
                    eventStatus = event['properties']['Status']['select']['name']
                except TypeError:
                    eventName= ''
                
                if eventName == (title + ' - ' + course):
                    foundMatchingEvent = True
                    break
                   
            if not foundMatchingEvent:
                event_names.append([title + ' - ' + course, date])

        return event_names
            


    def createDbElement(self, name: str, dueDate: str) -> str:
        updateData = {
            "parent": {
                "database_id": self.databaseId
            },
            "properties": {
                "Status": {
                    "select": {
                        "name": "Not started"
                    }
                },
                "Name": {
                    "title": [
                        {
                            "type": "text",
                            "text": {
                            "content": name
                            }
                        }
                    ]
                },
                "Due": {    
                    "date": {
                    "start": dueDate
                    }
                }
            }
        }
        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": "Bearer " + self.token,
            "accept": "application/json",
            "Notion-Version": "2022-06-28",
            "content-type": "application/json"
        }

        response = requests.post(url, json=updateData, headers=headers)

        return json.loads(response.text)
    
    def updateNotionDeadlines(self) -> None:
        self.login()
        sleep(5)
        deadlines = self.getDeadlines()
        sleep(5)
        self.driver.close()
        filteredModdleData = self.filterDeadlines(deadlines)
        notionData = self.readNotionDb()
        newDeadlines = self.filterUploadData(notionData, filteredModdleData)
        for name, dueDate in newDeadlines:
            resp = self.createDbElement(name, dueDate)
            if self.debug:
                print(resp)
            if self.notify_user:
                try:
                    test = resp['object']
                    status = '\u2705'
                except:
                    status = '\u274c'
                self.notifyUser(name, dueDate, status)
    

    def notifyUser(self, name: str, date: str, status: str):
        statusMsg = ''
        if len(status) != 0:
            statusMsg = '\nStatus: ' + status
        requests.get(self.URL+f'New Deadline!!!\nName: {name}\nDue: {date}{statusMsg}').json()


if __name__ == "__main__":
    f = open("misc/credentials.json")
    data = json.load(f)
    f.close()
    phone = ''

    moodle = MoodleReader(data['moodle']['username'], 
                                        data['moodle']['password'],
                                        data['telegram']['api_token'],
                                        data['telegram']['chat_id'],
                                        phone,
                                        data['notion']['token'],
                                        data['notion']['database_id'],
                                        True, 
                                        True
                                        )

    moodle.updateNotionDeadlines()
