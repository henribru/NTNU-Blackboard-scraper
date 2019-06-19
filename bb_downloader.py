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
	login(session)
	soup = session.get('https://ntnu.blackboard.com/webapps/ee-Eesypluginv2-BBLEARN/loader2.jsp').text
	info = json.loads(searchInString(soup, 'var eesy_userInfo=', ';\n'))
	
	return info

def getCourses(session, userId):
	parameters = {
		'userId': userId
	}
	response = session.get('https://ntnu.blackboard.com/learn/api/public/v1/users/'+userId+'/courses', params = parameters).json()
	
	result = response['results']

	while 'paging' in response:
		if 'nextPage' in response['paging']:
			response = session.get('https://ntnu.blackboard.com/' + response['paging']['nextPage']).json()
			result += response['results']
		else:
			break
	
	return result

def getCourseInfo(session, course):
	courseId = course['courseId']
	parameters = {
		'courseId': courseId
	}
	
	return session.get('https://ntnu.blackboard.com/learn/api/public/v1/courses/'+courseId, params = parameters).json()

def getTermInfo(session, termId):
	parameters = {
	'termId': termId
	}
	
	return session.get('https://ntnu.blackboard.com/learn/api/public/v1/terms/'+termId, params = parameters).json()


s = requests.Session()
userInfo = getUserInfo(s)

while len(userInfo) == 0:
	print("\nInnloggin feilet. Prøv igjen.")
	userInfo = getUserInfo(s)
print('*'*50, '\nLogget inn som', userInfo['fullname'], '\n'+'*'*50)
userId = userInfo['pk1']

courses = getCourses(s, userId)

courseByTerm = {}
for i in courses:
	courseInfo = getCourseInfo(s, i)
	term = getTermInfo(s, courseInfo['termId'])['name']
	if term not in courseByTerm:
		courseByTerm[term] = []
	courseByTerm[term].append(courseInfo)

print(json.dumps(courseByTerm, indent=2))

print(courseByTerm['Høst 2018'])