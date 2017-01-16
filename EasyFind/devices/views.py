from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response,get_object_or_404
from django import forms
from . import models
import personal_info
import json

# deviceForm
class deviceForm(forms.Form):
	name = forms.CharField()
	uuid = forms.CharField()

# Create your views here.
def devices(request,a):
	user = personal_info.models.User.objects(account=a).first()
	user_id = str(user._id)
	account = str(user.account)
	devices = models.Device.objects(owner=user_id).as_pymongo()
	if request.method == 'POST':
		form = deviceForm(request.POST)
		if form.is_valid():
			name = form.cleaned_data['name']
			uuid = form.cleaned_data['uuid']
			device = models.Device(name=name,owner=user_id,uuid=uuid).save()
			return render(request,'devices/devices.html',{'tag':json.dumps('ok')})
		else:
			return render(request,'devices/devices.html',{'tag':json.dumps('no')})
	else:
		form = deviceForm()
		return render(request,'devices/devices.html',{'form':form,'person':user,'devices':devices})

    #user = personal_info.models.User.objects(_id=id).as_pymongo()[0]
	#devicelist = models.Device.objects(_id__in=user.device).as_pymongo()[0]
	#return render(request,"devices/devices.html",{'devicelist':devicelist})
def addDevice(request,a):
	user = personal_info.models.User.objects(account=a).as_pymongo()[0]
	device = models.Device(uuid='c111',owner=user)
	device.save()
	device_json = str(device.to_mongo())
	return HttpResponse(user_json)

def removeDevice(request,device_id):
	device = models.Device.objects(uuid=device_id)
	device.delete()
	return HttpResponse(device)
