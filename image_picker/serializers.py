from rest_framework import serializers
from .models import Gallery
from .services import PickerSettings


class GallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Gallery
        fields = ['slug', 'title']


class SettingsSerializer(serializers.Serializer):
    selected_gallery = serializers.CharField(max_length=128)
    show_mode = serializers.CharField(max_length=20, default="unmarked")

    def save(self, **kwargs):
        settings = PickerSettings(
            self.validated_data['selected_gallery'],
            self.validated_data['show_mode']
        )

        settings.to_session(kwargs['request'])
        return settings

