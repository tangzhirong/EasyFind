from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response,get_object_or_404
from . import models
from django import forms
import devices
import json
import os
from EasyFind.config import DATA_PATH
from PIL import Image as image

#create personForm
class personForm(forms.Form):
	account = forms.CharField()
	password = forms.CharField()
	nickname = forms.CharField()
	gender = forms.CharField()
	email = forms.EmailField()
	phone = forms.CharField()
	province = forms.CharField()
	city = forms.CharField()
	# reputation = forms.IntegerField()
	picture = forms.FileField()

# Create your views here.
def handle_uploaded_file(userid,sort,taskid,f):
    #��~D�~P~F�~T��~H��~J��~@~A��~J��| �~[��~I~G�~P~M称  �~H~]步设为userid+miao+�~Z~O�~\��~U�
    if sort =="task":
        picturename = taskid+"."+str(f).split('.')[-1]
    else:
        picturename = userid+"."+str(f).split('.')[-1]
    if not os.path.exists(os.path.join(DATA_PATH,"image",userid,sort)):
        os.makedirs(os.path.join(DATA_PATH,"image",userid,sort))

    #picturename = userid+datetime.datetime.now().strftime('%S')+str(randint(100,999))+"."+str(f).split('.')[-1]
    try:
        destination = open(os.path.join(DATA_PATH,"image",userid,sort,picturename),'wb+')

        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()
        return picturename
    except Exception as e:
        return False

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
            widthRatio = float(arg['dst_w']) / ori_w #正确�~N��~O~V��~O�~U��~Z~D�~V���~O
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

#personInfo处理表单提交

def personInfo(request,a):
	person = models.User.objects(account=a).first()
	uid = str(person._id)
	account = str(person.account)
	if request.method == 'POST':
		form = personForm(request.POST,request.FILES)
		if form.is_valid():
			account = form.cleaned_data['account']
			password = form.cleaned_data['password']
			nickname = form.cleaned_data['nickname']
			gender = form.cleaned_data['gender']
			email = form.cleaned_data['email']
			phone = form.cleaned_data['phone']
			province = form.cleaned_data['province']
			city = form.cleaned_data['city']
			picture = request.FILES['picture']
			# reputation = form.cleaned_data['reputation']
			models.User.objects(account=a).update_one(password=password)
			models.User.objects(account=a).update_one(nickname=nickname)
			models.User.objects(account=a).update_one(gender=gender)
			models.User.objects(account=a).update_one(email=email)
			models.User.objects(account=a).update_one(phone=phone)
			models.User.objects(account=a).update_one(province=province)
			models.User.objects(account=a).update_one(city=city)
			sort = "photo"
			handle_uploaded_file(account,sort,"",picture)
			picturename = str(account)+"."+str(picture).split('.')[-1]
			picUrl = os.path.join(DATA_PATH,"image",account,sort,picturename)
			ori_img = picUrl
			sort = "compress_photo"
			if not os.path.exists(os.path.join(DATA_PATH,"image",account,sort)):
				os.makedirs(os.path.join(DATA_PATH,"image",account,sort))
			dst_img = os.path.join(DATA_PATH,"image",account,sort,picturename)
			resizeImg(ori_img=ori_img,dst_img=dst_img,dst_w=95,dst_h=95,save_q=35)
			models.User.objects(account=a).update_one(set__picUrl=dst_img)
			return render(request,'personal_info/personal_info.html',{'tag':json.dumps('ok')})
		else:
			return render(request,'personal_info/personal_info.html',{'tag':json.dumps('no')})
	else:
		form = personForm()
		return render(request,'personal_info/personal_info.html',{'form':form,'personInfo':person})

