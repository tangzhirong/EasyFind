from django.shortcuts import render
from django.shortcuts import render_to_response,get_object_or_404
from django.http import HttpResponse,HttpResponseRedirect
import personal_info
import json
import time
import random
from django import forms

class searchForm(forms.Form):
	account = forms.CharField()

# Create your views here.
#加载好友管理界面，提供添加好友功能
def friends(request,a):
	user = personal_info.models.User.objects(account=a).first()
	user_account = str(user.account)
	friends = personal_info.models.User.objects(account__in=user.friends).as_pymongo()
	if request.method == 'POST':
		form = searchForm(request.POST)
		if form.is_valid():
			account = form.cleaned_data['account']
			friend = personal_info.models.User.objects(account=account).first()
			if friend:
				personal_info.models.User.objects(account=a).update_one(push__friends=account)
				identifier = str(time.time())+","+str(random.random())+","+str(account)
				new_message = personal_info.models.Message(identifier=identifier,tag="friend",content=user_account+" "+" 已添加你为好友！")
				new_message.save()
				personal_info.models.User.objects(account=account).update_one(push__messages=identifier)
				return render(request,"friends/friends.html",{'tag':json.dumps('ok')})
			else:
				return render(request,"friends/friends.html",{'tag':json.dumps('no')})
			
			#return HttpResponseRedirect("/"+user_account)
		else:
			return HttpResponseRedirect("")
	else:
		form = searchForm()
		return render(request,"friends/friends.html",{'form':form,'person':user,'friends':friends})
		
#删除好友
def remove(request):
	response = HttpResponse()
	response['Content-Type']="text/javascript"
	user = request.POST.get("user","")
	friend = request.POST.get("friend","")
	personal_info.models.User.objects(account=user).update_one(pull__friends=friend)
	return HttpResponse('删除成功！')
