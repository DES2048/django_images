from functools import partial
import re
from glob import iglob
from random import shuffle, choice
import os


class ImageHelper:
    def __init__(self, dirname=".", exclude_marked=True):
        from pathlib import Path

        resolved_path = str(Path(dirname).resolve()) + '/*.*'

        self.images = list(filter(partial(re.match, r'.+[^_]\.(jpg|png|jpeg|gif)$'), iglob(resolved_path)))
        shuffle(self.images)

    def get_random_image(self):
        if not len(self.images):
            return None
        
        return choice(self.images)
        
    def mark_image(self, image):
        ext_start_index = image.rfind('.')
        filename = image[0: ext_start_index]
        extension = image[ext_start_index:]

        new_filename = filename + '_' + extension

        os.replace(image, new_filename)

        self.images.remove(image)

    def delete_image(self, image):
        os.remove(image)
        self.images.remove(image)
