from typing import cast

from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

from rest_framework import status, generics
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from image_picker.services import PickerSettings
from image_picker.serializers import ( SettingsSerializer, FavoriteImageSerializer )

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

