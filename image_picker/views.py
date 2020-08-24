import os
import json
from pathlib import Path
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from rest_framework import generics
from rest_framework.parsers import JSONParser
from .services import ImageHelper, PickerSettings
from .serializers import GallerySerializer, SettingsSerializer
from .models import Gallery


def home(request):
    return render(
        request,
        'image_picker/home.html'
    )


def get_random_image_url(request):
    picker_settings = PickerSettings.from_session(request)

    if not picker_settings:
        context = {
            'status': 'error',
            'message': 'Pick gallery in your sidenav'
        }
    else:
        gallery = Gallery.objects.get(pk=picker_settings.selected_gallery)
        helper = ImageHelper(
            gallery.dir_path,
            picker_settings.show_mode
        )

        fullname = helper.get_random_image()
        fname = fullname[fullname.rfind("/") + 1:]

        context = {
            'status': 'ok',
            "url": fname
        }

    return JsonResponse(
        data=context
    )


def images(request, gallery_slug):
	
	gallery = get_object_or_404(Gallery, pk=gallery_slug)
	show_mode = request.GET.get("show_mode", "unmarked")
	
	helper = ImageHelper(
            gallery.dir_path,
            show_mode
    )
	
	data = [
		{
			"name": Path(name).name,
			"url": reverse("get-image",
			    kwargs={
			        "gallery_slug" : gallery_slug,
			        "image_url" : Path(name).name
			    })
	    } for name in helper.images]
	
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
def settings_old(request):
    if request.method == 'GET':
        picker_settings = request.session.get("picker_settings")
        if not picker_settings:
            return JsonResponse(
                {}
            )
        else:
            return JsonResponse(
                picker_settings
            )
    elif request.method == 'POST':
        picker_settings = json.loads(request.body)
        request.session['picker_settings'] = picker_settings
        return HttpResponse()


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
