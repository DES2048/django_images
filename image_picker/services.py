import re
from glob import iglob
from pathlib import Path
from typing import TypedDict, Protocol

from .models import Gallery

class ImageDict(TypedDict):
    name: str
    marked: bool
    mod_time: float

class GalleryProto(Protocol):
    dir_path: str
    slug: str
    title: str

class ShowMode:
    ALL = 'all'
    MARKED = 'marked'
    UNMARKED = "unmarked"
    MODES_LIST = [ALL, MARKED, UNMARKED]


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

    def get_images(self, show_mode=ShowMode.UNMARKED) -> list[ImageDict]:
        path_all_files = str(self._dirpath / '*.*')

        fname_regex = r".+"
        ext_regex = r"\.(jpg|png|jpeg|gif|webp)$"

        if show_mode == ShowMode.UNMARKED:
            fname_regex += r"[^_]"
        elif show_mode == ShowMode.MARKED:
            fname_regex += "_"

        fname_regex += ext_regex
        regex = re.compile(fname_regex, re.IGNORECASE)
        return list(
            {
                "name": file.name,
                "marked": is_file_marked(file.name),
                "mod_time": self.get_mod_time(file)
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

    def mark_image(self, imagename:str) -> ImageDict:
        
        self.check_parent_and_raise(imagename)
        
        file = self.get_image_path(imagename)

        if not is_file_marked(file):
            new_filename = file.with_name(file.stem + "_"+ file.suffix)
            file.rename(new_filename)
            # update new filename
            file = new_filename
        return {
                "name": file.name,
                "marked": True,
                "mod_time": self.get_mod_time(file)
            }

    def delete_image(self, imagename:str) -> None:
        self.check_parent_and_raise(imagename)

        del_path = self.get_image_path(imagename)
        del_path.unlink()


SETTINGS_SESSION_KEY = "picker_config"
DEFAULT_SHOW_MODE = ShowMode.UNMARKED
class PickerSettings:
    
    @staticmethod
    def default_settings():
        return PickerSettings("", DEFAULT_SHOW_MODE)

    @staticmethod
    def from_session(request):
        data = request.session.get(SETTINGS_SESSION_KEY)
    
        if data:
            return PickerSettings(
                data.get('selected_gallery', ''),
                data.get('show_mode', DEFAULT_SHOW_MODE)
            )
        else:
            return PickerSettings.default_settings()

    def __init__(self, selected_gallery:str="", show_mode=DEFAULT_SHOW_MODE):
        self._selected_gallery = selected_gallery
        self._show_mode = show_mode

    @property
    def selected_gallery(self):
        return self._selected_gallery

    @property
    def show_mode(self):
        return self._show_mode
    
    def to_session(self, request):
        request.session[SETTINGS_SESSION_KEY] = self.to_dict()

    def to_dict(self):
        return {
            "selected_gallery": self._selected_gallery,
            "show_mode": self._show_mode
        }
