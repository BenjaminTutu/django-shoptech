from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Category, Review, Wishlist

def product_list(request):
    query = request.GET.get('q')
    products = Product.objects.all().order_by('-created_at')
    categories = Category.objects.all()
    if query:
        products = products.filter(name__icontains=query)
    return render(request, 'products/product_list.html', {
        'products': products,
        'categories': categories,
        'query': query
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]
    reviews = product.reviews.all().order_by('-created_at')
    avg_rating = sum(r.rating for r in reviews) / reviews.count() if reviews.count() > 0 else 0
    user_reviewed = False
    user_wishlisted = False
    if request.user.is_authenticated:
        user_reviewed = Review.objects.filter(
            product=product, user=request.user
        ).exists()
        user_wishlisted = Wishlist.objects.filter(
            product=product, user=request.user
        ).exists()
    return render(request, 'products/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'user_reviewed': user_reviewed,
        'user_wishlisted': user_wishlisted,
    })

def category_products(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    categories = Category.objects.all()
    return render(request, 'products/product_list.html', {
        'products': products,
        'categories': categories,
        'current_category': category
    })

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        if Review.objects.filter(product=product, user=request.user).exists():
            messages.error(request, 'You have already reviewed this product!')
        else:
            Review.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment
            )
            messages.success(request, 'Review added successfully!')
    return redirect('product_detail', slug=product.slug)

# @login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item = Wishlist.objects.filter(
        user=request.user, product=product
    ).first()
    if wishlist_item:
        wishlist_item.delete()
        messages.success(request, f'{product.name} removed from wishlist!')
    else:
        Wishlist.objects.create(user=request.user, product=product)
        messages.success(request, f'{product.name} added to wishlist!')
    return redirect('product_detail', slug=product.slug)

# @login_required
def wishlist(request):
    items = Wishlist.objects.filter(user=request.user).order_by('-added_at')
    return render(request, 'products/wishlist.html', {'items': items})