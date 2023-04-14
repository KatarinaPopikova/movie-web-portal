import json

from rest_framework.response import Response
from rest_framework.views import APIView

from movie_web_app.helpers.filter import Filter
from movie_web_app.actions.fetching_movies import FetchingMovies
from movie_web_app.actions.detect_movies import DetectMovies


class ListGenres(APIView):
    def get(self, request):
        genres = FetchingMovies.get_genre_names(all_genres=True)
        return Response(genres)


class ListCategoriesToDetect(APIView):
    def get(self, request):
        categories = DetectMovies.find_labels()
        print(categories)
        if len(categories) > 0:
            return Response(categories)
        else:
            return Response(data={'message': 'Can not load models for listing categories.'}, status=500)


class ListFilteredMovies(APIView):
    def get(self, request, format=None):
        movie_filter = Filter.parse_filters(request)

        if movie_filter.database:
            pass  # TODO
        else:
            if movie_filter.movie_database == 'TMDB':
                return filter_movie_tmdb(movie_filter)

        # movies = Movie.objects.all()
        # serializer = MovieSerializer(movies, many=True)
        # return Response(serializer.data)


def filter_movie_tmdb(movie_filter):
    movies = FetchingMovies.fetch_movie_tmdb(movie_filter)
    results = []
    detect_movies = DetectMovies()
    if detect_movies.make_detection(movie_filter.categories):

        if movie_filter.detect_type == "Poster":
            links, movie_ids = FetchingMovies.create_array_from_posters_link(movies)
            if movie_filter.yolo == "YOLOv7":
                results = detect_movies.detect_yolov7(links, movie_ids, movie_filter.categories,
                                                      movie_filter.confidence)
            else:
                results = detect_movies.detect_yolov8(links, movie_ids, movie_filter.categories,
                                                      movie_filter.confidence)
        else:
            movie_dict_with_links = FetchingMovies.create_movie_dict_with_trailer_link(movies)

            if movie_filter.yolo == "YOLOv8":
                results = detect_movies.make_trailer_detection(movie_dict_with_links, movie_filter.categories)
    else:
        results = movies

    return Response(results)


class ListPopularMoviesTmdb(APIView):
    def get(self, request):
        results = FetchingMovies.get_popular_movies_tmdb()
        return Response(results)


class MovieDetailTmdb(APIView):

    def get(self, request, movie_id):
        results = FetchingMovies.get_movie_detail_tmdb(movie_id)
        return Response(results)


class MovieReviewsTmdb(APIView):

    def get(self, request, movie_id):
        results = FetchingMovies.get_movie_reviews_tmdb(movie_id, request.GET["page"])
        return Response(results)


class MovieDetailImdb(APIView):

    def get(self, request, movie_id):
        results = FetchingMovies.get_movie_detail_imdb(movie_id)
        return Response(results)
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
#
#
# @api_view(['POST'])
# def my_api_view(request):
#     serializer = SearchFilterSerializer(data=request.data)
#     serializer.is_valid(raise_exception=True)
#
#     # Access validated data as a Python dictionary
#     search_filter = serializer.validated_data['searchFilter']
#     categories = search_filter['categories']
#     database = search_filter['database']
#     # etc.
#
#     # Process the search filter and return a response
#     # ...
#     return Response({'success': True})
