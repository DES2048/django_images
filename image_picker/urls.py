from django.urls import path
from .views import get_random_image_url, home, get_image, delete_image, GalleryListApiView, settings


urlpatterns = [
	path('', home),
	path('get-random-image-url/', get_random_image_url),
	path('get-image/<path:url>', get_image),
	path('delete-image/<str:url>/', delete_image),
	path('galleries/', GalleryListApiView.as_view()),
	path('settings/', settings),
]
