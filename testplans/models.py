from django.db import models
from django.conf import settings

class TestPlan(models.Model):
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="testplans"
    )
    test_name = models.CharField(max_length=50)
    test_date = models.CharField(max_length=50)
    test_place = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
