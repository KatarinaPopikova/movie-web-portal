from rest_framework.response import Response
from rest_framework import generics


class PosterView(generics.RetrieveAPIView):

    def get(self, request, *args, **kwargs):

        return Response(posters)
