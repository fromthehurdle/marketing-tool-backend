from django.urls import path, include, re_path 
from . import views 
from rest_framework.routers import DefaultRouter 
from django.conf import settings  
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView 


router = DefaultRouter()
router.register(r'searches', views.SearchViewSet, basename='search')
router.register(r'results', views.ResultViewSet, basename='result')
router.register(r'result-items', views.ResultItemViewSet, basename='resultitem')
router.register(r'history', views.HistoryViewSet, basename='history')
router.register(r'libraries', views.LibraryViewSet, basename='library')
router.register(r'analysis-results', views.AnalysisResultViewSet, basename='analysisresult')

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include(router.urls)),
]
