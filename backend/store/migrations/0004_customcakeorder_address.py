from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('store', '0003_customcakeorder')]
    operations = [migrations.AddField(model_name='customcakeorder', name='address', field=models.CharField(blank=True, max_length=300))]
