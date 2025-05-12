
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('userApp.urls')),
    path('specialization/', include('speciliarizationApp.urls')),
    path('lawyer/', include('professionalApp.urls')),
    path('client/', include('clientApp.urls')),
    path('case/', include('caseApp.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)