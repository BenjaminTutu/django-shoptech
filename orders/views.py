from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
import requests
from .models import Order, OrderItem, Coupon
from cart.models import Cart

@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.all():
        messages.error(request, 'Your cart is empty!')
        return redirect('cart_detail')

    coupon = None
    if 'coupon_code' in request.session:
        coupon = Coupon.objects.filter(code=request.session['coupon_code']).first()
    total = cart.get_total()

    if coupon:
        discount_percent = Decimal(coupon.discount_percent) / Decimal(100)
        discount_amount = total * discount_percent
        final_total = total - discount_amount
    else:
        final_total = total
    return render(request, 'orders/checkout.html',
                  {'cart': cart,
                   'final_total': final_total,
                   'coupon': coupon,
                        }
                  )


@login_required
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            coupon = Coupon.objects.get(
                code__iexact=code,
                active=True
            )
            if coupon.expiry_date and coupon.expiry_date < timezone.now().date():
                messages.error(request, 'This coupon has expired!')
            else:
                request.session['coupon_code'] = code
                messages.success(request, f'Coupon applied! {coupon.discount_percent}% off')
        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code!')
    return redirect('checkout')

@login_required
def place_order(request):
    if request.method == 'POST':
        cart = get_object_or_404(Cart, user=request.user)
        if not cart.items.all():
            messages.error(request, 'Your cart is empty!')
            return redirect('cart_detail')

        address = request.POST.get('address')
        total = cart.get_total()
        coupon = None
        discount_amount = 0

        # Apply coupon if exists in session
        coupon_code = request.session.get('coupon_code')
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code, active=True)
                discount_amount = (total * coupon.discount_percent) / 100
            except Coupon.DoesNotExist:
                pass

        order = Order.objects.create(
            user=request.user,
            total_price=total,
            address=address,
            coupon=coupon,
            discount_amount=discount_amount
        )

        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )

        cart.items.all().delete()
        # Clear coupon from session
        if 'coupon_code' in request.session:
            del request.session['coupon_code']

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
    url = 'https://api.paystack.co/transaction/initialize'
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'email': request.user.email,
        'amount': int(order.get_final_total() * 100),
        'reference': f'order_{order.id}_{request.user.username}',
        'callback_url': request.build_absolute_uri(f'/orders/verify/{order.id}/'),
        # 'metadata': {
        #     'order_id': order.id,
        #     'user_id': request.user.id
        # },
        'label': f'Hi,{request.user.username} make payment for you order #{order.id}!'
    }
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    if result['status']:
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
    url = f'https://api.paystack.co/transaction/verify/{reference}'
    headers = {'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}'}
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