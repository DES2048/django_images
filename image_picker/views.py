from typing import cast

from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, HttpRequest, HttpResponse, Http404
from django.urls import reverse

from rest_framework import status, generics, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .services import PickerSettings, FSImagesProvider, DEFAULT_SHOW_MODE, ShowModeA
from .serializers import GallerySerializer, SettingsSerializer
from .models import Gallery

# TODO mechanizm for checking ingoing image names /urls
# TODO images views to viewset
# TODO image serializer


def home(request:HttpRequest) -> HttpResponse:
    return render(
        request,
        'image_picker/index_vue.html'
    )

@api_view(['GET'])
def images(request:Request, gallery_slug:str) -> Response:

    gallery = get_object_or_404(Gallery, pk=gallery_slug)
    show_mode = request.GET.get("show_mode", DEFAULT_SHOW_MODE)

    helper = FSImagesProvider(gallery)
    
    images = helper.get_images(show_mode=cast(ShowModeA, show_mode))

    data = [
        {**image, 
         "url": reverse("get-image", kwargs={
                                        "gallery_slug":gallery_slug,
                                        "image_url": image["name"]
                                      })
        } for image in images
    ]
    return Response(data=data)
	

def get_image(_:HttpRequest, gallery_slug:str, image_url:str) -> FileResponse:
    
    gallery = get_object_or_404(Gallery, pk=gallery_slug)
    
    try:
        fname = FSImagesProvider(gallery).get_image_path(image_url)
    except FileNotFoundError as e:
        raise Http404(e.strerror)
    return FileResponse(
        open(fname, 'rb')
    )


@api_view(['POST'])
def mark_image(_, gallery_slug:str, image_url:str, mark:bool=True) -> Response:
  
    gallery = get_object_or_404(Gallery, pk=gallery_slug)
  
    helper = FSImagesProvider(gallery)
    try:
        image_info = helper.mark_image(image_url, mark=mark)
    except FileNotFoundError as e:
        raise Http404(e.strerror)
    
    data = {
        **image_info,
        "url": reverse("get-image", kwargs={
                                        "gallery_slug":gallery_slug,
                                        "image_url": image_info["name"]
                                      })
    }
    return Response(data=data)

  
@api_view(['POST'])
def delete_image(_, gallery_slug:str, image_url:str) -> Response:

    gallery = get_object_or_404(Gallery, pk=gallery_slug)
    helper = FSImagesProvider(gallery)
    
    try:
        helper.delete_image(image_url)
    except FileNotFoundError as e:
        raise Http404(e.strerror)

    return Response(status=status.HTTP_204_NO_CONTENT)

# TODO Validate gallery and show_mode from session stil exists
# TODO Move to ApiView or GenericApiView class    
@api_view(['GET', 'POST'])
def settings(request: Request) -> Response:
    if request.method == 'GET':
        picker_settings = PickerSettings.from_session(cast(HttpRequest,request))
        serializer = SettingsSerializer(instance=picker_settings)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = SettingsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(request=request)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class GalleryListApiView(generics.ListAPIView): # type: ignore
    serializer_class = GallerySerializer
    queryset = Gallery.objects.all()


@api_view(['POST'])
def pin_unpin_gallery(_, gallery_slug:str, pin:bool=True) -> Response:
    gallery = get_object_or_404(Gallery, pk=gallery_slug)
  
    gallery.pinned = pin
    gallery.save()

    s = GallerySerializer(gallery)
    
    return Response(data=s.data)

class GalleryViewSet(viewsets.ViewSet):

    def list(self, request:Request):
        qs = Gallery.objects.all()
        s = GallerySerializer(instance=qs, many=True)
        return Response(s.data)
    
    @action(detail=False)
    def images(self, request:Request, gallery_slug:str) -> Response:
        gallery = get_object_or_404(Gallery, pk=gallery_slug)
        show_mode = request.GET.get("show_mode", DEFAULT_SHOW_MODE)
	
        helper = FSImagesProvider(gallery)
    
        data = helper.get_images(show_mode=cast(ShowModeA, show_mode))
	
        return Response(data=data)
