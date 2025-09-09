from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'files', views.ExcelFileViewSet)
router.register(r'participants', views.ParticipantViewSet)
router.register(r'cohorts', views.CohortViewSet)
router.register(r'jobs', views.ProcessingJobViewSet)

urlpatterns = [
    path('cohorts/create/', views.CreateCohortsView.as_view(), name='create-cohorts'),
    path('', include(router.urls)),
]
