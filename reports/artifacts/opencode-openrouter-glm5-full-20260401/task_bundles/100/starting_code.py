import django
from django.conf import settings
from django.utils import timezone

settings.configure()
def get_time_in_utc(year: int, month: int, day: int) -> timezone.datetime:
