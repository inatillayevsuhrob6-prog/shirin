from rest_framework import serializers
from .models import Product, Category
class CategorySerializer(serializers.ModelSerializer):
    class Meta: model=Category; fields=('id','name','slug')
class ProductSerializer(serializers.ModelSerializer):
    category=CategorySerializer(read_only=True)
    image=serializers.SerializerMethodField()
    class Meta: model=Product; fields=('id','name','description','ingredients','weight','price','rating','image','available','category')
    def get_image(self,obj):
        return obj.display_image
