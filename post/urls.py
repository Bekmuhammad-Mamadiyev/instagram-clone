from django.urls import path

from post.views import PostListApiView, PostCreatView, PostRetrieveUpdateDestroyView, CommentListCreatApiView, \
    PostLikeListApiView, PostLikeApiView

urlpatterns = [
    path("posts/",PostListApiView.as_view()),
    path("post-create/",PostCreatView.as_view()),
    path("posts/<uuid:pk>/", PostRetrieveUpdateDestroyView.as_view()),
    # path("post-comment/<uuid:pk>/",PostCommentList.as_view()),
    # path("comment-create/<uuid:pk>/",PostCommentCreateView.as_view()),
    path("commentlist-create/",CommentListCreatApiView.as_view()),
    path("postlikelist/<uuid:pk>/",PostLikeListApiView.as_view()),
    path("postlike/<uuid:pk>/",PostLikeApiView.as_view()),
]