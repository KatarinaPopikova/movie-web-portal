from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=255)


class Movie(models.Model):
    tmdb_id = models.CharField(max_length=255, null=False)
    posterPath = models.CharField(max_length=255, null=True)
    title = models.CharField(max_length=255, null=False)
    releaseYear = models.DateField(null=True)
    popularity = models.FloatField(null=True)
    video = models.CharField(max_length=255, null=True)
    genres = models.ManyToManyField(Genre)


class VideoObject(models.Model):
    model = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    maxConf = models.DecimalField(max_digits=6, decimal_places=5, null=True)
    box = models.JSONField()
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)


class PosterObject(models.Model):
    model = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    maxConf = models.DecimalField(max_digits=6, decimal_places=5, null=True)
    box = models.JSONField()
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
