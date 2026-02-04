from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class TomatoSession(models.Model):
    """核心模型：记录一个完整的番茄钟会话（包括中断）"""
    # 基础信息
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tomato_sessions')
    name = models.CharField('任务名称', max_length=255, default='专注任务')

    # 时间点记录（核心字段，用于计算）
    planned_duration = models.PositiveIntegerField('计划时长(分钟)', default=25)  # 支持未来自定义
    work_start_at = models.DateTimeField('工作开始时间', null=True, blank=True)
    work_end_at = models.DateTimeField('工作结束时间', null=True, blank=True)

    # 中断记录（解耦设计：中断作为独立记录，便于复杂统计）
    leave_start_at = models.DateTimeField('暂离开始时间', null=True, blank=True)
    leave_end_at = models.DateTimeField('暂离结束时间', null=True, blank=True)

    # 状态与元数据
    STATUS_CHOICES = [
        ('planned', '计划中'),
        ('working', '进行中'),
        ('paused', '已暂停（暂离中）'),
        ('completed', '已完成'),
        ('abandoned', '已放弃'),
    ]
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='planned')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    # 计算属性（业务逻辑封装在模型层）
    @property
    def effective_work_seconds(self):
        """计算有效工作时长（秒），排除暂离时间"""
        if not self.work_start_at:
            return 0
        # 以实际结束时间或当前时间作为计算终点
        end_time = self.work_end_at or timezone.now()
        total_seconds = (end_time - self.work_start_at).total_seconds()
        # 扣除暂离时长
        if self.leave_start_at and self.leave_end_at:
            leave_seconds = (self.leave_end_at - self.leave_start_at).total_seconds()
            total_seconds -= leave_seconds
        elif self.leave_start_at:  # 暂离开始但未结束，扣除到现在的时长
            leave_seconds = (timezone.now() - self.leave_start_at).total_seconds()
            total_seconds -= leave_seconds
        return max(total_seconds, 0)  # 确保非负

    @property
    def effective_work_minutes(self):
        """计算有效工作时长（分钟）"""
        return round(self.effective_work_seconds / 60, 1)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '番茄钟会话'
        verbose_name_plural = '番茄钟会话'

    def __str__(self):
        return f'{self.user.username} - {self.name} ({self.get_status_display()})'