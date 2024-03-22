import os
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Dict, cast
from unittest.mock import Mock
from django.contrib.sessions.backends.base import SessionBase
from django.http import Http404
from django.test import TestCase
from .services import (PickerSettings, ShowMode, DEFAULT_SHOW_MODE, SETTINGS_SESSION_KEY,
                       FSImagesProvider, is_file_marked, FavoriteImagesService, ImagesFilter)
from .models import FavoriteImage, Gallery, Image, Tag

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
    tmpdir2:TemporaryDirectory[str]
    tmpdir_path: Path
    tmpdir_path2: Path
    gallery: Gallery
    gallery2: Gallery
    tags: list[Tag]
    filenames:list[str]
    jpg_filenames:list[str]

    @classmethod
    def touch_file(cls, filename:str) -> None:
        with open(os.path.join(cls.tmpdir_path, filename), "wb"):
                pass
    
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmpdir = TemporaryDirectory()
        cls.tmpdir2 = TemporaryDirectory()

        cls.tmpdir_path = Path(cls.tmpdir.name)
        cls.tmpdir_path2 = Path(cls.tmpdir2.name)

        Gallery.objects.all().delete()

        cls.gallery = Gallery.objects.create(title="sample-gall",
                                             slug="sample-gall",
                                             dir_path=cls.tmpdir_path)
        cls.gallery2 = Gallery.objects.create(title="sample-gall2",
                                             slug="sample-gall2",
                                             dir_path=cls.tmpdir_path2)
        
        cls.tags = [
            Tag.objects.create(name= "Super"),
            Tag.objects.create(name="Classic"),
        ]
        cls.filenames = [
            "1.jpg", "2.jpg", "3.jpg", "4_.jpg", "5_.jpg",
            "1.gif", "2_.gif", "3.jpeg", "4_.jpeg", "5.png",
            "6.png", "7_.png", "8_.webp", "9.webp",
            "10.JPG", "11.PNG", "12.jpg", "for_copy.jpg"
        ]
        cls.filenames_set = set(cls.filenames)
        cls.jpg_filenames = [f for f in cls.filenames if f.endswith("jpg")]

        # create files
        for f in cls.filenames_set:
            Path(cls.tmpdir_path / f).touch()
        
        return super().setUpClass()
    
    @classmethod
    def tearDownClass(cls) -> None:
        Gallery.objects.all().delete()
        FavoriteImage.objects.all().delete()

        if cls.tmpdir:
            cls.tmpdir.cleanup()
        return super().tearDownClass()

    def test_get_images(self):
        
        # check all files were created
        #self.assertEqual(
        #    len(list(self.tmpdir_path.iterdir())),
        #    len(filenames_set)
        #)

        # add favs
        favs = [self.filenames[0], self.filenames[1], self.filenames[2], self.filenames[3], self.filenames[-1]]
        for fav in favs:
            FavoriteImagesService.add(self.gallery.pk, fav)

        # add tags for jpg images
        tag = Tag.objects.create(name="jpg")
        no_image_tag = Tag.objects.create(name="no-image")

        for filename in self.jpg_filenames:
            image = Image.objects.create(gallery=self.gallery, filename=filename)
            image.tags.add(tag) # type: ignore
    
        # test get all images
        provider = FSImagesProvider(self.gallery)
        images = provider.get_images(ShowMode.ALL)
        images_names = {Path(i["name"]).name for i in images}
        self.assertSetEqual(
            self.filenames_set,
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
            {f for f in self.filenames_set if not is_file_marked(f)},
            images_names,
            "UNMARKED not equal"
        )

        # test get marked
        images_names = {Path(i["name"]).name for i in provider.get_images(ShowMode.MARKED)}
        self.assertSetEqual(
            {f for f in self.filenames_set if is_file_marked(f)},
            images_names,
            "MARKED NOT equal"
        )

        # test get with tags
        # get with tag existed
        images_filter = ImagesFilter(gallery=self.gallery, tags=[tag.pk])
        images = provider.get_images(show_mode=ShowMode.ALL, images_filter=images_filter)
        self.assertEqual(len(images), len(self.jpg_filenames))

        # get images with marked
        images = provider.get_images(show_mode=ShowMode.MARKED, images_filter=images_filter)
        self.assertEqual(len(images), len([f for f in self.jpg_filenames if f.endswith("_.jpg")]))

        # test get images with no tag
        # get images with marked
        images_filter = ImagesFilter(gallery=self.gallery, tags=[no_image_tag.pk])
        images = provider.get_images(show_mode=ShowMode.MARKED, images_filter=images_filter)
        self.assertFalse(images)

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
        # add oldfile to Image
        image = Image.objects.create(gallery=self.gallery, filename=oldfile.name)

        provider = FSImagesProvider(self.gallery)
        provider.mark_image(oldfile.name)
        self.assertFalse(oldfile.exists(), "OLD FILE STILL EXISTS")
        self.assertTrue(newfile.exists(), "MARK FILE DOESNT EXIST")
        
        # test old file in favs renames to new file
        self.assertFalse(FavoriteImagesService.exists(self.gallery.pk, oldfile.name))
        self.assertTrue(FavoriteImagesService.exists(self.gallery.pk, newfile.name))

        # test filename changed in Image
        image.refresh_from_db()
        self.assertEqual(image.filename, newfile.name)

    def test_unmark_image(self):
        oldfile = Path(self.tmpdir_path / "for_unmark_.jpg")
        newfile = Path(self.tmpdir_path / "for_unmark.jpg")
        oldfile.touch()

        # add oldfile to fav
        FavoriteImage.objects.create(gallery=self.gallery, name=oldfile.name)
        # add oldfile to Image
        image = Image.objects.create(gallery=self.gallery, filename=oldfile.name)

        provider = FSImagesProvider(self.gallery)
        provider.mark_image(oldfile.name, mark=False)
        self.assertFalse(oldfile.exists(), "OLD FILE STILL EXISTS")
        self.assertTrue(newfile.exists(), "MARK FILE DOESNT EXIST")

         # test old file in favs renames to new file
        self.assertFalse(FavoriteImagesService.exists(self.gallery.pk, oldfile.name))
        self.assertTrue(FavoriteImagesService.exists(self.gallery.pk, newfile.name))

         # test filename changed in Image
        image.refresh_from_db()
        self.assertEqual(image.filename, newfile.name)
    
    def test_rename_image(self):
        # smoke test
        oldfile = Path(self.tmpdir_path / "for_rename_.jpg")
        newfile = Path(self.tmpdir_path / "renamed.jpg")
        oldfile.touch()

        # add oldfile to fav
        FavoriteImage.objects.create(gallery=self.gallery, name=oldfile.name)
        # add oldfile to Image
        image = Image.objects.create(gallery=self.gallery, filename=oldfile.name)

        provider = FSImagesProvider(self.gallery)
        provider.rename_image(oldfile.name, newfile.name)

        self.assertFalse(oldfile.exists(), "FILE FOR RENAME STILL EXISTS")
        self.assertTrue(newfile.exists(), "RENAMED FILE DOESNT EXIST")

         # test old file in favs renames to new file
        self.assertFalse(FavoriteImagesService.exists(self.gallery.pk, oldfile.name))
        self.assertTrue(FavoriteImagesService.exists(self.gallery.pk, newfile.name))

         # test filename changed in Image
        image.refresh_from_db()
        self.assertEqual(image.filename, newfile.name)
    
    def test_delete_image(self):
        file_for_delete = Path(self.tmpdir_path / "for_delete.jpg")
        file_for_delete.touch()

        # add file to fav
        FavoriteImage.objects.create(gallery=self.gallery, name=file_for_delete.name)
        # add file to Image
        Image.objects.create(gallery=self.gallery, filename=file_for_delete.name)

        provider = FSImagesProvider(self.gallery)
        provider.delete_image(file_for_delete.name)
        self.assertFalse(file_for_delete.exists(), "FILE FOR DELETION STILL EXISTS")

         # test file was removed from favs
        self.assertFalse(FavoriteImagesService.exists(self.gallery.pk, file_for_delete.name))

         # test filename removed from Image
        #image.refresh_from_db()
        self.assertFalse(Image.objects.filter(gallery=self.gallery, filename=file_for_delete.name).exists())
    
    def test_copy_image(self):
        # smoke test
        oldfile = Path(self.tmpdir_path / "for_copy.jpg")
        newfile = Path(self.tmpdir_path2 / "for_copy.jpg")

        # add oldfile to fav
        FavoriteImage.objects.create(gallery=self.gallery, name=oldfile.name)
        # add oldfile to Image
        image = Image.objects.create(gallery=self.gallery, filename=oldfile.name)
        # add tags
        image.tags.add(*self.tags)
        self.assertEqual(image.tags.count(), len(self.tags))
                         
        provider = FSImagesProvider(self.gallery)
        provider.copy_move_image(self.gallery2, oldfile.name)

        self.assertTrue(oldfile.exists(), "FILE FOR COPY DOESNT EXISTS")
        self.assertTrue(newfile.exists(), "COPIED FILE DOESNT EXIST")

         # test old file in favs still exists
        self.assertTrue(FavoriteImagesService.exists(self.gallery.pk, oldfile.name))

         # test filename didnt change in Image
        image.refresh_from_db()
        self.assertEqual(image.filename, oldfile.name)
    
    def test_move_image(self):
        # smoke test
        oldfile = Path(self.tmpdir_path / "for_move.jpg")
        newfile = Path(self.tmpdir_path2 / "for_move.jpg")
        oldfile.touch()

        # add oldfile to fav
        FavoriteImage.objects.create(gallery=self.gallery, name=oldfile.name)
        # add oldfile to Image
        image = Image.objects.create(gallery=self.gallery, filename=oldfile.name)
        # add tags
        image.tags.add(*self.tags)
        self.assertEqual(image.tags.count(), len(self.tags))
                         
        provider = FSImagesProvider(self.gallery)
        provider.copy_move_image(self.gallery2, oldfile.name, move=True)

        self.assertFalse(oldfile.exists(), "FILE FOR MOVING STILL EXISTS")
        self.assertTrue(newfile.exists(), "MOVED FILE DOESNT EXIST")

         # test old file in favs changed
        self.assertFalse(FavoriteImagesService.exists(self.gallery.pk, oldfile.name))
        self.assertTrue(FavoriteImagesService.exists(self.gallery2.pk, oldfile.name))

        
        old_Image_qs = Image.objects.filter(gallery=self.gallery, filename=oldfile.name)
        # test old Image removed
        self.assertFalse(old_Image_qs.exists())
        
        new_Image_qs = Image.objects.filter(gallery=self.gallery2, filename=oldfile.name)
        # test new Image exist
        self.assertTrue(new_Image_qs.exists())
        # test tags moved as well
        self.assertEqual(new_Image_qs.first().tags.count(), 2)


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
