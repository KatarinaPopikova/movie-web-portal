import json

import requests

from rest_framework.response import Response
from rest_framework.views import APIView

from yolov7.detect import detect_main, find_labels

API_KEY_TMDB = "987b17603795152ebf41085b5587a581"
TMDB_API = "https://api.themoviedb.org/3/"

API_KEY_IMDB = "k_m1fupd6t"
IMDB_API = "https://imdb-api.com/en/API/"


class ListCategoriesToDetect(APIView):
    def get(self, request):
        categories = find_labels()

        response = {'credentials': categories}
        if len(categories) > 0:
            response['status'] = 200
            response['message'] = 'success'
        else:
            response['status'] = 300
            response['message'] = 'error'

        return Response(response)


class ListPopularMoviesTmdb(APIView):
    def get(self, request):
        external_response = requests.get(f'{TMDB_API}movie/popular?api_key={API_KEY_TMDB}')
        return manage_with_external_response(external_response)


class ListMoviesTmdb(APIView):
    def get(self, request):
        external_response = requests.get(f'{TMDB_API}search/movie?api_key={API_KEY_TMDB}&query={request.GET["query"]}/')
        return manage_with_external_response(external_response)


class PosterListMoviesTmdb(APIView):
    def get(self, request):
        if request.GET["query"] != "":
            external_request = f'{TMDB_API}search/movie?api_key={API_KEY_TMDB}&query={request.GET["query"]}/'
        else:
            external_request = f'{TMDB_API}discover/movie?api_key={API_KEY_TMDB}&with_genres={request.GET["genres"]}'
            f'&primary_release_date.gte={request.GET["date_from"]}&primary_release_date.lte={request.GET["date_to"]}'

        return call_api_multiple_times(external_request, request.GET["categories"])

class TrailerListMoviesTmdb(APIView):
    def get(self, request):
        external_request = f'{TMDB_API}discover/movie?api_key={API_KEY_TMDB}&query={request.GET["query"]}&with_genres={request.GET["genres"]}'
        f'&primary_release_date.gte={request.GET["date_from"]}&primary_release_date.lte={request.GET["date_to"]}'
        print("in Trailer")
        return get_trailer_link_list(external_request)


def get_trailer_link_list(external_request):
    response = {}
    data = {}

    for page in range(6):
        external_response = requests.get(f'{external_request}&page={page}')
        external_response_status = external_response.status_code

        if page == 1:
            response['status'] = external_response_status
            if external_response_status == 200:
                response['credentials'] = external_response.json()
                response['message'] = 'success'
            else:
                response['message'] = 'error'
                break
        else:
            if external_response_status == 200:
                data = (*data, *external_response.json()['results'])

    response['credentials']['results'] = (*data, *response['credentials']['results'])
    movie_ids = [movie['id'] for movie in response['credentials']['results']]
    response['credentials']['results'] = create_array_from_trailer_link(movie_ids)
    return Response(response)

def create_array_from_trailer_link(movie_ids):
    start_path = 'https://youtu.be/'
    trailer_dict = {}
    for movie_id in movie_ids:
        video_response = requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={API_KEY_TMDB}')
        print(video_response.json()["results"])
        trailer_list = {}
        for video in video_response.json()["results"]:
            if video["site"] == "YouTube":
                trailer_list.setdefault("link",start_path + video["key"])
        if len(trailer_list) > 0:
            #tie iste id mi prepisuje
            trailer_dict["id"] = movie_id
            trailer_dict["trailer"] = trailer_list

    return trailer_dict


class MovieDetailTmdb(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(f'{TMDB_API}movie/{movie_id}?api_key={API_KEY_TMDB}&append_to_response=credits')
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


def call_api_multiple_times(external_request, categories):
    response = {}
    data = {}

    for page in range(1, 21):
        external_response = requests.get(f'{external_request}&page={page}')
        external_response_status = external_response.status_code

        if page == 1:
            response['status'] = external_response_status
            if external_response_status == 200:
                response['credentials'] = external_response.json()
                response['message'] = 'success'
            else:
                response['message'] = 'error'
                break
        else:
            if external_response_status == 200:
                data = (*data, *external_response.json()['results'])

    response['credentials']['results'] = (*data, *response['credentials']['results'])
    posters_links, movie_ids = create_array_from_posters_link(response['credentials']['results'])
    results = detect_main(posters_links, movie_ids, categories.split(','))
    response['credentials'] = json.loads(results)
    return Response(response)


def create_array_from_posters_link(data):
    start_path = 'https://image.tmdb.org/t/p/w300'
    posters_links = []
    movie_ids = []
    for movie in data:
        if movie["poster_path"] is not None:
            posters_links.append(start_path + movie["poster_path"])
            movie_ids.append(movie['id'])
    return posters_links, movie_ids


def save_to_txt(data):
    posters_link = create_array_from_posters_link(data)

    with open('posters.txt', 'w') as f:
        f.write('\n'.join(posters_link))
