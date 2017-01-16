from mongoengine import *
import datetime
import devices
from PIL import Image
connect('easyfind',host='127.0.0.1', port=27017)

# Create your models here.
class User_location(Document):
	province = StringField()
	city = StringField()
	district = StringField()
	street = StringField()
	createTime = DateTimeField(default=datetime.datetime.now)
	editTime = DateTimeField(default=datetime.datetime.now)

class User(Document):
	_id = ObjectIdField()
	account = StringField(max_length=100,required=True,unique=True)
	password = StringField(min_length=6,max_length=20,required=True)
	nickname = StringField(max_length=10)
	gender = StringField()
	email = EmailField()
	phone = StringField(max_length=20)
	province = StringField()
	city = StringField()
	friends =  ListField(StringField())
	reputation = IntField(default=1000)
	createTime = DateTimeField(default=datetime.datetime.now)
	editTime = DateTimeField(default=datetime.datetime.now)
	location = ReferenceField(User_location)
	weight = IntField()
	#图片以URL形式保存
	picture = ImageField(size=(800, 600, True),collection_name='images')
	picUrl = StringField()
	isLogin = BooleanField(default=False)
	token = StringField()
	messages = ListField(StringField())
	taskOnRate = FloatField()

class Message(Document):
	_id = ObjectIdField()
	identifier = StringField(required=True,unique=True)
	tag = StringField()
	createTime = DateTimeField(default=datetime.datetime.now)
	content = StringField()
	is_read = BooleanField(default=False)