from bs4 import BeautifulSoup as bs
from bs4 import Comment
import requests
import os
import sys
import unicodedata
import string
import json
import mimetypes
from functions import *

def login(session):
	username = input("Brukernavn: ")
	password = input("Passord: ")

	url = "https://ntnu.blackboard.com/webapps/login/" # URL for innlogging
	r = session.get(url) # Henter nettsiden
	soup = bs(r.content, 'html5lib')
	nonce = soup.find('input', attrs={'name': 'blackboard.platform.security.NonceUtil.nonce'})['value']
	login_data = {
		'user_id' : username,
		'password': password,
		'action':'login',
		'blackboard.platform.security.NonceUtil.nonce': nonce
	}
	
	r = session.post(url, data=login_data) # Send innlogging til blackboard

def getContentAttachment(session):
    courseId = '_9418_1'
    contentId = '_503143_1'
    payload = {
        'Content-type' : 'application/json'
    }
    parameters = {
        'courseId':courseId,
        'contentId': contentId,
        'recursive': True
  
    }
    return session.get('https://ntnu.blackboard.com/learn/api/public/v1/courses/'+courseId+'/contents/'+contentId, data = payload ,params = parameters)

def getUserInfo(session):
	soup = session.get('https://ntnu.blackboard.com/webapps/ee-Eesypluginv2-BBLEARN/loader2.jsp').text
	info = json.loads(searchInString(soup, 'var eesy_userInfo=', ';\n'))
	return info


def getCourses(session, userId):
	parameters = {
		'userId': userId,
		'offset':0
    }
	return session.get('https://ntnu.blackboard.com/learn/api/public/v1/users/'+userId+'/courses', params = parameters)

s = requests.Session()
login(s)
userId = getUserInfo(s)['pk1']
print(json.dumps(getCourses(s, userId).json(), indent=2))
