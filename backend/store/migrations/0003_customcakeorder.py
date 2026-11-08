from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[('store','0002_product_image_upload')]
    operations=[migrations.CreateModel(name='CustomCakeOrder',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('name',models.CharField(max_length=120)),('phone',models.CharField(max_length=30)),('shape',models.CharField(default='dumaloq',max_length=40)),('color',models.CharField(default='#f4d7a1',max_length=20)),('cream',models.CharField(default='Vanilli',max_length=40)),('layers',models.PositiveSmallIntegerField(default=2)),('decorations',models.CharField(blank=True,max_length=300)),('inscription',models.CharField(blank=True,max_length=200)),('image',models.ImageField(upload_to='custom-cakes/')),('note',models.TextField(blank=True)),('status',models.CharField(default='new',max_length=20)),('created_at',models.DateTimeField(auto_now_add=True))])]
