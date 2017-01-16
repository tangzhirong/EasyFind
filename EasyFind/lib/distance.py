#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on 2015年11月18日

@author: taoriming
'''

#from lib.sqlite_controller.ParseDb import ParseDb
#from django.db.models import Q
import datetime
import time
import copy

import  math
import numpy as ny

EARTH_RADIUS  = 6378137  #赤道半径，单位m
def rad(d):
    return d*math.pi /180.0

def rssi2distance(rssi):
    try:
        intrssi = abs(int(rssi))
    except:
        return ""
    #
    #`P = P1 - 10*n*math.log10(x)
    #
    P1 = 63  #1m处的RSSI衰减值
    n = 2.02  #路径损耗因子
    if intrssi>P1:
        power = (intrssi - P1)/(10*n);
        distance = pow(10,power)
    else:
        return ""
    return distance

def getDistancd(lon1,lat1,lon2,lat2):
    radlat1 = rad(lat1)
    radlat2 = rad(lat2)

    a = radlat1  - radlat2
    b = rad(lon1) - rad(lon2);

    s = 2*math.asin(math.sqrt(math.pow(math.sin(a/2), 2)+\
        math.cos(radlat1)*math.cos(radlat2)*math.pow(math.sin(b/2), 2)))
    #print s
    s = s*EARTH_RADIUS
    return s

def lonlat2WebMercator(lon,lat):
    x = lon*20037508.34/180
    y = math.log(math.tan((90+lat)*math.pi/360))/(math.pi/180)
    y = y*20037508.34/180

    return x,y

def lon2WebMercator(lon):
    x = float(lon)*20037508.34/180
    return x

def lat2WebMercator(lat):

    y = math.log(math.tan((90+float(lat))*math.pi/360))/(math.pi/180)
    y = y*20037508.34/180
    return y

def mercator2lat(x,y):
    lon = x/20037508.34*180
    lat = y/20037508.34*180

    lat=180/math.pi*(2*math.atan(math.exp(lat*math.pi/180)) - math.pi/2)
    return  lon,lat

def mercator2Lon(x):
    lon = x/20037508.34*180
    return  lon

def mercator2Lat(y):
    lat = y/20037508.34*180
    lat=180/math.pi*(2*math.atan(math.exp(lat*math.pi/180)) - math.pi/2)
    return  lat

def leastSquareMethod(pointlist):
    A=[]
    B=[]
    for i in range(1,len(pointlist)):
            x2,y2,d2 = pointlist[i]
            x1,y1,d1 = pointlist[i-1]
            A.append([2*(x2-x1),2*(y2-y1)])
            B.append([math.pow(d1, 2)-math.pow(d2, 2)-\
                 (math.pow(x1, 2)+math.pow(y1, 2))+(math.pow(x2, 2)+math.pow(y2, 2))])


    matrix_A = ny.array(A)
    matrix_B = ny.array(B)

    try:
        matrix_A_inverse = ny.linalg.inv(ny.dot(matrix_A.T,matrix_A))
        matrix_X = ny.dot(ny.dot(matrix_A_inverse,matrix_A.T),matrix_B)  
        return matrix_X[0][0],matrix_X[1][0]
    except Exception as e:
        #mylog.error("count inverse error!.."+str(e))    
        return 0.0,0.0

'''
def task_result():
    taskid_set = set()
    taskresultid_set = set()
    obj = ParseDb("D:data.db")
    taskid_list = obj.get_xtable_record('id','users_task')
    taskresultid_list = obj.get_xtable_record('*','users_taskresult','discover_time')

    for taskid in taskresultid_list:
        taskresultid_set.add(taskid['id'])

    for taskid in taskid_list:
        taskid_set.add(taskid['id'])


    task_discover = obj.get_xtable_record('*','users_taskdiscover','discovertime')
    taskmap ={}
    print( "task_discover:"+task_discover)

    for taskdiscover in task_discover:
        if taskmap.has_key(taskdiscover['task_id']):
            tasklist = taskmap[taskdiscover['task_id']]
        else:
            tasklist = []
        tasklist.append(taskdiscover)
        taskmap[taskdiscover['task_id']] = tasklist


    print ("taskmap:"+taskmap)
    data2count = []


    for taskid in range(1,2):#taskid_set: #每一条任务
        lasttime = ""
        if taskid in taskresultid_set:#判断Result表格中是否含有该Task
            for task in taskresultid_list:
                if task['id'] ==taskid:
                    lasttime = task['discover_time']



        discover_list = taskmap[taskid]  #获取该条任务的discover list
        task_discover_valid = []
        #print ('len(discover_list):',len(discover_list)
        for i  in range(0,len(discover_list)):
            count = 1
            if discover_list[i]['discovertime']<lasttime:
                continue
            else:
                for j in range(i+1,len(discover_list)):

                    starttime = datetime.datetime.strptime(discover_list[j]['discovertime'],'%Y-%m-%d %H:%M:%S')
                    endtime = datetime.datetime.strptime(discover_list[i]['discovertime'],'%Y-%m-%d %H:%M:%S')+datetime.timedelta(seconds = 3)
                    #print "i:",i," j:",j," discovertime:",discover_list[i]['discovertime']," starttime:",starttime,"  endtime:",endtime
                    if starttime <= endtime:
                        count +=1
                    else:
                        break;

                if count<3:
                    continue
                else:
                    #print "count:",count
                    #print "fenpian：","i:",i," j:",j
                    if j==len(discover_list)-1:
                        task_discover_valid.append(copy.deepcopy(taskmap[taskid][i:len(discover_list)]))
                    else:
                        task_discover_valid.append(copy.deepcopy(taskmap[taskid][i:j]))


        #print   "task_discover_valid:",task_discover_valid

        for taskdata in task_discover_valid:
           # print "taskdata:",taskdata
            discover_time=0.0
            for data in taskdata:
                discover_time += time.mktime(time.strptime(data['discovertime'], '%Y-%m-%d %H:%M:%S'))
            discover_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(discover_time/len(taskdata)))
            #print "discover_time:",discover_time
            pointdata = [[lon2WebMercator(data['longtitude']),lat2WebMercator(data['latitude']),float(data['distance'])] for data in taskdata]
            x,y = leastSquareMethod(pointdata)
            #print 'x:',x,' y:',y

            insert_sql = "insert into users_taskresult(task_id,longtitude,latitude,discover_time) values('%s','%s','%s','%s')"%(taskdata[0]['task_id'],mercator2Lon(x),mercator2lat(y),discover_time)
            #print "insert_sql:",insert_sql
            obj.dbobj.exec_sql(insert_sql)
'''
#if __name__ =='__main__':
    #print rssi2distance('-69')
