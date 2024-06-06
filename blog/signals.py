from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Post


@receiver(post_save, sender=Post)
@receiver(post_delete, sender=Post)
def invalidate_post_cache(instance, sender, **kwargs):
    created = kwargs.get('created', None)
    if created is not None:
        print('post_save signal triggered')
    else:
        print('post_delete signal triggered')
    # needs to find the key dynamically
    cache.delete(
        'views.decorators.cache.cache_page..GET.8977436da8072f4decae6f73ba4e495b.65330eb47d0175f264fdb29633829c0b.en-us.UTC')