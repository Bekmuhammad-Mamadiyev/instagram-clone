from django.urls import path

from post.views import PostListApiView, PostCreatView

urlpatterns = [
    path("posts/",PostListApiView.as_view()),
    path("post-create/",PostCreatView.as_view())
]