"""
URL configuration for SensitivityAnalysis project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include

from dashboard import views as dashboard_views
from data_processing import views as proces_views
urlpatterns = [
    path('', dashboard_views.sentiment_dashboard, name='sentiment_dashboard'),
    path('loading/', dashboard_views.loading_view, name='loading'),
    path('analyze/', proces_views.run_analysis, name='run_analysis'),
    path('dashboard/', dashboard_views.results_dashboard, name='results_dashboard'),
    path('analyze-status/', proces_views.get_analysis_status, name='get_analysis_status'),
]

