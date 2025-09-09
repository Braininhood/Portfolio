from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'files', views.FileViewSet)
router.register(r'cohorts', views.CohortViewSet)
router.register(r'participants', views.ParticipantViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('upload/', views.FileUploadView.as_view(), name='file-upload'),
    path('upload/forms/', views.MicrosoftFormsImportView.as_view(), name='forms-import'),
    path('process/', views.ProcessDataView.as_view(), name='process-data'),
    path('analyze/', views.AnalyzeDataView.as_view(), name='analyze-data'),
    path('cohorts/create/', views.CreateCohortsView.as_view(), name='create-cohorts'),
    path('bpa/process/', views.BPAProcessView.as_view(), name='bpa-process'),
    path('bpa/demo/', views.BPADemoView.as_view(), name='bpa-demo'),
    path('dashboard/stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
]
