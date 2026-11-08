from django.core.management.base import BaseCommand
from store.models import Category, Product

class Command(BaseCommand):
    help='SHIRIN tort va shirinliklar katalogini yaratadi'
    def handle(self,*args,**options):
        catalog={
            'Tortlar':[
                ('Medovik','Asli bali retsepti bo‘yicha nozik asal qatlamlari va mayin qaymoq kremi.',140000,'https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=900&q=85'),
                ('Napoleon','Yumshoq qatlamlar va klassik vanilli kremdan tayyorlangan mazali tort.',155000,'https://images.unsplash.com/photo-1558961363-fa8fdf82db35?auto=format&fit=crop&w=900&q=85'),
                ('Shokoladli tort','Boy shokoladli krem, ganash va quyuq kakao biskvitining mukammal uyg‘unligi.',170000,'https://images.unsplash.com/photo-1571115177098-24ec42ed204d?auto=format&fit=crop&w=900&q=85'),
                ('Biskvit tort','Nafis biskvit, mavsum mevalari va qaymoqli engil krem bilan.',185000,'https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?auto=format&fit=crop&w=900&q=85'),
                ('Cheesecake','Karamelli yoki mevali toppingli kremli New York cheesecake.',200000,'https://images.unsplash.com/photo-1533134242443-d4fd215305ad?auto=format&fit=crop&w=900&q=85'),
                ('Maxsus tortlar','Sizning dizayningiz bo‘yicha individual qavatlar, ranglar va bezaklar.',215000,'https://images.unsplash.com/photo-1535254973040-607b474cb50d?auto=format&fit=crop&w=900&q=85'),
            ],
            'Shirinliklar':[
                ('Ekler','Qaymoqli fondantli zamonaviy eklerlar.',110000,'https://images.unsplash.com/photo-1549931319-a545dcf3bc73?auto=format&fit=crop&w=900&q=85'),
                ('Makaron','Har xil rang va ta\'mli fransuz makaronlari.',145000,'https://images.unsplash.com/photo-1569864358642-9d1684040f1b?auto=format&fit=crop&w=900&q=85'),
                ('Cupcake','O‘ziga xos bezakli mini tortchalar.',155000,'https://images.unsplash.com/photo-1486427944299-d1955d23e34d?auto=format&fit=crop&w=900&q=85'),
            ],
        }
        for cat_name,products in catalog.items():
            cat,_=Category.objects.get_or_create(name=cat_name,defaults={'slug':cat_name.lower().replace(' ','-')})
            for index,(name,description,price,image) in enumerate(products,1):
                Product.objects.update_or_create(name=name,defaults={'category':cat,'description':description,'ingredients':'Sariyog‘, un, tuxum, qaymoq, shokolad','weight':f'{0.8 + index/20:.1f} kg','price':price,'rating':4.7+(index%4)/10,'image':image,'available':True})
        Product.objects.exclude(name__in=[item for products in catalog.values() for item in [p[0] for p in products]]).delete()
        self.stdout.write(self.style.SUCCESS('To‘liq SHIRIN katalogi tayyor'))
