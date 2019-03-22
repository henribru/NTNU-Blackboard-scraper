# Download your Blackboard content at NTNU
# Nicholas Braaten, 2019

from bs4 import BeautifulSoup as bs
from bs4 import Comment
import requests
import os
import sys
import unicodedata
import string
import json


class GlobalSettings():
	def __init__(self):
		self.rootDir = os.path.abspath(os.path.curdir)
		self.downloadDir = os.path.join(self.rootDir, 'Blackboard-NTNU')
		self.session = requests.Session()

class Courses():
	def __init__(self, id, number, semester, kode, name):
		self.semester = semester
		self.id = id
		self.name = name
		self.nr = number	# Kønummer
		self.kode = kode	# Emnekode

class Content():
	def __init__(self, courseID, contentID, courseName):
		self.courseId = courseID
		self.coursename = courseName
		self.id = contentID
		self.coursePath = None
		self.type = None
		self.response = None
		self.size = 0
		self.name = None
		self.url = ("https://ntnu.blackboard.com/webapps/blackboard/execute/content/file?cmd=view&content_id="+
			contentID+
			"&course_id="+
			courseID+
			"&launch_in_new=true")

s = GlobalSettings()


def login_settings(username=None, password=None):
	if not(username and password):
		username = input("Brukernavn: ")
		password = input("Passord: ")
	return {
		'user_id' : username,
		'password': password,
		'login':'Logg på',
		'action':'login',
		'new_loc':'',
	}

def login():
	url = "https://ntnu.blackboard.com/webapps/login/" # URL for innlogging

	login_data = login_settings()

	r = s.session.get(url) # Henter nettsiden
	soup = bs(r.content, 'html5lib')
	login_data['blackboard.platform.security.NonceUtil.nonce'] = soup.find('input', attrs={'name': 'blackboard.platform.security.NonceUtil.nonce'})['value']
	r = s.session.post(url, data=login_data) # Send innlogging til blackboard
	soup = bs(r.content, 'html5lib')
	fullt_navn = soup.find(id='global-avatar').next_element.strip()  # Henter ut fullt navn

	print("*"*75+"\nLogget inn som", fullt_navn,"\n"+"*"*75) # Skriver ut fullt navn.
	return soup

def searchInString(string, startString, stopString=None):
	stopIndex = len(string)
	startIndex = string.find(startString)
	if stopString != None:
		stopIndex = string.find(stopString, startIndex+len(startString))

	return string[startIndex+len(startString):stopIndex]

def getCourseList():
	soup = login()
	ajaxRefresh = {
		'action': 'refreshAjaxModule',
	}

	# Finne riktig modul som inneholder emnene:
	for comment in soup.find_all(string=lambda text:isinstance(text, Comment)):
		if comment.strip() in['extid:learning/advancedcourses:']:
			updateAjaxScript = str(comment.find_next('script'))

	# Henter ut riktig form data for å requeste innhold i modulen
	updateAjaxScript = searchInString(updateAjaxScript, 'refreshAjaxModule', '\n') # Korte ned på søkevariabelen
	ajaxRefresh['modId'] = searchInString(updateAjaxScript, 'modId=', '&')
	ajaxRefresh['tabId'] = searchInString(updateAjaxScript,'tabId=','&')
	ajaxRefresh['tab_tab_group_id'] = searchInString(updateAjaxScript,'tab_tab_group_id',"'")

	# Poster data for å requeste innholdet i modulen
	rawCourseList = s.session.post('https://ntnu.blackboard.com/webapps/portal/execute/tabs/tabAction', data = ajaxRefresh)
	rawCourseList=  bs(rawCourseList.content, 'html5lib') # Behandle motatt data med beautiful soup
	
	#Sortere etter semester:
	teller = 1
	courses = rawCourseList.find_all(class_='termHeading-coursefakeclass')
	emner = {} # Dict av emneobjekter
	for sem in courses:
		semester = sem.span.next_sibling.strip()
		emne = sem.find_next('div')
		emne = emne.find_all('a')
		for a in emne:
			streng = str(a.text)
			emnekode = streng[:streng.find(' ')].strip()
			navn = streng[streng.find(' '):streng.find('(')-1].strip()
			courseId = searchInString(str(a.get('href')), 'id=', '&')
			emner[teller] = Courses(courseId, teller, semester, emnekode, navn) # Lagre som objekt i dictionary
			teller += 1

	return emner

# printe liste over emner
def printCourseList(emner):

	print('nr'.ljust(4)+ 'Emnekode'.ljust(12) + 'Semester'.ljust(12)+'Emne'.ljust(50))
	print('-'*75)
	for k in emner:
		print(str(emner[k].nr).ljust(3) + '|' + emner[k].kode.ljust(12) + emner[k].semester.ljust(12) + emner[k].name.ljust(50))
	print('-'*75)

# Spør hvilke emner skal lastes ned
def consoleCourseList(emner):
	print("List opp emnene du vil laste ned. 0 = alle\nEksempel: 1 3 9 10 15")
	choise = input("Valg: ")
	queue = []

	for k in emner:
		if (str(k) in [i.strip() for i in choise.split(' ')]) or (choise == '0'):	# Bare ta vare på gyldige instanser
			queue.append(emner[k])

	return queue

# Hente innholdsstruktur i valgte emner
def getCourseTree(id):
	parameters = {
		'initTree': 'true',
		'storeScope': 'Session',
		'expandAll': 'true',
		'course_id': id,
		'displayMode': 'courseMenu_newWindow',
		'editMode': 'false',
		'openInParentWindow': 'true'
	}

	response = s.session.post('https://ntnu.blackboard.com/webapps/blackboard/execute/course/menuFolderViewGenerator',
		data = parameters)
	#print(response.json())
	#print(bs(response.content, 'lxml'))
	return response


## Lager gyldige filnavn
def makeValidFilename(filename):
	whitelist = "-_.()æøåÆØÅ %s%s" % (string.ascii_letters, string.digits)
	char_limit = 255
	# Bytt ut mellomrom
	#filename = filename.replace(' ','_')
	filename = filename.replace('/','-')
	filename = filename.replace('\\','-')
	
	# Behold aksepterte tegn
	cleanFilename = ''.join(c for c in filename if c in whitelist)

	return cleanFilename[:char_limit]

def formatFileSize(bytesize):
	size = str(bytesize)+" B"
	if bytesize >= 1e9:
		size = str(round(bytesize/1e9, 2)) + " GB"
	elif bytesize >= 1e6:
		size = str(round(bytesize/1e6, 1)) + " MB"
	elif bytesize >= 1e3:
		size = str(round(bytesize/1e3, 0)) + " kB"
	return size

# Skrive data til fil
def printToFile(directory, filename):
	CURSOR_UP = '\x1b[1A' # Cursor up one line
	ERASE = '\x1b[2K' # Erase current line
	filename = makeValidFilename(filename)
	os.makedirs(directory, exist_ok=True)
	path = os.path.join(directory, filename)
	print("\tEmne:", c.coursename)
	print("\tFil: ",filename)
	with open(path, 'wb') as file:
		initFileDownload(c.courseId, c.id)
		if c.size == 0:
			file.write(c.response.content)
		else:
			dl = 0
			totSizeString = formatFileSize(c.size)
			for data in c.response.iter_content(chunk_size=1024):
				dl += len(data)
				progressString = formatFileSize(dl) + "/" + totSizeString
				file.write(data)
				done = int(30 * dl / c.size)
				sys.stdout.write(ERASE+"\r\t[%s%s]\t%s" % ('|' * done, '.' * (30-done), progressString) )
				sys.stdout.flush()
	print(ERASE+(CURSOR_UP+ERASE)*3+'\rLastet ned',filename,"\n---" )


def initFileDownload(course, content, url = None):
	c.response = s.session.get(c.url, stream = True, allow_redirects=True)
	if ('Content-Type' in c.response.headers):
		c.type = c.response.headers['Content-Type']
	if c.type[0:9] == 'text/html':
		if str(c.response.content).find('document.location') > 0: # Venter med å hente content om unødvendig.
			newURL = searchInString(str(c.response.content), "document.location = \\\'", "\\\';")
			c.url = "https://ntnu.blackboard.com"+newURL
			initFileDownload(course, content)	# Rekursiv redirecting

	else:
		if ('Content-Length' in c.response.headers):
			c.size = int(c.response.headers['Content-Length'])
	

def initCourseDownload(jsonDict, courseObj, path, indent=-1):
	global c
	title = ''
	if indent>-1:
		# Finne navn på innhold:
		if jsonDict['type'] == "NODE":
			title = searchInString(jsonDict["contents"], 'title=\"', '\"')

		elif jsonDict['type'] == "HEADER":
			title = jsonDict['contents']


		if jsonDict["hasChildren"]:
			path = os.path.join(path, makeValidFilename(title))
			for i in jsonDict["children"]:
				initCourseDownload(i, courseObj, path, indent+1)
		elif jsonDict['type'] == "NODE":
			if searchInString(jsonDict['id'],'blackboard.data.content.Link$ReferredToType:','::') == 'CONTENT':
				content = searchInString(jsonDict['id'], 'CONTENT:::')
				#getFile(course.id, content, title, path)
				c = Content(courseObj.id, content, courseObj.name)
				#initFileDownload(courseObj.id, content)
				printToFile(path ,title)
	else:
		print('Initialiserer', courseObj.kode)
		for i in jsonDict["children"]:
			initCourseDownload(i, courseObj, path, indent+1)


## MAIN ##
courses = getCourseList()	# Hent et dict med emneobjekter
printCourseList(courses)	# Skriv ut liste med alle emner
courseQueue = consoleCourseList(courses) # Opprette en kø med emneobjekter av valgte emner

# DEQUEUE
while len(courseQueue) > 0:
	pop = courseQueue.pop(0)
	tree = getCourseTree(pop.id)
	tree = tree.json()
	#print('Initialiserer', pop.kode)
	path = os.path.join(s.downloadDir, makeValidFilename(pop.semester))	# Mappestruktur etter semester
	path = os.path.join(path, makeValidFilename(pop.name))
	contentQueue = {}
	initCourseDownload(tree, pop, path)
	
print('Ferdig')
