import time

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from movie_web_app.helpers.filter import Filter
from movie_web_app.actions.fetch_movie_manager import FetchMovies
from movie_web_app.actions.movie_detection_manager import DetectMovies
from movie_web_app.actions.database_manager import DatabaseManager


class ListGenres(APIView):
    def get(self, request):
        genres = FetchMovies.get_genre_names(all_genres=True)
        return Response(genres)


class ListCategoriesToDetect(APIView):
    def get(self, request):
        categories = DetectMovies.find_labels()
        if len(categories) > 0:
            return Response(categories)
        else:
            return Response(data={'message': 'Can not load models for listing categories.'}, status=500)


class ListFilteredMovies(APIView):
    def get(self, request, format=None):
        movie_filter = Filter.parse_filters(request)
        results = {}

        if movie_filter.database:
            results["results"] = DatabaseManager.get_movies_from_db(movie_filter)
        else:
            results["results"] = FetchMovies.filter_movies(movie_filter)

        if results["results"] is None:
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        results["det_info"] = {
            "yolo": movie_filter.yolo,
            "categories": movie_filter.categories,
            "conf": movie_filter.confidence,
            "detType": movie_filter.detect_type,
        }

        return Response(results)


class ListPopularMoviesTmdb(APIView):
    def get(self, request):
        results = FetchMovies.get_popular_movies_tmdb()
        return Response(results)


class MovieDetailTmdb(APIView):

    def get(self, request, movie_id):
        results = FetchMovies.get_movie_detail_tmdb(movie_id)
        return Response(results)


class MovieReviewsTmdb(APIView):

    def get(self, request, movie_id):
        results = FetchMovies.get_movie_reviews_tmdb(movie_id, request.GET["page"])
        return Response(results)


class MovieDetailImdb(APIView):

    def get(self, request, movie_id):
        results = FetchMovies.get_movie_detail_imdb(movie_id)
        if results is None:
            return Response([], status=503)
        return Response(results)


class FillDatabase(APIView):
    def get(self, request):
        DatabaseManager.fill_empty_database()
        return Response()
