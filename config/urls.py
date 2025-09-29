from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),  # Changed 'users.urls' to 'accounts.urls'
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/personalize/', include('personalize.urls')),  
    path('api/events/', include('events.urls')),
    path('api/payment/', include('payment.urls')),
    path('api/support/', include('support.urls')),
    path('api/legal/', include('legal.urls')),

    # --- DRF-SPECTACULAR SWAGGER UI URLs ---
    # 1. OpenAPI schema: serves the raw OpenAPI spec (JSON/YAML)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # 2. Swagger UI: Renders the interactive documentation UI
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # --- END DRF-SPECTACULAR SWAGGER UI URLs ---
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)