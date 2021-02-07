import os
import json
from pathlib import Path
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse
from rest_framework import generics
from rest_framework.parsers import JSONParser
from .services import ImageHelper, ImageInfo, PickerSettings
from .serializers import GallerySerializer, SettingsSerializer
from .models import Gallery


def home(request):
    return render(
        request,
        'image_picker/index.html'
    )


def images(request, gallery_slug):
	
	gallery = get_object_or_404(Gallery, pk=gallery_slug)
	show_mode = request.GET.get("show_mode", "unmarked")
	
	helper = ImageHelper(
            gallery.dir_path,
            show_mode
    )
	
	data = [
	  ImageInfo(gallery_slug, name).__dict__ for name in helper.images]
	
	return JsonResponse(
		data=data,
		safe=False
	)
	

def get_image(request, gallery_slug, image_url):
    
    gallery = get_object_or_404(Gallery, pk=gallery_slug)
    
    fname = os.path.join(gallery.dir_path, image_url)

    return FileResponse(
        open(fname, 'rb')
    )


@csrf_exempt
@require_POST
def mark_image(request, gallery_slug, image_url):
  gallery = get_object_or_404(Gallery, pk=gallery_slug)
  img_path = os.path.join(
    gallery.dir_path, 
    image_url)
  
  new_img_path = ImageHelper.mark_image(
    img_path)
  
  data = ImageInfo(
    gallery_slug, new_img_path).__dict__
    
  return JsonResponse(
    data=data,
    status=200)

  
@csrf_exempt
def delete_image(request, gallery_slug, image_url):
    if request.method == "POST":
       
        gallery = get_object_or_404(Gallery, pk=gallery_slug)
        fname = os.path.join(gallery.dir_path, image_url)

        os.remove(fname)

        return JsonResponse(
            data={},
            status=200
        )
    else:
        return JsonResponse(
            data={},
            status=405
        )


@csrf_exempt
def settings(request):
    if request.method == 'GET':
        picker_settings = PickerSettings.from_session(request)
        data = picker_settings.to_dict() if picker_settings else {}

        serializer = SettingsSerializer(data=data)
        return JsonResponse(serializer.initial_data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = SettingsSerializer(data=data)
        if serializer.is_valid():
            serializer.save(request=request)
            return JsonResponse(serializer.data, status=200)
        return JsonResponse(serializer.errors, status=400)


class GalleryListApiView(generics.ListAPIView):
    serializer_class = GallerySerializer
    queryset = Gallery.objects.all()
