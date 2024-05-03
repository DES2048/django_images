from typing import Any, cast

from django.shortcuts import get_object_or_404
from django.db.models import Q, Count

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

    def get_queryset(self) -> Any:
        qs = super().get_queryset()
        # get value for count from query params if any
        count_for_val:str = cast(str, self.request.query_params.get("count-for", ""))
        
        # if present annotate each tag with images count in all galleries or in passed gallery
        if count_for_val:
            # when asterisk(*) - count for all
            gall_filter = None
            if count_for_val == "*":
                gall_filter = Q()
            else:
                # check gallery in db
                if Gallery.objects.filter(pk=count_for_val).exists():
                    gall_filter = Q(imagetag__image__gallery=count_for_val)
            
            if gall_filter is not None:
                self.with_count = True
                qs = qs.annotate(images_count=Count("imagetag__image", filter=gall_filter))
        
        return qs

    def get_serializer(self, *args: Any, **kwargs: Any) -> Any:
        serializer_class = self.get_serializer_class()
        
        kwargs.setdefault('context', self.get_serializer_context())
        with_count = getattr(self, "with_count", False)
        if with_count:
            kwargs.setdefault('with_count', True)
        return serializer_class(*args, **kwargs)


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

