#-*- coding:utf-8 -*-
'''
Created on 2015年10月13日

@author: toot
'''

from django.shortcuts import render_to_response,get_object_or_404
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render
from lib.final_logger import FinalLogger
from EasyFind.config import LOG_PATH,DATA_PATH
from django import forms
from ios.views import handle_uploaded_file,resizeImg
import datetime
import tasks
import personal_info
import os
import json
import base64
import sse
import time
import random
from django_sse.redisqueue import send_event
from django.core.exceptions import ValidationError
from PIL import Image as image
#django sse
from django.views.generic import TemplateView
from django_sse.redisqueue import RedisQueueView
from django_sse.views import BaseSseView
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

#class HomePage(TemplateView):
  #  template_name = 'index.html'

#class SSE(RedisQueueView):
 #   pass

logname = os.path.join(LOG_PATH,'sse.log')
mylog = FinalLogger.getLogger(logname)

#websocket
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage





#loginForm
class loginForm(forms.Form):
    account = forms.CharField()
    password = forms.CharField()

class logonForm(forms.Form):
    account = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    gender = forms.CharField()
    nickname = forms.CharField()
    phone = forms.CharField()
    # email = forms.CharField()
    email = forms.EmailField()
    province = forms.CharField()
    city = forms.CharField()
    picture = forms.FileField()

#主页
def index(request):
    # user = personal_info.models.User.objects(account=a).first()
    # publisher_id = str(user._id)
    # my_tasks = tasks.models.Task.objects(publisher=publisher_id).as_pymongo()
    account = request.COOKIES.get('account','')
    if account:
        user = personal_info.models.User.objects(account=account).first()
        city = user.city
        publisher_id = str(user._id)
        city_tasks = tasks.models.Task.objects(search_city=city).order_by("-createTime")
        my_tasks = tasks.models.Task.objects(publisher=publisher_id).order_by("-createTime").as_pymongo()
        all_tasks = tasks.models.Task.objects().order_by("-createTime")
        join_tasks = tasks.models.Task.objects.filter(participates__contains=publisher_id).order_by("-createTime").as_pymongo()
        messages = user.messages
        user_msgs = personal_info.models.Message.objects(identifier__in=messages)
        unReadNum =0
        for msg in user_msgs:
            if(msg.is_read == False):
                unReadNum+=1
        return render(request,"index.html",{'my_tasks':my_tasks,'all_tasks':all_tasks,'city_tasks':city_tasks,'user':user,'join_tasks':join_tasks,'info':'欢迎使用！','view_info':'none','user_msgs':user_msgs,'unReadNum':unReadNum})
    else:
        all_tasks = tasks.models.Task.objects().order_by("-createTime")
        return render(request,"index.html",{'all_tasks':all_tasks,'info':'请先登录!','view_info':'','logout':'none'})

def user_page(request,a):
    account = request.COOKIES.get('account','')
    user = personal_info.models.User.objects(account=a).first()
    city = user.city
    if account == a or user.isLogin ==True:
        publisher_id = str(user._id)
        city_tasks = tasks.models.Task.objects(search_city=city).order_by("-createTime")
        my_tasks = tasks.models.Task.objects(publisher=publisher_id).order_by("-createTime").as_pymongo()
        all_tasks = tasks.models.Task.objects().order_by("-createTime")
        join_tasks = tasks.models.Task.objects.filter(participates__contains=publisher_id).order_by("-createTime").as_pymongo()
        messages = user.messages
        user_msgs = personal_info.models.Message.objects(identifier__in=messages)
        unReadNum =0
        for msg in user_msgs:
            if(msg.is_read == False):
                unReadNum+=1
        return render(request,"index.html",{'my_tasks':my_tasks,'all_tasks':all_tasks,'city_tasks':city_tasks,'user':user,'join_tasks':join_tasks,'info':'欢迎使用！','view_info':'none','user_msgs':user_msgs,'unReadNum':unReadNum})
    else:
        return HttpResponse('非法访问！'+str(user.isLogin))

#登录
def login(request):
    if request.method == 'POST':
        form = loginForm(request.POST)
        if form.is_valid():
            account = form.cleaned_data['account']
            password = form.cleaned_data['password']
            user=personal_info.models.User.objects(account=account,password=password).first()
            if user:
                account = str(user.account)
                response = HttpResponseRedirect("/"+account)
                #将account写入cookie，失效时间为3600
                response.set_cookie('account',account,3600)
                personal_info.models.User.objects(account=account,password=password).update_one(set__isLogin=True)
                return response
            else:
                # return HttpResponseRedirect("/")
                # print "Invalid user"
                return render(request,"login.html",{'res':"账号或密码错误"})
        else: 
            return render(request,"login.html",{'res':"账号或密码不能为空"})

    else:
        form = loginForm()
        return render(request,"login.html",{'form':form})

#注册
def logon(request):
    if request.method == 'POST':
        form = logonForm(request.POST,request.FILES)
        if form.is_valid():
            account = form.cleaned_data['account']
            password = form.cleaned_data['password']
            gender = form.cleaned_data['gender']
            nickname = form.cleaned_data['nickname']
            picture = request.FILES['picture']
            phone = form.cleaned_data['phone']
            email = form.cleaned_data['email']
            province = form.cleaned_data['province']
            city = form.cleaned_data['city']
            newuser = personal_info.models.User(account=account,password=password,gender=gender,nickname=nickname,phone=phone,email=email,province=province,city=city)
            #newuser.picture = picture
            newuser.save()
            sort="photo"
            handle_uploaded_file(account,sort,"",picture)
            picturename = str(account)+"."+str(picture).split('.')[-1]
            picUrl = os.path.join(DATA_PATH,"image",account,sort,picturename)
            ori_img=picUrl
            sort="compress_photo"
            if not os.path.exists(os.path.join(DATA_PATH,"image",account,sort)):
                os.makedirs(os.path.join(DATA_PATH,"image",account,sort))
            dst_img=os.path.join(DATA_PATH,"image",account,sort,picturename)
            resizeImg(ori_img=ori_img,dst_img=dst_img,dst_w=95,dst_h=95,save_q=35)
            personal_info.models.User.objects(account=account).update_one(set__picUrl=dst_img)
            user_temp = personal_info.models.User.objects(account=account).first()
            uid = str(user_temp._id)
            #personal_info.models.User.objects(account=account).update_one(set__picUrl=picUrl)
            return HttpResponseRedirect("/login")
        else:
            # return HttpResponseRedirect("/logon")
            form = logonForm()
            return render(request,"logon.html",{'res':"注册失败",'form':form})
    else:
        form = logonForm()
        return render(request,"logon.html",{'form':form})

def logout(request,a):
    response = HttpResponseRedirect("/login")
    response.delete_cookie('account')
    # personal_info.models.User.objects(account=a).update_one(set__isLogin=False)
    return response

#竞价信息处理
def task_deliver(request):
    response = HttpResponse()
    response['Content-Type']="text/javascript"
    account = request.POST.get("account","")
    taskName = request.POST.get("taskName","")
    money = request.POST.get("money","")
    publisher = personal_info.models.User.objects(account=account).first()
    publisher_id = str(publisher._id)
    task = tasks.models.Task.objects(name=taskName).first()
    task_id = str(task._id)
    #判断是否已经上报竞价数据，如已上报，返回提醒
    isDeliver = tasks.models.Task_deliver.objects(task=task_id,user=publisher_id).first()
    publisher_account = []
    if isDeliver:
        ret = 'hasDeliver'
        response.write(ret)
        return response
    if account and taskName:
        #保存竞价信息
        deliver = tasks.models.Task_deliver(task=task_id,user=publisher_id,money=money)
        deliver.save()
        #如果任务已分配，检查任务剩余悬赏，如能满足，分配任务给他
        if task.isDeliver=='已分配' and task.money_left>=int(money):
            #将用户写入任务参与者列表中
            pid=[]
            p = personal_info.models.User.objects(account=account).as_pymongo()[0]
            pid.append(p['_id'])
            tasks.models.Task.objects(_id=task_id).update_one(push_all__participates=pid)
            users_name = []
            u = personal_info.models.User.objects(_id=p['_id']).first()
            users_name.append(u.nickname)
            tasks.models.Task.objects(_id=task_id).update_one(push_all__participates_name=users_name)
            users_account = []
            users_account.append(u.account)
            tasks.models.Task.objects(_id=task_id).update_one(push_all__participates_account=users_account)
            #更新任务剩余悬赏
            m = task.money_left-int(money)
            tasks.models.Task.objects(_id=task_id).update_one(set__money_left=m)


            #push message to publisher
            redis_publisher = RedisPublisher(facility='foobar', broadcast=True)
            message = RedisMessage(account+" "+'已经加入了你的任务:'+" "+task.name)
            publisher_account.append(task.publisher.account)
            redis_publisher.publish_message(publisher_account,message)

            identifier = str(time.time())+","+str(random.random())+","+str(publisher_account)
            new_message = personal_info.models.Message(identifier=identifier,tag="task",content=account+" "+'已经加入了你的任务:'+" "+task.name)
            new_message.save()
            personal_info.models.User.objects(account=publisher_account).update_one(push__messages=identifier)

            #update status
            tasks.models.Task.objects(_id=task_id).update_one(set__status='监测中')

            ret = 'taskOk'
            response.write(ret)
            return response
        elif task.isDeliver=='已分配' and task.money_left<int(money):
            ret = 'moneyWrong'
            response.write(ret)
            return response
        else:
            ret = 'deliverOk'
            response.write(ret)
            return response
    else:
        response.write("no enough params")
        return response

#退出参与的任务
def task_out(request):
    response = HttpResponse()
    response['Content-Type']="text/javascript"
    account = request.POST.get("account","")
    taskName = request.POST.get("taskName","")
    publisher = personal_info.models.User.objects(account=account).as_pymongo()[0]
    pid = []
    users_name = []
    users_account = []
    pid.append(publisher['_id'])
    task = tasks.models.Task.objects(name=taskName).first()
    task_id = str(task._id)
    tasks.models.Task.objects(_id=task_id).update_one(pull_all__participates=pid)
    u = personal_info.models.User.objects(_id=publisher['_id']).first()
    uid = str(u._id)
    users_name.append(u.nickname)
    users_account.append(u.account)
    tasks.models.Task.objects(_id=task_id).update_one(pull_all__participates_name=users_name)
    tasks.models.Task.objects(_id=task_id).update_one(pull_all__participates_account=users_account)
    deliver = tasks.models.Task_deliver.objects(task=task_id,user=uid).as_pymongo()[0]
    m = task.money_left+deliver['money']
    tasks.models.Task.objects(_id=task_id).update_one(set__money_left=m)

    #push message to publisher
    publisher_account = []
    redis_publisher = RedisPublisher(facility='foobar', broadcast=True)
    message = RedisMessage(account+" "+'已经退出了你的任务:'+" "+task.name)
    publisher_account.append(task.publisher.account)
    redis_publisher.publish_message(publisher_account,message)

    identifier = str(time.time())+","+str(random.random())+","+str(publisher_account)
    new_message = personal_info.models.Message(identifier=identifier,tag="task",content=account+" "+'已经退出了你的任务:'+" "+task.name)
    new_message.save()
    personal_info.models.User.objects(account=publisher_account).update_one(push__messages=identifier)

    ret = '已退出该任务！'
    response.write(ret)
    return response

#完结任务
@csrf_exempt
def task_over(request):
    response = HttpResponse()
    response['Content-Type']="text/javascript"
    taskName = request.POST.get("taskName","")
    task = tasks.models.Task.objects(name=taskName).first()
    task_id = str(task._id)
    users_account = []
    if task.status != '已完结':
        tasks.models.Task.objects(_id=task_id).update_one(set__status='已完结')
        task_discovers = tasks.models.TaskDiscover.objects(task=task_id)
        for task_discover in task_discovers:
            discover_id = str(task_discover.discover._id);
            reward = tasks.models.Task_deliver.objects(task=task_id).first().money
            user_reputation = personal_info.models.User.objects(_id=discover_id).first().reputation
            new_reputation = user_reputation+reward
            personal_info.models.User.objects(_id=discover_id).update_one(set_reputation=new_reputation)
        ret = '操作成功,悬赏已分配!'
        redis_publisher = RedisPublisher(facility='foobar', broadcast=True)
        message = RedisMessage('任务'+" "+task.name+" "+'已经完结，请查看你的悬赏!')
        for user_account in task.participates_account:
            users_account.append(user_account)
        redis_publisher.publish_message(users_account,message)

        for user_account in users_account:
            mylog.info(user_account)
            identifier = str(time.time())+","+str(random.random())+","+str(user_account)
            new_message = personal_info.models.Message(identifier=identifier,tag="task",content='任务'+" "+task.name+" "+'已经完结，请查看你的悬赏!')
            new_message.save()
            mylog.info("saved!")
            personal_info.models.User.objects(account=user_account).update_one(push__messages=identifier)
            mylog.info("pushed!")
    
    else:
        ret = '操作失败,任务已完结！'

    response.write(ret)
    return response

#showInfo
def showInfo(request):
    response = HttpResponse()
    response['Content-Type']="text/javascript"
    userName = request.POST.get("userName","")
    taskName = request.POST.get("taskName","")
    user = personal_info.models.User.objects(nickname=userName).first()
    task = tasks.models.Task.objects(name=taskName).first()
    task_id = str(task._id)
    uid = str(user._id)
    position = tasks.models.TaskDiscover.objects(discover=uid,task=task_id).as_pymongo()
    # ret = position
    ret = position.to_json()
    # position = [{'longitude':117.10,'latitude':40.55},{'longitude':117.08,'latitude':40.10}]
    #ret = json.dumps(position, ensure_ascii=False)
    # ret = pos.to_json()

    response.write(ret)
    return response

#获取任务位置信息
def getLocation(request):
    response = HttpResponse()
    response['Content-Type']="text/javascript"
    taskName = request.POST.get("taskName","")
    task = tasks.models.Task.objects(name=taskName).first()
    task_id = str(task._id)
    result = tasks.models.TaskResult.objects(task=task_id).as_pymongo()
    ret = result.to_json()
    response.write(ret)
    return response

#测试redis
def test(request):
	print('kkkk')
	#return render(request,"tasks/index.html")
	return render_to_response('test.html')

def userPage(request,a):
    account = request.COOKIES.get('account','')
    user = personal_info.models.User.objects(account=a).first()
    if user:
        publisher_id = str(user._id)
        my_tasks = tasks.models.Task.objects(publisher=publisher_id).order_by("-createTime").as_pymongo()
        join_tasks = tasks.models.Task.objects.filter(participates__contains=publisher_id).order_by("-createTime").as_pymongo()
        return render(request,"user_page.html",{'my_tasks':my_tasks,'user':user,'account':account,'join_tasks':join_tasks})
    else:
        return HttpResponse("wrong")

def addFriend(request):
    response = HttpResponse()
    response['Content-Type']="text/javascript"
    account = request.POST.get("account","")
    faccount = request.POST.get("faccount","")
    user = personal_info.models.User.objects(account=account).first()
    if user:
        friends = personal_info.models.User.objects(account__in=user.friends)
        for friend in friends:
            if(friend.account == faccount):
                ret = "该用户已是你的好友啦！"
                response.write(ret)
                return response
        personal_info.models.User.objects(account=account).update_one(push__friends=faccount)
        identifier = str(time.time())+","+str(random.random())+","+str(faccount)
        new_message = personal_info.models.Message(identifier=identifier,tag="friend",content=account+" "+" 已添加你为好友！")
        new_message.save()
        personal_info.models.User.objects(account=faccount).update_one(push__messages=identifier)
        ret = "添加好友成功！"
        response.write(ret)
        return response
    else:
        ret = "未登录，无法进行此操作！"
        response.write(ret)
        return response

def isRead(request):
    response = HttpResponse()
    response['Content-Type']="text/javascript"
    account = request.POST.get("account","")
    user = personal_info.models.User.objects(account=account).first()
    messages = personal_info.models.Message.objects(identifier__in=user.messages)
    for message in messages:
        personal_info.models.Message.objects(identifier=message.identifier).update_one(set__is_read=True)
    ret = 'ok'
    response.write(ret)
    return response

def showlog(request):
    users = personal_info.models.User.objects()
    return render(request,"log.html",{'users':users})

def showUserlog(request):
    users = personal_info.models.User.objects()
    return render(request,"userlog.html",{'users':users})

def showSystemIndex(request):
    response = HttpResponse()
    response['Content-Type']="text/javascript"
    data = tasks.models.SystemIndex.objects().as_pymongo()
    ret = data.to_json()
    response.write(ret)
    return response

@csrf_exempt
def getUserInfo(request):
    response = HttpResponse()
    response['Content-Type']="text/javascript"
    account = request.POST.get("account","")
    user = personal_info.models.User.objects(account=account).first()
    user_id= str(user._id)
    data = tasks.models.Task.objects(publisher=user_id).as_pymongo()
    ret = data.to_json()
    response.write(ret)
    return response



