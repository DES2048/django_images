from django.urls import path
#from rest_framework.routers import DefaultRouter
from .views import (
	home, get_image, delete_image, GalleryListApiView, settings, images, mark_image,
)

urlpatterns = [
	path('', home),
    path('galleries/', GalleryListApiView.as_view()),
	path("galleries/<slug:gallery_slug>/images/", images, name="images"),
	path("galleries/<slug:gallery_slug>/images/<path:image_url>/mark", mark_image, {"mark":True}, name="mark-image"),
    path("galleries/<slug:gallery_slug>/images/<path:image_url>/unmark", mark_image, {"mark":False}, name="unmark-image"),
	path('get-image/<slug:gallery_slug>/<path:image_url>', get_image, name="get-image"),
	path('delete-image/<slug:gallery_slug>/<path:image_url>', delete_image, name="delete-image"),
	path('settings/', settings),
]

#router = DefaultRouter()
#router.register("galleries", GalleryViewSet, basename="gallery")
#urlpatterns += router.urls
