import re
from glob import iglob
from pathlib import Path
from shutil import copy2

from ..models import Gallery

from .types import ImageDict, ShowMode, ShowModeA
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
            FavoriteImagesService.update(self._gallery.pk, imagename, new_filename.name)
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
        upd_result = FavoriteImagesService.update(self._gallery.pk, old_name, new_name)
        return {
            "name": new.name,
            "marked": is_file_marked(new.name),
            "mod_time": self.get_mod_time(new),
            "is_fav": upd_result > 0
        }

    def copy_move_image(self, gallery_dst: Gallery, img_name: str, move:bool=False):
        old_file = self.get_image_path(img_name)
        new_file = Path(gallery_dst.dir_path, img_name)

        if not old_file.exists():
            raise ImageNotFound(f"filename {img_name} not found in {self._gallery.title}")

        if new_file.exists():
            raise ImageAlreadyExists(f"filename {img_name} already exists in {self._gallery.title}")
    
        if move:
            old_file.rename(new_file)
            fav = FavoriteImagesService()
            if fav.exists(self._gallery.pk, img_name):
                fav.remove(self._gallery.pk, img_name)
                fav.add(gallery_dst.pk, img_name)
        else:
            copy2(str(old_file), str(new_file))

    def delete_image(self, imagename:str) -> None:
        self.check_parent_and_raise(imagename)

        del_path = self.get_image_path(imagename)
        del_path.unlink()
        # remove it from fav if any
        if FavoriteImagesService.exists(self._gallery.pk, imagename):
            FavoriteImagesService.remove(self._gallery.pk, imagename)
    
    def image_exists(self, imagename:str) -> bool:
        return self.get_image_path(imagename).exists()
