from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('orders/place/', views.place_order, name='place_order'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('orders/pay/<int:order_id>/', views.pay, name='pay'),
    path('orders/verify/<int:order_id>/', views.verify_payment, name='verify_payment'),
]