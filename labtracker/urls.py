from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from tracker import views as tracker_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tracker.urls')),
    path('auth/', include('social_django.urls', namespace='social')),
    path('login/', tracker_views.login_page, name='login'),
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),
]
