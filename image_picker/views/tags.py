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
from image_picker.services.types import ShowMode, ShowModeA


class TagListCreateApiView(generics.ListCreateAPIView): # type: ignore
    serializer_class = TagSerializer
    queryset = Tag.objects.all()

    def get_queryset(self) -> Any:
        qs = super().get_queryset()
        # get value for count from query params if any
        count_for_gallery:str = cast(str, self.request.query_params.get("count-for-gallery", ""))
        count_for_show_mode = cast(str, self.request.query_params.get("count-for-show-mode", str(ShowMode.ALL)))

        qs_filter = None
        # if present annotate each tag with images count in all galleries or in passed gallery
        if count_for_gallery:
            # when asterisk(*) - count for all
            
            if count_for_gallery == "*":
                qs_filter = Q()
            else:
                # check gallery in db
                if Gallery.objects.filter(pk=count_for_gallery).exists():
                    qs_filter = Q(imagetag__image__gallery=count_for_gallery)
            
            if qs_filter is not None:

                show_mode =  count_for_show_mode if count_for_show_mode and count_for_show_mode in ShowMode.MODES_LIST \
                            else ShowMode.ALL
                
                qs_filter &= Q(imagetag__image__filename__iregex=FSImagesProvider.get_filename_regex(show_mode).pattern)
                
                self.with_count = True
                qs = qs.annotate(images_count=Count("imagetag__image", filter=qs_filter))
        
        
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

