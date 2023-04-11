from django.db import models


class VideoObject(models.Model):
    name = models.CharField(max_length=255)
    maxConf = models.DecimalField(max_digits=6, decimal_places=5, null=True)


class Genre(models.Model):
    name = models.CharField(max_length=255)


class VideoMovieModelTmdb(models.Model):
    id = models.IntegerField(primary_key=True)
    posterPath = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    releaseYear = models.DateField(null=True)
    popularity = models.FloatField(null=True)
    video = models.CharField(max_length=255, null=True)
    objects = models.ManyToManyField(VideoObject)
    genres = models.ManyToManyField(Genre)

