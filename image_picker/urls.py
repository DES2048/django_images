from django.urls import path
#from rest_framework.routers import DefaultRouter
from .views import (
	home, get_image, delete_image, rename_image, copy_move_image, settings, images, mark_image, pin_unpin_gallery,
    FavoriteImageListCreateApiView, GalleryListApiView
)

urlpatterns = [
	path('', home),
    path('galleries/', GalleryListApiView.as_view(), name="galleries-list"), # type: ignore
    path('galleries/<slug:gallery_slug>/pin', pin_unpin_gallery, name="pin-gallery"),
    path('galleries/<slug:gallery_slug>/unpin', pin_unpin_gallery, {"pin": False}, name="unpin-gallery"),
	path("galleries/<slug:gallery_slug>/images/", images, name="images"),
    path("galleries/<slug:gallery_slug>/images/rename", rename_image, name="rename-image"),
    path("galleries/<slug:gallery_slug>/images/copy-move", copy_move_image, name="copy-move-image"),
	path("galleries/<slug:gallery_slug>/images/<path:image_url>/mark", mark_image, {"mark":True}, name="mark-image"),
    path("galleries/<slug:gallery_slug>/images/<path:image_url>/unmark", mark_image, {"mark":False}, name="unmark-image"),
	path('get-image/<slug:gallery_slug>/<path:image_url>', get_image, name="get-image"),
	path('delete-image/<slug:gallery_slug>/<path:image_url>', delete_image, name="delete-image"),
    path('fav-images/', FavoriteImageListCreateApiView.as_view(), name="fav-images"), # type: ignore
	path('settings/', settings),
]

#router = DefaultRouter()
#router.register("galleries", GalleryViewSet, basename="gallery")
#urlpatterns += router.urls
