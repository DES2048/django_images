import os
from pathlib import Path
from typing import Any, NotRequired, TypedDict, cast

from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status, generics, serializers
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from image_picker.services import PickerSettings,FavoriteImagesService
from image_picker.serializers import ( SettingsSerializer, FavoriteImageListSerializer, FavoriteImageCreateSerializer )

from image_picker.models import FavoriteImage

from .images import *
from .gallery import *
from .tags import *


def home(request:HttpRequest) -> HttpResponse:
    return render(
        request,
        'image_picker/index_vue.html'
    )


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


# Favorite images
class FavoriteImageListCreateApiView(generics.ListCreateAPIView, # type: ignore 
                                     generics.DestroyAPIView): # type: ignore
    serializer_class = FavoriteImageListSerializer
    queryset = FavoriteImage.objects.all().select_related("image__gallery")

    def get_serializer_class(self) -> serializers.BaseSerializer:
        return self.serializer_class if self.request.method == "GET" else FavoriteImageCreateSerializer

    def get_object(self) -> FavoriteImage:
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        queryset = self.filter_queryset(self.get_queryset())
        obj = generics.get_object_or_404(queryset, image__gallery_id=serializer.validated_data["gallery"],
                                         image__filename=serializer.validated_data["name"])

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def _get_queryset(self) -> generics.QuerySet: # type: ignore
        qs = super().get_queryset()

        show_mode = self.request.query_params.get("show_mode", DEFAULT_SHOW_MODE) # type: ignore
        qs = qs.filter(image__filename__iregex=FSImagesProvider.get_filename_regex(show_mode).pattern)
        return qs
    
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        #headers = self.get_success_headers(serializer.initial_data)
        out_serializer = FavoriteImageListSerializer(instance=serializer.instance)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request:Request, *args:Any, **kwargs:Any)-> Response:
        queryset = self.get_queryset()

        show_mode = request.query_params.get("show_mode", DEFAULT_SHOW_MODE) # type: ignore
        queryset = queryset.filter(image__filename__iregex=FSImagesProvider.get_filename_regex(show_mode).pattern)

        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@api_view(["POST"])
@csrf_exempt
def image_infos_by_paths(request: Request) -> Response:
    # TODO: to list serializer
    files_list = cast(list[str], request.data["files"])

    # get galleries
    galls: dict[Path, str] = {
        Path(gall.dir_path): gall.slug
        for gall in Gallery.objects.only("slug", "dir_path")
        if os.path.exists(gall.dir_path)
    }

    # set for dirs that not exists in galls
    nfound_paths: set[Path] = set()
    ImgDict = TypedDict("ImgDict", 
                        {"gallery_id": str,
                        "path": str,
                        "name": NotRequired[str],
                        "is_fav": NotRequired[bool],
                        "tags": NotRequired[list]}
                        )
    data:list[ImgDict] = []

    for image_file in files_list:
        img_path = Path(image_file)

        if img_path.parent in nfound_paths:
            continue

        gall_id = galls.get(img_path.parent)

        if not gall_id and os.getenv("TERMUX_VERSION"):
            # slow approach with samefile
            for path, slug in galls.items():
                if path.samefile(img_path.parent):
                    gall_id = slug
                    galls[img_path.parent] = slug
                    break

            if not gall_id:
                nfound_paths.add(img_path.parent)

        if gall_id:
            img:ImgDict = {
                "gallery_id": gall_id,
                "path" : image_file
            }
            
            # FIXME: n+1 query
            imageDb = Image.objects.filter(
                filename=img_path.name, gallery__pk=gall_id
            ).first()

            if imageDb:
                img["name"] = img_path.name
                img["is_fav"] = FavoriteImagesService().exists(gall_id, img_path.name)

                tags = [
                    {"id": t.id, "name": t.name}
                    for t in imageDb.tags.all().only("id", "name")
                ]
                if tags:
                    img["tags"] = tags

            data.append(img)

    return Response(status=200, data=data)
