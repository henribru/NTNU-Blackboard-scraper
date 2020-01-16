import sys, os, json
from PyInquirer import style_from_dict, Token, prompt, Separator
from pprint import pprint


'''
Here are some functions
'''

def searchInString(string, startString, stopString=None):
	stopIndex = len(string)
	if startString != None:
		startIndex = string.find(startString)
	else:
		startIndex = 0
		startString = ''
	if stopString != None:
		stopIndex = string.find(stopString, startIndex+len(startString))
		if stopIndex == -1:
			return string[startIndex+len(startString):]

	return string[startIndex+len(startString):stopIndex]


def filtertrue(predicate, iterable):
    # filterfalse(lambda x: x%2, range(10)) --> 0 2 4 6 8
    if predicate is None:
        predicate = bool
    for x in iterable:
        if predicate(x):
            yield x


def clear_screen(name=None):
	if sys.platform == 'win32':
		os.system('cls')
	else:
		os.system('clear')
	
	print('-'*43)
	print(' Nedlastingsskript for Blackboard ved NTNU')
	print('-'*43)
	
	if name != None:
		print('Logget inn som', name, '\n')

def json_to_file(payload, file_path):
	os.makedirs("debug", exist_ok=True)
	path = os.path.join("debug", file_path)
	with open(path, 'w', encoding='utf-8') as f:
		json.dump(payload, f, ensure_ascii=False, indent=4)

def coursePrompt(course_list):
	questions = [{
		'type': 'checkbox',
        'message': 'Velg emner',
        'name': 'courseIds',
        'choices': []
	}]
	for term in course_list:
		questions[0]['choices'].append(Separator(term))
		for course in course_list[term]:
			questions[0]['choices'].append(
				{
					'name': course['name'],
					'value': course['id']
				}
			)
	return prompt(questions)