from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'templates', views.EmailTemplateViewSet)
router.register(r'campaigns', views.EmailCampaignViewSet)
router.register(r'recipients', views.EmailRecipientViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('send/', views.SendEmailView.as_view(), name='send-email'),
    path('preview/', views.PreviewEmailView.as_view(), name='preview-email'),
    path('test-connection/', views.TestEmailConnectionView.as_view(), name='test-email-connection'),
    path('generate-templates/', views.GenerateTemplatesView.as_view(), name='generate-templates'),
    path('config/', views.GetEmailConfigView.as_view(), name='get-email-config'),
]
