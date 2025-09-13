"""
URL configuration for credit_approval project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from api import views
from api import health
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger/OpenAPI documentation setup
schema_view = get_schema_view(
    openapi.Info(
        title="Credit Approval System API",
        default_version='v1',
        description="API for managing customer loans and credit approvals",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="admin@creditapproval.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),  # Root URL shows API docs
    
    # API endpoints
    path('register', views.register, name='register'),
    path('check-eligibility', views.check_eligibility, name='check-eligibility'),
    path('create-loan', views.create_loan, name='create-loan'),
    path('view-loan/<int:loan_id>', views.view_loan, name='view-loan'),
    path('view-loans/<int:customer_id>', views.view_loans, name='view-loans'),
    
    # Health check endpoints
    path('health/', health.health_check, name='health'),
    path('health/detailed/', health.health_check_detailed, name='health-detailed'),
    path('health/ready/', health.readiness_check, name='health-ready'),
    path('health/live/', health.liveness_check, name='health-live'),
]
