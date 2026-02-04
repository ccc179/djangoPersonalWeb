from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import TomatoSession
import json


# ==================== 基础页面视图 ====================

def hello_world(request):
    """首页 - Hello World页面"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>部署成功！</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                text-align: center; 
                padding: 50px; 
                background-color: #f4f4f4;
            }
            h1 { 
                color: #2c3e50; 
            }
            .container { 
                background: white; 
                padding: 40px; 
                border-radius: 10px; 
                display: inline-block; 
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            .success { 
                color: #27ae60; 
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 Hello World!</h1>
            <p class="success">恭喜！你的 Django 应用已在华为云成功部署。</p>
            <p>服务器时间：<span id="datetime"></span></p>
            <p><a href="/admin/">访问管理后台</a> | <a href="/pomodoro/">番茄钟应用</a></p>
        </div>
        <script>
            function updateTime() {
                document.getElementById('datetime').textContent = new Date().toLocaleString();
            }
            updateTime();
            setInterval(updateTime, 1000);
        </script>
    </body>
    </html>
    """
    return HttpResponse(html_content)


def pomodoro_timer(request):
    """番茄钟主页面 - 渲染番茄钟应用界面"""
    return render(request, 'myapp/pomodoro.html')


# ==================== 番茄钟API视图（供前端JavaScript调用） ====================

@csrf_exempt  # 为简化开发，先禁用CSRF，生产环境需要启用
@require_POST
def api_create_session(request):
    """API: 创建一个新的番茄钟会话"""
    try:
        data = json.loads(request.body)
        planned_duration = data.get('planned_duration', 25)

        # 创建新的番茄钟会话
        session = TomatoSession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=data.get('name', '专注任务'),
            planned_duration=planned_duration,
            status='planned',
            work_start_at=None,
            work_end_at=None,
        )

        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'message': '番茄钟会话创建成功'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_POST
def api_start_session(request, session_id):
    """API: 开始一个番茄钟会话（开始工作）"""
    try:
        session = get_object_or_404(TomatoSession, id=session_id)

        # 只能开始状态为'planned'的会话
        if session.status != 'planned':
            return JsonResponse({
                'success': False,
                'error': f'会话状态为{session.status}，无法开始'
            }, status=400)

        session.status = 'working'
        session.work_start_at = timezone.now()
        session.save()

        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'status': session.status,
            'work_start_at': session.work_start_at.isoformat() if session.work_start_at else None,
            'message': '番茄钟已开始'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_POST
def api_pause_session(request, session_id):
    """API: 暂停番茄钟（开始暂离）"""
    try:
        session = get_object_or_404(TomatoSession, id=session_id)

        # 只能暂停状态为'working'的会话
        if session.status != 'working':
            return JsonResponse({
                'success': False,
                'error': f'会话状态为{session.status}，无法暂停'
            }, status=400)

        session.status = 'paused'
        session.leave_start_at = timezone.now()
        session.save()

        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'status': session.status,
            'leave_start_at': session.leave_start_at.isoformat() if session.leave_start_at else None,
            'message': '番茄钟已暂停（暂离开始）'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_POST
def api_resume_session(request, session_id):
    """API: 恢复番茄钟（结束暂离）"""
    try:
        session = get_object_or_404(TomatoSession, id=session_id)

        # 只能恢复状态为'paused'的会话
        if session.status != 'paused':
            return JsonResponse({
                'success': False,
                'error': f'会话状态为{session.status}，无法恢复'
            }, status=400)

        session.status = 'working'
        session.leave_end_at = timezone.now()
        session.save()

        # 计算本次暂离时长
        leave_duration = 0
        if session.leave_start_at and session.leave_end_at:
            leave_duration = (session.leave_end_at - session.leave_start_at).total_seconds()

        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'status': session.status,
            'leave_end_at': session.leave_end_at.isoformat() if session.leave_end_at else None,
            'leave_duration_seconds': leave_duration,
            'message': '番茄钟已恢复（暂离结束）'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_POST
def api_complete_session(request, session_id):
    """API: 完成番茄钟会话"""
    try:
        session = get_object_or_404(TomatoSession, id=session_id)

        # 只能完成状态为'working'或'paused'的会话
        if session.status not in ['working', 'paused']:
            return JsonResponse({
                'success': False,
                'error': f'会话状态为{session.status}，无法完成'
            }, status=400)

        session.status = 'completed'
        session.work_end_at = timezone.now()

        # 如果暂离开始但未结束，结束暂离
        if session.status == 'paused' and session.leave_start_at and not session.leave_end_at:
            session.leave_end_at = timezone.now()

        session.save()

        # 计算有效工作时长
        effective_seconds = session.effective_work_seconds
        effective_minutes = session.effective_work_minutes

        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'status': session.status,
            'work_end_at': session.work_end_at.isoformat() if session.work_end_at else None,
            'effective_work_seconds': effective_seconds,
            'effective_work_minutes': effective_minutes,
            'message': '番茄钟已完成'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_POST
def api_abandon_session(request, session_id):
    """API: 放弃番茄钟会话"""
    try:
        session = get_object_or_404(TomatoSession, id=session_id)

        # 只能放弃未完成的会话
        if session.status in ['completed', 'abandoned']:
            return JsonResponse({
                'success': False,
                'error': f'会话状态为{session.status}，无法放弃'
            }, status=400)

        session.status = 'abandoned'
        session.save()

        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'status': session.status,
            'message': '番茄钟已放弃'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_GET
def api_get_session(request, session_id):
    """API: 获取单个番茄钟会话详情"""
    try:
        session = get_object_or_404(TomatoSession, id=session_id)

        # 构建响应数据
        session_data = {
            'id': session.id,
            'user': session.user.username if session.user else None,
            'name': session.name,
            'planned_duration': session.planned_duration,
            'status': session.status,
            'status_display': session.get_status_display(),
            'work_start_at': session.work_start_at.isoformat() if session.work_start_at else None,
            'work_end_at': session.work_end_at.isoformat() if session.work_end_at else None,
            'leave_start_at': session.leave_start_at.isoformat() if session.leave_start_at else None,
            'leave_end_at': session.leave_end_at.isoformat() if session.leave_end_at else None,
            'effective_work_seconds': session.effective_work_seconds,
            'effective_work_minutes': session.effective_work_minutes,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
        }

        return JsonResponse({
            'success': True,
            'session': session_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_GET
def api_list_sessions(request):
    """API: 获取当前用户的番茄钟会话列表"""
    try:
        # 如果是登录用户，获取其所有会话；否则返回空列表
        if request.user.is_authenticated:
            sessions = TomatoSession.objects.filter(user=request.user).order_by('-created_at')
        else:
            sessions = TomatoSession.objects.none()

        # 限制返回数量，避免数据过多
        limit = request.GET.get('limit', 50)
        sessions = sessions[:int(limit)]

        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'id': session.id,
                'name': session.name,
                'planned_duration': session.planned_duration,
                'status': session.status,
                'status_display': session.get_status_display(),
                'effective_work_minutes': session.effective_work_minutes,
                'created_at': session.created_at.isoformat(),
            })

        # 统计信息
        total_count = sessions.count()
        completed_count = sessions.filter(status='completed').count()
        total_effective_minutes = sum(s.effective_work_minutes for s in sessions if s.effective_work_minutes)

        return JsonResponse({
            'success': True,
            'sessions': sessions_data,
            'stats': {
                'total_count': total_count,
                'completed_count': completed_count,
                'total_effective_minutes': total_effective_minutes,
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_GET
def api_stats(request):
    """API: 获取番茄钟统计信息"""
    try:
        # 如果是登录用户，统计其数据；否则返回空统计
        if request.user.is_authenticated:
            user_sessions = TomatoSession.objects.filter(user=request.user)
        else:
            user_sessions = TomatoSession.objects.none()

        # 基础统计
        total_sessions = user_sessions.count()
        completed_sessions = user_sessions.filter(status='completed').count()
        abandoned_sessions = user_sessions.filter(status='abandoned').count()

        # 时长统计
        total_effective_seconds = sum(s.effective_work_seconds for s in user_sessions)
        total_effective_minutes = round(total_effective_seconds / 60, 1)
        total_effective_hours = round(total_effective_minutes / 60, 1)

        # 平均专注时长
        avg_effective_minutes = round(total_effective_minutes / completed_sessions, 1) if completed_sessions > 0 else 0

        # 成功率
        success_rate = round(completed_sessions / total_sessions * 100, 1) if total_sessions > 0 else 0

        return JsonResponse({
            'success': True,
            'stats': {
                'total_sessions': total_sessions,
                'completed_sessions': completed_sessions,
                'abandoned_sessions': abandoned_sessions,
                'total_effective_seconds': total_effective_seconds,
                'total_effective_minutes': total_effective_minutes,
                'total_effective_hours': total_effective_hours,
                'avg_effective_minutes': avg_effective_minutes,
                'success_rate': success_rate,
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ==================== 辅助功能视图 ====================

def health_check(request):
    """健康检查端点（用于部署监控）"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'service': 'django-pomodoro-app'
    })


def csrf_token_view(request):
    """获取CSRF令牌（供前端JavaScript使用）"""
    from django.middleware.csrf import get_token
    token = get_token(request)
    return JsonResponse({'csrfToken': token})