import json
import requests

from rest_framework.response import Response
from rest_framework.views import APIView

from movie_web_app.helpers.filter import Filter
from movie_web_app.actions.fetching_movies import FetchingMovies
from movie_web_app.actions.detect_movies import DetectMovies

from yolov7.detect import detect_main, find_labels


import movie_web_app.helpers.keys as keys


class ListGenres(APIView):
    def get(self, request):
        genres = FetchingMovies.get_genre_names(all_genres=True)
        return Response(genres)


class ListCategoriesToDetect(APIView):
    def get(self, request):
        categories = find_labels()

        response = {'credentials': categories}
        if len(categories) > 0:
            response['status'] = 200
            response['message'] = 'success'
        else:
            response['status'] = 500
            response['message'] = 'error'

        return Response(response)


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
    response = FetchingMovies.fetch_movie_tmdb(movie_filter)
    movies = response['credentials']['results']
    results = []
    detect_movies = DetectMovies()
    if detect_movies.make_detection(movie_filter.categories):

        if movie_filter.detect_type == "Poster":
            links, movie_ids = FetchingMovies.create_array_from_posters_link(movies)
            if movie_filter.yolo == "YOLOv7":
                results = detect_main(links, movie_ids, movie_filter.categories, movie_filter.confidence)
            else:
                results = detect_movies.detect_yolov8(links, movie_ids, movie_filter.categories, movie_filter.confidence)
        else:
            movie_dict_with_links = FetchingMovies.create_movie_dict_with_trailer_link(movies)

            if movie_filter.yolo == "YOLOv8":
                results = detect_movies.make_trailer_detection(movie_dict_with_links, movie_filter.categories)

        response['credentials'] = json.loads(results)
    return Response(response)


class ListPopularMoviesTmdb(APIView):
    def get(self, request):
        external_response = requests.get(f'{keys.TMDB_API}movie/popular?api_key={keys.API_KEY_TMDB}')
        return Response(FetchingMovies.manage_with_external_response(external_response))


class ListMoviesWithTitleTmdb(APIView):
    def get(self, request):
        external_response = requests.get(f'{keys.TMDB_API}search/movie?api_key={keys.API_KEY_TMDB}&query={request.GET["query"]}/')
        return Response(FetchingMovies.manage_with_external_response(external_response))


class ListMoviesTmdb(APIView):
    def get(self, request):
        external_response = f'{keys.TMDB_API}discover/movie?api_key={keys.API_KEY_TMDB}&with_genres={request.GET["genres"]}&release_date.gte={request.GET["date_from"]}&release_date.lte={request.GET["date_to"]}'
        print(external_response)
        response = FetchingMovies.call_api_multiple_times(external_response)
        response["credentials"]["results"] = [movie for movie in response["credentials"]["results"] if
                                              movie.get('title').lower().find(request.GET["query"].lower()) != -1]
        return Response(response)


class MovieDetailTmdb(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(
            f'{keys.TMDB_API}movie/{movie_id}?api_key={keys.API_KEY_TMDB}&append_to_response=credits')
        return Response(FetchingMovies.manage_with_external_response(external_response))


class MovieImagesTmdb(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(f'{keys.TMDB_API}movie/{movie_id}/images?api_key={keys.API_KEY_TMDB}')
        return Response(FetchingMovies.manage_with_external_response(external_response))


class MovieReviewsTmdb(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(
            f'{keys.TMDB_API}movie/{movie_id}/reviews?api_key={keys.API_KEY_TMDB}&page={request.GET["page"]}')
        return Response(FetchingMovies.manage_with_external_response(external_response))


class MovieDetailImdb(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(f'{keys.IMDB_API}Title/{keys.API_KEY_IMDB}/{movie_id}/FullActor,Posters')
        return Response(FetchingMovies.manage_with_external_response(external_response))


class MovieImagesImdb(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(f'{keys.IMDB_API}Images/{keys.API_KEY_IMDB}/{movie_id}/')
        print(external_response.json())

        return Response(FetchingMovies.manage_with_external_response(external_response))


class MoviePostersImdb(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(f'{keys.IMDB_API}Posters/{keys.API_KEY_IMDB}/{movie_id}/')
        print(external_response.json())
        return Response(FetchingMovies.manage_with_external_response(external_response))

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
