# Download your Blackboard content at NTNU
# Nicholas Braaten, 2019

from bs4 import BeautifulSoup as bs
from bs4 import Comment
import requests
import os
import unicodedata
import string

#s = None # Global session-variabel

class GlobalSettings():
	def __init__(self):
		self.rootDir = os.path.abspath(os.path.curdir)
		self.downloadDir = os.path.join(self.rootDir, 'Nedlastinger')
		self.session = requests.Session()

class Courses():
	def __init__(self, id, number, semester, kode, name):
		self.semester = semester
		self.id = id
		self.name = name
		self.nr = number	# Kønummer
		self.kode = kode	# Emnekode

class Content():
	def __init__(self):
		self.courseId
		self.contentId


s = GlobalSettings()


def login_settings(username=None, password=None):	# Husk å endre dette!
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
	#global s
	url = "https://ntnu.blackboard.com/webapps/login/" # URL for innlogging

	login_data = login_settings()



	#s = requests.Session()
	r = s.session.get(url) # Henter nettsiden
	soup = bs(r.content, 'html5lib')
	login_data['blackboard.platform.security.NonceUtil.nonce'] = soup.find('input', attrs={'name': 'blackboard.platform.security.NonceUtil.nonce'})['value']
	r = s.session.post(url, data=login_data) # Send innlogging til blackboard
	soup = bs(r.content, 'html5lib')
	fullt_navn = soup.find(id='global-avatar').next_element.strip()  # Henter ut fullt navn

	print("*"*75+"\nLogget inn som", fullt_navn,"\n"+"*"*75) # Skriver ut fullt navn.
	return soup

def searchInString(string, startString, stopString):
	startIndex = string.find(startString)
	stopIndex = string.find(stopString, startIndex)

	return string[startIndex+len(startString):stopIndex]

def getCourseList():
	#global s
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
			#emner.append((emnekode, semester, navn, courseId, teller)) # Lagre i tuppel
			teller += 1

	return emner

# printe liste over emner
def printCourseList(emner):

	print('nr'.ljust(4)+ 'Emnekode'.ljust(12) + 'Semester'.ljust(12)+'Emne'.ljust(50))
	print('-'*75)
	#for j in emner:
	#	print(str(j[4]).ljust(3) + '|' + j[0].ljust(12) + j[1].ljust(12) + j[2].ljust(50))
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
	response = s.session.post('https://ntnu.blackboard.com/webapps/blackboard/execute/course/menuFolderViewGenerator', data = parameters)
	return response


## Lager gyldige filnavn
def makeValidFilename(filename):
	whitelist = "-_.()æøåÆØÅ %s%s" % (string.ascii_letters, string.digits)
	char_limit = 255
	# Bytt ut mellomrom
	filename = filename.replace(' ','_')
	
	
	cleanFilename = unicodedata.normalize('NFKD', filename).encode('UTF-8', 'ignore').decode()
	
	# Behold aksepterte tegn
	cleanFilename = ''.join(c for c in cleanFilename if c in whitelist)

	return cleanFilename[:char_limit]


# Skrive data til fil
def printToFile(directory, filename, data):
	filename = makeValidFilename(filename)
	path = os.path.join(directory, filename) 
	with open(path, 'wb') as file:
		file.write(data)


courses = getCourseList()	# Hent et array med tuppler av alle emner
printCourseList(courses)	# Skriv ut liste med alle emner
FIFO = consoleCourseList(courses) # Opprette en kø av valgte emner

os.makedirs(s.downloadDir, exist_ok=True)
# DEQUEUE
while len(FIFO) > 0:
	pop = FIFO.pop(0)
	tree = getCourseTree(pop.id)
	printToFile(s.downloadDir, pop.name+".txt", tree.content)