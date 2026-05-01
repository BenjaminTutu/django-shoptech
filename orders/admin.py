from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, Coupon
from products.models import Product

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price']

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total_price', 'discount_amount', 'created_at']
    list_filter = ['status']
    search_fields = ['user__username']
    list_editable = ['status']
    inlines = [OrderItemInline]
    readonly_fields = ['user', 'total_price', 'created_at']

class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'active', 'expiry_date']
    list_editable = ['active']

class LowStockProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price' , 'stock', 'category', 'stock_status']
    list_filter = ['category']
    search_fields = ['name']
    list_per_page = 10

    # def stock_status(self, obj):
    #     if obj.stock == 0:
    #         return format_html('<span style="color:red;">❌ Out of Stock</span>')
    #     elif obj.stock <= 5:
    #         return format_html('<span style="color:orange;">⚠️ Low Stock</span>')
    #     return format_html('<span style="color:green;">✅ In Stock</span>')
    # stock_status.short_description = 'Stock Status'

    def stock_status(self, obj):
        if obj.stock == 0:
            return format_html(
                '<span style="color:red;">{}</span>', '❌ Out of Stock'
            )
        elif obj.stock <= 5:
            return format_html(
                '<span style="color:orange;">{}</span>', '⚠️ Low Stock ({})'.format(obj.stock)
            )
        return format_html(
            '<span style="color:green;">{}</span>', '✅ In Stock ({})'.format(obj.stock)
        )

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('stock')

admin.site.register(Order, OrderAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(Product, LowStockProductAdmin)