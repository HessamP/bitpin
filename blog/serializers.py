from rest_framework import serializers
from .models import Post, Score, ScoreFraudSetting


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'content',
            'created_date',
        ]


class ScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Score
        fields = [
            'user',
            'post',
            'score',
        ]


class ScoreFraudSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreFraudSetting
        fields = [
            'user',
            'post',
            'time_window',
            'forbidden_scores',
            'score_count_limit',
        ]

    def validate_score_count_limit(self, value):
        if value == 0:
            raise serializers.ValidationError("score count limit cannot be zero.")
        return value

    def validate_time_window(self, value):
        if value == 0:
            raise serializers.ValidationError("time window cannot be zero.")
        return value

    def validate_forbidden_scores(self, value):
        valid_scores = {0, 1, 2, 3, 4, 5}
        if not set(value).issubset(valid_scores):
            raise serializers.ValidationError(f"forbidden scores must be a subset of {valid_scores}.")
        return value

