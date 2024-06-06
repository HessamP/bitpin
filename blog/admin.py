from django.contrib import admin
from .models import Post, Score,ScoreFraudSetting,ScoreAnomaly


class ScoreAdmin(admin.TabularInline):
    model = Score


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    inlines = [ScoreAdmin]

    list_display = [
        'id',
        'title',
        'content',
        'created_date',
    ]
    fields = [
        'title',
        'content'
    ]

@admin.register(Score)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'post',
        'user',
        'created_date',
        'updated_date',
    ]


@admin.register(ScoreFraudSetting)
class ScoreFraudSettingAdmin(admin.ModelAdmin):
    list_display = [
        'post',
        'user',
        'time_window',
        'score_count_limit',
        'forbidden_scores',
        'created_date',
        'updated_date',
    ]
    fields = [
        'post',
        'user',
        'time_window',
        'score_count_limit',
        'forbidden_scores',
    ]

@admin.register(ScoreAnomaly)
class ScoreAnomalyAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'post',
        'score',
        'is_published',
        'z_score',
        'is_anomaly',
        'created_date',
    ]