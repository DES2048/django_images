from django.contrib import admin
from .models import Gallery, FavoriteImage

class WidgetAttrsMixin:
    widgets_attrs = {}
    
    def get_widgets_attrs(self):
        return self.widgets_attrs
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        widgets_attrs = self.get_widgets_attrs()
        
        for field, attrs in widgets_attrs.items():
            form.base_fields[field].widget.attrs.update(attrs)
        
        return form
    
@admin.register(Gallery)
class GalleryAdmin(WidgetAttrsMixin, admin.ModelAdmin):
    widgets_attrs = {
        'title': {'autocomplete' : 'off'},
        'slug': {'autocomplete' : 'off'},
        'dir_path': {'autocomplete' : 'off'}
    }
    list_display = ('title', 'dir_path')
    
@admin.register(FavoriteImage)
class FavImageAdmin(admin.ModelAdmin):
    list_display = ("gallery", "name")
