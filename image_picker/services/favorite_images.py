from pathlib import Path
from django.shortcuts import get_object_or_404

from ..models import Gallery, FavoriteImage
from .types import ImageDict
from .utils import is_file_marked, get_mod_time


class FavoriteImagesService:
    
    @classmethod
    def add(cls, gallery_id:str, image_name:str):
        gall = Gallery.objects.only("pk").get(pk=gallery_id)
        FavoriteImage.objects.update_or_create(
            defaults={
                "name": image_name
            },
            gallery=gall, name=image_name
        )

    @classmethod
    def remove(cls, gallery_id:str, image_name:str):
        obj = get_object_or_404(FavoriteImage, gallery=gallery_id, name=image_name)
        obj.delete()
    

    @classmethod
    def update(cls, gallery_id:str, old_image_name:str, new_image_name:str) -> int:
        return FavoriteImage.objects.filter(gallery=gallery_id, name=old_image_name) \
            .update(name=new_image_name)

    @classmethod
    def exists(cls, gallery_id:str, image_name:str) -> bool:
        return FavoriteImage.objects.filter(gallery=gallery_id, name=image_name).exists()
    
    @classmethod
    def get_favorites_set(cls, gallery_id: str)-> set[str]:
        
        favs = FavoriteImage.objects.filter(gallery=gallery_id).values_list("name", flat=True)
        return set(favs)

    @classmethod
    def list_images(cls) -> list[ImageDict]:
        favs = FavoriteImage.objects.all().select_related()
        # TODO filter files that doesnt exist
        return list(
            {
                "name": fav.name,
                "marked": is_file_marked(fav.name),
                "mod_time": get_mod_time(Path(fav.gallery.dir_path) / fav.name),
                "is_fav": True
            }
            for fav in favs
        )
