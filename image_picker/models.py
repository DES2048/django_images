from django.db import models


class Gallery(models.Model):
    title = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, db_index=True, primary_key=True)
    dir_path = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "Galleries"

    def __str__(self):
        return self.dir_path
