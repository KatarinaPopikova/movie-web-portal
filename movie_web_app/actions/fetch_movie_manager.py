from datetime import datetime
import requests

from .movie_detection_manager import DetectMovies
from ..helpers import keys


class FetchMovies:
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
    def filter_movies(cls, movie_filter):
        if movie_filter.movie_database == 'TMDB':
            return cls.filter_movie_tmdb(movie_filter)
        elif movie_filter.movie_database == 'IMDB':
            return cls.filter_movie_imdb(movie_filter)

    @classmethod
    def filter_movie_tmdb(cls, movie_filter):
        movies = cls.fetch_movies_tmdb_with_filter(movie_filter)
        results = []
        if len(movies) == 0:
            return results
        detect_movies = DetectMovies()
        if detect_movies.make_detection(movie_filter.categories):
            if movie_filter.detect_type == "Poster":
                links, movies = cls.get_poster_links_with_movies(movies, 'https://image.tmdb.org/t/p/w400')
                if movie_filter.yolo == "yolov7":
                    results = detect_movies.detect_yolov7(links, movies, movie_filter.categories,
                                                          movie_filter.confidence)
                else:
                    results = detect_movies.detect_yolov8(links, movie_filter.yolo, movies,
                                                          movie_filter.categories,
                                                          movie_filter.confidence)
            else:
                movie_dict_with_links = cls.create_movie_array_with_trailer_link_tmdb(movies[:movie_filter.max_pages])

                if "yolov8" in movie_filter.yolo:
                    results = detect_movies.make_trailer_detection(movie_dict_with_links, movie_filter.yolo,
                                                                   movie_filter.categories,
                                                                   movie_filter.confidence)

        else:
            results = movies

        return results

    @classmethod
    def filter_movie_imdb(cls, movie_filter):
        movies = cls.fetch_movies_imdb_with_filter(movie_filter)
        if movies == None:
            return None
        results = []
        if len(movies) == 0:
            return results
        if len(movie_filter.categories) > 0:
            if len(movies) == 0:
                return []
            detect_movies = DetectMovies()

            if movie_filter.detect_type == "Poster":
                links, movies = cls.get_poster_links_with_movies(movies)
                if movie_filter.yolo == "yolov7":
                    results = detect_movies.detect_yolov7(links, movies, movie_filter.categories,
                                                          movie_filter.confidence)
                else:
                    results = detect_movies.detect_yolov8(links, movie_filter.yolo, movies,
                                                          movie_filter.categories,
                                                          movie_filter.confidence)
            else:
                print(len(movies))
                print(len(movies[:movie_filter.max_pages]))
                movie_dict_with_links = cls.create_movie_array_with_trailer_link_imdb(movies[:movie_filter.max_pages])
                if movie_dict_with_links == None:
                    return None

                if "yolov8" in movie_filter.yolo:
                    results = detect_movies.make_trailer_detection(movie_dict_with_links, movie_filter.yolo,
                                                                   movie_filter.categories,
                                                                   movie_filter.confidence)
        else:
            results = movies

        return results

    @classmethod
    def fetch_movies_imdb_with_filter(cls, movie_filter):
        print("Fetching imdb.")
        array_count = movie_filter.max_pages if movie_filter.detect_type != 'Trailer' and len(
            movie_filter.categories) > 0 else 1
        count = [50, 100, 250][array_count]
        external_request = f'{keys.IMDB_API}AdvancedSearch/{keys.API_KEY_IMDB}?count={count}' \
                           f'&title={movie_filter.query}' \
                           f'&genres={",".join(movie_filter.genres)}' \
                           f'&release_date={movie_filter.date_from_str},{movie_filter.date_to_str}'
        if movie_filter.query == "" and len(
                movie_filter.genres) == 0 and not movie_filter.date_to and not movie_filter.date_from:
            external_request += '&groups=top_250'
        movies = cls.make_imdb_movie_dict(external_request)

        print("Fetching finished.")
        return movies

    @classmethod
    def make_imdb_movie_dict(cls, external_request):
        external_response = requests.get(f'{external_request}')

        data = external_response.json()

        if (data.get('errorMessage', "") and 'Maximum usage' in data.get('errorMessage',"") ):
            return None

        data.get('results', [])
        movies_list = []

        for movie in data:
            movies_list.append({
                "id": movie["id"],
                "apiDb": "IMDB",
                "title": movie["title"],
                "poster_path": movie.get("image", None),
                "release_date": movie.get("description")[1:-1],
                "popularity": movie["imDbRating"],
                "genres": movie.get("genres", "").split(",") if movie.get("genres", "") is not None else "",
            })
        return movies_list

    @classmethod
    def fetch_movie_tmdb_with_trailers(cls, max_page, from_page, date_from):
        print("Fetching tmdb.")
        # external_response = f'{keys.TMDB_API}discover/movie?api_key={keys.API_KEY_TMDB}&include_adult=false'
        # if date_from != "":
        #     external_response += f'&sort_by=release_date.asc&release_date.gte={date_from}'
        external_response = f'{keys.TMDB_API}discover/movie?api_key={keys.API_KEY_TMDB}&include_adult=false&sort_by=primary_release_date.desc&release_date.lte=2023-05-07&release_date.gte=2023-01-01&&with_original_language=sk|en'
        movies = cls.call_api_multiple_times_make_and_tmdb_movie_dict(external_response, max_page, from_page)
        movies = cls.create_movie_array_with_trailer_link_tmdb(movies, True)
        print("Fetching finished.")
        return movies

    @classmethod
    def fetch_movies_tmdb_with_filter(cls, movie_filter):
        print("Fetching tmdb.")
        if movie_filter.query != "":
            external_response = f'{keys.TMDB_API}search/movie?api_key={keys.API_KEY_TMDB}' \
                                f'&query={movie_filter.query}' \
                                f'&include_adult=false'
        else:
            external_response = f'{keys.TMDB_API}discover/movie?api_key={keys.API_KEY_TMDB}' \
                                f'&with_genres={cls.get_genre_ids(movie_filter.genres)}' \
                                f'&release_date.gte={movie_filter.date_from_str}' \
                                f'&release_date.lte={movie_filter.date_to_str}' \
                                f'&include_adult=false'

        max_pages = 1 if movie_filter.database else movie_filter.max_pages
        movies = cls.call_api_multiple_times_make_and_tmdb_movie_dict(external_response, max_pages)
        movies = cls.filter_movies_with_title_and_more_filters(
            movies, movie_filter.query, movie_filter.genres,
            movie_filter.date_from, movie_filter.date_to)

        print("Fetching finished.")
        return movies

    @classmethod
    def filter_movies_with_title_and_more_filters(cls, movies, query, genres, date_from, date_to):
        if query != "" and (len(genres) > 0 or date_to or date_to):
            if genres:
                movies = [movie for movie in movies if
                          all(genre in movie["genres"] for genre in genres)]
            if date_from:
                movies = [movie for movie in movies
                          if movie["release_date"] and movie["release_date"] >= date_from]
            if date_to:
                movies = [movie for movie in movies
                          if movie["release_date"] and movie["release_date"] <= date_to]

        return movies

    @classmethod
    def call_api_multiple_times_make_and_tmdb_movie_dict(cls, external_response, max_page=1, start_page=1):
        data = cls.call_api_multiple_times(external_response, max_page, start_page)
        movies_list = []
        for movie in data:
            movies_list.append({
                "id": movie["id"],
                "apiDb": "TMDB",
                "title": movie["title"],
                "poster_path": movie.get("poster_path", None),
                "release_date": datetime.strptime(movie.get("release_date"), "%Y-%m-%d").date()
                if movie.get("release_date", None) else None,
                "popularity": movie["popularity"],
                "genres": cls.get_genre_names(movie.get("genre_ids", [])),
            })
        return movies_list

    @classmethod
    def call_api_multiple_times(cls, external_request, max_pages, start_page):
        data = []
        total_pages = None
        actual_page = start_page
        while actual_page < (start_page + max_pages) and (
                total_pages is None or actual_page <= total_pages):
            external_response = requests.get(f'{external_request}&page={actual_page}')

            if actual_page == 1:
                total_pages = external_response.json().get('total_pages', 0) + 1

            data += external_response.json().get('results', [])
            actual_page += 1
        return data

    @classmethod
    def get_poster_links_with_movies(cls, movies, start_path=""):
        posters_links = []
        movies_list = []
        for movie in movies:
            if movie["poster_path"] is not None and movie[
                "poster_path"] != "https://imdb-api.com/images/original/nopicture.jpg":
                posters_links.append(start_path + movie["poster_path"])
                movie["det"] = []
                movies_list.append(movie)
        return posters_links, movies_list

    @classmethod
    def create_movie_array_with_trailer_link_tmdb(cls, movies, database=False):
        print("Start fetching trailer links")
        start_path = 'https://www.youtube.com/watch?v='
        movie_with_trailer_list = []

        for movie in movies:
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

            movie["trailer_link"] = start_path + trailer_video["key"] if trailer_video else None
            movie["trailer_objects"] = []
            if trailer_video or database:
                movie_with_trailer_list.append(movie)

        return movie_with_trailer_list

    @classmethod
    def create_movie_array_with_trailer_link_imdb(cls, movies):
        print("Start fetching trailer links")
        movie_with_trailer_list = []

        for movie in movies:
            video_response = requests.get(
                f'{keys.IMDB_API}YouTubeTrailer/{keys.API_KEY_IMDB}/{movie["id"]}')

            video = video_response.json()
            if (video.get('errorMessage', "") and 'Maximum usage' in video.get('errorMessage',"") ):
                return None
            trailer_video = video.get("videoUrl", []) if video else None
            movie["trailer_link"] = trailer_video if trailer_video else None
            movie["trailer_objects"] = []
            if trailer_video:
                movie_with_trailer_list.append(movie)

        return movie_with_trailer_list

    @classmethod
    def get_popular_movies_tmdb(cls):
        external_response = requests.get(f'{keys.TMDB_API}movie/popular?api_key={keys.API_KEY_TMDB}')
        return external_response.json().get('results', [])

    @classmethod
    def get_movie_detail_tmdb(cls, movie_id):
        external_response = requests.get(
            f'{keys.TMDB_API}movie/{movie_id}?api_key={keys.API_KEY_TMDB}&append_to_response=credits')
        data = external_response.json()
        cast = []
        cast_data = data.get("credits").get("cast", []) if len(data.get("credits").get("cast", [])) > 0 else []
        for person in cast_data:
            cast.append({"profile_path": person["profile_path"], "name": person["name"]})
        reviews = cls.get_movie_reviews_tmdb(movie_id, 1)
        genres = [genre.get('name', '') for genre in data.get("genres", [])]

        movie = {
            "id": data.get("id"),
            "imdb_id": data.get("imdb_id"),
            "original_title": data.get("title", ""),
            "cast": cast,
            "genres": genres,
            "poster_path": data.get("poster_path", ""),
            "plot": data.get("overview", ""),
            "rating": data.get("vote_average", ""),
            "backdrop_path": data.get("backdrop_path", ""),
            "release_date": datetime.strptime(data.get("release_date"), "%Y-%m-%d").date() if data.get(
                "release_date") else "",
            "runTimeStr": "{0}h {1}min".format(*divmod(int(data.get("runtime", "")), 60)),
            "runtime": data.get("runtime", ""),
            "reviews": reviews,
            "homepage": data.get("homepage", "")
        }
        return movie

    @classmethod
    def get_movie_reviews_tmdb(cls, movie_id, page):
        external_response = requests.get(
            f'{keys.TMDB_API}movie/{movie_id}/reviews?api_key={keys.API_KEY_TMDB}&page={page}')
        data = external_response.json().get("results")
        reviews = []
        for review in data[:10]:
            date_str = review.get("created_at")
            date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            date = date_obj.strftime('%d %b %Y')

            reviews.append(
                {
                    "username": review.get("author"),
                    "date": date,
                    "rate": review.get("author_details").get("rating"),
                    "title": "",
                    "content": review.get("content")
                }
            )
        return reviews

    @classmethod
    def get_movie_detail_imdb(cls, movie_id):
        external_response = requests.get(
            f'{keys.IMDB_API}Title/{keys.API_KEY_IMDB}/{movie_id}/FullActor,Posters')
        data = external_response.json()
        if (data.get('errorMessage', "") and 'Maximum usage' in data.get('errorMessage',"") ):
            return None

        reviews = cls.get_movie_reviews_imdb(data.get("id"))

        backdrop = data.get("posters", []).get("backdrops")[0].get("link") if data.get("posters") and data.get(
            "posters").get(
            "backdrops") and len(
            data.get("posters").get("backdrops")) > 0 else ""
        cast = []
        best_stars_count = len(data.get("stars", "").split(",") if data.get("stars", "") else [])

        if data.get("actorList"):
            for person in data.get("actorList", [])[:best_stars_count]:
                cast.append({"profile_path": person.get("image", ""), "name": person.get("name", "")})

        movie = {
            "id": data.get("id"),
            "imdb_id": data.get("id"),
            "original_title": data.get("title", ""),
            "cast": cast,
            "genres": data.get("genres", "").split(",") if data.get("genres", "") is not None else "",
            "poster_path": data.get("image", ""),
            "plot": data.get("plot", ""),
            "rating": data.get("imdb_rating", ""),
            "backdrop_path": backdrop,
            "release_date": datetime.strptime(data.get("release_date"), "%Y-%m-%d").date() if data.get(
                "release_date") else "",
            "runTimeStr": data.get("runTimeStr", ""),
            "runtime": data.get("runtimeMins", ""),
            "reviews": reviews,
            "homepage": ""
        }
        return movie

    @classmethod
    def get_movie_reviews_imdb(cls, movie_id):
        external_response = requests.get(
            f'{keys.IMDB_API}Reviews/{keys.API_KEY_IMDB}/{movie_id}')
        data = external_response.json()
        if (data.get('errorMessage', "") and 'Maximum usage' in data.get('errorMessage',"") ):
            return None

        data = data.get("items")
        reviews = []
        if data == None:
            return reviews
        for review in data[:10]:
            reviews.append(
                {
                    "username": review.get("username"),
                    "date": review.get("date"),
                    "rate": review.get("rate"),
                    "title": review.get("title"),
                    "content": review.get("content")
                }
            )
        return reviews
