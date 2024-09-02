from tempfile import TemporaryDirectory
from pathlib import Path
from typing import cast

from django.test import TestCase

from image_picker.models import FavoriteImage, Gallery

from .serializers import FavoriteImageCreateSerializer
from .serializers import SettingsSerializer

class FavoriteImageCreateSerializerTest(TestCase):
    gallery1: Gallery
    dir_path1: TemporaryDirectory[str]

    @classmethod
    def setUpClass(cls) -> None:
        cls.dir_path1 = TemporaryDirectory()
        cls.gallery1,_ = Gallery.objects.get_or_create(
            title="serializer_test_gallery",
            slug="serializer_test_gallery",
            dir_path=cls.dir_path1.name
            )
        
        return super().setUpClass()
    
    @classmethod
    def tearDownClass(cls) -> None:
        cls.dir_path1.cleanup()

        return super().tearDownClass()
    
    def test_add_image_not_exist(self):
        data = {
            "name": "1.jpg",
            "gallery": self.gallery1.pk
        }

        serializer = FavoriteImageCreateSerializer(data=data)

        is_valid = serializer.is_valid()
        self.assertFalse(is_valid)
    
    def test_add_ok(self):
        filename = "2.jpg"
        (Path(self.dir_path1.name) / filename ).touch()

        data = {
            "name": filename,
            "gallery": self.gallery1.pk
        }

        serializer = FavoriteImageCreateSerializer(data=data)

        is_valid = serializer.is_valid()
        self.assertTrue(is_valid)

        fav_image = cast(FavoriteImage,serializer.save())
        self.assertIsNotNone(fav_image)
        self.assertEqual(fav_image.image.filename, filename)
        self.assertEqual(fav_image.image.gallery_id, self.gallery1.pk)


class SettingsSerializerTestCase(TestCase):
    gallery: Gallery
    dir_path: TemporaryDirectory[str]

    @classmethod
    def setUpClass(cls) -> None:
        cls.dir_path = TemporaryDirectory()
        
        cls.gallery,_ = Gallery.objects.get_or_create(
            title="sserializer_test_gallery",
            slug="sserializer_test_gallery",
            dir_path=cls.dir_path.name
            )
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.dir_path.cleanup()
        return super().tearDownClass()
    
    def test_selected_gallery_validation(self):
        # when fav_images_mode is false, validate field
        # validation OK
        data = {
            "fav_images_mode": False,
            "selected_gallery": self.gallery.pk,
            "selected_tags": []
        }

        s = SettingsSerializer(data=data)
        self.assertTrue(s.is_valid())

        # check no gallery passed
        del data["selected_gallery"]
        s = SettingsSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertTrue("selected_gallery" in s.errors)
        
        self.assertTrue(s.errors["selected_gallery"][0].code,"blank")

        # check gallery pass blank value
        data["selected_gallery"] = ""
        s = SettingsSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertTrue("selected_gallery" in s.errors)
        
        self.assertTrue(s.errors["selected_gallery"][0].code,"blank")

        # check invalid gallery
        data["selected_gallery"] = "!!!!"
        s = SettingsSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertTrue("selected_gallery" in s.errors)
        
        self.assertTrue(s.errors["selected_gallery"][0].code,"invalid")
        #print(f"errors: {s.errors}")
        # otherwise ignore selected_gallery
        data["fav_images_mode"] = True
        s = SettingsSerializer(data=data)
        self.assertTrue(s.is_valid())