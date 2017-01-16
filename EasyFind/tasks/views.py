from django.shortcuts import render
from django.shortcuts import render_to_response,get_object_or_404
from django.http import HttpResponse,HttpResponseRedirect
from django import forms
from . import models
from . import tasks
import personal_info
import devices
import time
import base64
import json

#add
from lib.distance import rssi2distance,lon2WebMercator,lat2WebMercator,leastSquareMethod,mercator2Lon,mercator2Lat
from lib.final_logger import FinalLogger
from EasyFind.config import LOG_PATH,DATA_PATH
from ios.views import handle_uploaded_file,resizeImg
import datetime
import redis
import copy
import os

rds = redis.StrictRedis(host='localhost', port='6379', db=0)
logname = os.path.join(LOG_PATH,'viewtask.log')
mylog = FinalLogger.getLogger(logname)

#add end

#websocket
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage



# Create your views here.

class taskForm(forms.Form):
	name = forms.CharField()
	device = forms.CharField()
	info = forms.CharField(required=False)
	province = forms.CharField()
	city = forms.CharField()
	district = forms.CharField(required=False)
	street = forms.CharField(required=False)
	total = forms.IntegerField()
	picture = forms.FileField()

#发布任务
def publish(request,a):
	publisher = personal_info.models.User.objects(account=a).first()
	publisher_id = str(publisher._id)
	account = str(publisher.account)
	devicelist = devices.models.Device.objects(owner=publisher_id).as_pymongo()
	if request.method == 'POST':
		form = taskForm(request.POST,request.FILES)
		if form.is_valid():
                        name = form.cleaned_data['name']
                        device_uuid = form.cleaned_data['device']
                        info = form.cleaned_data['info']
                        province = form.cleaned_data['province']
                        city = form.cleaned_data['city']
                        district = form.cleaned_data['district']
                        street = form.cleaned_data['street']
                        total = form.cleaned_data['total']
                        picture = request.FILES['picture']
                        device = devices.models.Device.objects(uuid=device_uuid).first()
                        device_id = str(device._id)
                        task = models.Task(name=name,info=info,device=device_id,publisher=publisher_id,publisher_name=publisher.nickname,search_province=province,search_city=city,search_district=district,search_street=street,reward=total,money_left=total,isDeliver='未分配')
                        #task.picture = picture
                        task.save()
                        sort="task"
                        task_temp = models.Task.objects(name=name,info=info).first()
                        picturename = handle_uploaded_file(account,sort,str(task_temp._id),picture)
                        task_id = str(task_temp._id)
                        # picturename = task_id+"."+str(picture).split('.')[-1]
                        picUrl = os.path.join(DATA_PATH,"image",account,sort,picturename)
                        ori_img=picUrl
                        sort="compress_task"
                        if not os.path.exists(os.path.join(DATA_PATH,"image",account,sort)):
                            os.makedirs(os.path.join(DATA_PATH,"image",account,sort))
                        dst_img=os.path.join(DATA_PATH,"image",account,sort,picturename)
                        resizeImg(ori_img=ori_img,dst_img=dst_img,dst_w=250,dst_h=250,save_q=50)
                        #personal_info.models.User.objects(account=account).update_one(set__picUrl=dst_img)
                        #models.Task.objects(_id=str(newtask._id)).update_one(set__picUrl=dst_img)
                        models.Task.objects(_id=task_id).update_one(push__picUrl=dst_img)
                        tasks.deliverTask.delay(task_id,task_temp)
                        #deliverTask(task_id,task_temp)
                        #return HttpResponseRedirect("/"+account)
                        return render(request,'tasks/tasks.html',{'tag':json.dumps('ok')})


		else:
			#return HttpResponseRedirect("/")
			return render(request,'tasks/tasks.html',{'tag':json.dumps('no')})
	else:
		form = taskForm()
		return render(request,'tasks/tasks.html',{'form':form,'publisher':publisher,'devices':devicelist,'user':publisher,'tag':json.dumps('get_method')})

#add
def redis_discover(request):
	dicts={}
	if request.method == 'GET':
		device_uuid  = request.GET['uuid']
		longitude = request.GET['longitude']
		latitude = request.GET['latitude']
		account = request.GET['account']
		#distance = request.POST['distance']
		rssi = request.GET['rssi']
		discovertime = request.GET['discovertime']
		distance = rssi2distance(rssi)

		if distance == "":
			return HttpResponse('Noo')

		#查找任务目标为当前设备的任务
		tasklist = models.Task.objects.filter(device = devices.models.Device.objects.get(uuid = device_uuid)._id)
		strp_discovertime = datetime.datetime.strptime(discovertime,'%Y-%m-%d %H:%M:%S')
		for task in tasklist:
			lastid = rds.get('%s:lastid'%task._id)
			if lastid:
				lastid = lastid.decode()
			else:
				rds.set('%s:lastid'%task._id,1)
				lastid = str(1)
			mylog.info('lastid:'+lastid)

			#判断是否进行定位计算
			#判断依据：该条数据距离上一个数据时间间隔大于3秒
			rdslast = rds.hmget('TaskDiscover:%s:%s'%(task._id,lastid),'discovertime')[0]  #集合数据类型
			if rdslast:
				lasttime = datetime.datetime.strptime(rdslast.decode(),'%Y-%m-%d %H:%M:%S')
				if  strp_discovertime> lasttime + datetime.timedelta(seconds = 3):
					mylog.info('enter redis_result...'+str(task._id)+str(discovertime))
					redis_result(task._id,discovertime)


			nextid = rds.incrby('%s:lastid'%task._id,1)
			rds.lpush('%s:list'%task._id,nextid)
			rds.hmset('TaskDiscover:%s:%s'%(task._id,nextid), {'discover':account,'longitude':longitude,'latitude':latitude,'rssi':rssi,'distance':distance,'discovertime':discovertime})
			#rds.hmget('TaskDiscover:%s:%s'%(task._id,nextid),'discoverTime')



	return HttpResponse('okkk')


def redis_result(task_id,discovertime):

    #获取该任务当前定位数据
    #mylog.info("task_result.......task_id:"+str(task_id))

    #计算Redis中 该任务的数据条数
    id_len = rds.llen('%s:list'%task_id)

    #获取该任务的所有定位数据
    id_list = rds.lrange('%s:list'%task_id,0,id_len)
    mylog.info('id_list:  '+str(id_list))

    #mylog.info('taskdiscoverlist:'+str(taskdiscoverlist))
    #判断是否进行定位数据计算：当条记录时间 距离最近一条记录时间间隔大于3秒
    mylog.info('discovertime:'+str(datetime.datetime.strptime(discovertime,'%Y-%m-%d %H:%M:%S')))

    #获取该任务的定位结果数据
    taskresultidlist= models.Task_result.objects.filter(task = task_id).order_by('-discoverTime')#从大到小排序

    #初始化一个最晚时间
    lasttime = datetime.datetime.strptime('2000-01-01 00:00:00','%Y-%m-%d %H:%M:%S')
    if len(taskresultidlist):#定位结果存在该条记录，获取最大时间
        lasttime = taskresultidlist.first().discoverTime    #datetime 类型
    mylog.info(str(lasttime))
    task_discover_valid = []

    #获取该任务所有的有效定位发现数据
    taskdiscoverlist=[]
    for id in id_list:
        discover = rds.hgetall('TaskDiscover:%s:%s'%(task_id,id.decode()))
        idtime = datetime.datetime.strptime(discover.get(b'discovertime').decode(),'%Y-%m-%d %H:%M:%S')
        if idtime > lasttime:
            taskdiscoverlist.append(discover)

    #定位数据列表按时间排序
    discoverlist = sorted(taskdiscoverlist,key=lambda k:k[b'discovertime'])

    #有效数据分组整合
    for i  in range(0,len(taskdiscoverlist)):
        count = 1
        for j in range(i+1,len(taskdiscoverlist)):
            starttime = datetime.datetime.strptime(taskdiscoverlist[j][b'discovertime'].decode(),'%Y-%m-%d %H:%M:%S')
            endtime = starttime+datetime.timedelta(seconds = 3)

            mylog.info("i:"+str(i)+" j:"+str(j) +"discovertime:"+str(taskdiscoverlist[i][b'discovertime'])+" starttime:"+str(starttime)+"  endtime:"+str(endtime))
            if starttime <= endtime:
                count +=1
            else:
                break;

        if count<3:
            continue

        else:
            mylog.info('count > 3')
            #if j==len(taskdiscoverlist)-1:
                #task_discover_valid.append(copy.deepcopy(taskdiscoverlist[i:len(taskdiscoverlist)]))
            #else:
            task_discover_valid.append(copy.deepcopy(taskdiscoverlist[i:j+1]))

    mylog.info("log testsetestst")
    mylog.info("task_discover_valid:"+str(task_discover_valid))

    # 对定位数据进行计算
    for taskdata in task_discover_valid:
            discover_time=0.0

            #计算定位结果的时间（所有定位数据的平均值）
            for data in taskdata:
                mylog.info(data[b'discovertime'].decode()+' '+data[b'distance'].decode()+' '+data[b'longitude'].decode()+' '+data[b'latitude'].decode())
                discover_time += time.mktime(time.strptime(data[b'discovertime'].decode(), '%Y-%m-%d %H:%M:%S'))
            discover_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(discover_time/len(taskdata)))
            mylog.info('result discovertime:  '+str(discover_time))
            #计算经纬度
            try:
                pointdata = [[lon2WebMercator(data[b'longitude'].decode()),lat2WebMercator(data[b'latitude'].decode()),float(data[b'distance'].decode())] for data in taskdata]
                x,y = leastSquareMethod(pointdata)
            #print 'x:',x,' y:',y
            except:
                #最小二乘法计算错误，  定位数据有问题
                return False
            mylog.info("x:"+str(mercator2Lon(x))+"  y:"+str(mercator2Lat(y)))

            #计算结果插入到定位结果数据表
            longitude = mercator2Lon(x)
            latitude = mercator2Lat(y)


            models.Task_result.objects.create(task = task_id,longitude = longitude,latitude = latitude ,discoverTime = discover_time)

            message = {'longitude':str(longitude),'latitude':str(latitude),'task_id':str(task_id),'discover_time':str(discover_time)}

    return True



