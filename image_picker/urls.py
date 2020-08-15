from django.urls import path
from .views import get_random, home, get_image


urlpatterns = [
	path('', home),
	path('get-random-image-url/', get_random),
	path('get-image/<str:url>/', get_image),
]