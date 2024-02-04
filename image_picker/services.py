import re
from glob import iglob
from pathlib import Path
from typing import TypedDict, Protocol, TypeAlias, Literal, cast

from django.http import HttpRequest
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Gallery, FavoriteImage

class MySettings(Protocol):
    DEBUG: bool


settings = cast(MySettings, settings)

class ImageDict(TypedDict):
    name: str
    marked: bool
    mod_time: float
    is_fav: bool

class GalleryProto(Protocol):
    dir_path: str
    slug: str
    title: str

class ShowMode:
    ALL = 'all'
    MARKED = 'marked'
    UNMARKED = "unmarked"
    MODES_LIST = [ALL, MARKED, UNMARKED]

ShowModeA: TypeAlias = Literal["all", "marked", "unmarked"]

def is_file_marked(filename:str|Path) -> bool:
    file = filename if type(filename) == Path else Path(filename)
    return file.stem.endswith("_")    

class ImagesException(Exception):
    pass

# TODO wraps image/images to image info class
class FSImagesProvider():
    
    @classmethod
    def get_mod_time(cls, filename:str|Path) -> float:
        file = filename if type(filename) == Path else Path(filename)
        return file.stat().st_mtime * 1000
    
    def __init__(self, gallery:Gallery) -> None:
        self._gallery = gallery
        self._dirpath = Path(gallery.dir_path).resolve()

    def get_images(self, show_mode:ShowModeA=ShowMode.UNMARKED) -> list[ImageDict]:
        path_all_files = str(self._dirpath / '*.*')

        fname_regex = r".+"
        ext_regex = r"\.(jpg|png|jpeg|gif|webp)$"

        if show_mode == ShowMode.UNMARKED:
            fname_regex += r"[^_]"
        elif show_mode == ShowMode.MARKED:
            fname_regex += "_"

        fname_regex += ext_regex
        regex = re.compile(fname_regex, re.IGNORECASE)

        # get favorites for this gallery
        favs_set = FavoriteImagesService.get_favorites_set(self._gallery.pk)
        return list(
            {
                "name": file.name,
                "marked": is_file_marked(file.name),
                "mod_time": self.get_mod_time(file),
                "is_fav": file.name in favs_set
            }
            for file in map(Path, filter(regex.match, iglob(path_all_files)))
        )
    
    def check_parent(self, imagename:str) -> bool:
        return self._dirpath == (self._dirpath / imagename).parent
    
    def check_parent_and_raise(self, imagename:str) -> bool:
        if not self.check_parent(imagename):
            raise ImagesException(
                f"image {imagename} doesn't belong to gallery {self._gallery.dir_path}"
            )
        return True
    
    def get_image_path(self, imagename:str) -> Path:
        """" Returns full images path relative to galery by imagename"""
        file = self._dirpath / imagename
        if not file.exists():
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
            FavoriteImagesService.update(self._gallery.pk, imagename, new_filename.name)
        return {
                "name": file.name,
                "marked": mark,
                "mod_time": self.get_mod_time(file),
                "is_fav": FavoriteImagesService.exists(self._gallery.pk, file.name)
            }

    def delete_image(self, imagename:str) -> None:
        self.check_parent_and_raise(imagename)

        del_path = self.get_image_path(imagename)
        del_path.unlink()
        # remove it from fav if any
        if FavoriteImagesService.exists(self._gallery.pk, imagename):
            FavoriteImagesService.remove(self._gallery.pk, imagename)


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
    def update(cls, gallery_id:str, old_image_name:str, new_image_name:str):
        FavoriteImage.objects.filter(gallery=gallery_id, name=old_image_name) \
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

        return list(
            {
                "name": fav.name,
                "marked": is_file_marked(fav.name),
                "mod_time": FSImagesProvider.get_mod_time(Path(fav.gallery.dir_path) / fav.name),
                "is_fav": True
            }
            for fav in favs
        )

# Picker settings
class PickerSettingsDict(TypedDict):
    selected_gallery: str
    show_mode: ShowModeA
    fav_images_mode: bool
    shuffle_pics_when_loaded: bool

SETTINGS_SESSION_KEY = "picker_config"
DEFAULT_SHOW_MODE = ShowMode.UNMARKED
class PickerSettings:
    
    @staticmethod
    def default_settings():
        return PickerSettings(
            selected_gallery="",
            show_mode=DEFAULT_SHOW_MODE,
            fav_images_mode=False,
            shuffle_pics_when_loaded=False
        )

    @staticmethod
    def from_session(request:HttpRequest):
        data = request.session.get(SETTINGS_SESSION_KEY)
    
        if data:
            # set default values if not set in session
            return PickerSettings(
                data.get('selected_gallery', ''),
                data.get('show_mode', DEFAULT_SHOW_MODE),
                data.get('fav_images_mode', False),
                data.get('shuffle_pics_when_loaded', False)
            )
        else:
            return PickerSettings.default_settings()

    def __init__(self, selected_gallery:str="", show_mode:ShowModeA=DEFAULT_SHOW_MODE,
                 fav_images_mode:bool=False, shuffle_pics_when_loaded:bool=False):
        self._selected_gallery = selected_gallery
        self._show_mode = show_mode
        self._fav_images_mode = fav_images_mode
        self._shuffle_pics_when_loaded = shuffle_pics_when_loaded

    @property
    def selected_gallery(self) -> str:
        return self._selected_gallery

    @property
    def show_mode(self) -> ShowModeA:
        return cast(ShowModeA,self._show_mode)
    
    @property
    def fav_images_mode(self) -> bool:
        return self._fav_images_mode
    
    @property
    def shuffle_pics_when_loaded(self) ->bool:
        return self._shuffle_pics_when_loaded
    
    def to_session(self, request:HttpRequest) -> None:
        request.session[SETTINGS_SESSION_KEY] = self.to_dict()

    def to_dict(self) -> PickerSettingsDict:
        return {
            "selected_gallery": self._selected_gallery,
            "show_mode": cast(ShowModeA,self._show_mode),
            "fav_images_mode":self._fav_images_mode,
            "shuffle_pics_when_loaded": self._shuffle_pics_when_loaded
        }
