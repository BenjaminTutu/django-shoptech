from django.contrib import admin
from .models import Category, Product


# class ProductAdmin(admin.ModelAdmin):
#     prepopulated_fields = {'slug': ('name',)}
#     list_display = ['name', 'price', 'stock' ,'category', ]
#     search_fields = ['name']
#     list_filter = ['category']
#     list_per_page = 10

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


# class CartAdmin(admin.ModelAdmin):

# admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)


