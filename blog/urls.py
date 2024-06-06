from django.urls import path
from .views import PostView, ScoreView, PostViewAnnotation, PostViewOptimized, ScoreFraudSettingView, \
    ScoreFraudEnabledView

urlpatterns = [
    path('post-list/', PostView.as_view()),
    path('post-list-annotation/', PostViewAnnotation.as_view()),
    path('post-list-optimized/', PostViewOptimized.as_view()),
    path('post-score/<str:post_id>', ScoreView.as_view()),
    path('score-fraud-setting/<str:post_id>', ScoreFraudSettingView.as_view()),
    path('post-score-fe/<str:post_id>', ScoreFraudEnabledView.as_view()),
]
