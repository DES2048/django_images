from typing import cast, TypedDict
from rest_framework import serializers
from rest_framework.request import Request
from typing_extensions import Unpack
from .models import Gallery
from .services import PickerSettings, ShowMode, DEFAULT_SHOW_MODE, PickerSettingsDict

# TYPES
SaveKwargs = TypedDict("SaveKwargs", {"request": Request})

class GallerySerializer(serializers.ModelSerializer[Gallery]):
    
    class Meta: # type: ignore
        model = Gallery
        fields = ['slug', 'title']
    
    #Meta = cast(type[serializers.ModelSerializer[Gallery].Meta], _Meta)

class SettingsSerializer(serializers.Serializer[PickerSettings]):
    selected_gallery = serializers.CharField(max_length=128)
    show_mode = serializers.CharField(max_length=20, default=DEFAULT_SHOW_MODE)

    
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

