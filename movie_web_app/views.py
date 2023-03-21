import copy
import json
import os
import time
import requests

from rest_framework.response import Response
from rest_framework.views import APIView

from yolov7.detect import detect_main, find_labels
from ultralytics import YOLO

from pytube import YouTube

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
            response['status'] = 500
            response['message'] = 'error'

        return Response(response)


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


def detect_yolov8(posters_links, movie_ids, categories, confidence, yolov7_det):
    model = YOLO()
    #
    results = model.predict(source=posters_links)
    names = results[0].names
    detection = {"results": []}

    add_detection = {}
    for index, result in enumerate(results):
        current_img = {
            "poster_path": posters_links[index],
            "id": movie_ids[index],
            "det": []
        }
        print(movie_ids[index])
        add_detection[str(movie_ids[index])] = current_img
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

    for det in yolov7_det["results"]:
        det["yolov8"] = add_detection[str(det["id"])]["det"]

    json_object = json.dumps(yolov7_det, indent=4)
    print(json_object)

    return json_object


class PosterListMoviesTmdb(APIView):
    def get(self, request):

        if request.GET["query"] != "":
            external_response = f'{TMDB_API}search/movie?api_key={API_KEY_TMDB}&query={request.GET["query"]}/'
        else:
            external_response = f'{TMDB_API}discover/movie?api_key={API_KEY_TMDB}&with_genres={request.GET["genres"]}' \
                                f'&primary_release_date.gte={request.GET["date_from"]}' \
                                f'&primary_release_date.lte={request.GET["date_to"]}'
        response = call_api_multiple_times(external_response)
        posters_links, movie_ids = create_array_from_posters_link(response['credentials']['results'])
        confidence = float(request.GET["confidence"]) / 100
        categories = request.GET["categories"].split(',')

        results = detect_main(posters_links, movie_ids, request.GET["categories"].split(','), confidence)
        results = detect_yolov8(posters_links, movie_ids, categories, confidence, json.loads(results))

        response['credentials'] = json.loads(results)
        return Response(response)


class TrailerListMoviesTmdb(APIView):
    def get(self, request):
        external_request = f'{TMDB_API}discover/movie?api_key={API_KEY_TMDB}&query={request.GET["query"]}&with_genres={request.GET["genres"]}'
        f'&primary_release_date.gte={request.GET["date_from"]}&primary_release_date.lte={request.GET["date_to"]}'
        response = call_api_multiple_times(external_request)
        movie_ids = [movie['id'] for movie in response['credentials']['results']]
        trailers_links = response['credentials']['results'] = create_array_from_trailer_link(movie_ids)

        model = YOLO()


        tic = time.perf_counter()
        # results = model.predict(source=trailers_links[0]['link'], device="cpu", verbose=False, imgsz=192)
        toc = time.perf_counter()
        tic2 = time.perf_counter()

        for i in range(3):
            youtubeObject = YouTube(trailers_links[i]['link'])
            youtubeObject = youtubeObject.streams.get_highest_resolution()
            try:
                youtubeObject.download(output_path='trailers', filename=str(trailers_links[i]['id']) + '.mp4')
            except:
                print("An error has occurred: " + str(trailers_links[i]['id']))
            print("Download is completed successfully")

            source = 'trailers/'+str(trailers_links[i]['id'])+'.mp4'
            results = model.predict(source=source, device=0, vid_stride=5, show=True, verbose=False, imgsz=192)
            toc2 = time.perf_counter()

            print(f"Results in {toc - tic:0.4f} seconds")
            print(f"2: Results in {toc2 - tic2:0.4f} seconds")

            names = results[0].names
            objectsInVideo = list(
                set([names[int(box.cls)]
                     for result in results if result is not None
                     for box in result.boxes]))

            print(objectsInVideo)

            os.remove(source)

        return Response(response)


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


def create_array_from_trailer_link(movie_ids):
    start_path = 'https://youtu.be/'
    trailer_list = []

    for movie_id in movie_ids:
        video_response = requests.get(
            f'https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={API_KEY_TMDB}')
        videos = [video for video in video_response.json().get("results", []) if video.get("site") == "YouTube"]

        if not videos:
            continue

        trailer_video = None
        for video in videos:
            if video.get("name") == "Official Trailer":
                trailer_video = video
                break
            elif video.get("official") == "true" and not trailer_video:
                trailer_video = video
            elif not trailer_video:
                trailer_video = video

        trailer_list.append({
            "id": movie_id,
            "link": start_path + trailer_video["key"]
        })

    return trailer_list
