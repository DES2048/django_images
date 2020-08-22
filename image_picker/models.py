from django.db import models
from .validators import validate_path_exists, validate_is_dir


class Gallery(models.Model):
    title = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, db_index=True, primary_key=True)
    dir_path = models.CharField(max_length=255, unique=True,
    validators=(validate_path_exists, validate_is_dir))

    class Meta:
        verbose_name_plural = "Galleries"

    def __str__(self):
        return self.dir_path
