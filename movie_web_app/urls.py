
from django.urls import path
from .views import ListCategoriesToDetect, ListGenres, ListPopularMoviesTmdb, ListMoviesWithTitleTmdb, ListMoviesTmdb, MovieDetailTmdb, MovieImagesTmdb, \
    MovieDetailImdb,  MovieImagesImdb, MoviePostersImdb, MovieReviewsTmdb, ListFilteredMovies

urlpatterns = [
    path('categories_to_detect', ListCategoriesToDetect.as_view(), name='list_categories_to_detect'),
    path('genres', ListGenres.as_view(), name='list_genres'),
    path('tmdb/movies', ListFilteredMovies.as_view(), name='list_all_movies_tmdb'),
    path('tmdb/movies/<int:movie_id>', MovieDetailTmdb.as_view(), name='movie_detail_tmdb'),
    path('tmdb/movies/popular', ListPopularMoviesTmdb.as_view(), name='list_popular_movies_tmdb'),
    path('tmdb/movies/searchMoviesWithTitle', ListMoviesWithTitleTmdb.as_view(), name='list_movies_with_title_tmdb'),
    path('tmdb/movies/searchMovies', ListMoviesTmdb.as_view(), name='list_movies_tmdb'),
    path('tmdb/movies/images/<int:movie_id>', MovieImagesTmdb.as_view(), name='movie_images_tmdb'),
    path('tmdb/movies/reviews/<int:movie_id>', MovieReviewsTmdb.as_view(), name='movie_reviews_tmdb'),

    path('imdb/movies/<str:movie_id>', MovieDetailImdb.as_view(), name='movie_detail_imdb'),
    path('imdb/movies/images/<str:movie_id>', MovieImagesImdb.as_view(), name='movie_images_imdb'),
    path('imdb/movies/posters/<str:movie_id>', MoviePostersImdb.as_view(), name='movie_posters_imdb'),


]
