import json
import requests
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt

API_KEY = "987b17603795152ebf41085b5587a581"
EXTERNAL_API = "https://api.themoviedb.org/3/"


class ListMovies(APIView):
    def get(self, request, query):
        external_response = requests.get(f'{EXTERNAL_API}search/movie?api_key={API_KEY}&query={query}/')
        return manage_with_external_response(external_response)


class MovieDetail(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(f'{EXTERNAL_API}movie/{movie_id}?api_key={API_KEY}')
        return manage_with_external_response(external_response)


class MovieImages(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(f'{EXTERNAL_API}movie/{movie_id}/images?api_key={API_KEY}')
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
