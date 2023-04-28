from rest_framework import serializers
from ..models import Genre, Movie, VideoObject, PosterObject


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('name',)


class VideoObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoObject
        fields = ('model', 'label', 'maxConf')


class PosterObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosterObject
        fields = ('model', 'label', 'conf', 'box')


class MovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True)
    video_objects = VideoObjectSerializer(source='videoobject_set', many=True)
    poster_objects = PosterObjectSerializer(source='posterobject_set', many=True)

    class Meta:
        model = Movie
        fields = (
            'tmdb_id', 'apiDb', 'posterPath', 'title', 'releaseYear', 'popularity', 'video', 'genres', 'video_objects',
            'poster_objects')


class SearchFilterSerializer(serializers.Serializer):
    categories = serializers.ListField(child=serializers.CharField())
    database = serializers.BooleanField()
    yolo = serializers.CharField()
    conf = serializers.IntegerField()
    movieDatabase = serializers.CharField()
    genres = serializers.ListField(child=serializers.CharField())
    query = serializers.CharField()
    dateFrom = serializers.DateField()
    dateTo = serializers.DateField()
