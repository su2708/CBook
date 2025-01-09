from django.urls import path
from . import views

app_name = 'testplans'

urlpatterns = [
    path('', views.create_plan, name='create_plan'),
    path('user/<int:user_id>/', views.get_plan, name='get_plan'),
    # path('<int:user_id>'/, PlanListView.as_view(), name="plan")
]

