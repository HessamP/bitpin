from django.conf import settings
from django.db import models
from uuid import uuid4
from django.core.validators import MinValueValidator, MaxValueValidator


class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False, db_index=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return self.title


class Score(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, db_index=True)
    score = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)


class ScoreFraudSetting(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, db_index=True)
    time_window = models.PositiveIntegerField()
    forbidden_scores = models.JSONField()
    score_count_limit = models.PositiveIntegerField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_date = models.DateTimeField(auto_now=True)


class ScoreAnomaly(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, db_index=True)
    score = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    is_published = models.BooleanField(default=True)
    z_score = models.FloatField()
    is_anomaly = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
