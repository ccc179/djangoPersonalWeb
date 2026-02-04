from django.contrib import admin
from .models import TomatoSession

@admin.register(TomatoSession)
class TomatoSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'status', 'planned_duration', 'effective_work_minutes', 'created_at')
    list_filter = ('status', 'user', 'created_at')
    search_fields = ('name', 'user__username')
    readonly_fields = ('effective_work_seconds', 'effective_work_minutes') # 计算字段只读
    fieldsets = (
        ('基本信息', {'fields': ('user', 'name', 'planned_duration', 'status')}),
        ('时间记录', {'fields': ('work_start_at', 'work_end_at', 'leave_start_at', 'leave_end_at')}),
        ('统计信息', {'fields': ('effective_work_minutes',)}),
    )