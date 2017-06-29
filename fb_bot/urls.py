from django.conf.urls import include, url
from .views import FbBotView

urlpatterns = [
    url(r'^foo/?$', FbBotView.as_view())
]