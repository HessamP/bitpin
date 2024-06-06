from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('backoffice/', admin.site.urls),
    path('api/v1/user/', include('user.urls')),
    path('api/v1/blog/', include('blog.urls')),

]
