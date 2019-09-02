from __future__ import print_function, unicode_literals
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
	clear_screen()
	credentials = [
		{
        'type': 'input',
        'name': 'username',
        'message': 'Brukernavn:',
    },
	{
        'type': 'password',
        'name': 'password',
        'message': 'Passord:',
    }]
	answers = prompt(credentials)
	url = base_URL + "/webapps/login/" # URL for innlogging
	r = session.get(url) # Henter nettsiden
	soup = bs(r.content, 'html5lib')
	nonce = soup.find('input', attrs={'name': 'blackboard.platform.security.NonceUtil.nonce'})['value']
	login_data = {
		'user_id' : answers['username'],
		'password': answers['password'],
		'action':'login',
		'blackboard.platform.security.NonceUtil.nonce': nonce
	}
	
	r = session.post(url, data=login_data) # Send innlogging til blackboard """

def getContentAttachment(session, courseId, contentId):
	payload = {
		'Content-type' : 'application/json'
	}
	parameters = {
		'courseId':courseId,
		'contentId': contentId,
		'recursive': True
  
	}
	return session.get(base_URL + '/learn/api/public/v1/courses/'+courseId+'/contents/'+contentId, data = payload ,params = parameters)

def getUserInfo(session):
	login(session)
	soup = session.get(base_URL + '/webapps/ee-Eesypluginv2-BBLEARN/loader2.jsp').text
	info = json.loads(searchInString(soup, 'var eesy_userInfo=', ';\n'))
	
	return info

def getCourseList(session, userId):
	print("\nHenter liste med emner...")
	courses = []
	response = getCourses(session, userId, 0).json()

	while len(response['results']) > 0:
		courses += response['results']
		if 'paging' in response:
			if 'nextPage' in response['paging']:
				response = session.get(base_URL + '' + response['paging']['nextPage']).json()
	courses[:] = filtertrue(isCourseAvailable, courses)

	json_to_file(courses, "courses.json")
	return courses

def getCourseInfo(session, course):
	courseId = course['courseId']
	parameters = {
		'courseId': courseId
	}
	return session.get(base_URL + '/learn/api/public/v1/courses/'+courseId, params = parameters).json()

def getTermInfo(session, termId):
	parameters = {
	'termId': termId
	}
	
	return session.get(base_URL + '/learn/api/public/v1/terms/'+termId, params = parameters).json()

def getCourseContent(session, courseId):
	parameters = {
		'courseId': courseId,
		'recursive': True
	}
	content = session.get(base_URL + '/learn/api/public/v1/courses/'+courseId+'/contents', params = parameters).json()
	#json_to_file(content, courseId+'.json')
	return content

def getChildrenContent(session, courseId,contentId):
	parameters = {
		'courseId': courseId,
		'contentId': contentId,
		'recursive': True
	}
	content = session.get(base_URL + '/learn/api/public/v1/courses/'+courseId+'/contents/'+contentId+'/children', params = parameters).json()
	json_to_file(content, contentId+'.json')
	return content


base_URL = 'https://ntnu.blackboard.com'
s = requests.Session()
userInfo = getUserInfo(s)

while len(userInfo) == 0:
	print("\nInnlogging feilet. Prøv igjen.")
	userInfo = getUserInfo(s)
print('\nLogget inn som', userInfo['fullname'])
userId = userInfo['pk1']

courses = getCourseList(s, userId)

courseByTerm = {}
for i in courses:
	courseInfo = getCourseInfo(s, i)
	term = getTermInfo(s, courseInfo['termId'])['name']
	if term not in courseByTerm:
		courseByTerm[term] = []
	courseByTerm[term].append(courseInfo)

selected_courses = coursePrompt(courseByTerm)
for course in selected_courses['courseIds']:
	courseContent = getCourseContent(s, course)
	for item in courseContent['results']:
		if item['hasChildren'] == True:
			getChildrenContent(s, course, item['id'])
