from typing import cast
from django.http import HttpRequest
from .types import DEFAULT_SHOW_MODE, ShowModeA, PickerSettingsDict


SETTINGS_SESSION_KEY = "picker_config"

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
