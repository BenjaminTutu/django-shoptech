from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import requests
from .models import Order, OrderItem
from cart.models import Cart

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.all():
        messages.error(request, 'Your cart is empty!')
        return redirect('cart_detail')
    return render(request, 'orders/checkout.html', {'cart': cart})

@login_required
def place_order(request):
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        if not cart.items.all():
            messages.error(request, 'Your cart is empty!')
            return redirect('cart_detail')

        address = request.POST.get('address')

        order = Order.objects.create(
            user=request.user,
            total_price=cart.get_total(),
            address=address
        )

        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )

        cart.items.all().delete()
        messages.success(request, f'Order #{order.id} placed successfully!')
        return redirect('order_list')
    return redirect('checkout')

@login_required
def order_list(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'Pending':
        order.status = 'Cancelled'
        order.save()
        messages.success(request, f'Order #{order.id} cancelled!')
    else:
        messages.error(request, 'Only pending orders can be cancelled!')
    return redirect('order_list')

@login_required
def pay(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status != 'Pending':
        messages.error(request, 'This order has already been paid!')
        return redirect('order_list')

    # Initialize Paystack transaction
    url = 'https://api.paystack.co/transaction/initialize'
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'email': request.user.email,
        'amount': int(order.total_price * 100),  # Paystack uses kobo/pesewas
        'reference': f'order_{order.id}_{request.user.id}',
        'callback_url': request.build_absolute_uri(f'/orders/verify/{order.id}/'),
        'metadata': {
            'order_id': order.id,
            'user_id': request.user.id
        }
    }

    response = requests.post(url, json=data, headers=headers)
    result = response.json()

    if result['status']:
        # Redirect to Paystack payment page
        return redirect(result['data']['authorization_url'])
    else:
        messages.error(request, 'Payment initialization failed. Try again.')
        return redirect('order_list')

@login_required
def verify_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    reference = request.GET.get('reference')

    if not reference:
        messages.error(request, 'Payment reference not found!')
        return redirect('order_list')

    # Verify payment with Paystack
    url = f'https://api.paystack.co/transaction/verify/{reference}'
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
    }

    response = requests.get(url, headers=headers)
    result = response.json()

    if result['status'] and result['data']['status'] == 'success':
        order.status = 'Paid'
        order.save()
        messages.success(request, f'Payment successful! Order #{order.id} is confirmed.')
        return redirect('order_detail', order_id=order.id)
    else:
        messages.error(request, 'Payment verification failed. Contact support.')
        return redirect('order_list')