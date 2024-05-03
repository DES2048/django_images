from dataclasses import dataclass
from typing import Literal, Protocol, TypeAlias, TypedDict 
from ..models import Gallery

class ShowMode:
    ALL = 'all'
    MARKED = 'marked'
    UNMARKED = "unmarked"
    MODES_LIST = [ALL, MARKED, UNMARKED]

ShowModeA: TypeAlias = Literal["all", "marked", "unmarked"]
DEFAULT_SHOW_MODE = ShowMode.UNMARKED

class GalleryProto(Protocol):
    dir_path: str
    slug: str
    title: str

class ImageDict(TypedDict):
    name: str
    marked: bool
    mod_time: float
    is_fav: bool


@dataclass
class ImagesFilter:
    gallery: Gallery
    show_mode: ShowModeA = DEFAULT_SHOW_MODE
    tags: list[int] | None = None


class PickerSettingsDict(TypedDict):
    selected_gallery: str
    show_mode: ShowModeA
    fav_images_mode: bool
    shuffle_pics_when_loaded: bool
    selected_tags: list[int]
