import copy
import json
import os
import time
from datetime import datetime

import requests
from pytube import YouTube

from rest_framework.response import Response
from rest_framework.views import APIView

from movie_web_app.helpers.filter import parse_filters

from yolov7.detect import detect_main, find_labels
from ultralytics import YOLO

API_KEY_TMDB = "987b17603795152ebf41085b5587a581"
TMDB_API = "https://api.themoviedb.org/3/"

API_KEY_IMDB = "k_m1fupd6t"
IMDB_API = "https://imdb-api.com/en/API/"

GENRES_CACHE = {}
GENRES_ID_CACHE = {}


def fetch_genres():
    print("Fetching genres.")
    response = requests.get(f'{TMDB_API}genre/movie/list?api_key={API_KEY_TMDB}')
    genres = response.json().get('genres')
    genre_name_to_id = {genre['name']: genre['id'] for genre in genres}
    GENRES_CACHE.update(genre_name_to_id)
    genre_id_to_name = {str(genre['id']): genre['name'] for genre in genres}
    GENRES_ID_CACHE.update(genre_id_to_name)


def get_genre_names(genre_ids):
    if not GENRES_ID_CACHE:
        fetch_genres()
    return [GENRES_ID_CACHE.get(str(genre_id)) for genre_id in genre_ids]


def get_genre_ids(genre_names):
    if not GENRES_CACHE:
        fetch_genres()
    try:
        return ', '.join(str(GENRES_CACHE[name]) for name in genre_names)
    except KeyError:
        return ""


class ListGenres(APIView):
    def get(self, request):
        fetch_genres()
        genres = list(GENRES_CACHE.keys())
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
        movie_filter = parse_filters(request)

        if movie_filter.database:
            pass  # TODO
        else:
            if movie_filter.movie_database == 'TMDB':
                return filter_movie_tmdb(movie_filter)

        # movies = Movie.objects.all()
        # serializer = MovieSerializer(movies, many=True)
        # return Response(serializer.data)


def filter_movie_tmdb(movie_filter):
    response = fetch_movie_tmdb(movie_filter)
    movies = response['credentials']['results']
    results = []
    if make_detection(movie_filter.categories):

        if movie_filter.detect_type == "Poster":
            links, movie_ids = create_array_from_posters_link(movies)
            if movie_filter.yolo == "YOLOv7":
                results = detect_main(links, movie_ids, movie_filter.categories, movie_filter.confidence)
            else:
                results = detect_yolov8(links, movie_ids, movie_filter.categories, movie_filter.confidence)
        else:
            movie_dict_with_links = create_movie_dict_with_trailer_link(movies)

            if movie_filter.yolo == "YOLOv8":
                results = make_trailer_detection(movie_dict_with_links, movie_filter.categories)

        response['credentials'] = json.loads(results)
    return Response(response)


def make_detection(categories):
    return len(categories) > 0


def fetch_movie_tmdb(movie_filter):
    print("Fetching tmdb.")
    if movie_filter.query != "":
        external_response = f'{TMDB_API}search/movie?api_key={API_KEY_TMDB}&query={movie_filter.query}/'
    else:
        external_response = f'{TMDB_API}discover/movie?api_key={API_KEY_TMDB}&with_genres={get_genre_ids(movie_filter.genres)}' \
                            f'&release_date.gte={movie_filter.date_from_str}' \
                            f'&release_date.lte={movie_filter.date_to_str}'
    response = call_api_multiple_times(external_response, movie_filter.max_pages)
    if movie_filter.query != "" and (len(movie_filter.genres) > 0 or movie_filter.date_to or movie_filter.date_to):
        response["credentials"]["results"] = [
            movie for movie in response["credentials"]["results"]
            if all(genre_id in movie.get("genre_ids") for genre_id in movie_filter.genres) and
               movie_filter.date_from <= datetime.strptime(movie.get("release_date"),
                                                           "%Y-%m-%d").date() <= movie_filter.date_to
        ]

    print("Fetching finished.")
    return response


class ListPopularMoviesTmdb(APIView):
    def get(self, request):
        external_response = requests.get(f'{TMDB_API}movie/popular?api_key={API_KEY_TMDB}')
        return manage_with_external_response(external_response)


class ListMoviesWithTitleTmdb(APIView):
    def get(self, request):
        external_response = requests.get(f'{TMDB_API}search/movie?api_key={API_KEY_TMDB}&query={request.GET["query"]}/')
        return manage_with_external_response(external_response)


class ListMoviesTmdb(APIView):
    def get(self, request):
        external_response = f'{TMDB_API}discover/movie?api_key={API_KEY_TMDB}&with_genres={request.GET["genres"]}&release_date.gte={request.GET["date_from"]}&release_date.lte={request.GET["date_to"]}'
        print(external_response)
        response = call_api_multiple_times(external_response)
        response["credentials"]["results"] = [movie for movie in response["credentials"]["results"] if
                                              movie.get('title').lower().find(request.GET["query"].lower()) != -1]
        return Response(response)


def detect_yolov8(posters_links, movie_ids, categories, confidence):
    print("Start detection on posters yolov8.")
    model = YOLO()
    #
    results = model.predict(source=posters_links, conf=confidence, device=0)
    names = results[0].names
    detection = {"results": []}

    for index, result in enumerate(results):
        current_img = {
            "poster_path": posters_links[index],
            "id": movie_ids[index],
            "det": []
        }
        if result is not None:
            must_detect_categories = copy.deepcopy(categories)

            for box in reversed(result.boxes):
                xywh = box.xywhn.squeeze()
                cls = box.cls.squeeze()
                conf = box.conf.squeeze()
                if names[int(cls)] in categories:
                    if names[int(cls)] in must_detect_categories:
                        must_detect_categories.remove(names[int(cls)])

                    current_img["det"].append({
                        "label": names[int(cls)],
                        "box": xywh.tolist(),
                        "conf": float(conf)
                    })

            if len(must_detect_categories) == 0:
                detection["results"].append(current_img)

    detection["results"] = sorted(detection['results'], key=lambda x: (max(image_det['conf'] for image_det in
                                                                           x['det'])), reverse=True)
    json_object = json.dumps(detection, indent=4)

    print("Detection finished.")

    return json_object


def make_trailer_detection(movie_dict_with_links, categories):
    print("Start detection on trailers yolov8.")

    movie_with_searching_objects = {"results": []}

    model = YOLO()
    for movie_result in movie_dict_with_links:
        youtube_object = YouTube(movie_result['link'])
        youtube_object = youtube_object.streams.get_highest_resolution()
        try:
            youtube_object.download(output_path='trailers', filename=str(movie_result['id']) + '.mp4')
        except:
            print("An error has occurred: " + str(movie_result['id']))

        print("Download is completed successfully")

        source = 'trailers/' + str(movie_result['id']) + '.mp4'
        results = model.predict(source=source, device=0, vid_stride=5, verbose=False, imgsz=192)

        os.remove(source)

        all_objects = get_all_objects_with_best_conf(results)

        objects = contains_all_searching_objects(all_objects, categories)

        movie_result["objects"] = objects

        if objects:
            movie_with_searching_objects["results"].append(movie_result)

    print("Detection finished.")

    return json.dumps(movie_with_searching_objects, indent=4)


def get_all_objects_with_best_conf(results):
    print("Getting all objects and their conf from trailers.")
    names = results[0].names
    name_to_conf = {}

    for result in results:
        if result is not None:
            for box in result.boxes:
                name = names[int(box.cls)]
                conf = float(box.conf)
                if name not in name_to_conf or conf > name_to_conf[name]:
                    name_to_conf[name] = conf

    return [{'object': name, 'conf': conf} for name, conf in name_to_conf.items()]


def contains_all_searching_objects(objects_in_video, categories):
    searching_categories = list(filter(lambda obj: obj['object'] in categories, objects_in_video))
    return searching_categories if len(searching_categories) == len(categories) else None


class MovieDetailTmdb(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(
            f'{TMDB_API}movie/{movie_id}?api_key={API_KEY_TMDB}&append_to_response=credits')
        return manage_with_external_response(external_response)


class MovieImagesTmdb(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(f'{TMDB_API}movie/{movie_id}/images?api_key={API_KEY_TMDB}')
        return manage_with_external_response(external_response)


class MovieReviewsTmdb(APIView):

    def get(self, request, movie_id):
        external_response = requests.get(
            f'{TMDB_API}movie/{movie_id}/reviews?api_key={API_KEY_TMDB}&page={request.GET["page"]}')
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


def call_api_multiple_times(external_request, max_pages=1):
    response = {}
    data = {}
    total_pages = 1
    actual_page = 1

    while actual_page <= total_pages and actual_page <= max_pages:
        external_response = requests.get(f'{external_request}&page={actual_page}')
        external_response_status = external_response.status_code

        if actual_page == 1:
            total_pages = external_response.json().get('total_pages', 0) + 1
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
        actual_page += 1

    response['credentials']['results'] = (*data, *response['credentials']['results'])
    return response


def create_array_from_posters_link(data):
    start_path = 'https://image.tmdb.org/t/p/w300'
    posters_links = []
    movie_ids = []
    for movie in data:
        if movie["poster_path"] is not None:
            posters_links.append(start_path + movie["poster_path"])
            movie_ids.append(movie['id'])
    return posters_links, movie_ids


def create_movie_dict_with_trailer_link(movies):
    print("Start fetching trailer links")
    start_path = 'https://youtu.be/'
    movie_with_trailer_list = []

    for movie in movies:
        if len(movie_with_trailer_list) > 2:
            break
        video_response = requests.get(
            f'https://api.themoviedb.org/3/movie/{movie["id"]}/videos?api_key={API_KEY_TMDB}')

        trailer_video = None
        for video in video_response.json().get("results", []):
            if video.get("name") == "Official Trailer" and video.get("site") == "YouTube":
                trailer_video = video
                break
            elif video.get("official") == "true" and not trailer_video:
                trailer_video = video
            elif not trailer_video:
                trailer_video = video

        if trailer_video:
            movie_with_trailer_list.append({
                "id": movie["id"],
                "title": movie["title"],
                "poster_path": movie["poster_path"],
                "release_date": movie["release_date"],
                "popularity": movie["popularity"],
                "genres": get_genre_names(movie["genre_ids"]),
                "link": start_path + trailer_video["key"]
            })

    return movie_with_trailer_list

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
