import datetime
from django.utils import timezone
from rest_framework.views import APIView
from .models import Post, Score, ScoreFraudSetting, ScoreAnomaly
from .serializers import PostSerializer, ScoreSerializer, ScoreFraudSettingSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Avg, Count
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.utils.cache import get_cache_key


class PostListPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page'
    max_page_size = 10


class PostView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PostListPagination

    def get(self, request):
        user = request.user
        paginator = self.pagination_class()
        post_queryset = Post.objects.all().order_by('-created_date')
        paginated_post_queryset = paginator.paginate_queryset(post_queryset, request)

        results = []
        for post in paginated_post_queryset:
            post_id = post.id
            score_count = Score.objects.filter(post__id=post_id).count()
            score_avg = Score.objects.filter(post__id=post_id).aggregate(score_average=Avg('score'))['score_average']
            post_serialized_data = PostSerializer(post).data
            my_score = Score.objects.filter(post__id=post_id, user=user).first()
            if my_score:
                score = my_score.score
            else:
                score = None

            post_data = {
                'id': post_serialized_data['id'],
                'title': post_serialized_data['title'],
                'content': post_serialized_data['content'],
                'score_count': score_count,
                'score_avg': score_avg,
                'my_score': score
            }
            results.append(post_data)

        return paginator.get_paginated_response(results)


class ScoreView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        user = request.user
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({'message': 'post not found'}, status=status.HTTP_404_NOT_FOUND)

        allowed_keys = {'score'}
        request_keys = set(request.data.keys())
        if not request_keys.issubset(allowed_keys):
            return Response({'message': 'invalid request'},
                            status=status.HTTP_400_BAD_REQUEST)

        score = request.data.get('score')
        valid_scores = [0, 1, 2, 3, 4, 5]
        if score not in valid_scores:
            return Response({'message': 'score is not valid'}, status=status.HTTP_400_BAD_REQUEST)

        score_data = {
            'user': user.id,
            'post': post.id,
            'score': score
        }

        try:
            current_score = Score.objects.get(post=post, user=user)
            score_serializer = ScoreSerializer(current_score, data=score_data)
            score_serializer.is_valid(raise_exception=True)
            score_serializer.save()
            return Response({'message': 'score has been updated successfully'}, status=status.HTTP_200_OK)
        except Score.DoesNotExist:
            score_serializer = ScoreSerializer(data=score_data)
            score_serializer.is_valid(raise_exception=True)
            score_serializer.save()
            return Response({'message': 'score saved successfully'}, status=status.HTTP_200_OK)


class PostViewAnnotation(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PostListPagination

    def get(self, request):
        user = request.user
        paginator = self.pagination_class()

        post_queryset = Post.objects.annotate(
            score_count=Count('score'),
            score_avg=Avg('score__score')
        ).order_by('-created_date')

        paginated_post_queryset = paginator.paginate_queryset(post_queryset, request)

        results = []
        for post in paginated_post_queryset:
            post_serialized_data = PostSerializer(post).data
            my_score = post.score_set.filter(user=user).first()
            score_count = post.score_count
            score_avg = post.score_avg

            post_data = {
                'id': post_serialized_data['id'],
                'title': post_serialized_data['title'],
                'content': post_serialized_data['content'],
                'score_count': score_count,
                'score_avg': score_avg,
                'my_score': my_score.score if my_score else None
            }
            results.append(post_data)

        return paginator.get_paginated_response(results)


class PostViewOptimized(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PostListPagination

    @method_decorator(cache_page(60 * 60))
    def get(self, request):
        cache_key = get_cache_key(request)
        print('cache_key', cache_key)

        user = request.user
        paginator = self.pagination_class()

        post_queryset = Post.objects.annotate(
            score_count=Count('score'),
            score_avg=Avg('score__score')
        ).order_by('-created_date')

        post_queryset = post_queryset.prefetch_related('score_set')

        paginated_post_queryset = paginator.paginate_queryset(post_queryset, request)

        results = []
        for post in paginated_post_queryset:
            post_serialized_data = PostSerializer(post).data

            my_score = None
            for score in post.score_set.all():
                if score.user_id == user.id:
                    my_score = score
                    break

            score_count = post.score_count
            score_avg = post.score_avg

            post_data = {
                'id': post_serialized_data['id'],
                'title': post_serialized_data['title'],
                'content': post_serialized_data['content'],
                'score_count': score_count,
                'score_avg': score_avg,
                'my_score': my_score.score if my_score else None
            }
            results.append(post_data)

        return paginator.get_paginated_response(results)


class ScoreFraudSettingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        user = request.user
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({'message': 'post not found'}, status=status.HTTP_404_NOT_FOUND)

        allowed_keys = {'post', 'time_window', 'forbidden_scores', 'score_count_limit', 'user'}
        request_keys = set(request.data.keys())
        if not request_keys.issubset(allowed_keys):
            return Response({'message': 'invalid request'},
                            status=status.HTTP_400_BAD_REQUEST)

        setting_data = request.data
        setting_data['user'] = user.id
        setting_data['post'] = post_id

        try:
            current_setting = ScoreFraudSetting.objects.get(post__id=post_id)
            serialized_data = ScoreFraudSettingSerializer(current_setting, data=setting_data)
            serialized_data.is_valid(raise_exception=True)
            serialized_data.save()
            return Response({'message': 'fraud setting has been updated successfully'}, status=status.HTTP_200_OK)
        except ScoreFraudSetting.DoesNotExist:
            setting_serializer = ScoreFraudSettingSerializer(data=setting_data)
            setting_serializer.is_valid(raise_exception=True)
            setting_serializer.save()
            return Response({'message': 'score fraud settings are saved successfully'}, status=status.HTTP_201_CREATED)


class ScoreFraudEnabledView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        user = request.user
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({'message': 'post not found'}, status=status.HTTP_404_NOT_FOUND)

        allowed_keys = {'score'}
        request_keys = set(request.data.keys())
        if not request_keys.issubset(allowed_keys):
            return Response({'message': 'invalid request'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            fraud_settings = ScoreFraudSetting.objects.get(post__id=post_id)
            fraud_time_window = fraud_settings.time_window
            fraud_forbidden_scores = fraud_settings.forbidden_scores
            fraud_score_count = fraud_settings.score_count_limit

            effective_date = timezone.now() - datetime.timedelta(minutes=fraud_time_window)
            current_score_count = Score.objects.filter(post__id=post_id, created_date__gt=effective_date,
                                                       score__in=fraud_forbidden_scores).count()
            if current_score_count >= fraud_score_count:
                return Response({'message': 'currently not available, please try again later'},
                                status=status.HTTP_400_BAD_REQUEST)  # we could nego on the response message
                # and the status code
            else:
                valid_scores = [0, 1, 2, 3, 4, 5]
                score = request.data.get('score')

                if score not in valid_scores:
                    return Response({'message': 'score is not valid'}, status=status.HTTP_400_BAD_REQUEST)
                score_data = {
                    'user': user.id,
                    'post': post.id,
                    'score': score
                }
                try:
                    current_score = Score.objects.get(post=post, user=user)
                    serialized_score = ScoreSerializer(current_score, data=score_data)
                    serialized_score.is_valid(raise_exception=True)
                    current_score.save()
                    return Response({'message': 'score has been updated successfully'}, status=status.HTTP_200_OK)
                except Score.DoesNotExist:
                    score_serializer = ScoreSerializer(data=score_data)
                    score_serializer.is_valid(raise_exception=True)
                    score_serializer.save()
                    return Response({'message': 'score saved successfully'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            valid_scores = [0, 1, 2, 3, 4, 5]
            score = request.data.get('score')

            if score not in valid_scores:
                return Response({'message': 'score is not valid'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                current_score = Score.objects.get(post=post, user=user)
                current_score.score = score
                current_score.save()
                return Response({'message': 'score has been updated successfully'}, status=status.HTTP_200_OK)
            except Score.DoesNotExist:
                score_data = {
                    'user': user.id,
                    'post': post.id,
                    'score': score
                }
                score_serializer = ScoreSerializer(data=score_data)
                score_serializer.is_valid(raise_exception=True)
                score_serializer.save()
                return Response({'message': 'score saved successfully'}, status=status.HTTP_201_CREATED)

