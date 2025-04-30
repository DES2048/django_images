from django.contrib import admin
from django.http import HttpRequest
from django.db.models import QuerySet

from typing import Iterable
from pathlib import Path

from .models import Gallery, FavoriteImage, Tag, Image, ImageTag

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
    #list_display = ("gallery", "name")
    pass


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


class TagInline(admin.TabularInline):
    model = ImageTag
    #fields = ("tag__name",)


class FileExistsFilter(admin.SimpleListFilter):
    title = "file exists"
    parameter_name = "file_exists"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> Iterable[tuple[str,str]] | None:
        return [("yes", "Yes"), ("no", "No")]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet | None:
        if not self.value():
            return queryset

        images = queryset.all().select_related("gallery").only("id", "filename","gallery__dir_path")

        not_existed_id =list(
            map(lambda e: e.id,
                filter(lambda i:  not (Path(i.gallery.dir_path) / i.filename).exists(), images)
            )
        )

        return queryset.exclude(id__in=not_existed_id) if self.value() == "yes" else queryset.filter(id__in=not_existed_id)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("filename", "gallery")
    list_filter = (FileExistsFilter, "gallery")
    search_fields = ("filename",)
    inlines = (TagInline,)
