from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from post.models import Post
from post.serializers import PostSerializer
from shared.custom_pagination import CustomPagination


class PostListApiView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination

    def get_queryset(self):
        return Post.objects.all()


class PostCreatView(generics.CreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated,]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)