from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[('store','0001_initial')]
    operations=[migrations.AddField(model_name='product',name='image_upload',field=models.ImageField(blank=True,null=True,upload_to='products/'))]
