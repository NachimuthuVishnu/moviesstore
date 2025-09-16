from django import template
from movies.models import ReviewReport

register = template.Library()

@register.filter(name='exclude_reported')
def exclude_reported(reviews, user):
    if user is None or not getattr(user, 'is_authenticated', False):
        return reviews
    reported_ids = ReviewReport.objects.filter(user=user).values_list('review_id', flat=True)
    return reviews.exclude(id__in=reported_ids)

@register.filter(name='exclude_reported_any')
def exclude_reported_any(reviews):
    reported_any_ids = ReviewReport.objects.values_list('review_id', flat=True)
    return reviews.exclude(id__in=reported_any_ids)


