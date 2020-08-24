from django.urls import path
from .views import get_random_image_url, home, get_image, delete_image, GalleryListApiView, settings, images


urlpatterns = [
	path('', home),
	path("galleries/<slug:gallery_slug>/images/", images, name="images"),
	path('get-random-image-url/', get_random_image_url),
	path('get-image/<slug:gallery_slug>/<path:image_url>', get_image, name="get-image"),
	path('delete-image/<slug:gallery_slug>/<path:image_url>', delete_image),
	path('galleries/', GalleryListApiView.as_view()),
	path('settings/', settings),
]
