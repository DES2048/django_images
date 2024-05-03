from pathlib import Path
from typing import cast, Any
import tempfile

from unittest import SkipTest
from unittest.mock import Mock
from django.urls import reverse

from rest_framework.test import APITestCase
from rest_framework.response import Response

from  .models import Gallery, FavoriteImage
from  .services import FavoriteImagesService

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
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), len(self.files_list))
        # check url
        self.assertEqual(resp.data[0]["url"], f"/get-image/gallery/{resp.data[0]['name']}")

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


class ExistedGalleriesTestCase(APITestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.existed_path = tempfile.TemporaryDirectory()
        Gallery.objects.all().delete()
        Gallery.objects.create(title="non-existed", slug="non-existed", dir_path="not_existed_path")
        Gallery.objects.create(title="existed", slug="existed", dir_path=cls.existed_path.name)
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        Gallery.objects.all().delete()
        cls.existed_path.cleanup()
        return super().tearDownClass()
    
    def testReturnOnlyExistedGalleries(self):
        url = reverse("galleries-list")
        resp = cast(Response,self.client.get(url))

        # check status
        self.assertEqual(resp.status_code, 200)

        # check only existed in response
        data = cast(list[dict[str, Any]], resp.data)
        # check length
        self.assertEqual(len(data), 1)
        # check elem
        self.assertEqual(data[0]["title"], "existed")


class FavoriteImageViewsTestCase(APITestCase):
    tmp_dir: tempfile.TemporaryDirectory[str]
    gall1: Gallery
    gall2: Gallery

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp_dir = tempfile.TemporaryDirectory()
        Gallery.objects.all().delete()
        tmp_path = Path(cls.tmp_dir.name)
        gall1_dir = (tmp_path / "fav1")
        gall2_dir = (tmp_path / "fav2")
        gall1_dir.mkdir()
        gall2_dir.mkdir()
        cls.gall1 = Gallery.objects.create(title="for-fav-1", slug="for_fav_1", dir_path=gall1_dir)
        cls.gall2 = Gallery.objects.create(title="for-fav-2", slug="for_fav_2", dir_path=gall2_dir)
        
        # create favs
        cls.fav_images = [{"gallery":cls.gall1.pk, "dir_path":gall1_dir, "name": f"fav1_{i+1}.jpg"} for i in range(5)]
        cls.fav_images.extend([{"gallery":cls.gall2.pk,  "dir_path":gall2_dir, "name": f"fav2_{i+1}.jpg"} for i in range(6)])
        
        # create files
        for img in cls.fav_images:
            (img["dir_path"] / img["name"]).touch() # type: ignore
        for img in cls.fav_images:
            FavoriteImagesService.add(gallery_id = img["gallery"], image_name=img["name"])
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        Gallery.objects.all().delete()
        FavoriteImage.objects.all().delete()

        cls.tmp_dir.cleanup()
        return super().tearDownClass()
    
    def test_list_fav_images(self) -> None:
        
        url = reverse("fav-images")
        resp = cast(Response,self.client.get(url))

        # check status
        self.assertEqual(resp.status_code, 200)

        # check list
        data = cast(list[dict[str, str]], resp.data)
        # check length
        self.assertEqual(len(data), len(self.fav_images))

        # checking data
        # check has image url
        self.assertIsNotNone(data[0].get("url", None))
    
    def test_add_to_fav_view(self):
        exp_image_name = "add_fav1.jpg"
        # create file
        (Path(self.gall1.dir_path) / exp_image_name).touch()
        
        url = reverse("fav-images")
        resp = cast(Response,self.client.post(url, {"gallery": self.gall1.pk, "name": exp_image_name},
                                              format='json'
                                              ))

        # check status
        self.assertEqual(resp.status_code, 201)
        
        # check created
        self.assertTrue(FavoriteImage.objects.filter(image__gallery=self.gall1, image__filename=exp_image_name).exists())
    
    def test_delete_from_fav(self):
        # add image for deletion
        img_name_for_del ="fav_for_delete.jpg"
        (Path(self.gall1.dir_path) / img_name_for_del).touch()
        FavoriteImagesService.add(gallery_id=self.gall1.pk, image_name=img_name_for_del)

        url = reverse("fav-images")
        resp = cast(Response,self.client.delete(url,  {"gallery": self.gall1.pk, "name": img_name_for_del},
                                              format='json'))
        self.assertEqual(resp.status_code, 204)

        # check deleted from db
        self.assertFalse(FavoriteImage.objects.filter(image__gallery=self.gall1, image__filename=img_name_for_del).exists())
        