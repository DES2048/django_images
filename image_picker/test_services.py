import os
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Dict, cast
from unittest.mock import Mock
from django.contrib.sessions.backends.base import SessionBase
from django.test import TestCase
from .services import (PickerSettings, ShowMode, DEFAULT_SHOW_MODE, SETTINGS_SESSION_KEY,
                       FSImagesProvider, is_file_marked)


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
    
class FSImageProviderTestCase(TestCase):
    
    tmpdir:TemporaryDirectory[str]
    tmpdir_path: Path

    @classmethod
    def touch_file(cls, filename:str) -> None:
        with open(os.path.join(cls.tmpdir_path, filename), "wb"):
                pass
    
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmpdir = TemporaryDirectory()
        cls.tmpdir_path = Path(cls.tmpdir.name)
        return super().setUpClass()
    
    @classmethod
    def tearDownClass(cls) -> None:
        if cls.tmpdir:
            cls.tmpdir.cleanup()
        return super().tearDownClass()

    def test_get_images(self):
        filenames = set([
            "1.jpg", "2.jpg", "3.jpg", "4_.jpg", "5_.jpg",
            "1.gif", "2_.gif", "3.jpeg", "4_.jpeg", "5.png",
            "6.png", "7_.png", "8_.webp", "9.webp",
            "10.JPG", "11.PNG"
        ])
        for f in filenames:
            Path(self.tmpdir_path / f).touch()
        
        # check all files were created
        self.assertEqual(
            len(list(self.tmpdir_path.iterdir())),
            len(filenames)
        )
        gallery = Mock()
        gallery.dir_path = self.tmpdir.name

        # test get all images
        provider = FSImagesProvider(gallery)
        images = {Path(i["name"]).name for i in provider.get_images(ShowMode.ALL)}
        self.assertSetEqual(
            filenames,
            images,
            "ALL images not equal"
        )
        
        # test get unmarked
        images = {Path(i["name"]).name for i in provider.get_images(ShowMode.UNMARKED)}
        self.assertSetEqual(
            {f for f in filenames if not is_file_marked(f)},
            images,
            "UNMARKED not equal"
        )

        # test get marked
        images = {Path(i["name"]).name for i in provider.get_images(ShowMode.MARKED)}
        self.assertSetEqual(
            {f for f in filenames if is_file_marked(f)},
            images,
            "MARKED NOT equal"
        )
    
    def test_get_mod_time(self):
        filename = "mod_time.jpg"
        self.touch_file(filename)

        self.assertTrue((self.tmpdir_path / filename).exists(), "FAIL CREATE FILE FOR MOD TIME TEST")
        self.assertGreater(FSImagesProvider.get_mod_time(self.tmpdir_path / filename), 0)


    def test_mark_image(self):
        oldfile = Path(self.tmpdir_path / "aaaaaa.jpg")
        newfile = Path(self.tmpdir_path / "aaaaaa_.jpg")
        oldfile.touch()

        gallery = Mock()
        gallery.dir_path = self.tmpdir.name
        provider = FSImagesProvider(gallery)
        provider.mark_image(oldfile.name)
        self.assertFalse(oldfile.exists(), "OLD FILE STILL EXISTS")
        self.assertTrue(newfile.exists(), "MARK FILE DOESNT EXIST")