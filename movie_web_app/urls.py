from .views import ListCategoriesToDetect, ListGenres, ListPopularMoviesTmdb, MovieDetailTmdb, MovieDetailImdb, \
    MovieReviewsTmdb, ListFilteredMovies

urlpatterns = [
    path('categories_to_detect', ListCategoriesToDetect.as_view(), name='list_categories_to_detect'),
    path('genres', ListGenres.as_view(), name='list_genres'),
    path('tmdb/movies', ListFilteredMovies.as_view(), name='list_all_movies_tmdb'),
    path('tmdb/movies/<int:movie_id>', MovieDetailTmdb.as_view(), name='movie_detail_tmdb'),
    path('tmdb/movies/popular', ListPopularMoviesTmdb.as_view(), name='list_popular_movies_tmdb'),
    path('tmdb/movies/reviews/<int:movie_id>', MovieReviewsTmdb.as_view(), name='movie_reviews_tmdb'),

    path('imdb/movies/<str:movie_id>', MovieDetailImdb.as_view(), name='movie_detail_imdb'),
    path('img', ImgProcess.as_view(), name='get_trailer_img'),
    path('fill_database', FillDatabase.as_view(), name='fill_database'),

]
