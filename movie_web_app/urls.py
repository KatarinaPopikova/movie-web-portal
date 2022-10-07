from django.urls import path
from . views import PosterView

urlpatterns = [
    path('posters/', PosterView.as_view(), name='posters_view')
]