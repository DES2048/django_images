from functools import partial
import re
from glob import iglob
import os
from pathlib import Path
from django.urls import reverse


class ShowMode:
    ALL = 'all'
    MARKED = 'marked'
    UNMARKED = "unmarked"


class ImageHelper:
    def __init__(self, dirname=".", show_mode="unmarked"):

        resolved_path = str(Path(dirname).resolve()) + '/*.*'

        fname_regex = r".+"
        ext_regex = r"\.(jpg|png|jpeg|gif|webp)$"

        if show_mode == "unmarked":
            fname_regex += r"[^_]"
        elif show_mode == "marked":
            fname_regex += "_"

        fname_regex += ext_regex

        self._images = list(filter(partial(re.match, fname_regex), iglob(resolved_path)))
	
    @property
    def images(self):
	       return self._images
    
    @classmethod
    def is_marked(cls, image_name):
        return Path(image_name).stem.endswith("_")

    @classmethod    
    def mark_image(cls, image):
        ext_start_index = image.rfind('.')
        filename = image[0: ext_start_index]
        extension = image[ext_start_index:]

        new_filename = filename + '_' + extension

        os.replace(image, new_filename)
        
        return new_filename


    def delete_image(self, image):
        os.remove(image)
        self.images.remove(image)


class ImageInfo:
  
  def __init__(self, gallery_id, img_path):
    path = Path(img_path)
    self.name = path.name
    self.url = reverse(
      "get-image",
		  kwargs={
			  "gallery_slug" : gallery_id,
			  "image_url" : self.name
    })
    self.marked = ImageHelper.is_marked(self.name)
    self.mod_date = path.stat().st_mtime * 1000


class PickerSettings:
    
    @staticmethod
    def from_session(request):
        data = request.session.get("picker_config")
        defaults = {
            'selected_gallery': "",
        }

        if data:
            return PickerSettings(
                data.get('selected_gallery', ''),
                data.get('show_mode', ShowMode.UNMARKED)
            )
        else:
            return PickerSettings(**defaults)

    def __init__(self, selected_gallery, show_mode=ShowMode.UNMARKED):
        self._selected_gallery = selected_gallery
        self.show_mode = show_mode

    @property
    def selected_gallery(self):
        return self._selected_gallery

    def to_session(self, request):
        request.session["picker_config"] = self.to_dict()

    def to_dict(self):
        return {
            "selected_gallery": self._selected_gallery,
            "show_mode": self.show_mode
        }
