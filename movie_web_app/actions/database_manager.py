from datetime import datetime

from movie_web_app.actions.fetch_movie_manager import FetchMovies
from movie_web_app.actions.movie_detection_manager import DetectMovies
from movie_web_app.models import Genre, Movie, VideoObject, PosterObject
from django.db import IntegrityError


class DatabaseManager:
    @classmethod
    def fill_empty_database(cls):
        cls.fill_genres()
        cls.save_to_database()

    @classmethod
    def save_to_database(cls, start_page=1, date_from=""):
        fetch_movies = FetchMovies
        detect_movies = DetectMovies
        max_page = 1
        movies = fetch_movies.fetch_movie_tmdb_with_trailers(max_page, start_page, date_from)
        movies_links, movies_with_poster_link = fetch_movies.get_poster_links_with_movies(movies)
        yolov7_det = detect_movies.detect_yolov7(movies_links, movies_with_poster_link)
        yolov8n_det = detect_movies.detect_yolov8(movies_links, movies_with_poster_link, "nano")
        yolov8l_det = detect_movies.detect_yolov8(movies_links, movies_with_poster_link, "large")
        movies = detect_movies.make_trailer_detection(movies)

        cls.save_all_to_database(movies, yolov7_det, yolov8n_det, yolov8l_det)

    @classmethod
    def save_all_to_database(cls, movies, yolov7_det, yolov8n_det, yolov8l_det):

        index = 0
        for movie_data in movies:

            try:
                genres = Genre.objects.filter(name__in=movie_data['genres'])

                movie = Movie(
                    tmdb_id=movie_data['id'],
                    apiDb='TMDB',
                    title=movie_data['title'],
                    posterPath=movie_data['poster_path'],
                    releaseYear=movie_data['release_date'],
                    popularity=movie_data['popularity'],
                    video=movie_data['trailer_link'],
                )

                for genre in genres:
                    movie.genres.add(genre)

                movie.save()

                cls.save_trailers(movie, movie_data)

                if movie.posterPath == yolov7_det[index]["poster_path"]:
                    index += 1
                    cls.save_posters(movie, yolov7_det[index], 'yolov7')
                    cls.save_posters(movie, yolov8n_det[index], 'yolov8n')
                    cls.save_posters(movie, yolov8l_det[index], 'yolov8l')

            except IntegrityError:
                continue

    @classmethod
    def save_posters(cls, movie, yolo, model):
        for poster_object in yolo["det"]:
            poster_obj = PosterObject.objects.create(
                model=model,
                label=poster_object["label"],
                maxConf=poster_object["conf"],
                box=poster_object["box"],
                movie=movie,
            )
            poster_obj.save()

    @classmethod
    def save_trailers(cls, movie, movie_data):
        for vid_object in movie_data["trailer_objects"]:
            video_obj = VideoObject.objects.create(
                model='yolov8n',
                label=vid_object["label"],
                maxConf=vid_object["conf"],
                movie=movie,
            )
            video_obj.save()

    @classmethod
    def fill_genres(cls):

        fetch_movies = FetchMovies
        genres = fetch_movies.get_genre_names(all_genres=True)
        for genre_str in genres:
            genre = Genre.objects.create(name=genre_str)
            genre.save()

    @classmethod
    def get_movies_from_db(cls, movie_filter):
        movies = Movie.objects.filter(genres__name__in=movie_filter.genres)

        num_genres = len(movie_filter.genres)
        num_categories = len(movie_filter.categories)

        if movie_filter.query:
            movies = movies.filter(title__icontains=movie_filter.query)
        if movie_filter.date_from:
            movies = movies.filter(releaseYear__gte=movie_filter.date_from)
        if movie_filter.date_to:
            movies = movies.filter(releaseYear__lte=movie_filter.date_to)
        if movie_filter.categories and movie_filter.detect_type == 'Poster':
            movies = movies.filter(posterobject__label__in=movie_filter.categories,
                                   posterobject__model=movie_filter.yolo,
                                   posterobject__conf__gt=movie_filter.confidence).distinct()
        elif movie_filter.categories and movie_filter.detect_type == 'Trailer':
            movies = movies.filter(videoobject__label__in=movie_filter.categories, videoobject__model=movie_filter.yolo,
                                   videoobject__maxConf__gt=movie_filter.confidence).distinct()

        filtered_movies = []
        labels = 0
        for movie in movies:
            common_genres = movie.genres.filter(name__in=movie_filter.genres)
            if movie_filter.categories and movie_filter.detect_type == 'Poster':
                labels = movie.posterobject_set.filter(label__in=movie_filter.categories).values_list('label',
                                                                                                      flat=True).distinct()

            elif movie_filter.categories and movie_filter.detect_type == 'Trailer':
                labels = movie.videoobject_set.filter(label__in=movie_filter.categories).values_list('label',
                                                                                                      flat=True).distinct()

            if len(common_genres) == num_genres and len(labels) == num_categories:
                filtered_movies.append(movie)

        return filtered_movies

