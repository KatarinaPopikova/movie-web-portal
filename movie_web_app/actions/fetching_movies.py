from datetime import datetime
import requests
from ..helpers import keys


class FetchingMovies:
    genres_id_cache = {}
    genres_cache = {}

    @classmethod
    def fetch_genres(cls):
        print("Fetching genres.")
        response = requests.get(f'{keys.TMDB_API}genre/movie/list?api_key={keys.API_KEY_TMDB}')
        return response.json().get('genres')

    @classmethod
    def get_genre_names(cls, genre_ids=None, all_genres=False):
        if not cls.genres_id_cache:
            genres = cls.fetch_genres()
            cls.genres_id_cache = {str(genre['id']): genre['name'] for genre in genres}

        if all_genres:
            return list(cls.genres_id_cache.values())

        return [cls.genres_id_cache.get(str(genre_id)) for genre_id in genre_ids]

    @classmethod
    def get_genre_ids(cls, genre_names):
        if not cls.genres_cache:
            genres = cls.fetch_genres()
            cls.genres_cache = {genre['name']: genre['id'] for genre in genres}
        return ', '.join(str(cls.genres_cache[name]) for name in genre_names)

    @classmethod
    def fetch_movie_tmdb(cls, movie_filter):
        print("Fetching tmdb.")
        if movie_filter.query != "":
            external_response = f'{keys.TMDB_API}search/movie?api_key={keys.API_KEY_TMDB}&query={movie_filter.query}/'
        else:
            external_response = f'{keys.TMDB_API}discover/movie?api_key={keys.API_KEY_TMDB}&with_genres={cls.get_genre_ids(movie_filter.genres)}' \
                                f'&release_date.gte={movie_filter.date_from_str}&release_date.lte={movie_filter.date_to_str}'
        response = cls.call_api_multiple_times(external_response, movie_filter.max_pages)
        if movie_filter.query != "" and (len(movie_filter.genres) > 0 or movie_filter.date_to or movie_filter.date_to):
            movies = response["credentials"]["results"]
            if movie_filter.genres:
                movies = [movie for movie in movies if
                          all(genre in cls.get_genre_names(movie.get("genre_ids", [])) for genre in
                              movie_filter.genres)]
            if movie_filter.date_from:
                movies = [movie for movie in movies if
                          movie.get("release_date") and datetime.strptime(movie.get("release_date"),
                                                                          "%Y-%m-%d").date() >= movie_filter.date_from]
            if movie_filter.date_to:
                movies = [movie for movie in movies if
                          movie.get("release_date") and datetime.strptime(movie.get("release_date"),
                                                                          "%Y-%m-%d").date() <= movie_filter.date_to]

            response["credentials"]["results"] = movies

        print("Fetching finished.")
        return response

    @classmethod
    def manage_with_external_response(cls, external_response):
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

        return response

    @classmethod
    def call_api_multiple_times(cls, external_request, max_pages=1):
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

    @classmethod
    def create_array_from_posters_link(cls, data):
        start_path = 'https://image.tmdb.org/t/p/w300'
        posters_links = []
        movie_ids = []
        for movie in data:
            if movie["poster_path"] is not None:
                posters_links.append(start_path + movie["poster_path"])
                movie_ids.append(movie['id'])
        return posters_links, movie_ids

    @classmethod
    def create_movie_dict_with_trailer_link(cls, movies):
        print("Start fetching trailer links")
        start_path = 'https://youtu.be/'
        movie_with_trailer_list = []

        for movie in movies:
            if len(movie_with_trailer_list) > 2:
                break
            video_response = requests.get(
                f'https://api.themoviedb.org/3/movie/{movie["id"]}/videos?api_key={keys.API_KEY_TMDB}')

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
                    "genres": cls.get_genre_names(movie["genre_ids"]),
                    "trailer_link": start_path + trailer_video["key"],
                    "objects": []
                })

        return movie_with_trailer_list

    @classmethod
    def get_popular_movies_tmdb(cls):
        external_response = requests.get(f'{keys.TMDB_API}movie/popular?api_key={keys.API_KEY_TMDB}')
        return cls.manage_with_external_response(external_response)

    @classmethod
    def get_movie_detail_tmdb(cls, movie_id):
        external_response = requests.get(
            f'{keys.TMDB_API}movie/{movie_id}?api_key={keys.API_KEY_TMDB}&append_to_response=credits')
        return cls.manage_with_external_response(external_response)

    @classmethod
    def get_movie_reviews_tmdb(cls, movie_id, page):
        external_response = requests.get(
            f'{keys.TMDB_API}movie/{movie_id}/reviews?api_key={keys.API_KEY_TMDB}&page={page}')
        return cls.manage_with_external_response(external_response)

    @classmethod
    def get_movie_detail_imdb(cls, movie_id):
        external_response = requests.get(f'{keys.IMDB_API}Title/{keys.API_KEY_IMDB}/{movie_id}/FullActor,Posters')
        return cls.manage_with_external_response(external_response)

