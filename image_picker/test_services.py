from django.test import TestCase
from unittest.mock import MagicMock

from .services import (
    ShowMode,
    PickerSettings
)

def SessionMock(data):
    mock = MagicMock()
    mock.__getitem__.return_value = data
    mock.get.return_value = data
    return mock


class PickerSettingTestCase(TestCase):
    @classmethod 
    def setUp(cls):
        
        cls._defaultSettingsDict = {
            "selected_gallery": "",
            "show_mode": "unmarked"
        }    

    def test_to_dict(self):
        to = PickerSettings("favorite").to_dict()

        expect = {
            "selected_gallery": 'favorite',
            "show_mode": ShowMode.UNMARKED
        }

        self.assertDictEqual(to, expect)

    def test_from_session(self):

        # if no session yet return default
        request_mock = MagicMock()
        request_mock.session = SessionMock(data=None)

        to = PickerSettings.from_session(request_mock).to_dict()
        
        request_mock.session.get.assert_called_with("picker_config")
        self.assertDictEqual(to, self._defaultSettingsDict)

        # or return data in session
        ret_val = self._defaultSettingsDict
        ret_val['selected_gallery'] = "favorites"
        request_mock.session = SessionMock(data=ret_val)

        to = PickerSettings.from_session(request_mock).to_dict()
        self.assertDictEqual(to, ret_val)

    def test_to_session(self):
        request_mock = MagicMock()
        request_mock.session = MagicMock()

        settings = PickerSettings("favorites", ShowMode.ALL)
        settings.to_session(request_mock)

        request_mock.session.__setitem__.assert_called_with(
            'picker_config',
            settings.to_dict()
        )
