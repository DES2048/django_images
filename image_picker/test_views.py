from pathlib import Path
from typing import cast, Any
import tempfile

from unittest.mock import Mock
from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework.response import Response

from  .models import Gallery

stat_mock = Mock()
stat_mock.stat = Mock(return_value={'st_mtime':1000})

# TODO test for checks all attribute of return image infos
class ImagesTestCase(APITestCase):
    
    @classmethod
    def setUpClass(cls) -> None:
       

        #tmp_dir
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.tmp_dir_path = Path(cls.tmp_dir.name)

        # create files
        cls.files_list = [str(i).rjust(2,'0') + ('.jpg' if i%2 else '_.jpg') for i in range(1,11)]
        #print(cls.files_list)

        for fname in cls.files_list:
            f = cls.tmp_dir_path / fname
            #print(f)
            f.touch()

        Gallery.objects.create(title="gallery", slug="gallery", dir_path=cls.tmp_dir.name)
    
    @classmethod
    def tearDownClass(cls) -> None:
        if cls.tmp_dir:
            cls.tmp_dir.cleanup()
    
    
    def test_images_status_code(self):
        # test ok
        url = reverse("images", args=['gallery'])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

        # test not found
        url = reverse("images", args=['gallery1'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_images(self):
        
        # test images all
        
        url = reverse("images", args=['gallery']) +"?show_mode=all"
        resp = self.client.get(url)
        #print(resp.data)
        self.assertEqual(len(resp.data), len(self.files_list))

        # unmarked
        url = reverse("images", args=['gallery'])
        resp = self.client.get(url)
        #print(resp.data)
        self.assertEqual(len(resp.data), len(self.files_list)//2)
        self.assertEqual(
            len(list(filter(lambda e: e['marked'], resp.data))), 0
        )

        # marked
        url = reverse("images", args=['gallery']) +"?show_mode=marked"
        resp = self.client.get(url)
        #print(resp.data)
        self.assertEqual(len(resp.data), len(self.files_list)//2)
        self.assertEqual(
            len(list(filter(lambda e: not e['marked'], resp.data))), 0
        )
    
    def test_get_image(self):
        # normal path
        url = reverse("get-image", args=["gallery", self.files_list[0]])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        resp.close()
        
        # file doesnt exists
        url = reverse("get-image", args=["gallery", "not_exists"])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 404)
    
    def test_mark_image(self):

        # already marked
        marked = self.tmp_dir_path / "marked_.jpg"
        marked.touch()

        url = reverse("mark-image", args=["gallery", marked.name])
        resp = cast(Response,self.client.post(url))

        # check status
        self.assertEqual(resp.status_code, 200)

        # check data
        self.assertIn("name", cast(dict,resp.data))
        self.assertEqual(cast(dict,resp.data)["name"], "marked_.jpg")
        self.assertTrue(cast(dict,resp.data)["marked"])
        
        #check marked
        for_mark = self.tmp_dir_path / "for_mark.jpg"
        for_mark.touch()

        url = reverse("mark-image", args=["gallery", for_mark.name])
        resp = cast(Response,self.client.post(url))

        # check status
        self.assertEqual(resp.status_code, 200)

        # check data
        data = cast(dict,resp.data)
        self.assertEqual(data["name"], for_mark.stem + "_" + for_mark.suffix)
        self.assertTrue(data["marked"])

        # check file doesnt exists
        url = reverse("mark-image", args=["gallery", "mark_not_exists.jpg"])
        resp = cast(Response,self.client.post(url))

        # check status
        self.assertEqual(resp.status_code, 404)

    def test_unmark_image(self):

        # check already umarked
        unmarked = self.tmp_dir_path / "umarked.jpg"
        unmarked.touch()

        url = reverse("unmark-image", args=["gallery", unmarked.name])
        resp = cast(Response,self.client.post(url))

        # check status
        self.assertEqual(resp.status_code, 200)

        # check data
        self.assertIn("name", cast(dict,resp.data))
        self.assertEqual(cast(dict,resp.data)["name"], unmarked.name)
        self.assertFalse(cast(dict,resp.data)["marked"])
        
        #check unmark
        for_unmark = self.tmp_dir_path / "for_unmark_.jpg"
        for_unmark.touch()

        url = reverse("unmark-image", args=["gallery", for_unmark.name])
        resp = cast(Response,self.client.post(url))

        # check status
        self.assertEqual(resp.status_code, 200)

        # check data
        data = cast(dict, resp.data)
        self.assertEqual(data["name"], for_unmark.stem[:-1] + for_unmark.suffix)
        self.assertFalse(data["marked"])

        # check file doesnt exists
        url = reverse("unmark-image", args=["gallery", "unmark_not_exists.jpg"])
        resp = cast(Response,self.client.post(url))

        # check status
        self.assertEqual(resp.status_code, 404)

    def test_delete_image(self):
        for_delete = self.tmp_dir_path / "for_delete.jpg"
        for_delete.touch()

        # test normal deletion
        url = reverse("delete-image", args=["gallery", for_delete.name])
        resp = cast(Response,self.client.post(url))

        # check status
        self.assertEqual(resp.status_code, 204)

        # test doesn't exist
        url = reverse("delete-image", args=["gallery", "not_exists_for_del.jpg"])
        resp = cast(Response,self.client.post(url))

        # check status
        self.assertEqual(resp.status_code, 404)


class GalleriesViewTestCase(APITestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp_dir = tempfile.TemporaryDirectory()
        gallery = Gallery()
        gallery.title = "for-pin-view"
        gallery.slug = "for-pin_view"
        gallery.dir_path = cls.tmp_dir.name
        gallery.save()
        cls.gallery = gallery

        return super().setUpClass()
    
    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp_dir.cleanup()
        cls.gallery.delete()
        return super().tearDownClass()
    
    def test_pin(self):
    
        url = reverse("pin-gallery", args=[self.gallery.slug])
        resp = cast(Response,self.client.post(url))

        # check status
        self.assertEqual(resp.status_code, 200)

        # check pinned
        data = cast(dict[str, Any], resp.data)
        self.assertTrue(data["pinned"])
        self.assertIsNotNone(data["pinned_date"])
        
    def test_unpin(self):
        url = reverse("unpin-gallery", args=[self.gallery.slug])
        resp = cast(Response,self.client.post(url))

        # check status
        self.assertEqual(resp.status_code, 200)

        # check pinned
        data = cast(dict[str, Any], resp.data)
        self.assertFalse(data["pinned"])
        self.assertIsNone(data["pinned_date"])