import os
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Dict, cast
from unittest.mock import Mock
from django.contrib.sessions.backends.base import SessionBase
from django.http import Http404
from django.test import TestCase
from .services import (PickerSettings, ShowMode, DEFAULT_SHOW_MODE, SETTINGS_SESSION_KEY,
                       FSImagesProvider, is_file_marked, FavoriteImagesService)
from .models import FavoriteImage, Gallery

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
        given = PickerSettings.from_session(request)
        self.assertDictEqual(
            PickerSettings.default_settings().to_dict(),
            given.to_dict()
        )

        # if settings exists in session returns it
        expected = {
            'selected_gallery': "Gallery",
            'show_mode': ShowMode.ALL,
            'fav_images_mode': False 
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
    gallery: Gallery

    @classmethod
    def touch_file(cls, filename:str) -> None:
        with open(os.path.join(cls.tmpdir_path, filename), "wb"):
                pass
    
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmpdir = TemporaryDirectory()
        cls.tmpdir_path = Path(cls.tmpdir.name)
        
        Gallery.objects.all().delete()
        cls.gallery = Gallery.objects.create(title="sample-gall",
                                             slug="sample-gall",
                                             dir_path=cls.tmpdir_path)
        return super().setUpClass()
    
    @classmethod
    def tearDownClass(cls) -> None:
        Gallery.objects.all().delete()
        FavoriteImage.objects.all().delete()

        if cls.tmpdir:
            cls.tmpdir.cleanup()
        return super().tearDownClass()

    def test_get_images(self):
        filenames = [
            "1.jpg", "2.jpg", "3.jpg", "4_.jpg", "5_.jpg",
            "1.gif", "2_.gif", "3.jpeg", "4_.jpeg", "5.png",
            "6.png", "7_.png", "8_.webp", "9.webp",
            "10.JPG", "11.PNG"
        ]
        filenames_set = set(filenames)
        
        # create files
        for f in filenames_set:
            Path(self.tmpdir_path / f).touch()
        
        # check all files were created
        self.assertEqual(
            len(list(self.tmpdir_path.iterdir())),
            len(filenames_set)
        )

         # add favs
        favs = [filenames[0], filenames[1], filenames[2], filenames[3], filenames[-1]]
        for fav in favs:
            FavoriteImagesService.add(self.gallery.pk, fav)

    
        # test get all images
        provider = FSImagesProvider(self.gallery)
        images = provider.get_images(ShowMode.ALL)
        images_names = {Path(i["name"]).name for i in images}
        self.assertSetEqual(
            filenames_set,
            images_names,
            "ALL images not equal"
        )
        
        # test favs
        # filter favs image names from images
        given_favs = set(
                map(
                    lambda x: x["name"],
                    filter(lambda f:f["is_fav"], images)
                )
        )
        self.assertSetEqual(
            given_favs,
            set(favs)
        )
        # test get unmarked
        images_names = {Path(i["name"]).name for i in provider.get_images(ShowMode.UNMARKED)}
        self.assertSetEqual(
            {f for f in filenames_set if not is_file_marked(f)},
            images_names,
            "UNMARKED not equal"
        )

        # test get marked
        images_names = {Path(i["name"]).name for i in provider.get_images(ShowMode.MARKED)}
        self.assertSetEqual(
            {f for f in filenames_set if is_file_marked(f)},
            images_names,
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

        # add oldfile to fav
        FavoriteImage.objects.create(gallery=self.gallery, name=oldfile.name)

        provider = FSImagesProvider(self.gallery)
        provider.mark_image(oldfile.name)
        self.assertFalse(oldfile.exists(), "OLD FILE STILL EXISTS")
        self.assertTrue(newfile.exists(), "MARK FILE DOESNT EXIST")

        # test old file in favs renames to new file
        self.assertFalse(FavoriteImagesService.exists(self.gallery.pk, oldfile.name))
        self.assertTrue(FavoriteImagesService.exists(self.gallery.pk, newfile.name))

    def test_unmark_image(self):
        oldfile = Path(self.tmpdir_path / "for_unmark_.jpg")
        newfile = Path(self.tmpdir_path / "for_unmark.jpg")
        oldfile.touch()

        # add oldfile to fav
        FavoriteImage.objects.create(gallery=self.gallery, name=oldfile.name)

        provider = FSImagesProvider(self.gallery)
        provider.mark_image(oldfile.name, mark=False)
        self.assertFalse(oldfile.exists(), "OLD FILE STILL EXISTS")
        self.assertTrue(newfile.exists(), "MARK FILE DOESNT EXIST")

         # test old file in favs renames to new file
        self.assertFalse(FavoriteImagesService.exists(self.gallery.pk, oldfile.name))
        self.assertTrue(FavoriteImagesService.exists(self.gallery.pk, newfile.name))


class FavoriteImagesServiceTestCase(TestCase):

    tmpdir:TemporaryDirectory[str]
    tmpdir_path: Path
    gallery: Gallery

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmpdir = TemporaryDirectory()
        cls.tmpdir_path = Path(cls.tmpdir.name)

        Gallery.objects.all().delete()
        cls.gallery = Gallery.objects.create(title="sample-gall",
                                             slug="sample-gall",
                                             dir_path=cls.tmpdir_path)
        return super().setUpClass()
    
    @classmethod
    def tearDownClass(cls) -> None:
        Gallery.objects.all().delete()
        FavoriteImage.objects.all().delete()
        if cls.tmpdir:
            cls.tmpdir.cleanup()
        return super().tearDownClass()

    def test_add(self):
        # when first add new image to favs
        image_name = "image_1.jpg"
        FavoriteImagesService.add(self.gallery.slug, image_name)

        fav = FavoriteImage.objects.get(gallery=self.gallery.pk, name=image_name)
        self.assertIsNotNone(fav)
        self.assertEqual(fav.gallery.pk, self.gallery.pk)
        self.assertEqual(fav.name, image_name)
        self.assertIsNotNone(fav.add_date)
        fav_add_date = fav.add_date
        # add again and ensure notning has changed
        FavoriteImagesService.add(self.gallery.slug, image_name)

        fav = FavoriteImage.objects.get(gallery=self.gallery.pk, name=image_name)
        self.assertIsNotNone(fav)
        self.assertEqual(fav.gallery.pk, self.gallery.pk)
        self.assertEqual(fav.name, image_name)
        self.assertEqual(fav.add_date, fav_add_date)
    
    def test_remove(self):
        image_name = "image_2.jpg"
        FavoriteImagesService.add(self.gallery.pk, image_name)

        # delete existed
        FavoriteImagesService.remove(self.gallery.pk, image_name)

        with self.assertRaises(FavoriteImage.DoesNotExist): 
            FavoriteImage.objects.get(gallery=self.gallery, name=image_name)
        
        # delete unexisted
        with self.assertRaises(Http404):
            FavoriteImagesService.remove(self.gallery.pk, "not_exist.jpg")
    
    def test_update(self):

        image_name = "image_1.jpg"
        FavoriteImagesService.add(self.gallery.slug, image_name)
        new_image_name = "new_image.jpg"

        FavoriteImagesService.update(self.gallery.pk, image_name, new_image_name)
        fav = FavoriteImage.objects.get(gallery=self.gallery.pk, name=new_image_name)
        self.assertEqual(fav.name, new_image_name)
    
    def test_get_favorites_set(self):
        FavoriteImage.objects.all().delete()
        images = [f"{i+1}.jpg" for i in range(10)]

        for image in images:
            FavoriteImagesService.add(self.gallery.pk, image)
        
        # test existed favs
        given_images_set = FavoriteImagesService.get_favorites_set(self.gallery.pk)
        self.assertSetEqual(given_images_set, set(images))

        # test no favs for gallery
        given_images_set = FavoriteImagesService.get_favorites_set("unxesisted")
        self.assertSetEqual(given_images_set, set())
    
    def test_exists(self):
        image_name = "image_1.jpg"
        FavoriteImagesService.add(self.gallery.slug, image_name)

        # exists
        self.assertTrue(FavoriteImagesService.exists(self.gallery.pk, image_name))

        # doesnt exist
        self.assertFalse(FavoriteImagesService.exists(self.gallery.pk, "not_exist.jpg"))
