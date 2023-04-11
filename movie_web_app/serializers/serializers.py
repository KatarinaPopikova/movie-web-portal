from rest_framework import serializers


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
