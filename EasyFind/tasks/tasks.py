from __future__ import absolute_import

from celery import shared_task

from django.shortcuts import render
from django.shortcuts import render_to_response,get_object_or_404
from django.http import HttpResponse,HttpResponseRedirect
from django import forms
from EasyFind.config import LOG_PATH
from lib.final_logger import FinalLogger
from . import models
import personal_info
import devices
import time
import random
import os
import json
import datetime
from django_sse.redisqueue import send_event

#websocket
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage

logname = os.path.join(LOG_PATH,'sse.log')
mylog = FinalLogger.getLogger(logname)

@shared_task
def add(a,b):
    mylog.info("add start!")

#calculate task finished rate
@shared_task
def calTaskfRate():
    #get time now
    now = datetime.datetime.now()
    start = now-datetime.timedelta(days=5)
    allTask = models.Task.objects( createTime__lt=now).count()
    finishedTask = models.Task.objects(createTime__lt=now,createTime__gte=start,status='已完结').count()
    rate = finishedTask/allTask
    mylog.info(rate)
    models.SystemIndex(taskFinishedRate=rate,time=now).save()
    # nowStr = now.strftime("%Y-%m-%d %H:%M:%S")
    # log = {'time':nowStr,'rate':rate}
    # readed = json.load(open('log.json', 'r'))
    # with open('log.json','w') as f:
    #     f.write(json.dumps(log,ensure_ascii=False))
    #     json.dump(readed, f)

@shared_task
def calUserInfo():
    now = datetime.datetime.now()
    users = personal_info.models.User.objects()
    for user in users:
        publisher_id = str(user._id)
        publish_tasks = models.Task.objects(publisher=publisher_id)
        task_on = publish_tasks.count()
        for publish_task in publish_tasks:
            if publish_task.status == '未分配':
                task_on -=1
        rate = task_on/publish_tasks.count()
        personal_info.models.User.objects(account=user.account).update_one(set__taskOnRate=rate)



#calculate 
@shared_task
def deliverTask(task_id,task_temp):
    #服务器sleep(5min),等待竞价数据的获取
    time.sleep(60)
    #查询该任务所有的竞价数据
    task_delivers = models.Task_deliver.objects(task=task_id).as_pymongo()
    users=[]
    users_account = []
    publisher_account = []
    #users_weight=[]
    money=0
    i=0
    # 执行竞价算法：基于先到先得、排除歧点的冒泡排序思路
    for task_deliver in task_delivers:
        user = personal_info.models.User.objects(_id=task_deliver['user']).first()
        #定义用户权重
        weight = user['reputation']-task_deliver['money']
        if i>0:
            if weight >weight_temp:
                if money<task_temp.reward:
                    users.append(task_deliver['user'])
                    users_account.append(user.account)
                    money += task_deliver['money']
            else:
                if money<task_temp.reward:
                    users.append(deliver_ttemp['user'])
                    users_account.append(user_wtemp.account)
                    money += deliver_ttemp['money']
                    user_wtemp = user
                    weight_temp = weight
                    deliver_ttemp = task_deliver
        else:
            user_wtemp = user
            weight_temp = weight
            deliver_ttemp = task_deliver
        i +=1
    #处理最后一个竞争者
    if task_delivers:
        if money<=task_temp.reward-deliver_ttemp['money']:
            users.append(deliver_ttemp['user'])
            users_account.append(user_wtemp.account)
            money += deliver_ttemp['money']


    #按排名将task_deliver.user push到该任务的participates里
    models.Task.objects(_id=task_id).update_one(push_all__participates=users)
    users_name=[]
    for user in users:
        p = personal_info.models.User.objects(_id=user).first()
        users_name.append(p.nickname)
    models.Task.objects(_id=task_id).update_one(push_all__participates_name=users_name)
    models.Task.objects(_id=task_id).update_one(push_all__participates_account=users_account)

    #修改该任务的剩余金额和状态
    models.Task.objects(_id=task_id).update_one(set__money_left=task_temp.reward-money)
    models.Task.objects(_id=task_id).update_one(set__isDeliver='已分配')
    if users:
        models.Task.objects(_id=task_id).update_one(set__status='监测中')
    
    redis_publisher = RedisPublisher(facility='foobar', broadcast=True)
    task = models.Task.objects(_id=task_id).first()
    message1 = RedisMessage('任务:'+" "+task.name+" "+'已分配给你！!')
    message2 = RedisMessage('任务'+" "+task.name+" "+'有了新的参与者！')

    #add message
    mylog.info("before loop")
    for user_account in users_account:
        mylog.info(user_account)
        identifier = str(time.time())+","+str(random.random())+","+str(user_account)
        new_message = personal_info.models.Message(identifier=identifier,tag="task",content='任务:'+" "+task.name+" "+'已分配给你！!')
        new_message.save()
        mylog.info("saved!")
        personal_info.models.User.objects(account=user_account).update_one(push__messages=identifier)
        mylog.info("pushed!")

    identifier = str(time.time())+","+str(random.random())+","+str(publisher_account)
    new_message = personal_info.models.Message(identifier=identifier,tag="task",content='任务'+" "+task.name+" "+'有了新的参与者！')
    new_message.save()
    personal_info.models.User.objects(account=publisher_account).update_one(push__messages=identifier)


    # publish message

    publisher_account.append(task.publisher.account)
    redis_publisher.publish_message(users_account,message1)
    redis_publisher.publish_message(publisher_account,message2)


