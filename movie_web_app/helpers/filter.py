from datetime import datetime


class Filter:
    def __init__(self, categories, database, yolo, confidence, movie_database,
                 genres, query, date_from, date_to, detect_type, max_pages):
        self.categories = categories.split(",") if categories else []
        self.database = True if database == "true" else False
        self.yolo = yolo
        self.confidence = float(confidence) / 100
        self.movie_database = movie_database
        self.genres = genres.split(",") if genres else []
        self.query = query
        self.date_from = datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else None
        self.date_from_str = date_from
        self.date_to = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else None
        self.date_to_str = date_to
        self.detect_type = detect_type
        self.max_pages = int(max_pages)


def parse_filters(request):
    categories = request.GET.get("categories")
    yolo = request.GET.get("yolo")
    confidence = request.GET.get("confidence")
    database = request.GET.get("database")
    movie_database = request.GET.get("movieDatabase")
    genres = request.GET.get("genres")
    query = request.GET.get("query")
    date_to = request.GET.get("dateTo")
    date_from = request.GET.get("dateFrom")
    detect_type = request.GET.get("detectType")
    max_pages = request.GET.get("maxPages")
    return Filter(categories, database, yolo, confidence, movie_database, genres, query, date_from, date_to,
                  detect_type, max_pages)
