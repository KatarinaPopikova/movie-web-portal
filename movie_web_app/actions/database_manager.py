import copy

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
        movies_links, movies_with_poster_link = fetch_movies.get_poster_links_with_movies(movies, 'https://image.tmdb.org/t/p/w400')
        yolov7_det = detect_movies.detect_yolov7(movies_links, copy.deepcopy(movies_with_poster_link))
        cls.save_posters(yolov7_det, 'yolov7')
        yolov8n_det = detect_movies.detect_yolov8(movies_links, copy.deepcopy(movies_with_poster_link), "nano")
        cls.save_posters(yolov8n_det, 'yolov8n')
        yolov8l_det = detect_movies.detect_yolov8(movies_links, copy.deepcopy(movies_with_poster_link), "large")
        cls.save_posters(yolov8l_det, 'yolov8l')
        # cls.save_genres(movies_with_poster_link)

        # movies = detect_movies.make_trailer_detection(movies)

        # cls.save_all_to_database(movies)

    @classmethod
    def save_all_to_database(cls, movies):

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

                movie.save()

                for genre in genres:
                    movie.genres.add(genre)

                movie.save()

                cls.save_trailers(movie, movie_data)

            except IntegrityError:
                continue

    @classmethod
    def save_posters(cls, poster_detection, model):
        for poster in poster_detection:
            movie = Movie.objects.get(tmdb_id=poster['id'])
            cls.save_poster(movie, poster, model)

    @classmethod
    def save_poster(cls, movie, yolo, model):
        for poster_object in yolo["det"]:
            poster_obj = PosterObject.objects.create(
                model=model,
                label=poster_object["label"],
                conf=poster_object["conf"],
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
    def save_genres(cls, movies):
        for movie in movies:
            genres = Genre.objects.filter(name__in=movie['genres'])

            movie = Movie.objects.get(tmdb_id=movie['id'])

            for genre in genres:
                movie.genres.add(genre)

            movie.save()

    @classmethod
    def fill_genres(cls):

        fetch_movies = FetchMovies
        genres = fetch_movies.get_genre_names(all_genres=True)
        for genre_str in genres:
            genre = Genre.objects.create(name=genre_str)
            genre.save()

    @classmethod
    def get_movies_from_db(cls, movie_filter):

        movies = Movie.objects.all()

        if movie_filter.genres:
            movies = movies.filter(genres__name__in=movie_filter.genres)

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
                                   posterobject__model='yolov8l',
                                   posterobject__conf__gt=movie_filter.confidence).distinct()
        elif movie_filter.categories and movie_filter.detect_type == 'Trailer':

            movies = movies.filter(videoobject__label__in=movie_filter.categories, videoobject__model='yolov8n',
                                   videoobject__maxConf__gt=movie_filter.confidence).distinct()

        filtered_movies = []
        labels_count = 0
        for movie in movies:
            common_genres_count = len(movie.genres.filter(name__in=movie_filter.genres))
            if movie_filter.categories and movie_filter.detect_type == 'Poster':
                labels_count = len(movie.posterobject_set.filter(label__in=movie_filter.categories,
                                                                 model='yolov8l',
                                                                 conf__gt=movie_filter.confidence) \
                                   .values_list('label', flat=True).distinct())

            elif movie_filter.categories and movie_filter.detect_type == 'Trailer':
                labels_count = len(movie.videoobject_set.filter(label__in=movie_filter.categories,
                                                                model='yolov8n',
                                                                maxConf__gt=movie_filter.confidence) \
                                   .values_list('label', flat=True).distinct())

            if common_genres_count == num_genres and labels_count == num_categories:
                filtered_movies.append(movie)
        movies_dict = []
        for movie in filtered_movies:
            movies_dict.append(movie_serializer(movie, movie_filter))
        return movies_dict


def movie_serializer(movie, movie_filter):
    # Get all genres for the movie and create a list of genre names
    genres = list(movie.genres.values_list('name', flat=True))

    videos = [{'model': model, 'label': label, 'maxConf': max_conf} for model, label, max_conf in
              movie.videoobject_set.filter(label__in=movie_filter.categories, model='yolov8n',
                                           maxConf__gt=movie_filter.confidence).distinct().values_list("model", "label",
                                                                                                       "maxConf")]

    posters = [{'model': poster[0], 'label': poster[1], 'conf': poster[2], 'box': poster[3]}
               for poster in movie.posterobject_set.filter(label__in=movie_filter.categories,
                                                           model='yolov8l',
                                                           conf__gt=movie_filter.confidence) \
                   .values_list("model", "label", "conf", "box").distinct()
               ]

    movie_dict = {
        'id': movie.tmdb_id,
        'api_db': movie.apiDb,
        'poster_path': movie.posterPath,
        'title': movie.title,
        'release_year': movie.releaseYear,
        'popularity': movie.popularity,
        'video': videos,
        'genres': genres,
        'det': posters,
    }

    return movie_dict
