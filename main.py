# Download your Blackboard content at NTNU
# Nicholas Braaten, 2019

from bs4 import BeautifulSoup as bs
from bs4 import Comment
import requests

s = None # Global session-variabel

def login_settings():

    username = input('Brukernavn: ')
    password = input("Passord: ")
    return {
        'user_id' : username,
        'password': password,
        'login':'Logg på',
        'action':'login',
        'new_loc':'',
    }

def login():
	global s
	url = "https://ntnu.blackboard.com/webapps/login/" # URL for innlogging

	login_data = login_settings()



	s = requests.Session()
	r = s.get(url) # Henter nettsiden
	soup = bs(r.content, 'html5lib')
	login_data['blackboard.platform.security.NonceUtil.nonce'] = soup.find('input', attrs={'name': 'blackboard.platform.security.NonceUtil.nonce'})['value']
	r = s.post(url, data=login_data) # Send innlogging til blackboard
	soup = bs(r.content, 'html5lib')
	fullt_navn = soup.find(id='global-avatar').next_element.strip()  # Henter ut fullt navn

	print("*"*75+"\nLogget inn som", fullt_navn,"\n"+"*"*75) # Skriver ut fullt navn.
	return soup

def searchInString(string, startString, stopString):
    startIndex = string.find(startString)
    stopIndex = string.find(stopString, startIndex)

    return string[startIndex+len(startString):stopIndex]

def getCourseList():
	global s
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
	rawCourseList = s.post('https://ntnu.blackboard.com/webapps/portal/execute/tabs/tabAction', data = ajaxRefresh)
	rawCourseList=  bs(rawCourseList.content, 'html5lib') # Behandle motatt data med beautiful soup

	#Sortere etter semester:
	teller = 1
	courses = rawCourseList.find_all(class_='termHeading-coursefakeclass')
	emner = []
	for sem in courses:
		semester = sem.span.next_sibling.strip()
		emne = sem.find_next('div')
		emne = emne.find_all('a')
		for a in emne:
			streng = str(a.text)
			emnekode = streng[:streng.find(' ')].strip()
			navn = streng[streng.find(' '):streng.find('(')-1].strip()
			courseId = searchInString(str(a.get('href')), 'id=', '&')
			emner.append((emnekode, semester, navn, courseId, teller)) # Lagre i tuppel
			teller += 1

	return emner

# printe liste over emner
def printCourseList(emner):

	print('nr'.ljust(4)+ 'Emnekode'.ljust(12) + 'Semester'.ljust(12)+'Emne'.ljust(50))
	print('-'*75)
	for j in emner:
		print(str(j[4]).ljust(3) + '|' + j[0].ljust(12) + j[1].ljust(12) + j[2].ljust(50))
	print('-'*75)

# Spør hvilke emner skal lastes ned
def consoleCourseList(emner):
	antEmner = len(emner)

	print("List opp emnene du vil laste ned. 0 = alle\nEksempel: 1 3 9 10 15")
	choise = input("Valg: ")
	queue = []
	if choise == "0":
		for i in range(antEmner):
			queue.append(i)
	else:
		for j in [i.strip() for i in choise.split(' ')]:
			queue.append(int(j)-1)

	return queue

# Hente innholdsstruktur i valgte emner
def getCourseTree(id):
	parameters = {
		'initTree': 'true',
		'storeScope': 'Session',
		'course_id': id,
		'displayMode': 'courseMenu_newWindow',
		'editMode': 'false',
		'openInParentWindow': 'true'
	}
	response = s.post('https://ntnu.blackboard.com/webapps/blackboard/execute/course/menuFolderViewGenerator', data = parameters)

courses = getCourseList()
printCourseList(courses)
FIFO = consoleCourseList(courses) # Opprette en kø av valgte emner

# DEQUEUE
while len(FIFO) > 0:
	pop = FIFO.pop(0)
	id = courses[pop][3]
	getCourseTree(id)
