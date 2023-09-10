from typing import cast
from rest_framework import serializers
from .models import Gallery
from .services import PickerSettings, ShowMode, DEFAULT_SHOW_MODE


class GallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Gallery
        fields = ['slug', 'title']


class SettingsSerializer(serializers.Serializer):
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
    
    def save(self, **kwargs):
        settings = PickerSettings(
            cast(dict,self.validated_data)['selected_gallery'],
            cast(dict,self.validated_data)['show_mode']
        )

        settings.to_session(kwargs['request'])
        return settings

