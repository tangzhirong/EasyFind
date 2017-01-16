from django.shortcuts import render

# Create your views here.
#coding: utf8
from django.http import HttpResponse,Http404
from django.template import RequestContext
from django.template.loader import get_template
from django.shortcuts import render_to_response,get_object_or_404,render
import json
from django import forms
from django.forms import model_to_dict
from django.db.models import Q
from django.core.context_processors import csrf


from lib.distance import lon2WebMercator,lat2WebMercator,mercator2Lon,mercator2Lat,leastSquareMethod,rssi2distance
from EasyFind.config import DATA_PATH,LOG_PATH
import os
import copy
import time
import datetime
import _thread
import base64
from lib.final_logger import FinalLogger
from random import randint
from PIL import Image as image
import devices
import tasks
import personal_info
from django.views.decorators.csrf import csrf_exempt
from lib.PyAPNs_master.apns import APNs, Frame, Payload
from personal_info.views import personForm
from EasyFind.config import PUSH_PATH

logname = os.path.join(LOG_PATH,'ios.log')
mylog = FinalLogger.getLogger(logname)

class taskForm(forms.Form):
    user_id = forms.CharField()
    task_name = forms.CharField()
    device_id = forms.CharField()
    info = forms.CharField()
    province = forms.CharField()
    city = forms.CharField()
    district = forms.CharField()
    street = forms.CharField()
    total = forms.IntegerField()
    picture = forms.FileField()

class imageForm(forms.Form):
    account = forms.CharField()
    task_id = forms.CharField()
    picture = forms.FileField()

def resizeImg(**args):
    args_key = {'ori_img':'','dst_img':'','dst_w':'','dst_h':'','save_q':75}
    arg = {}
    for key in args_key:
        if key in args:
            arg[key] = args[key]
        
    im = image.open(arg['ori_img'])
    ori_w,ori_h = im.size
    widthRatio = heightRatio = None
    ratio = 1
    if (ori_w and ori_w > arg['dst_w']) or (ori_h and ori_h > arg['dst_h']):
        if arg['dst_w'] and ori_w > arg['dst_w']:
            widthRatio = float(arg['dst_w']) / ori_w #正确获取小数的方式
        if arg['dst_h'] and ori_h > arg['dst_h']:
            heightRatio = float(arg['dst_h']) / ori_h

        if widthRatio and heightRatio:
            if widthRatio < heightRatio:
                ratio = widthRatio
            else:
                ratio = heightRatio

        if widthRatio and not heightRatio:
            ratio = widthRatio
        if heightRatio and not widthRatio:
            ratio = heightRatio
            
        newWidth = int(ori_w * ratio)
        newHeight = int(ori_h * ratio)
    else:
        newWidth = ori_w
        newHeight = ori_h
        
    im.resize((newWidth,newHeight),image.ANTIALIAS).save(arg['dst_img'],quality=arg['save_q'])

@csrf_exempt
def app_login(request):
    dicts={}
    if request.method == 'POST':
        #userid = request.GET['userid']
        #pw = request.GET['password']
        try:
            mylog.info(request.POST)
            senseddata = request.POST['sensedData']
            senseddata  = json.loads(senseddata)
            account = senseddata['user_id']
            pw = senseddata['password']
            token = senseddata['token']
        except Exception as e:
            dicts["status"] =  '102'  #数据错误
            x = json.dumps(dicts,ensure_ascii = False)
            mylog.info(str(account)+"log_in error"+str(e))
            return HttpResponse(x)



        user= personal_info.models.User.objects(account=account).first()
        if(not user):
            dicts["status"] =  '104'          #用户不存在错误
        elif(user.password != pw):
            dicts["status"] =  '102'          #用户账号或密码错误
        else:
            user.token=token      #更新用户token值
            user.save()
            mylog.info(str(user)+"  login success!!")
            #friends=dict(deviceid = User.objects.device_of(userid))
            #devices={}
            #tasks={}
            # dicts = personal_info.models.User.objects(account=account).get_json()
            dicts["status"] =  '101' #验证成功返回yes
#             dicts["friends"] = dict(User.objects.friends_of(userid).values_list('user_id','user_name',))
#             dicts['devices']  = dict(User.objects.device_of(userid).values_list('device_id','device_name'))
#             dicts['tasks'] = dict(User.objects.task_of(userid).values_list('id','task_name'))
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)
    else:
        dicts["status"] =   '103'  #访问方式错误
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)

@csrf_exempt
def app_register(request):
    dicts={}
    mylog.info("test:"+str(request))
    if request.method == 'POST':
        try:
            form = personForm(request.POST,request.FILES)
            if form.is_valid():
                mylog.info("data correct:"+form.cleaned_data['account'])
                account = form.cleaned_data['account']
                password = form.cleaned_data['password']
                gender = form.cleaned_data['gender']
                nickname = form.cleaned_data['nickname']
                phone = form.cleaned_data['phone']
                email = form.cleaned_data['email']
                province = form.cleaned_data['province']
                city = form.cleaned_data['city']
                #picture = form.cleaned_data['picture']
                picture = request.FILES['picture']
                user= personal_info.models.User.objects.filter(account=account)
                if(len(user) == 0):
                    newuser = personal_info.models.User(account=account,password=password,gender=gender,nickname=nickname,phone=phone,email=email,province=province,city=city)
                    #newuser.picture = picture
                    newuser.save()
                    sort="photo"
                    handle_uploaded_file(account,sort,"",picture)
                    picturename=str(account)+"."+str(picture).split('.')[-1]
                    picUrl=os.path.join(DATA_PATH,"image",account,sort,picturename)
                    #personal_info.models.User.objects(account=account).update_one(set__picUrl=picUrl)
                    ori_img=picUrl
                    sort="compress_photo"
                    if not os.path.exists(os.path.join(DATA_PATH,"image",account,sort)):
                        os.makedirs(os.path.join(DATA_PATH,"image",account,sort))
                    dst_img=os.path.join(DATA_PATH,"image",account,sort,picturename)
                    resizeImg(ori_img=ori_img,dst_img=dst_img,dst_w=95,dst_h=95,save_q=35)
                    personal_info.models.User.objects(account=account).update_one(set__picUrl=dst_img)
                    dicts["status"] =  '101'#可以新建用户，新建用户成功
                else:
                    dicts["status"] =  '104'          #用户账号已存在
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)
            else:
                dicts["status"] =  '105'    #DataType Wrong
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)
        except Exception as e:
            dicts["status"] =  '102'  #数据错误
            x = json.dumps(dicts,ensure_ascii = False)
            mylog.error("test"+str(e))
            return HttpResponse(x)
    else:
        dicts["status"] =   '103'  #访问方式错误
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)

#  device  operation
@csrf_exempt
def get_device(request):
    dicts ={}
    if request.method == 'POST':

        try:
            senseddata = request.POST['sensedData']
            senseddata  = json.loads(senseddata)
            account = senseddata['user_id']
            #userid = request.POST['user_id']
        except Exception as e:
            dicts["status"] =  '102'  #数据错误
            x = json.dumps(dicts,ensure_ascii = False)
            mylog.info(str(e))
            return HttpResponse(x)

        user = personal_info.models.User.objects(account=account).first()
        if user:
            user_id = str(user._id)
            device = devices.models.Device.objects(owner=user_id)
            dicts["status"] =   '101'
            dicts['device']= [{'device_id':b.uuid,'device_name':b.name} for b in device]
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)
        else:
            dicts["status"] =   '102'  #访问方式错误
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)

    else:
        dicts["status"] =   '103'  #访问方式错误
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)



@csrf_exempt
def add_device(request):
    dicts={}
    if request.method == 'POST':
        try:
            senseddata = request.POST['sensedData']
            senseddata  = json.loads(senseddata)
            mylog.info(senseddata)
            user = personal_info.models.User.objects(account=senseddata['device_owner']).first()
            if user:
                user_id = str(user._id)
                device = devices.models.Device(name=senseddata['device_name'],owner=user_id,uuid=senseddata['device_id']).save()
                dicts["status"] =  '101'
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)
            else:
                dicts["status"] =   '104' #用户不存在
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)
        except Exception as e:
            dicts["status"] =  '102'
            x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)
    else:
        dicts["status"] =   '103'
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)

@csrf_exempt
def delete_device(request):
    dicts={}
    if request.method == 'POST':
        try:
            senseddata = request.POST['sensedData']
            senseddata  = json.loads(senseddata)
            user = personal_info.models.User.objects(account=senseddata['device_owner']).first()
            if user:
                mylog.info('user exist')
                user_id = str(user._id)
                device = devices.models.Device.objects(uuid=senseddata['device_id'],owner=user_id)
                if device:
                    mylog.info('device exist')
                    device.delete()
                    dicts["status"] =  '101' #删除成功
                    x = json.dumps(dicts,ensure_ascii = False)
                    return HttpResponse(x)
                else:
                    dicts["status"] =  '105' #设备不存在
                    x = json.dumps(dicts,ensure_ascii = False)
                    return HttpResponse(x)
            else:
                dicts["status"] =  '104' #用户不存在
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)
        except Exception as e:
            dicts["status"] =  '102' #数据错误
            mylog.info(e)
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)
    else:
        dicts["status"] =  '103' #访问方式错误
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)

@csrf_exempt
def search_user(request):
    dicts={}
    try:
        senseddata = request.POST['sensedData']
        senseddata  = json.loads(senseddata)
        user = personal_info.models.User.objects(account=senseddata['user_id']).first()
        if user:
            userlist = personal_info.models.User.objects(account__contains=senseddata['searchword'])
            dicts["status"] =  '101'  #查找成功
            dicts['users']=[{'user_id':b.account,'user_name':b.nickname} for b in userlist]
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)
        else:
            dicts["status"] =  '104'  #用户不存在
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)
    except Exception as e:
        dicts["status"] =  '102'  #查找失败
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)

#  friends  operation
@csrf_exempt
def get_friends(request):
    dicts ={}
    if request.method == 'POST':

        try:
            senseddata = request.POST['sensedData']
            senseddata  = json.loads(senseddata)
            account = senseddata['user_id']
            #userid = request.POST['user_id']
        except Exception as e:
            dicts["status"] =  '102'  #数据错误
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)

        user = personal_info.models.User.objects(account=account).first()
        if user:
            user_account = str(user.account)
            friendlist = personal_info.models.User.objects(account__in=user.friends)
            dicts["status"] =  '101'
            dicts['friends']= [{'user_id':b.account,'user_name':b.nickname} for b in friendlist]
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)
        else:
            dicts["status"] =   '104'  #用户不存在
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)

    else:
        dicts["status"] =   '103'  #访问方式错误
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)

@csrf_exempt
def add_friend(request):
    dicts={}
    if request.method == 'POST':
        try:
            senseddata = request.POST['sensedData']
            senseddata  = json.loads(senseddata)

            user = personal_info.models.User.objects(account=senseddata['from_user']).first()
            if user:
                to_user= personal_info.models.User.objects(account = senseddata['to_user'])
                if(len(to_user) == 0):
                    dicts["status"] =   '105' #用户不存在
                    x = json.dumps(dicts,ensure_ascii = False)
                    return HttpResponse(x)
                friends = personal_info.models.User.objects(account__in=user.friends).as_pymongo()
                for friend in friends:
                    if(friend.account == senseddata['to_user']):
                        dicts["status"] =   '104' #用户已是好友
                        x = json.dumps(dicts,ensure_ascii = False)
                        return HttpResponse(x)
                personal_info.models.User.objects(account=senseddata['from_user']).update_one(push__friends=senseddata['to_user'])
                token = personal_info.models.User.objects(account=senseddata['to_user']).first().token
                message = {'msg':str(user.nickname)+'刚添加你为好友！'}
                apns = APNs(use_sandbox=True, cert_file=PUSH_PATH, key_file=PUSH_PATH)
                payload = Payload(alert="New Message！", custom = message)
                apns.gateway_server.send_notification(token, payload)
                dicts["status"] =   '101' #好友申请成功
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)

        except Exception as e:
            dicts["status"] =   '102' #数据传输错误
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)

    else:
        dicts["status"] =   '103'  #访问方式错误
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)

@csrf_exempt
def delete_friend(request):
    dicts={}
    mylog.info(u'friendshipdelete')
    if request.method == 'POST':
        try:
            senseddata = request.POST['sensedData']
            senseddata  = json.loads(senseddata)
            user = personal_info.models.User.objects(account=senseddata['from_user']).first()
            if user:
                personal_info.models.User.objects(account=senseddata['from_user']).update_one(pull__friends=senseddata['to_user'])
                dicts["status"] =  '101'  #删除成功
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)
            else:
                dicts["status"] =  '104'  #用户不存在
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)
        except Exception as e:
            dicts["status"] =  '102'  #数据问题
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)
    else:
        dicts["status"] =  '103'  #访问方式错误
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)

# task operation
@csrf_exempt
def get_tasks(request):
    dicts ={}
    if request.method == 'POST':
        try:
            # mylog.info(request.POST)
            senseddata = request.POST['sensedData']
            senseddata  = json.loads(senseddata)
            account = senseddata['user_id']
            #userid = request.GET['user_id']
            # mylog.info(userid+"request for  task list...")
        except Exception as e:
            dicts["status"] =  '102'  #数据错误
            x = json.dumps(dicts,ensure_ascii = False)
            mylog.info(str(e))
            return HttpResponse(x)
        user = personal_info.models.User.objects(account=account).first()
        if user:
            publisher_id = str(user._id)
            my_tasks = tasks.models.Task.objects(publisher=publisher_id).order_by("-createTime")
            all_tasks = tasks.models.Task.objects().order_by("-createTime")
            join_tasks = tasks.models.Task.objects.filter(participates__contains=publisher_id).order_by("-createTime")
            dicts["status"] =  '101'

            dicts['my_tasks']= [{'task_id':str(b._id),'publisher':b.publisher_name,'name':b.name,'picture':str(b.picUrl),'device':devices.models.Device.objects(_id=str(b.device._id)).first().uuid,'info':b.info,'province':b.search_province,'city':b.search_city,
            'district':b.search_district,'street':b.search_street,'reward':b.reward,'time':b.createTime.strftime("%Y-%m-%d-%H"),'status':b.status,'participatesName'
            :b.participates_name,'money_left':b.money_left} for b in my_tasks]

            dicts['all_tasks']= [{'task_id':str(b._id),'publisher':b.publisher_name,'name':b.name,'picture':str(b.picUrl),'device':devices.models.Device.objects(_id=str(b.device._id)).first().uuid,'info':b.info,'province':b.search_province,'city':b.search_city,
            'district':b.search_district,'street':b.search_street,'reward':b.reward,'time':b.createTime.strftime("%Y-%m-%d-%H"),'status':b.status,'participatesName'
            :b.participates_name,'money_left':b.money_left} for b in all_tasks]

            dicts['join_tasks']= [{'task_id':str(b._id),'publisher':b.publisher_name,'name':b.name,'picture':str(b.picUrl),'device':devices.models.Device.objects(_id=str(b.device._id)).first().uuid,'info':b.info,'province':b.search_province,'city':b.search_city,
            'district':b.search_district,'street':b.search_street,'reward':b.reward,'time':b.createTime.strftime("%Y-%m-%d-%H"),'status':b.status,'participatesName'
            :b.participates_name,'money_left':b.money_left} for b in join_tasks]
            x = json.dumps(dicts,ensure_ascii = False)
            mylog.info("task list  OKKKKK")
            return HttpResponse(x)
        else:
            dicts["status"] =   '104'  #用户不存在
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)

    else:
        dicts["status"] =   '103'  #访问方式错误
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)

@csrf_exempt
def accept_task(request):
    dicts ={}
    if request.method == 'POST':
        #mylog.info(str(request))
        try:
            senseddata = request.POST['sensedData']
            senseddata  = json.loads(senseddata)
            account = senseddata['user_id']
            taskid = senseddata['task_id']
            task_id = str(taskid)
            device_id = tasks.models.Task.objects(_id=task_id).first().device._id
            uuid = devices.models.Device.objects(_id=str(device_id)).first().uuid
            pid=[]
            p = personal_info.models.User.objects(account=account).as_pymongo()[0]
            if p:
                pid.append(p['_id'])
                tasks.models.Task.objects(_id=task_id).update_one(push_all__participates=pid)
                users_name = []
                u = personal_info.models.User.objects(_id=p['_id']).first()
                users_name.append(u.nickname)
                tasks.models.Task.objects(_id=task_id).update_one(push_all__participates_name=users_name)

                publisher_id = str(tasks.models.Task.objects(_id=task_id).first().publisher)
                token = personal_info.models.User.objects(_id=publisher_id).first().token
                message = {'msg':str(u.nickname)+'刚参与了你的任务:'+str(tasks.models.Task.objects(_id=task_id).first().name)}
                apns = APNs(use_sandbox=True, cert_file=PUSH_PATH, key_file=PUSH_PATH)
                payload = Payload(alert="New Message！", custom = message)
                apns.gateway_server.send_notification(token, payload)
                dicts["status"] =  '101'
                dicts["device"] = uuid
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)
        except Exception as e:
            dicts["status"] =  '102'  #数据错误
            x = json.dumps(dicts,ensure_ascii = False)
            mylog.info(str(e))
            return HttpResponse(x)

    else:
        dicts["status"] =   '103'  #访问方式错误
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)

#handle task img upload
@csrf_exempt
def upload_taskImg(request):
    dicts = {}
    if request.method == 'POST':
        try:
            form = imageForm(request.POST,request.FILES)
            if form.is_valid():
                account = form.cleaned_data['account']
                taskid = form.cleaned_data['task_id']
                picture = request.FILES['picture']
                sort = "task"
                picturename = handle_uploaded_file(account,sort,str(taskid),picture)
                #picturename = str(newtask._id)+"."+str(picture).split('.')[-1]
                mylog.info("picture loaded")
                picUrl = os.path.join(DATA_PATH,"image",account,sort,picturename)
                ori_img=picUrl
                sort="compress_task"
                if not os.path.exists(os.path.join(DATA_PATH,"image",account,sort)):
                    os.makedirs(os.path.join(DATA_PATH,"image",account,sort))
                dst_img=os.path.join(DATA_PATH,"image",account,sort,picturename)
                resizeImg(ori_img=ori_img,dst_img=dst_img,dst_w=95,dst_h=95,save_q=35)
                #personal_info.models.User.objects(account=account).update_one(set__picUrl=dst_img)
                #tasks.models.Task.objects(_id=str(newtask._id)).update_one(set__picUrl=dst_img)
                tasks.models.Task.objects(_id=str(taskid)).update_one(push__picUrl=dst_img)
                dicts["status"] =  '101'
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)
        except Exception as e:
            dicts["status"] =  '102'  #数据错误
            x = json.dumps(dicts,ensure_ascii = False)
            mylog.info(str(e))
            return HttpResponse(x)
    else:
        dicts["status"] =   '103'  #访问方式错误
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)
       

@csrf_exempt
def publish_task(request):
    dicts={}
    if request.method == 'POST':
        try:
            form = taskForm(request.POST,request.FILES)
            if form.is_valid():
                mylog.info("data correct")
                account = form.cleaned_data['user_id']
                taskname = form.cleaned_data['task_name']
                deviceid = form.cleaned_data['device_id']
                info = form.cleaned_data['info']
                province = form.cleaned_data['province']
                city = form.cleaned_data['city']
                district = form.cleaned_data['district']
                street = form.cleaned_data['street']
                total = form.cleaned_data['total']
                #picture = request.FILES['picture']
                #pictures = request.FILES.getlist('picture')
            else:
                dicts["status"] =  '106' #数据错误
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)

        except Exception as e:
            dicts["status"] =  '102' #数据错误
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)

        publisher = personal_info.models.User.objects(account=account).first()
        if publisher:
            mylog.info("publihser exist")
            publisher_id = str(publisher._id)
            publisher_name = personal_info.models.User.objects(_id=publisher_id).first().nickname;
            device = devices.models.Device.objects(uuid=deviceid,owner=publisher_id).first()
            if device:
                mylog.info("device exist")
                device_id = str(device._id)
                task = tasks.models.Task(name=taskname,info=info,device=device_id,publisher=publisher_id,publisher_name=publisher_name,search_province=province,search_city=city,search_district=district,search_street=street,reward=total,money_left=total,isDeliver='未分配')
                #task.picture = picture
                task.save()
                newtask = tasks.models.Task.objects(name=taskname,info=info,publisher=publisher_id).first()
                dicts["status"] =   '101' #任务添加成功
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)
                # for picture in pictures:
                #     sort = "task"
                #     #picturename = handle_uploaded_file(account,sort,str(newtask._id),picture)
                #     picturename = str(newtask._id)+"."+str(picture).split('.')[-1]
                #     picUrl = os.path.join(DATA_PATH,"image",account,sort,picturename)
                #     ori_img=picUrl
                #     sort="compress_task"
                #     if not os.path.exists(os.path.join(DATA_PATH,"image",account,sort)):
                #         os.makedirs(os.path.join(DATA_PATH,"image",account,sort))
                #     dst_img=os.path.join(DATA_PATH,"image",account,sort,picturename)
                #     resizeImg(ori_img=ori_img,dst_img=dst_img,dst_w=95,dst_h=95,save_q=35)
                #     personal_info.models.User.objects(account=account).update_one(set__picUrl=dst_img)
                #     tasks.models.Task.objects(_id=str(newtask._id)).update_one(set__picUrl=dst_img)
                    #tasks.models.Task.objects(_id=str(newtask._id)).update_one(push_picUrl=dst_img)
                    # dicts["status"] =   '101' #任务添加成功
                    # x = json.dumps(dicts,ensure_ascii = False)
                    # return HttpResponse(x)
            else:
                dicts["status"] =  '105' #用户设备不存在
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)
        else:
            dicts["status"] =  '104' #用户不存在
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)
    else:
        dicts["status"] =  '103' #访问方式错误
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)


#退出任务
@csrf_exempt
def task_out(request):
    dicts={}
    mylog.info(str(request))
    if request.method == 'POST':
        try:
            senseddata = request.POST['sensedData']
            senseddata  = json.loads(senseddata)

            account= senseddata['user_id']
            taskid= senseddata['task_id']

            publisher = personal_info.models.User.objects(account=account).as_pymongo()[0]
            if publisher:
                pid = []
                users_name = []
                pid.append(publisher['_id'])
                task_id = str(taskid)
                tasks.models.Task.objects(_id=task_id).update_one(pull_all__participates=pid)
                u = personal_info.models.User.objects(_id=publisher['_id']).first()
                uid = str(u._id)
                users_name.append(u.nickname)
                tasks.models.Task.objects(_id=task_id).update_one(pull_all__participates_name=users_name)
                # deliver = tasks.models.Task_deliver.objects(task=task_id,user=uid).as_pymongo()[0]
                # m = task.money_left+deliver['money']
                # tasks.models.Task.objects(_id=task_id).update_one(set__money_left=m)
                dicts["status"] =  '101' #删除任务成功
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)
            else:
                dicts["status"] =  '104' #用户不存在
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)

        except Exception as e:
            dicts["status"] =  '102' #删除任务失败
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)
    else:
        dicts["status"] =  '103' #访问方式错误
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)

#完结任务
@csrf_exempt
def task_over(request):
    dicts={}
    mylog.info(str(request))
    if request.method == 'POST':
        try:
            senseddata = request.POST['sensedData']
            senseddata  = json.loads(senseddata)

            account= senseddata['user_id']
            taskid= senseddata['task_id']
            task_id = str(taskid)
            user = personal_info.models.User.objects(account=account).first()
            if user:
                tasks.models.Task.objects(_id=task_id).update_one(set__status='已完结')
                dicts["status"] =  '101'
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)
            else:
                dicts["status"] =  '104' #用户不存在
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)
        except Exception as e:
            dicts["status"] =  '102' #删除任务失败
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)
    else:
        dicts["status"] =  '103' #访问方式错误
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)


#上传到指定路径的功能函数
def handle_uploaded_file(userid,sort,taskid,f):
    #处理用户动态上传图片名称  初步设为userid+miao+随机数
    if sort =="task":
        #picturename = taskid+"."+str(f).split('.')[-1]
        picturename = taskid+datetime.datetime.now().strftime('%S')+str(randint(100,999))+"."+str(f).split('.')[-1]
        mylog.info(picturename)
    else:
        picturename = userid+"."+str(f).split('.')[-1]
        mylog.info(picturename)
    if not os.path.exists(os.path.join(DATA_PATH,"image",userid,sort)):
        os.makedirs(os.path.join(DATA_PATH,"image",userid,sort))

    #picturename = userid+datetime.datetime.now().strftime('%S')+str(randint(100,999))+"."+str(f).split('.')[-1]
    try:
        mylog.info(os.path.join(DATA_PATH,str(f)))
        destination = open(os.path.join(DATA_PATH,"image",userid,sort,picturename),'wb+')

        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()
        return picturename
    except Exception as e:
        return False



@csrf_exempt
def task_discover(request):
    dicts={}
    mylog.info("hhhhhh")
    if True:
        try:
            mylog.info(str(request))
            if request.method == 'POST':
                senseddata = request.POST['sensedData']
                senseddata  = json.loads(senseddata)
                device_id  = senseddata['UUID']
                longitude = senseddata['longitude']
                latitude = senseddata['latitude']
                user_id = senseddata['user_id']
                rssi = senseddata['RSSI']
                discovertime = senseddata['discoverTime']
            else:
                device_id  = request.GET['uuid']
                longitude = request.GET['longitude']
                latitude = request.GET['latitude']
                user_id = request.GET['account']
                rssi = request.GET['rssi']
                discovertime = request.GET['discovertime']

            mylog.info("rssi:"+str(rssi))

            distance = rssi2distance(rssi)

            if distance == "":
                dicts["status"] =  '102' #数据错误
                mylog.error("rssi error!!")
                x = json.dumps(dicts,ensure_ascii = False)
                return HttpResponse(x)

            mylog.info("distance:"+str(distance))

            #查找任务目标为当前设备的任务
            device = devices.models.Device.objects(uuid = device_id).first()
            deviceid = str(device._id)
            tasklist = tasks.models.Task.objects(device=deviceid)

            user = personal_info.models.User.objects(account=user_id).first()
            userid = str(user._id)

            # #查找任务目标为当前设备的任务
            # target_list = Device.objects.filter(device_id = device_id)
            #
            # #获得空列表
            # tasklist = Task.objects.get_empty_query_set()
            # for target in target_list:
            #     tasklist = tasklist|Task.objects.filter(task_target = target)
            #

            #分别插入定位数据

            for task in tasklist:
                # TaskDiscover.objects.create(task = Task.objects.get(id = task.id),discover = User.objects.get(user_id = user_id),rssi=rssi,\
                #                             longtitude = longitude,latitude=latitude,discovertime = discovertime,distance = distance,status=0)
                task_discover =  tasks.models.TaskDiscover(task=str(task._id),discover=userid,rssi=rssi,longitude=longitude,latitude=latitude,discovertime=discovertime,distance=distance)
                task_discover.save()

        except Exception as e:
            dicts["status"] =  '102' #数据错误
            mylog.error("data error!!"+str(e))
            x = json.dumps(dicts,ensure_ascii = False)
            return HttpResponse(x)

        #定位计算
        for task in tasklist:
            _thread.start_new_thread(task_result, (str(task._id),discovertime))
        dicts["status"] =  '101' #流程结束 正确
        mylog.info("task discover data upload success!!")
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)
    else:
        dicts["status"] =  '103' #访问方式错误
        mylog.error("error access method!")
        x = json.dumps(dicts,ensure_ascii = False)
        return HttpResponse(x)
        return HttpResponse('okkk')

@csrf_exempt
def task_result(task_id,discovertime):

    #获取该任务当前定位数据
    mylog.info("task_result.......task_id:"+task_id)
    # taskdiscoverlist = TaskDiscover.objects.filter(task = Task.objects.get(id = task_id),status=0).order_by('discovertime')
    taskdiscoverlist = tasks.models.TaskDiscover.objects.filter(task = task_id,is_used=False).order_by('discovertime')
    #判断是否进行定位数据计算：当条记录时间 距离最近一条记录时间间隔大于3秒
    #if (datetime.datetime.strptime(discovertime,'%Y-%m-%d %H:%M:%S') > taskdiscoverlist.latest('discovertime').discovertime+datetime.timedelta(seconds = 50)) \
    #    or taskdiscoverlist.count()>6:  #当前发现时间距离最早一次时间大于30s或者未被计算数据条数大于6条。
    if(taskdiscoverlist.count()>6):
        mylog.info('start calculate task result..'+str(taskdiscoverlist.count()))
        #获取该任务当前定位结果数据
        # taskresultidlist= TaskResult.objects.filter(task = Task.objects.get(id = task_id)).order_by('-discover_time')#从大到小排序
        taskresultidlist= tasks.models.TaskResult.objects.filter(task = task_id).order_by('-discovertime')#从大到小排序
        mylog.info('result data'+str(taskresultidlist))

        lasttime = datetime.datetime.strptime('2000-01-01 00:00:00','%Y-%m-%d %H:%M:%S') #初始化一个最大时间
        if len(taskresultidlist):#定位结果存在该条记录，获取最大时间
            lasttime = taskresultidlist[0].discovertime    #datetime 类型

        task_discover_valid = []

        #获取有效定位发现数据
        mylog.info("lasttime: "+str(lasttime)+"  discovertime: "+str(discovertime))
        taskdiscoverlist = taskdiscoverlist.filter(discovertime__gte = lasttime).order_by('discovertime')
        mylog.info('discover data'+str(taskdiscoverlist))

        for i  in range(0,len(taskdiscoverlist)):
            count = 1
            endtime = taskdiscoverlist[i].discovertime+datetime.timedelta(seconds = 30)
            for j in range(i+1,len(taskdiscoverlist)):
                starttime = taskdiscoverlist[j].discovertime
                #mylog.info("starttime:"+str(starttime)+" endtime:"+str(endtime))
                if starttime <= endtime:
                    count +=1
                else:
                    break;

            if count<3:
                continue

            else:

                if j==len(taskdiscoverlist)-1:
                    task_discover_valid.append(copy.deepcopy(taskdiscoverlist[i:len(taskdiscoverlist)]))
                else:
                    task_discover_valid.append(copy.deepcopy(taskdiscoverlist[i:j]))



        mylog.info("task_discover_valid:"+str(task_discover_valid))


        for tasklist in task_discover_valid:
             for task in tasklist:
                 mylog.info("longtitude: "+str(task.longitude)+"  latitude: "+str(task.latitude)+"  distance: "+str(task.distance)+"  discovertime: "+str(task.discovertime))

        # 对定位数据进行计算
        for taskdata in task_discover_valid:
            discover_time=0.0

            #计算定位结果的时间（所有定位数据的平均值）
            for data in taskdata:
                #mylog.info(data.discovertime+' '+data.distance+' '+data.longtitude+' '+data.latitude)
                #将时间换成秒 进行相加求平均
                discover_time += time.mktime(time.strptime(data.discovertime.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'))
            #将时间换成日期形式
            discover_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(discover_time/len(taskdata)))
            mylog.info( "result  discover_time:"+str(discover_time))

            #计算经纬度
            try:
                pointdata = [[lon2WebMercator(data.longitude),lat2WebMercator(data.latitude),float(data.distance)] for data in taskdata]
                x,y = leastSquareMethod(pointdata)
            #print 'x:',x,' y:',y
            except Exception as e:
                #最小二乘法计算错误，  定位数据有问题
                mylog.error('zuixiaoercheng cuowu,data error...'+str(e))
                #return False

            mylog.info("x:"+str(mercator2Lon(x))+"  y:"+str(mercator2Lat(y)))

            #计算结果插入到定位结果数据表
            longitude = mercator2Lon(x)
            latitude = mercator2Lat(y)
            # task = Task.objects.get(id = task_id)
            # TaskResult.objects.create(task = task,longtitude = longitude,latitude = latitude ,discover_time = discover_time)
            result = tasks.models.TaskResult(task = task_id,longitude = longitude,latitude = latitude ,discovertime = discover_time)
            result.save()
            tasks.models.Task.objects(_id=task_id).update_one(set__status="已定位")
            if(-1<(longitude-float(taskdata[0].longitude))<1 and -1<(latitude-float(taskdata[0].latitude))<1):
                mylog.info('success count task result..')
                task = tasks.models.Task.objects(_id=task_id).first()
                token = personal_info.models.User.objects(_id=str(task.publisher._id)).first().token
                message = {'longitude':str(longitude),'latitude':str(latitude),'task_id':task_id,'discover_time':str(discover_time)}
                try:
                    # push_message(message,token)
                    apns = APNs(use_sandbox=True, cert_file=PUSH_PATH, key_file=PUSH_PATH)
                    # Send a notification
                    # token_hex = '6653d92e6319ad89d2d49c79d78df8a380ac8c910e0e8cb455beec9ebc84a58b'
                    # payload = Payload(alert="Hello World!", sound="default", badge=1)
                    payload = Payload(alert="New Message！", custom = message)
                    apns.gateway_server.send_notification(token, payload)

                    mylog.info('push message okkk...'+str(message))
                except Exception as e:
                    mylog.error('push message error...'+str(e))



        #全部计算完毕之后  选择最近的一组进行消息通知
        '''
        keys = dir()
        if('task' in keys and 'longitude' in keys and 'latitude' in keys):
            mylog.info('success count task result..')
            token = task.task_sponsor.token
            message = {'longitude':str(longitude),'latitude':str(latitude),'task_id':str(task_id),'discover_time':str(discover_time)}
            try:
                push_message(message,token)
                mylog.info('push message okkk...'+str(message))
            except Exception,e:
                mylog.error('push message error...'+str(e))
        '''
        #修改数据状态 为1  表示数据已经经过计算
        for task in taskdiscoverlist:
            task.is_used=True
            task.save()
            # mylog.info("change tast status.."+str(task.id))
    #修改任务数据计算状态
    #taskdiscoverlist = TaskDiscover.objects.filter(task = Task.objects.get(id = task_id),status=0)

    return True
