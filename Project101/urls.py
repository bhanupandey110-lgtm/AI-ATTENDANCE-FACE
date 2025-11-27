from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

def root_redirect(request):
    return redirect('login')  # Redirect root URL to login page

urlpatterns = [
    path('', root_redirect),
    path('', include('app1.urls')),
    path('admin/', admin.site.urls),
]
