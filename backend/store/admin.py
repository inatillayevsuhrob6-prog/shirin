from django.contrib import admin
from .models import Category,Product,Customer,Order,PromoCode,CustomCakeOrder
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin): list_display=('name','slug')
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display=('name','category','price','rating','available')
    list_display_links=('name',)
    list_editable=('price','available')
    list_filter=('category','available')
    search_fields=('name','description')
    ordering=('category__name','name')
    fieldsets=((None,{'fields':('category','name','description','ingredients','weight','price','rating','available')}),('Rasm',{'fields':('image_upload','image')}))
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin): list_display=('name','phone','bonus_points','birthday')
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display=('id','phone','total','status','payment','created_at')
    list_display_links=('id','phone')
    list_editable=('status',)
    list_filter=('status','payment','created_at')
    search_fields=('id','phone','address','dedup_key')
    ordering=('status','-created_at')
@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin): list_display=('code','percent','active')

@admin.register(CustomCakeOrder)
class CustomCakeOrderAdmin(admin.ModelAdmin):
    list_display=('name','phone','address','shape','layers','status','created_at')
    list_filter=('status','shape','layers')
    search_fields=('name','phone','inscription')
    readonly_fields=('created_at',)
