from collections.abc import Iterable
from django.db import models
from django.utils import timezone as tz
from .validators import validate_path_exists, validate_is_dir


class Gallery(models.Model):
    title = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, db_index=True, primary_key=True)
    dir_path = models.CharField(max_length=255, unique=True,
    validators=(validate_path_exists, validate_is_dir))
    pinned = models.BooleanField(default=False)
    pinned_date = models.DateTimeField(null=True, blank=True)

    class Meta: # type: ignore
        verbose_name_plural = "Galleries"

    def __str__(self):
        return self.dir_path

    def save(self, force_insert: bool = False, force_update: bool = False, using: str | None = None, update_fields: Iterable[str] | None = None) -> None:
        if self.pinned and not self.pinned_date:
            self.pinned_date = tz.now()
        if not self.pinned and self.pinned_date:
            self.pinned_date = None
        return super().save(force_insert, force_update, using, update_fields)


class FavoriteImage(models.Model):
    gallery = models.ForeignKey(Gallery, on_delete=models.DO_NOTHING, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    add_date = models.DateTimeField(auto_now_add=True)

    class Meta: # type: ignore
        db_table = "favorite_image"
        verbose_name = "Favorite image"
        verbose_name_plural = "Favorite images"
