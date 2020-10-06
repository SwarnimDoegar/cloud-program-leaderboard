from django.conf import settings
from core.models import UserModel
import requests 
from bs4 import BeautifulSoup
from celery import shared_task
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# define the scope
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

# add credentials to the account
creds = ServiceAccountCredentials.from_json_keyfile_name('core/qwiklabs-ranking-dsccu-2a5152d2a2f2.json', scope)

# authorize the clientsheet 
client = gspread.authorize(creds)

sheet = client.open('30 Days of Google Cloud event')
sheet_instance = sheet.get_worksheet(1)



CHALLENGES_AVAILABLE = [
    'Integrate with Machine Learning APIs', 
    'Perform Foundational Data, ML, and AI Tasks in Google Cloud', 
    'Explore Machine Learning Models with Explainable AI', 
    'Engineer Data in Google Cloud', 
    'Insights from Data with BigQuery', 
    'Deploy to Kubernetes in Google Cloud', 
    'Build and Secure Networks in Google Cloud', 
    'Deploy and Manage Cloud Environments with Google Cloud', 
    'Set up and Configure a Cloud Environment in Google Cloud', 
    'Perform Foundational Infrastructure Tasks in Google Cloud', 
    'Getting Started: Create and Manage Cloud Resources',
    'Google Cloud Essentials'
    ]



URL = "https://google.qwiklabs.com/public_profiles/7e0abd7b-15e0-4e51-8db2-1d552322ad3c"
def GetCountAndResourcesDone(URL):
    COMPLETED_QUESTS = []
    r = requests.get(URL) 
    soup = BeautifulSoup(r.content, 'html5lib')
    quests = soup.findAll('div', attrs = {'class':'public-profile__badges'})   
    for row in quests[0].findAll('div', attrs = {'class':'public-profile__badge'}): 
        divs = row.findChildren("div" , recursive=False)
        badge = {}
        date = divs[2].text.strip()[7:].split(" ")
        if divs[1].text.strip() in CHALLENGES_AVAILABLE:
            badge['name'] = divs[1].text.strip()
            badge['img'] = divs[0].img['src']
            badge['earned'] = divs[2].text.strip()[7:]
        COMPLETED_QUESTS.append(badge)

    profile = soup.findAll('div', attrs = {'class':'public-profile__hero'})[0]
    dp = profile.img['src']
    name = profile.h1.text
    return {
        "quests":COMPLETED_QUESTS,
        "dp":dp,
        "name":name.strip()
    }



@shared_task
def summary():
    print("Starting scrap")
    URLS = sheet_instance.col_values(3)[1:]
    URLS = [i for i in URLS if i]
    for  i in URLS:
        try:
            data = GetCountAndResourcesDone(i)
        except:
            data = {
                "quests":[],
                "dp":'',
                "name":''
            }
        user = UserModel.objects.filter(qwiklabs_id=i)
        if user.exists():
            user = user[0]
            user.quests_status = len(data['quests'])
            user.quests = data['quests']
            user.name = data['name']
            user.dp = data['dp']
        else:
            user = UserModel()
            user.qwiklabs_id = i
            user.quests_status = len(data['quests'])
            user.quests = data['quests']
            user.name = data['name']
            user.dp = data['dp']
        user.save()
        print(i)
