from tempfile import TemporaryDirectory
from django.test import TestCase
from .models import Gallery

class GalleryTestCase(TestCase):

    def test_pin(self):
        with TemporaryDirectory() as tmp_dir:
            gallery = Gallery()
            gallery.title = "for-pin"
            gallery.slug = "for-pin"
            gallery.dir_path = tmp_dir
            gallery.save()

            # check defaults for pinned
            self.assertFalse(gallery.pinned, "by default pinned must be false")
            self.assertIsNone(gallery.pinned_date, "by default pinned date is none")

            gallery.pinned = True
            gallery.save()
            
            # check pinned
            self.assertTrue(gallery.pinned, "pinned must be true")
            self.assertIsNotNone(gallery.pinned_date, "pinned date must be set")
    
    def test_unpin(self):
        with TemporaryDirectory() as tmp_dir:
            gallery = Gallery()
            gallery.title = "for-unpin"
            gallery.slug = "for-unpin"
            gallery.dir_path = tmp_dir
            gallery.pinned = True
            gallery.save()

            # check pinned
            self.assertTrue(gallery.pinned, "pinned must be true")
            self.assertIsNotNone(gallery.pinned_date, "pinned date must be set")

            gallery.pinned = False
            gallery.save()
            
            # check unpinned
            self.assertFalse(gallery.pinned, "for unpin pinned must be false")
            self.assertIsNone(gallery.pinned_date, "pinned date must be unset")