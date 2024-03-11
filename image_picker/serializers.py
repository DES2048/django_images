from datetime import datetime
from pathlib import Path

from typing import Any, cast, TypedDict
from typing_extensions import Unpack

from django.urls import reverse

from rest_framework import serializers
from rest_framework.request import Request

from .models import Gallery, FavoriteImage
from .services import (PickerSettings, ShowMode, DEFAULT_SHOW_MODE, PickerSettingsDict,
                       ImageDict,is_file_marked, FSImagesProvider)

# TYPES
SaveKwargs = TypedDict("SaveKwargs", {"request": Request})

# fields
class JsUnixDateTimeField(serializers.Field): # type: ignore

    def to_representation(self, value: datetime) -> float:
        return datetime.timestamp(value)* 1000 if datetime else 0


class PrimaryKeyField(serializers.PrimaryKeyRelatedField):

    def to_representation(self, obj):
        return obj


class GallerySerializer(serializers.ModelSerializer[Gallery]):
    
    pinned_date = JsUnixDateTimeField(read_only=True)
    class Meta: # type: ignore
        model = Gallery
        fields = ['slug', 'title', "pinned", "pinned_date", "dir_path"]
        #extra_kwargs = {'dir_path': {'write_only': True}}

    #Meta = cast(type[serializers.ModelSerializer[Gallery].Meta], _Meta)

class SettingsSerializer(serializers.Serializer[PickerSettings]):
    #selected_gallery = PrimaryKeyField(queryset=Gallery.objects.all())
    selected_gallery = serializers.CharField(max_length=128)
    show_mode = serializers.CharField(max_length=20, default=DEFAULT_SHOW_MODE)
    fav_images_mode = serializers.BooleanField(default=False)
    shuffle_pics_when_loaded = serializers.BooleanField(default=False)

    def validate_selected_gallery(self, value:str) -> str:
        try:
            Gallery.objects.get(pk=value)
        except Gallery.DoesNotExist:
            raise serializers.ValidationError(f" gallery '{value}' doesn't exist")
        return value
    
    def validate_show_mode(self, value:str) -> str:
        if value not in ShowMode.MODES_LIST:
            raise serializers.ValidationError("invalid show_mode value")
        
        return value
    
   
    def save(self, **kwargs:Unpack[SaveKwargs]) -> PickerSettings:  # type: ignore
        data = cast(PickerSettingsDict, self.validated_data)
        
        settings = PickerSettings(
            **data
        )

        settings.to_session(kwargs['request'])
        return settings

class ImageSerializer(serializers.Serializer[ImageDict]):
    name = serializers.CharField(max_length=255, trim_whitespace=False)
    marked = serializers.BooleanField()
    mod_time = serializers.FloatField()
    is_fav = serializers.BooleanField()
    url = serializers.SerializerMethodField()

    def get_url(self, obj:ImageDict) -> str:
        return reverse(
            viewname="get-image", 
            kwargs={
                    "gallery_slug":self.context["gallery_slug"],
                    "image_url": obj["name"]
            })
    
class FavoriteImageSerializer(serializers.ModelSerializer[FavoriteImage]):
    add_to_fav_date = JsUnixDateTimeField(read_only=True, source="add_date")
    url = serializers.SerializerMethodField(read_only=True)
    name = serializers.CharField(max_length=255, trim_whitespace=False)
    marked = serializers.SerializerMethodField(read_only=True)
    mod_time = serializers.SerializerMethodField(read_only=True)
    is_fav = serializers.BooleanField(default=True, read_only=True)
    class Meta: # type: ignore
        model = FavoriteImage
        fields = ["gallery","name", "add_to_fav_date", "url", "mod_time", "is_fav", "marked"]
    
    def get_url(self, obj:FavoriteImage) -> str:
        return reverse(
            viewname="get-image", 
            kwargs={
                    "gallery_slug":obj.gallery_id, # type: ignore
                    "image_url": obj.name
            })
    
    def get_marked(self, obj:FavoriteImage) -> bool:
        return is_file_marked(obj.name)

    def get_mod_time(self, obj:FavoriteImage)-> float:
        return FSImagesProvider.get_mod_time(Path(obj.gallery.dir_path) / obj.name)


class NewImageNameSerializer(serializers.Serializer): # type: ignore
    old_name = serializers.CharField(max_length=256, write_only=True, trim_whitespace=False)
    new_name = serializers.CharField(max_length=256, write_only=True,trim_whitespace=False)

    def __init__(self, data: Any, gallery: Gallery, *args, **kwargs):
        self.gallery = gallery
        super().__init__(None, data, *args, **kwargs)
    
    def validate_old_name(self, old_name: str) -> str:
        gall_path = Path(self.gallery.dir_path)

        if not (gall_path / old_name).exists():
            raise serializers.ValidationError(f"image {old_name} doesn't exist in {self.gallery.title}")
        
        return old_name

    def validate_new_name(self, new_name: str) -> str:
        gall_path = Path(self.gallery.dir_path)

        if (gall_path / new_name).exists():
            raise serializers.ValidationError(f"image {new_name} already exists in {self.gallery.title}")
        
        return new_name


class CopyMoveImageSerializer(serializers.Serializer): # type: ignore
    image_name = serializers.CharField(max_length=256, write_only=True, trim_whitespace=False)
    dst_gallery= serializers.PrimaryKeyRelatedField(queryset=Gallery.objects.all())
    move = serializers.BooleanField(write_only=True, default=False)

    def __init__(self, data: Any, src_gallery: Gallery, *args, **kwargs):
        self.src_gallery = src_gallery
        super().__init__(None, data, *args, **kwargs)
    
    def validate_image_name(self, img_name: str) -> str:
        gall_path = Path(self.src_gallery.dir_path)
        print(gall_path)
        if not (gall_path / img_name).exists():
            raise serializers.ValidationError(f"image {img_name} doesn't exist in {self.src_gallery.title}")

        return img_name

    def validate(self, attrs: Any) -> Any:
        path = Path(attrs["dst_gallery"].dir_path) / attrs["image_name"]
        if path.exists():
            raise serializers.ValidationError({"image_name": [f"image '{attrs['image_name']}' already exist in '{attrs['dst_gallery'].pk}'"]})

        return attrs