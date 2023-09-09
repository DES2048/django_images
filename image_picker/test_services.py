from typing import Dict, cast
from unittest.mock import Mock
from django.contrib.sessions.backends.base import SessionBase
from django.test import TestCase
from .services import PickerSettings, ShowMode, DEFAULT_SHOW_MODE, SETTINGS_SESSION_KEY


class PickerSettingsTestCase(TestCase):

    def test_default_settings(self):
        settings = PickerSettings.default_settings()
        self.assertEqual(settings.selected_gallery, "")
        self.assertEqual(settings.show_mode,DEFAULT_SHOW_MODE)

    def test_from_session(self):
        # session mock
        request = Mock()
        request.session = SessionBase()

        # for empty settings in session return default settings
        settings = PickerSettings.from_session(request)
        self.assertDictEqual(
            {'selected_gallery': "",
            'show_mode': DEFAULT_SHOW_MODE},
            settings.to_dict()
        )

        # if settings exists in session returns it
        expected = {
            'selected_gallery': "Gallery",
            'show_mode': ShowMode.ALL 
        }
        session = SessionBase()
        session[SETTINGS_SESSION_KEY] = expected
        request.session = session
        settings = PickerSettings.from_session(request)
        self.assertDictEqual(
            expected,
            settings.to_dict()
        )

    def test_to_session(self):
        gall = "Gallery"
        show = ShowMode.ALL
        request = Mock()
        request.session = SessionBase()
        settings = PickerSettings(gall, show)
        settings.to_session(request)

        self.assertIsNotNone(request.session.get(SETTINGS_SESSION_KEY))
        data = cast(Dict[str,str],request.session.get(SETTINGS_SESSION_KEY))
        self.assertEqual(data.get("selected_gallery"), gall)
        self.assertEqual(data.get("show_mode"), show)
    
class ViewsTestCase(TestCase):

    def test_get_settings(self):
        pass
