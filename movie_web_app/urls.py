from django.urls import path
from .views import ListMovies, MovieDetail, MovieImages

urlpatterns = [
    path('movies/<int:movie_id>', MovieDetail.as_view(), name='movie_detail'),
    path('movies/searchTitle/<str:query>', ListMovies.as_view(), name='list_movies'),
    path('movies/images/<int:movie_id>', MovieImages.as_view(), name='movie_detail'),
]
