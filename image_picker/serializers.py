from rest_framework import serializers
from .models import Gallery
from .services import PickerSettings, ShowMode


class GallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Gallery
        fields = ['slug', 'title']


class SettingsSerializer(serializers.Serializer):
    selected_gallery = serializers.CharField(max_length=128)
    show_mode = serializers.CharField(max_length=20, default=ShowMode.UNMARKED)

    def validate_selected_gallery(self, value):
        try:
            Gallery.objects.get(pk=value)
        except Gallery.DoesNotExist:
            raise serializers.ValidationError(f" gallery '{value}' doesn't exist")
        return value
    
    def validate_show_mode(self, value):
        if value not in ShowMode.MODES_LIST:
            raise serializers.ValidationError("invalid show_mode value")
        
        return value
    
    def save(self, **kwargs):
        settings = PickerSettings(
            self.validated_data['selected_gallery'],
            self.validated_data['show_mode']
        )

        settings.to_session(kwargs['request'])
        return settings

