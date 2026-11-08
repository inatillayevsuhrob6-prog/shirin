from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name=models.CharField(max_length=120)
    slug=models.SlugField(unique=True)
    def __str__(self): return self.name

class Product(models.Model):
    category=models.ForeignKey(Category,on_delete=models.CASCADE,related_name='products')
    name=models.CharField(max_length=160)
    description=models.TextField()
    ingredients=models.TextField(blank=True)
    weight=models.CharField(max_length=50,default='1 kg')
    price=models.DecimalField(max_digits=10,decimal_places=2)
    rating=models.DecimalField(max_digits=3,decimal_places=1,default=5.0)
    image=models.URLField(blank=True)
    image_upload=models.ImageField(upload_to='products/',blank=True,null=True)
    available=models.BooleanField(default=True)
    @property
    def display_image(self):
        if self.image_upload:
            return self.image_upload.url
        return self.image
    def __str__(self): return self.name

class Customer(models.Model):
    telegram_id=models.BigIntegerField(unique=True,null=True,blank=True)
    phone=models.CharField(max_length=30)
    name=models.CharField(max_length=120,blank=True)
    bonus_points=models.PositiveIntegerField(default=0)
    birthday=models.DateField(null=True,blank=True)
    def __str__(self): return self.name or self.phone

class Order(models.Model):
    STATUS_CHOICES=[('new','Yangi'),('confirmed','Adminga tayinlandi'),('baking','Tayyorlanmoqda'),('delivery','Yetkazilmoqda'),('done','Yetkazildi'),('cancelled','Bekor qilindi')]
    PAYMENT_CHOICES=[('cash','Naqd'),('card','Karta')]
    dedup_key=models.CharField(max_length=80,unique=True)
    customer=models.ForeignKey(Customer,on_delete=models.SET_NULL,null=True,blank=True,related_name='orders')
    telegram_id=models.BigIntegerField(null=True,blank=True)
    items=models.JSONField(default=list)
    total=models.DecimalField(max_digits=12,decimal_places=2)
    payment=models.CharField(max_length=20,choices=PAYMENT_CHOICES,default='cash')
    phone=models.CharField(max_length=30)
    address=models.CharField(max_length=300)
    location=models.CharField(max_length=120,blank=True)
    delivery_time=models.CharField(max_length=80,blank=True)
    note=models.TextField(blank=True)
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default='new')
    deep_link_used=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'#{self.id} {self.total} so\'m'

class PromoCode(models.Model):
    code=models.CharField(max_length=40,unique=True)
    percent=models.PositiveSmallIntegerField(default=10)
    active=models.BooleanField(default=True)

class CustomCakeOrder(models.Model):
    name=models.CharField(max_length=120)
    phone=models.CharField(max_length=30)
    address=models.CharField(max_length=300,blank=True)
    shape=models.CharField(max_length=40,default='dumaloq')
    color=models.CharField(max_length=20,default='#f4d7a1')
    cream=models.CharField(max_length=40,default='Vanilli')
    layers=models.PositiveSmallIntegerField(default=2)
    decorations=models.CharField(max_length=300,blank=True)
    inscription=models.CharField(max_length=200,blank=True)
    image=models.ImageField(upload_to='custom-cakes/')
    note=models.TextField(blank=True)
    status=models.CharField(max_length=20,default='new')
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} — {self.phone}'
