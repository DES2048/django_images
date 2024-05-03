import re
from pathlib import Path
from shutil import copy2
from typing import Any, cast
from django.db.models import Q, ExpressionWrapper, BooleanField

from ..models import Gallery, ImageTag, Image, FavoriteImage

from .types import ImageDict, ShowMode, ShowModeA, ImagesFilter
from .favorite_images import FavoriteImagesService
from .utils import is_file_marked, get_mod_time


# TODO to exceptions module
class ImagesException(Exception):
    pass

class ImageNotFound(ImagesException):
    pass

class ImageAlreadyExists(ImagesException):
    pass


class FSImagesProvider():
    
    @classmethod
    def get_mod_time(cls, filename:str|Path) -> float:
        return get_mod_time(filename)

    @classmethod
    def get_images_from_db(cls, images_filter:ImagesFilter) ->list[ImageDict]:
        
        qs_filter = Q()
        
        if images_filter.gallery:
            qs_filter &= Q(gallery=images_filter.gallery)
        if images_filter.tags:
            qs_filter &= Q(tags__in=images_filter.tags)
        
        images = Image.objects.select_related("favoriteimage", "gallery").filter(qs_filter).annotate(
            is_fav=ExpressionWrapper(Q(favoriteimage__isnull=False), output_field=BooleanField())
        )
        
        regex = cls.get_filename_regex(images_filter.show_mode)

        def image_filter(image:Image):
            p = Path(image.gallery.dir_path) / image.filename
            return p.exists and regex.match(p.name) 

        filtered_images = filter(
            image_filter,
            images
        )
         # type: ignore
        k:list[ImageDict]= [
            {
                "name": image.filename,
                "marked": is_file_marked(image.filename),
                "mod_time": cls.get_mod_time(Path(image.gallery.dir_path) / image.filename),
                "is_fav": cast(bool,image.is_fav) # type: ignore
            }
            for image in filtered_images
        ]
        return k
    
    @classmethod
    def get_filename_regex(cls, show_mode:ShowModeA) -> re.Pattern[str]:
        fname_regex = r".*"
        ext_regex = r"\.(jpg|png|jpeg|gif|webp)$"

        if show_mode == ShowMode.UNMARKED:
            fname_regex += r"[^_]"
        elif show_mode == ShowMode.MARKED:
            fname_regex += "_"

        fname_regex += ext_regex
        return re.compile(fname_regex, re.IGNORECASE)
    
    @classmethod
    def filter_images2(cls, images_filter:ImagesFilter) -> list[ImageDict]:
        # получим regex для фильтрации
        regex = cls.get_filename_regex(images_filter.show_mode)

        # фильтруем либо по только по картинкам из бд
        if images_filter.tags:
            return cls.get_images_from_db(images_filter)

        # либо по картинкам из файловой системы
        # получим список файлов и отфильтруем по show_mode и расширениям        
        paths = filter(
            lambda p: regex.match(p.name),
            Path(images_filter.gallery.dir_path).glob("*.*")
        )
        
        # get favorites for this gallery
        favs_set = FavoriteImagesService.get_favorites_set(images_filter.gallery.pk)
        
        # вернем
        return list(
            {
                "name": file.name,
                "marked": is_file_marked(file.name),
                "mod_time": cls.get_mod_time(file),
                "is_fav": file.name in favs_set
            }
            for file in paths
        )
        

    @classmethod
    def filter_images(cls, images_filter:ImagesFilter):
        # images filter
        paths = []
        filter_tags = images_filter.tags
        if filter_tags:
            # filter images by tags
            #reset_queries()
            gallery_filter = images_filter.gallery if images_filter.gallery else None
            images = ImageTag.objects.filter(tag__in=filter_tags, image__gallery=gallery_filter) \
                .select_related("image__gallery")
            paths = [Path(image.image.gallery.dir_path) / image.image.filename for image in images]
            #print(len(connection.queries))
            paths = list(filter(lambda p:p.exists(), paths))
        
        return paths
    
    def __init__(self, gallery:Gallery) -> None:
        self._gallery = gallery
        self._dirpath = Path(gallery.dir_path).resolve()

    def get_images(self, show_mode:ShowModeA=ShowMode.UNMARKED, images_filter:ImagesFilter|None=None) -> list[ImageDict]:
        if images_filter:
            images_filter.gallery = self._gallery
            images_filter.show_mode = show_mode
        else:
            images_filter = ImagesFilter(gallery=self._gallery, show_mode=show_mode)
            
        
        return self.filter_images2(images_filter)
    
        fname_regex = r".*"
        ext_regex = r"\.(jpg|png|jpeg|gif|webp)$"

        if show_mode == ShowMode.UNMARKED:
            fname_regex += r"[^_]"
        elif show_mode == ShowMode.MARKED:
            fname_regex += "_"

        fname_regex += ext_regex
        regex = re.compile(fname_regex, re.IGNORECASE)

        paths = filter(
            lambda p: regex.match(p.name),
            self.filter_images(images_filter) if images_filter.tags \
                else self._dirpath.glob("*.*")
        )
        
        # get favorites for this gallery
        favs_set = FavoriteImagesService.get_favorites_set(self._gallery.pk) #if not paths \
        #else set(FavoriteImage.objects.filter(name__in=map(lambda p:p.name, paths)).values_list("name", flat=True))
        
        
        return list(
            {
                "name": file.name,
                "marked": is_file_marked(file.name),
                "mod_time": self.get_mod_time(file),
                "is_fav": file.name in favs_set
            }
            for file in paths
            # FIXME regex doesnt work properly on only filenames without full path
            #for file in filter(lambda p:regex.match(p.name), self._dirpath.glob("*.*"))
        )
    
    def check_parent(self, imagename:str) -> bool:
        return self._dirpath == (self._dirpath / imagename).parent
    
    def check_parent_and_raise(self, imagename:str) -> bool:
        if not self.check_parent(imagename):
            raise ImagesException(
                f"image {imagename} doesn't belong to gallery {self._gallery.dir_path}"
            )
        return True
    
    def get_image_path(self, imagename:str, raise_not_found:bool=True) -> Path:
        """" Returns full images path relative to galery by imagename"""
        file = self._dirpath / imagename
        if not file.exists() and raise_not_found:
            raise FileNotFoundError(f"file {imagename} doesn't exist in gallery {self._dirpath}")
        return file

    def mark_image(self, imagename:str, mark:bool=True) -> ImageDict:
        
        self.check_parent_and_raise(imagename)
        
        file = self.get_image_path(imagename)

        new_filename: Path| None = None
        if mark and not is_file_marked(file):
            new_filename = file.with_name(file.stem + "_"+ file.suffix)
        elif not mark and is_file_marked(file):
            new_filename = file.with_name(file.stem[:-1] + file.suffix)
    
        if new_filename:
            file.rename(new_filename)
            file = new_filename

            # update filename in favs
            #FavoriteImagesService.update(self._gallery.pk, imagename, new_filename.name)
            # update Image if exists in db
            Image.objects.filter(gallery=self._gallery, filename=imagename).update(filename=new_filename.name)
        return {
                "name": file.name,
                "marked": mark,
                "mod_time": self.get_mod_time(file),
                "is_fav": FavoriteImagesService.exists(self._gallery.pk, file.name)
            }
    
    def rename_image(self, old_name:str, new_name:str) -> ImageDict:
        old = self.get_image_path(old_name)
        new = self.get_image_path(new_name, raise_not_found=False)

        if not old.exists():
            raise ImageNotFound(f"filename {old_name} not found in {self._gallery.title}")

        if new.exists():
            raise ImageAlreadyExists(f"filename {new_name} already exists in {self._gallery.title}")
        
        new = old.rename(new)

        # update in fav if any
        #upd_result = FavoriteImagesService.update(self._gallery.pk, old_name, new_name)
        # update in Images
        Image.objects.filter(gallery=self._gallery, filename=old_name).update(filename=new_name)
        return {
            "name": new.name,
            "marked": is_file_marked(new.name),
            "mod_time": self.get_mod_time(new),
            "is_fav": FavoriteImagesService.exists(self._gallery.pk, new_name)
        }

    def copy_move_image(self, gallery_dst: Gallery, img_name: str, move:bool=False):
        old_file = self.get_image_path(img_name)
        new_file = Path(gallery_dst.dir_path, img_name)

        if not old_file.exists():
            raise ImageNotFound(f"filename {img_name} not found in {self._gallery.title}")

        if new_file.exists():
            raise ImageAlreadyExists(f"filename {img_name} already exists in {self._gallery.title}")

        image = Image.objects.filter(gallery=self._gallery, filename=img_name).first()

        if move:
            old_file.rename(new_file)
            
            #fav = FavoriteImagesService()
            
            '''
            if fav.exists(self._gallery.pk, img_name):
                fav.remove(self._gallery.pk, img_name)
                fav.add(gallery_dst.pk, img_name)
            '''
            # update Image in db if any
            if image:
                image.gallery = gallery_dst
                image.save()
            
        else:
            copy2(str(old_file), str(new_file))
            # copy tags
           
            if image:
                # get tags
                tag_ids = image.tags.all().only("pk").values_list(flat=True)
                #save copy of image
                image.pk = None
                image.gallery = gallery_dst
                image.save()
                image.tags.add(*tag_ids)

    def delete_image(self, imagename:str) -> None:
        self.check_parent_and_raise(imagename)

        del_path = self.get_image_path(imagename)
        del_path.unlink()
        # remove it from fav if any
        if FavoriteImagesService.exists(self._gallery.pk, imagename):
            FavoriteImagesService.remove(self._gallery.pk, imagename)
        
        # remove image from Images
        Image.objects.filter(gallery=self._gallery, filename=imagename).delete()
    
    def image_exists(self, imagename:str) -> bool:
        return self.get_image_path(imagename).exists()
