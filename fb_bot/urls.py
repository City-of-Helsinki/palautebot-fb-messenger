from django.conf.urls import include, url
from .views import FbBotView

urlpatterns = [
    url(r'^039e6165434596d7a4071fe280c6fb61dab3018a5cce613085?$', FbBotView.as_view())
]