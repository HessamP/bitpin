from django.utils import timezone
from .models import Score, ScoreAnomaly
import numpy as np
import datetime
from celery import shared_task


@shared_task()
def check_new_scores() -> None:
    now = timezone.now()
    last_30_mins = now - datetime.timedelta(minutes=30)
    last_24_hours = now - datetime.timedelta(minutes=24 * 60)
    newly_added_scores = Score.objects.filter(created_date__gt=last_30_mins)

    post_ids = newly_added_scores.values_list('post_id', flat=True).distinct()

    outliers_list = []
    for post_id in post_ids:
        print(post_id)
        post_last_24_scores = Score.objects.filter(
            post_id=post_id,
            created_date__gt=last_24_hours,
            created_date__lt=last_30_mins
        )
        post_last_30_mins_scores = newly_added_scores.filter(post_id=post_id)

        last_24_scores_arr = np.array(post_last_24_scores.values_list('score', flat=True))
        last_24_mean = np.mean(last_24_scores_arr)
        last_24_std = np.std(last_24_scores_arr)
        last_24_z_scores = []

        if last_24_std != 0:
            for score in last_24_scores_arr:
                last_24_z_scores.append((score - last_24_mean) / last_24_std)
        else:
            last_24_z_scores = [0] * len(last_24_scores_arr)

        last_30_mins_scores_arr = np.array(post_last_30_mins_scores.values_list('score', flat=True))
        last_30_mins_z_scores = []

        if last_24_std != 0:
            for score in last_30_mins_scores_arr:
                last_30_mins_z_scores.append((score - last_24_mean) / last_24_std)
        else:
            last_30_mins_z_scores = [0] * len(last_30_mins_scores_arr)

        print('last_30minz_scores', last_30_mins_z_scores)

        threshold = 2
        outliers = []
        for i, score in enumerate(post_last_30_mins_scores):
            if abs(last_30_mins_z_scores[i]) > threshold:
                outliers.append(score)

        for outlier in outliers:
            index = list(post_last_30_mins_scores).index(outlier)
            score_anomaly = ScoreAnomaly.objects.create(
                user=outlier.user,
                post=outlier.post,
                score=outlier.score,
                z_score=last_30_mins_z_scores[index],
                is_anomaly=True
            )
            score_anomaly.save()
        print('outlier', outliers)
        outliers_list.append({
            'post_id': post_id,
            'last_30mins_scores': list(post_last_30_mins_scores.values('id', 'score')),
            'last_24h_scores': list(post_last_24_scores.values('id', 'score')),
            'last_24h_z_scores': last_24_z_scores,
            'last_30mins_z_scores': last_30_mins_z_scores,
            'outliers_in_last_30mins': outliers
        })
        print('result', outliers_list)
