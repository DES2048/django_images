#from __future__ import annotations
import os
from typing import cast

from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, HttpRequest, HttpResponse, Http404

from rest_framework import status, generics, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .services import PickerSettings, FSImagesProvider, DEFAULT_SHOW_MODE, ShowModeA
from .serializers import ( GallerySerializer, SettingsSerializer, FavoriteImageSerializer,ImageSerializer, NewImageNameSerializer, CopyMoveImageSerializer)

from .models import Gallery, FavoriteImage

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
    serializer = ImageSerializer(instance=images, many=True, context={"gallery_slug": gallery_slug}) # type: ignore
    
    return Response(data=serializer.data)
	

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
    # TODO raise 500 on other exceptions
    try:
        image_info = helper.mark_image(image_url, mark=mark)
    except FileNotFoundError as e:
        raise Http404(e.strerror)
    
    serializer = ImageSerializer(instance=image_info, context={"gallery_slug":gallery_slug})
    return Response(data=serializer.data)


@api_view(['POST'])
def rename_image(request:Request , gallery_slug:str) -> Response:
    gallery = get_object_or_404(Gallery, pk=gallery_slug)

    serializer = NewImageNameSerializer(data=request.data, gallery=gallery)
    if serializer.is_valid():
        helper = FSImagesProvider(gallery)
        image_info = helper.rename_image(
            serializer.validated_data.get("old_name"),
            serializer.validated_data.get("new_name")
        )
        serializer = ImageSerializer(instance=image_info, context={"gallery_slug":gallery_slug})
        return Response(data=serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def copy_move_image(request:Request , gallery_slug:str) -> Response:
    gallery = get_object_or_404(Gallery, pk=gallery_slug)

    serializer = CopyMoveImageSerializer(data=request.data, src_gallery=gallery)
    if serializer.is_valid():
        helper = FSImagesProvider(gallery)
        helper.copy_move_image(
            serializer.validated_data.get("dst_gallery"),
            serializer.validated_data.get("image_name"),
            serializer.validated_data.get("move")
        )
        return Response(data=None)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def delete_image(_, gallery_slug:str, image_url:str) -> Response:

    gallery = get_object_or_404(Gallery, pk=gallery_slug)
    helper = FSImagesProvider(gallery)
    # TODO raise 500 on other exceptions
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


class GalleryListApiView(generics.ListCreateAPIView): # type: ignore
    serializer_class = GallerySerializer
    queryset = Gallery.objects.all()

    def list(self, request, *args, **kwargs):
        # returns only galleries that exist on filesystem
        queryset = self.get_queryset()

        galls = list(filter(lambda g: os.path.exists(g.dir_path), queryset))

        serializer = self.get_serializer(galls, many=True)
        return Response(serializer.data)


class GalleryRetUpdDelView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GallerySerializer
    queryset = Gallery.objects.all()
    lookup_field = "slug"

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
    

# Favorite images
class FavoriteImageListCreateApiView(generics.ListCreateAPIView, # type: ignore 
                                     generics.DestroyAPIView): # type: ignore
    serializer_class = FavoriteImageSerializer
    queryset = FavoriteImage.objects.all().select_related("gallery")

    def get_object(self) -> FavoriteImage:
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        queryset = self.filter_queryset(self.get_queryset())
        obj = generics.get_object_or_404(queryset, gallery=serializer.validated_data["gallery"],
                                         name=serializer.validated_data["name"])

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
