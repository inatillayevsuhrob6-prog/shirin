import json
import logging
import mimetypes
import os
import re
from pathlib import Path
from decimal import Decimal
from urllib import request as urlrequest
from urllib.parse import quote_plus
from django.core import signing
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from .models import Category, Product, Customer, Order, CustomCakeOrder
from .serializers import ProductSerializer
from .text import new_uzbek_alphabet

logger=logging.getLogger(__name__)

def api_error(message,status=400):
    return JsonResponse({'error':new_uzbek_alphabet(message)},status=status)

class ProductList(ListAPIView):
    queryset=Product.objects.select_related('category').filter(available=True)
    serializer_class=ProductSerializer
    permission_classes=[AllowAny]

@csrf_protect
@require_http_methods(['POST'])
def create_order(request):
    try:
        data=json.loads(request.body)
    except json.JSONDecodeError:
        return api_error('Noto‘g‘ri JSON')
    if not data.get('items') or not data.get('phone') or not data.get('address'):
        return api_error('Telefon, manzil va mahsulotlar majburiy')
    if not isinstance(data['items'],list):
        return api_error('Savat ma’lumotlari noto‘g‘ri')
    order_items=[]
    total=Decimal('0.00')
    for entry in data['items']:
        if not isinstance(entry,dict):
            return api_error('Savat ma’lumotlari noto‘g‘ri')
        try:
            product=Product.objects.get(pk=int(entry['id']),available=True)
            quantity=int(entry.get('qty',0))
        except (KeyError,TypeError,ValueError,Product.DoesNotExist):
            return api_error('Savatdagi mahsulotlardan biri topilmadi')
        if quantity<1 or quantity>99:
            return api_error('Mahsulot miqdori noto‘g‘ri')
        unit_price=product.price
        total+=unit_price*quantity
        order_items.append({'id':product.id,'name':product.name,'price':str(unit_price),'qty':quantity})
    dedup_key=(data.get('dedup_key') or '').strip()
    if not dedup_key:
        return api_error('Xavfsizlik kaliti majburiy')
    customer=None
    if data.get('telegram_id'):
        customer,_=Customer.objects.get_or_create(telegram_id=data['telegram_id'],defaults={'phone':data['phone'],'name':data.get('name','')})
    elif data.get('phone'):
        customer,_=Customer.objects.get_or_create(phone=data['phone'],defaults={'name':data.get('name','')})
    if customer and data.get('name') and not customer.name:
        customer.name=data['name'][:120]
        customer.save(update_fields=['name'])
    with transaction.atomic():
        order,created=Order.objects.get_or_create(dedup_key=dedup_key,defaults={'customer':customer,'telegram_id':data.get('telegram_id'),'items':order_items,'total':total,'payment':data.get('payment','cash'),'phone':data['phone'],'address':data['address'],'location':data.get('location',''),'delivery_time':data.get('delivery_time',''),'note':data.get('note','')})
    if created:
        token=signing.dumps({'order_id':order.id,'dedup_key':dedup_key},salt='shirin.deep-link',compress=True)
        notified=notify_admins_order(order)
        return JsonResponse({'id':order.id,'dedup_key':order.dedup_key,'status':order.status,'items':order.items,'total':str(order.total),'admin_notified':notified,'token':token,'telegram_url':f'https://t.me/ShirinDessert_bot?start=order_{token}'},status=201)
    return JsonResponse({'id':order.id,'dedup_key':order.dedup_key,'status':order.status,'items':order.items,'total':str(order.total),'duplicate':True},status=200)

@require_http_methods(['GET'])
def order_status(request,dedup_key):
    try:
        order=Order.objects.get(dedup_key=dedup_key)
    except Order.DoesNotExist:
        return api_error('Buyurtma topilmadi',404)
    return JsonResponse({'id':order.id,'status':order.status,'status_label':order.get_status_display(),'payment':order.payment,'total':str(order.total),'created_at':order.created_at.isoformat()})

def notify_admins_order(order):
    token=os.getenv('BOT_TOKEN','')
    admin_ids=list(dict.fromkeys(['5944526629',*[value.strip() for value in os.getenv('ADMIN_TELEGRAM_IDS','').split(',') if value.strip()]]))
    recipients=admin_ids
    if not token:
        logger.error('Order notification skipped: BOT_TOKEN is not configured')
        return False
    item_lines=[]
    product_ids=[]
    for item in order.items or []:
        try:
            qty=int(item.get('qty',1))
            price=Decimal(str(item.get('price',0)))
            name=new_uzbek_alphabet(item.get('name','Mahsulot'))
            item_lines.append(f"• {name} — {qty} dona × {int(price):,} so‘m = {int(price*qty):,} so‘m".replace(',', ' '))
            product_id=int(item.get('id',0))
            if product_id:
                product_ids.append(product_id)
        except (TypeError, ValueError, ArithmeticError):
            logger.warning('Invalid item data in order %s',order.id)
    customer_name=new_uzbek_alphabet(order.customer.name if order.customer else 'Ko‘rsatilmagan')
    address=new_uzbek_alphabet(order.address)
    map_link=order.location or f"https://maps.google.com/?q={quote_plus(order.address)}"
    note=new_uzbek_alphabet(order.note or 'Yo‘q')
    delivery=new_uzbek_alphabet(order.delivery_time or 'Kelishiladi')
    telegram_id=order.telegram_id or (order.customer.telegram_id if order.customer else None)
    payment=f"💳 Karta — {int(order.total):,} so‘m" if order.payment=='card' else '💵 Naqd'
    text=(f"🔔 YANGI BUYURTMA!\n\n"
          f"👤 {customer_name}\n"
          +(f"🆔 {telegram_id}\n" if telegram_id else "")+
          f"📞 Telefon: {order.phone}\n"
          f"\n🛒 Buyurtma:\n"+'\n'.join(item_lines)+
          f"\n\n💰 Jami: {int(order.total):,} so‘m\n".replace(',', ' ')+
          f"📍 Manzil: {address}\n🗺 Xarita: {map_link}\n"
          f"💳 To‘lov: {payment}")
    if order.delivery_time:
        text+=f"\n🕒 Yetkazish: {delivery}"
    if order.note:
        text+=f"\n📝 Izoh: {note}"
    text=re.sub(r'</?b>', '', new_uzbek_alphabet(text), flags=re.IGNORECASE)
    actions={
        'new':('admin_confirm','👤 Adminga tayinlash'),
        'confirmed':('admin_baking','👩‍🍳 Tayyorlanmoqda'),
        'baking':('admin_delivery','🚚 Yetkazilmoqda'),
        'delivery':('admin_done','✅ Yetkazildi'),
    }
    keyboard_rows=[]
    if order.status in actions:
        action,label=actions[order.status]
        keyboard_rows.append([{'text':label,'callback_data':f'{action}_{order.id}'}])
    if order.status not in ('done','cancelled'):
        keyboard_rows.append([{'text':'❌ Bekor qilish','callback_data':f'admin_cancel_{order.id}'}])
    keyboard={'inline_keyboard':keyboard_rows}
    admin_sent=False
    for chat_id in recipients:
        if not telegram_request(token,'sendMessage',{'chat_id':chat_id,'text':text,'reply_markup':keyboard,'disable_web_page_preview':True}):
            continue
        if chat_id=='5944526629':
            admin_sent=True
        for product in Product.objects.filter(pk__in=product_ids):
            photo=Path(product.image_upload.path) if product.image_upload else product.image.strip()
            if not photo:
                continue
            _send_telegram_photo(
                token,chat_id,photo,
                new_uzbek_alphabet(f"🍰 {product.name} — {int(product.price):,} so‘m".replace(',', ' ')),
                order.id,
            )
        if order.payment=='card':
            card_image=Path(__file__).resolve().parent.parent/'static'/'img'/'payment-card.png'
            if card_image.is_file():
                _send_telegram_photo(token,chat_id,card_image,
                    new_uzbek_alphabet(f'💳 Karta orqali to‘lov: {int(order.total):,} so‘m'.replace(',', ' ')),order.id)
    return admin_sent

def telegram_request(token,method,payload,upload=None):
    endpoint=f'https://api.telegram.org/bot{token}/{method}'
    try:
        if upload:
            field_name,filename,content_type,content=upload
            boundary='----shirin-'+os.urandom(12).hex()
            body=bytearray()
            for key,value in payload.items():
                encoded=json.dumps(value,ensure_ascii=False) if isinstance(value,(dict,list)) else str(value)
                body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{encoded}\r\n'.encode())
            body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode())
            body.extend(content+f'\r\n--{boundary}--\r\n'.encode())
            req=urlrequest.Request(endpoint,data=bytes(body),headers={'Content-Type':f'multipart/form-data; boundary={boundary}'},method='POST')
        else:
            req=urlrequest.Request(endpoint,data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'},method='POST')
        result=json.loads(urlrequest.urlopen(req,timeout=20).read())
    except Exception as exc:
        logger.error('Telegram %s request failed: %s',method,type(exc).__name__)
        return False
    if not result.get('ok'):
        logger.error('Telegram %s rejected request: %s',method,result.get('description','unknown error'))
        return False
    return True

def _send_telegram_photo(token,chat_id,photo,caption,order_id):
    payload={'chat_id':chat_id,'caption':caption}
    try:
        if isinstance(photo,Path):
            if not photo.is_file():
                logger.warning('Image for order %s is missing: %s',order_id,photo.name)
                return False
            mime=mimetypes.guess_type(photo.name)[0] or 'application/octet-stream'
            return telegram_request(token,'sendPhoto',payload,('photo',photo.name,mime,photo.read_bytes()))
        if photo.startswith(('https://','http://')):
            return telegram_request(token,'sendPhoto',{**payload,'photo':photo})
        logger.warning('Unsupported image reference for order %s',order_id)
    except OSError as exc:
        logger.error('Could not read image for order %s: %s',order_id,type(exc).__name__)
    return False

def notify_admins_custom_cake(order,image_field):
    token=os.getenv('BOT_TOKEN','')
    admin_ids=list(dict.fromkeys(['5944526629',*[value.strip() for value in os.getenv('ADMIN_TELEGRAM_IDS','').split(',') if value.strip()]]))
    if not token:
        logger.error('Custom cake notification skipped: BOT_TOKEN is not configured')
        return False
    text=new_uzbek_alphabet(f"🎂 YANGI MAXSUS TORT BUYURTMASI\n"
          f"👤 Ism: {order.name}\n📞 Telefon: {order.phone}\n📍 Manzil: {getattr(order, 'address', '') or 'Ko‘rsatilmagan'}\n"
          f"Shakl: {order.shape}\nQavatlar: {order.layers}\nKrem: {order.cream}\n"
          f"Rang: {order.color}\nBezaklar: {order.decorations}\n"
          f"Tort ustidagi yozuv: {order.inscription or 'Yo‘q'}\n"
          f"Izoh: {order.note or 'Yo‘q'}")
    sent=False
    try:
        image_field.seek(0)
        content=image_field.read()
        filename=getattr(image_field,'name','cake.jpg').rsplit('/',1)[-1]
        mime=image_field.content_type if hasattr(image_field,'content_type') else 'image/jpeg'
        for chat_id in admin_ids:
            sent=telegram_request(token,'sendPhoto',{'chat_id':chat_id,'caption':text},
                                  ('photo',filename,mime,content)) or sent
    except Exception as exc:
        logger.error('Could not forward custom cake image: %s',type(exc).__name__)
    return sent

@csrf_protect
@require_http_methods(['POST'])
def custom_cake(request):
    required=('name','phone','address','shape','color','cream','layers')
    if any(not request.POST.get(key) for key in required):
        return JsonResponse({'error':'Ism, telefon, shakl, rang, krem va qavatlar majburiy'},status=400)
    if not request.FILES.get('image'):
        return JsonResponse({'error':'Tort uchun rasm yuklang'},status=400)
    order=CustomCakeOrder.objects.create(
        name=request.POST['name'][:120],phone=request.POST['phone'][:30],address=request.POST['address'][:300],shape=request.POST['shape'][:40],
        color=request.POST['color'][:20],cream=request.POST['cream'][:40],layers=int(request.POST['layers']),
        decorations=request.POST.get('decorations','')[:300],inscription=request.POST.get('inscription','')[:200],
        note=request.POST.get('note',''),image=request.FILES['image'])
    notified=notify_admins_custom_cake(order,request.FILES['image'])
    return JsonResponse({'id':order.id,'status':'received','admin_notified':notified,'message':'Buyurtma qabul qilindi'},status=201)

@require_http_methods(['POST'])
def deep_link(request,token):
    try:
        payload=signing.loads(token,salt='shirin.deep-link',max_age=3600)
    except signing.BadSignature:
        return JsonResponse({'error':'Link yaroqsiz yoki muddati tugagan'},status=400)
    order=get_object_or_404(Order,id=payload['order_id'])
    if order.dedup_key != payload['dedup_key'] or order.deep_link_used:
        return JsonResponse({'error':'Bu bir martalik havola allaqachon ishlatilgan'},status=409)
    order.deep_link_used=True
    order.save(update_fields=['deep_link_used'])
    return JsonResponse({'id':order.id,'items':order.items,'total':str(order.total),'payment':order.payment,'address':order.address,'phone':order.phone,'status':order.status})


def _cart_products():
    return list(Product.objects.filter(available=True).values('id', 'name', 'price'))

def home(request): return render(request,'store/home.html',{'products':Product.objects.filter(available=True)[:8], 'cart_products': _cart_products()})
def catalog(request): return render(request,'store/catalog.html',{'categories':Category.objects.all(),'products':Product.objects.filter(available=True).select_related('category'), 'cart_products': _cart_products()})
def tracking(request): return render(request,'store/tracking.html', {'cart_products': _cart_products()})
def contact(request): return render(request,'store/contact.html', {'cart_products': _cart_products()})
