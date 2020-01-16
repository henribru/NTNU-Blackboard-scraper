'''
Here are some functions used to interface the blackboard API's
'''

def getCourses(session, userId, offset):
	parameters = {
		'userId': userId,
		'offset':offset,
        'availability.available':'Yes',
        'expand':'course'
    }
	json = session.get('https://ntnu.blackboard.com/learn/api/public/v1/users/'+userId+'/courses', params = parameters)
	return json
