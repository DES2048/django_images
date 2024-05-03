from pathlib import Path
from django.shortcuts import get_object_or_404

from ..models import Gallery, FavoriteImage, Image
from .types import ImageDict
from .utils import is_file_marked, get_mod_time


class FavoriteImagesService:
    
    @classmethod
    def add(cls, gallery_id:str, image_name:str):
        image,_ = Image.objects.get_or_create(gallery_id=gallery_id, filename=image_name)
        fav, _ = FavoriteImage.objects.get_or_create(
            image_id = image.pk
        )
        return fav

    @classmethod
    def _add(cls, gallery_id:str, image_name:str):
        gall = Gallery.objects.only("pk").get(pk=gallery_id)
        FavoriteImage.objects.update_or_create(
            defaults={
                "name": image_name
            },
            gallery=gall, name=image_name
        )

    @classmethod
    def remove(cls, gallery_id:str, image_name:str):
        image = get_object_or_404(Image, gallery=gallery_id, filename=image_name)
        obj = get_object_or_404(FavoriteImage, image=image)
        obj.delete()
    

    @classmethod
    def update(cls, gallery_id:str, old_image_name:str, new_image_name:str) -> int:
        return FavoriteImage.objects.filter(gallery=gallery_id, name=old_image_name) \
            .update(name=new_image_name)

    @classmethod
    def exists(cls, gallery_id:str, image_name:str) -> bool:
        return FavoriteImage.objects.select_related("image__gallery").filter(image__gallery=gallery_id, image__filename=image_name).exists()
    
    @classmethod
    def get_favorites_set(cls, gallery_id: str)-> set[str]:
        
        favs = FavoriteImage.objects.select_related("image__gallery").filter(image__gallery=gallery_id).values_list("image__filename", flat=True)
        return set(favs)

    @classmethod
    def list_images(cls) -> list[ImageDict]:
        favs = FavoriteImage.objects.all().select_related("image__gallery")
        # TODO filter files that doesnt exist
        return list(
            {
                "name": fav.image.filename,
                "marked": is_file_marked(fav.image.filename),
                "mod_time": get_mod_time(Path(fav.image.gallery.dir_path) / fav.image.filename),
                "is_fav": True
            }
            for fav in favs
        )
