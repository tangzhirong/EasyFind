
from mongoengine import *
import datetime
import personal_info
import devices
from PIL import Image

#链接本地easyfind数据库
connect('easyfind',host='127.0.0.1', port=27017)

#任务Document
class Task(Document):
	_id = ObjectIdField()
	name = StringField(max_length=50,required=True,unique=True)
	publisher = ReferenceField('personal_info.models.User')
	publisher_name = StringField()
	device = ReferenceField('devices.models.Device')
	info = StringField(max_length=200)

	#图片以URL形式保存
	picture = ImageField(size=(800, 600, True),collection_name='images')
	picUrl = ListField(StringField())
	#通过下拉栏选择搜索地址
	search_province = StringField()
	search_city = StringField()
	search_district = StringField()
	search_street = StringField()

	#悬赏总额为整数
	reward = IntField()

	#任务发布、编辑时间默认为当前时间
	createTime = DateTimeField(default=datetime.datetime.now)
	editTime = DateTimeField(default=datetime.datetime.now)
	finishTime = DateTimeField()

	#任务状态：‘未分配’、‘监测中’、‘已定位’、‘已完结’
	status = StringField(max_length=20,default='未分配')
	isDeliver = StringField()

	participates = ListField(ReferenceField('personal_info.models.User'))
	participates_name = ListField(StringField())
	participates_account = ListField(StringField())
	money_left = IntField()

#定位Document
class TaskDiscover(Document):
	discover  = ReferenceField('personal_info.models.User')
	task = ReferenceField(Task)
	longitude = FloatField()
	latitude = FloatField()

	#j待定为浮点型
	distance= FloatField()
	rssi = FloatField()

	discovertime = DateTimeField(default=datetime.datetime.now)

	#定位信息默认未参与计算
	is_used = BooleanField(default=False)

#任务竞价分配Document
class Task_deliver(Document):
	user = ReferenceField('personal_info.models.User')
	task = ReferenceField(Task)
	gps_x = FloatField()
	gps_y = FloatField()
	money = IntField()
	createTime = DateTimeField(default=datetime.datetime.now)
	editTime = DateTimeField(default=datetime.datetime.now)

class TaskResult(Document):
	_id = ObjectIdField()
	task= ReferenceField(Task)
	longitude = FloatField()
	latitude = FloatField()
	discovertime = DateTimeField()

class SystemIndex(Document):
	taskFinishedRate = FloatField()
	time = DateTimeField()