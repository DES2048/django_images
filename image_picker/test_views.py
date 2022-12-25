from pathlib import Path
import tempfile
from unittest import skip
from unittest.mock import Mock, patch
from django.urls import reverse

from rest_framework.test import APITestCase

from image_picker.services import is_file_marked

from  .models import Gallery

stat_mock = Mock()
stat_mock.stat = Mock(return_value={'st_mtime':1000})

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

        self.assertEqual(resp.status_code, 200)
