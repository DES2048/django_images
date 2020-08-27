from django.urls import path
from .views import home, get_image, delete_image, GalleryListApiView, settings, images, mark_image


urlpatterns = [
	path('', home),
  path('galleries/', GalleryListApiView.as_view()),
	path("galleries/<slug:gallery_slug>/images/", images, name="images"),
	path("galleries/<slug:gallery_slug>/images/<path:image_url>/mark", mark_image, name="mark-image"),
	path('get-image/<slug:gallery_slug>/<path:image_url>', get_image, name="get-image"),
	path('delete-image/<slug:gallery_slug>/<path:image_url>', delete_image),
	path('settings/', settings),
]
