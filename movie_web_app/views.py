import requests

from rest_framework.response import Response
from rest_framework.views import APIView

API_KEY_TMDB = "987b17603795152ebf41085b5587a581"
TMDB_API = "https://api.themoviedb.org/3/"

API_KEY_IMDB = "k_m1fupd6t"
IMDB_API = "https://imdb-api.com/en/API/"


class ListMoviesTmdb(APIView):
    def get(self, request):
        external_response = requests.get(f'{TMDB_API}search/movie?api_key={API_KEY_TMDB}&query={request.GET["query"]}/')
        return manage_with_external_response(external_response)


class PosterListMoviesTmdb(APIView):
    def get(self, request):
        external_response = requests.get(
            f'{TMDB_API}discover/movie?api_key={API_KEY_TMDB}&query={request.GET["query"]}&with_genres={request.GET["genres"]}'
            f'&primary_release_date.gte={request.GET["date_from"]}&primary_release_date.lte={request.GET["date_to"]}&page=1')
        for page in range(2,5):
            external_response = requests.get(
                f'{TMDB_API}discover/movie?api_key={API_KEY_TMDB}&query={request.GET["query"]}&with_genres={request.GET["genres"]}'
                f'&primary_release_date.gte={request.GET["date_from"]}&primary_release_date.lte={request.GET["date_to"]}&page={page}')
        print(external_response)
        return manage_with_external_response(external_response)


class MovieDetailTmdb(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(f'{TMDB_API}movie/{movie_id}?api_key={API_KEY_TMDB}')
        return manage_with_external_response(external_response)


class MovieImagesTmdb(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(f'{TMDB_API}movie/{movie_id}/images?api_key={API_KEY_TMDB}')
        return manage_with_external_response(external_response)


class MovieDetailImdb(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(f'{IMDB_API}Title/{API_KEY_IMDB}/{movie_id}/FullActor,Posters')
        return manage_with_external_response(external_response)


class MovieImagesImdb(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(f'{IMDB_API}Images/{API_KEY_IMDB}/{movie_id}/')
        print(external_response.json())

        return manage_with_external_response(external_response)


class MoviePostersImdb(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(f'{IMDB_API}Posters/{API_KEY_IMDB}/{movie_id}/')
        print(external_response.json())
        return manage_with_external_response(external_response)


def manage_with_external_response(external_response):
    response = {}
    external_response_status = external_response.status_code
    response['status'] = external_response_status

    if external_response_status == 200:
        data = external_response.json()
        response['message'] = 'success'
        response['credentials'] = data
    else:
        response['message'] = 'error'
        response['credentials'] = {}

    return Response(response)
