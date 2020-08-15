from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.conf import settings
from .services import ImageHelper
import os

def home(request):
	return render(
		request,
		'image_picker/random.html'
	)

def get_random(request):
	helper = ImageHelper(
		settings.IMAGE_PICKER_DIR
	)
	fullname = helper.get_random_image()
	fname = fullname[fullname.rfind("/")+1:]
	
	return JsonResponse(
		{ "url": fname}
	)
	
def get_image(request, url):
	fname = os.path.join(settings.IMAGE_PICKER_DIR, url)
	
	return FileResponse(
		open(fname, 'rb')
	)