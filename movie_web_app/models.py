from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=255)


class Movie(models.Model):
    tmdb_id = models.CharField(primary_key=True, max_length=255)
    apiDb = models.CharField(max_length=255)
    posterPath = models.CharField(max_length=255, null=True)
    title = models.CharField(max_length=255)
    releaseYear = models.DateField(null=True)
    popularity = models.FloatField(null=True)
    video = models.CharField(max_length=255, null=True)
    genres = models.ManyToManyField(Genre)


class VideoObject(models.Model):
    model = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    maxConf = models.DecimalField(max_digits=6, decimal_places=5)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)


class PosterObject(models.Model):
    model = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    conf = models.DecimalField(max_digits=6, decimal_places=5)
    box = models.JSONField()
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
