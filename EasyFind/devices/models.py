from mongoengine import *
import datetime
import personal_info
connect('easyfind',host='127.0.0.1', port=27017)

class Device(Document):
	#uuid唯一
	_id = ObjectIdField()
	name = StringField(required=True)
	uuid = StringField(required=True,unique=True)
	owner = ReferenceField('personal_info.models.User')
	createTime = DateTimeField(default=datetime.datetime.now)
	editTime = DateTimeField(default=datetime.datetime.now)
