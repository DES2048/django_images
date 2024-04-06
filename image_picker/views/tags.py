from django.shortcuts import get_object_or_404

from rest_framework import status, generics
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from image_picker.services import FSImagesProvider
from image_picker.serializers import (  TagSerializer, ImageTagsUpdateSerializer)

from image_picker.models import Gallery, Tag, Image


class TagListCreateApiView(generics.ListCreateAPIView): # type: ignore
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class TagRetUpdDelApiView(generics.RetrieveUpdateDestroyAPIView): # type: ignore
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


@api_view(["GET", "POST"])
def image_tags(request: Request, gallery_slug:str, image_url:str) -> Response:
    gallery = get_object_or_404(Gallery, pk=gallery_slug)
    provider = FSImagesProvider(gallery)
    
    if not provider.image_exists(image_url):
        return Response(status=404)
    
    image = Image.objects.filter(filename=image_url, gallery=gallery).first()

    if request.method == "GET":
       if image:
           tags = [{"id": t.id, "name": t.name } for t in image.tags.all().only("id", "name")]
           return Response(data=tags, status=200)
       else:
           return Response(data=[], status=200)
    else:
        serializer = ImageTagsUpdateSerializer(data=request.data)
        if serializer.is_valid():
            # adding tags
            if not image:
                image = Image.objects.create(gallery=gallery, filename=image_url)
            tags = serializer.validated_data["tags"]
            if not tags:
                image.tags.clear()
                image.save()
            else:
                image.tags.add(*tags)
            return Response(status=200)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

