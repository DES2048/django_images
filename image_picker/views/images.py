from typing import cast

from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpRequest, Http404

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from image_picker.models import Gallery
from image_picker.services import DEFAULT_SHOW_MODE, FSImagesProvider, ImagesFilter, ShowModeA

from image_picker.serializers import ImageSerializer, ImagesFilterSerializer, NewImageNameSerializer, CopyMoveImageSerializer

# TODO mechanizm for checking ingoing image names /urls
# TODO images views to viewset
# TODO image serializer

@api_view(['GET'])
def images(request:Request, gallery_slug:str) -> Response:

    gallery = get_object_or_404(Gallery, pk=gallery_slug)
    show_mode = request.GET.get("show_mode", DEFAULT_SHOW_MODE)

    # get tags 
    tagsRaw = request.query_params.getlist("tags") # type:ignore
    tags = []
    if isinstance(tagsRaw, list):
        tags = [int(t) for t in tagsRaw] # type:ignore

    helper = FSImagesProvider(gallery)
    images_filter:ImagesFilter = ImagesFilter(gallery=gallery, tags=tags)

    images = helper.get_images(show_mode=cast(ShowModeA, show_mode), images_filter=images_filter)
    serializer = ImageSerializer(instance=images, many=True, context={"gallery_slug": gallery_slug}) # type: ignore
    
    return Response(data=serializer.data)
	

@api_view(["POST"])
def filter_images(request:Request) -> Response:
    # get from gallery filter serializer
    serializer = ImagesFilterSerializer(data=request.data)

    if serializer.is_valid():
        images_filter:ImagesFilter = serializer.save() # type: ignore
        images = FSImagesProvider.filter_images2(images_filter) # type: ignore
        rs = ImageSerializer(instance=images, many=True) # type: ignore
        return Response(data=rs.data)
    else:
        return Response(data=serializer.errors, status=400)
    # get images from images provider
    # return response


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
