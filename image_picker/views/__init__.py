from typing import Any, cast

from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

from rest_framework import status, generics, serializers
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from image_picker.services import PickerSettings
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
    
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        #headers = self.get_success_headers(serializer.initial_data)
        out_serializer = FavoriteImageListSerializer(instance=serializer.instance)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

