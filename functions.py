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