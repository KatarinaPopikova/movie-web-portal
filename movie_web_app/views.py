import time

from rest_framework.response import Response
from rest_framework.views import APIView

from movie_web_app.helpers.filter import Filter
from movie_web_app.actions.fetch_movie_manager import FetchMovies
from movie_web_app.actions.movie_detection_manager import DetectMovies
from movie_web_app.actions.database_manager import DatabaseManager
from django.http import HttpResponse
import cv2


class ListGenres(APIView):
    def get(self, request):
        genres = FetchMovies.get_genre_names(all_genres=True)
        return Response(genres)


class ListCategoriesToDetect(APIView):
    def get(self, request):
        time.sleep(10)
        categories = DetectMovies.find_labels()
        if len(categories) > 0:
            return Response(categories)
        else:
            return Response(data={'message': 'Can not load models for listing categories.'}, status=500)




class ListFilteredMovies(APIView):
    def get(self, request, format=None):
        movie_filter = Filter.parse_filters(request)

        if movie_filter.database:
            return Response(DatabaseManager.get_movies_from_db(movie_filter))
        else:
            return Response(FetchMovies.filter_movies(movie_filter))




class ListPopularMoviesTmdb(APIView):
    def get(self, request):
        results = FetchMovies.get_popular_movies_tmdb()
        return Response(results)


class MovieDetailTmdb(APIView):

    def get(self, request, movie_id):
        results = FetchMovies.get_movie_detail_tmdb(movie_id)
        return Response(results)


class MovieReviewsTmdb(APIView):

    def get(self, request, movie_id):
        results = FetchMovies.get_movie_reviews_tmdb(movie_id, request.GET["page"])
        return Response(results)


class MovieDetailImdb(APIView):

    def get(self, request, movie_id):
        results = FetchMovies.get_movie_detail_imdb(movie_id)
        return Response(results)


class FillDatabase(APIView):
    def get(self, request):
        DatabaseManager.fill_empty_database()
        return Response()


class ImgProcess(APIView):
    def get(self, request):
        # video_url = request.GET.get('video_url')
        # Open the video stream and read the first frame
        video_url = 'https://www.youtube.com/watch?v=_H1G9BsxhDw'
        import pafy
        video_url = pafy.new(video_url).getbest(preftype="mp4").url
        cap = cv2.VideoCapture(video_url)
        frame_index = 180  # 0-indexed, so 4 is the 5th frame

        while frame_index > 0:
            ret, frame = cap.read()
            frame_index -= 1
        ret, frame = cap.read()

        cap.release()

        frame = DetectMovies.detect_and_plot(frame, "yolov8n.pt")
        frame = DetectMovies.detect_and_plot(frame, "yolov8_custom.pt")

        # Convert the color space to RGB and encode as JPEG
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ret, jpeg = cv2.imencode('.jpg', rgb_frame)
        frame_bytes = jpeg.tobytes()

        # Return the JPEG image bytes in an HTTP response
        response = HttpResponse(frame_bytes, content_type='image/jpeg')
        response['Content-Disposition'] = 'inline'
        return response
