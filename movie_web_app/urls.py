from django.urls import path
from .views import ListMoviesTmdb, MovieDetailTmdb, MovieImagesTmdb, MovieDetailImdb, MovieImagesImdb, MoviePostersImdb

urlpatterns = [
    path('tmdb/movies/<int:movie_id>', MovieDetailTmdb.as_view(), name='movie_detail_tmdb'),
    path('tmdb/movies/searchTitle/<str:query>', ListMoviesTmdb.as_view(), name='list_movies_tmdb'),
    path('tmdb/movies/images/<int:movie_id>', MovieImagesTmdb.as_view(), name='movie_images_tmdb'),
    path('imdb/movies/<str:movie_id>', MovieDetailImdb.as_view(), name='movie_detail_imdb'),
    path('imdb/movies/images/<str:movie_id>', MovieImagesImdb.as_view(), name='movie_images_imdb'),
    path('imdb/movies/posters/<str:movie_id>', MoviePostersImdb.as_view(), name='movie_posters_imdb'),
]
