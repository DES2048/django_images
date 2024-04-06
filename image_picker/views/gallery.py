import os
from typing import cast

from django.shortcuts import get_object_or_404

from rest_framework import generics, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.request import Request
from rest_framework.response import Response

from image_picker.services import FSImagesProvider, DEFAULT_SHOW_MODE, ShowModeA
from image_picker.serializers import GallerySerializer

from image_picker.models import Gallery

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
   