from django.contrib import admin
from django.urls import path, include
from myapp.views import (
    hello_world, pomodoro_timer,
    api_create_session, api_start_session, api_pause_session,
    api_resume_session, api_complete_session, api_abandon_session,
    api_get_session, api_list_sessions, api_stats,
    health_check, csrf_token_view
)


urlpatterns = [
    # 基础页面
    path('', hello_world, name='home'),
    path('pomodoro/', pomodoro_timer, name='pomodoro'),

    # API端点
    path('api/tomato/create/', api_create_session, name='api_create_session'),
    path('api/tomato/<int:session_id>/start/', api_start_session, name='api_start_session'),
    path('api/tomato/<int:session_id>/pause/', api_pause_session, name='api_pause_session'),
    path('api/tomato/<int:session_id>/resume/', api_resume_session, name='api_resume_session'),
    path('api/tomato/<int:session_id>/complete/', api_complete_session, name='api_complete_session'),
    path('api/tomato/<int:session_id>/abandon/', api_abandon_session, name='api_abandon_session'),
    path('api/tomato/<int:session_id>/', api_get_session, name='api_get_session'),
    path('api/tomato/list/', api_list_sessions, name='api_list_sessions'),
    path('api/tomato/stats/', api_stats, name='api_stats'),

    # 辅助功能
    path('health/', health_check, name='health_check'),
    path('csrf-token/', csrf_token_view, name='csrf_token'),

    # 管理后台
    path('admin/', admin.site.urls),
]