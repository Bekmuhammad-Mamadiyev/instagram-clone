from django.shortcuts import render
from django.template.context_processors import request
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from post.models import Post, PostComment, PostLike, CommentLike
from post.serializers import PostSerializer, CommentSerializer, PostLikeSerializer
from shared.custom_pagination import CustomPagination


class PostListApiView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = (AllowAny,)
    pagination_class = CustomPagination

    def get_queryset(self):
        return Post.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostCreatView(generics.CreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated,]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]


    def put(self,request,*args,**kwargs):
        post = self.get_object()
        serializer = self.serializer_class(post, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "success":True,
                "code":status.HTTP_200_OK,
                "message":"Post successfully updated",
                "data":serializer.data

            }
        )

    def delete(self, request, *args, **kwargs):
        post = self.get_object()
        post.delete()
        return Response(
            {
                "success": True,
                "code": status.HTTP_204_NO_CONTENT,
                "message": "Post successfully deleted",
            }
        )


# class PostCommentList(generics.ListAPIView):
#     serializer_class = CommentSerializer
#     permission_classes = [AllowAny,]
#
#
#     def get_queryset(self):
#         post_id = self.kwargs['pk']
#         queryset = PostComment.objects.filter(post_id=post_id)
#         return queryset
#
#
# class PostCommentCreateView(generics.CreateAPIView):
#     serializer_class = CommentSerializer
#     permission_classes = [IsAuthenticated,]
#
#     def perform_create(self, serializer):
#         post_id = self.kwargs["pk"]
#         serializer.save(author=self.request.user, post_id=post_id)


class CommentListCreatApiView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly,]
    queryset = PostComment.objects.all()
    pagination_class = CustomPagination

    def get_queryset(self):
        return self.queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostLikeListApiView(generics.ListAPIView):
    serializer_class = PostLikeSerializer
    permission_classes = [AllowAny,]

    def get_queryset(self):
        post_id = self.kwargs["pk"]
        return PostLike.objects.filter(author=self.request.user, post_id=post_id)



class CommentLikeListApiView(generics.ListAPIView):
    serializer_class = PostLikeSerializer
    permission_classes = [AllowAny,]

    def get_queryset(self):
        comment_id = self.kwargs['pk']
        return CommentLike.objects.filter(comment_id=comment_id)


class PostLikeApiView(APIView):
    def post(self, request, pk):
        try:
            post_like = PostLike.objects.create(author =self.request.user,
                                                post_id=pk)
            serializer = PostLikeSerializer(post_like)

            data = {
                "success":True,
                "message":"Postga like bosildi",
                "data":serializer.data

            }
            return Response(data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return  Response(str(e), status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request,pk):
        try:
            post_like = PostLike.objects.get(
                author = self.request.user,
                post_id = pk,
            )
            post_like.delete()
            data = {
                "success":True,
                "message":"like uchdi",
                "data":None
            }
            return Response(data,status=status.HTTP_200_OK)

        except Exception as e:
            data = {
                "success":False,
                "message":f"{str(e)}"
            }
            return Response(data)