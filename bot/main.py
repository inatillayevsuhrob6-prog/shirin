import os, sys, uuid, asyncio, re
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
BASE_DIR=Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR/'.env')
sys.path.insert(0,str(BASE_DIR/'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()

from django.core import signing
from asgiref.sync import sync_to_async
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, BotCommand, FSInputFile,
    CopyTextButton)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from store.models import Category, Product, Customer, Order
from store.text import new_uzbek_alphabet

ADMIN_ID=5944526629
CARD_NUMBER='5614985747478987'
CARD_OWNER='I. Suhrob'
CARD_IMAGE=BASE_DIR/'backend'/'static'/'img'/'payment-card.png'
CARD_RECEIPT_IMAGE=BASE_DIR/'backend'/'static'/'img'/'payment-receipt.png'
bot=Bot(os.environ['BOT_TOKEN'])
dp=Dispatcher(storage=MemoryStorage())
carts={}


def main_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='🍰 Katalog'),KeyboardButton(text='🛒 Savat')],
        [KeyboardButton(text='📦 Buyurtmalarim'),KeyboardButton(text='📞 Aloqa')],
        [KeyboardButton(text='📍 Manzil yuboriş'),KeyboardButton(text='❓ Yordam')],
    ],resize_keyboard=True)


async def notify_admin(text):
    await bot.send_message(ADMIN_ID,new_uzbek_alphabet(text),disable_web_page_preview=True)


def admin_order_keyboard(order_id,status='new'):
    next_action={
        'new':('admin_confirm','👤 Adminga tayinlash'),
        'confirmed':('admin_baking','👩‍🍳 Tayyorlanmoqda'),
        'baking':('admin_delivery','🚚 Yetkazilmoqda'),
        'delivery':('admin_done','✅ Yetkazildi'),
    }
    rows=[]
    if status in next_action:
        action,label=next_action[status]
        rows.append([InlineKeyboardButton(text=label,callback_data=f'{action}_{order_id}')])
    if status not in ('done','cancelled'):
        rows.append([InlineKeyboardButton(text='❌ Bekor qilish',callback_data=f'admin_cancel_{order_id}')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def order_details(order, username=None):
    lines=[]
    for item in order.items or []:
        name=new_uzbek_alphabet(item.get('name','Mahsulot'))
        quantity=int(item.get('qty',1))
        unit=int(float(item.get('price',0)))
        lines.append(f'{name} × {quantity} — {unit*quantity:,} söm'.replace(',',' '))
    address=new_uzbek_alphabet(order.address)
    map_link=order.location or (order.address if str(order.address).startswith('http') else f'https://maps.google.com/?q={quote_plus(order.address)}')
    person=new_uzbek_alphabet('Mijoz')
    if username:
        person+=f' (@{username}) 🇺🇿'
    payment=f'💳 Karta — {int(order.total):,} so‘m'.replace(',',' ') if order.payment=='card' else '💵 Naqd'
    buyer=f'(@{username}) 🇺🇿' if username else person
    text=(f'🔔 YANGI BUYURTMA!\n\n'
          f'👤 {buyer}\n🆔 {order.telegram_id or "—"}\n\n'
          f'🛒 Buyurtma:\n'+'\n'.join(lines)+
          f'\n\n💰 Jami: {int(order.total):,} so‘m'.replace(',',' ')+
          f'\n📞 Telefon: {order.phone}\n📍 Manzil: {address}\n🗺 Xarita: {map_link}\n💳 To‘lov: {payment}')
    if order.delivery_time:
        text+=f'\n🕒 Yetkazish: {new_uzbek_alphabet(order.delivery_time)}'
    if order.note:
        text+=f'\n📝 Izoh: {new_uzbek_alphabet(order.note)}'
    return re.sub(r'</?b>', '', new_uzbek_alphabet(text), flags=re.IGNORECASE)


@dp.message(CommandStart())
async def start(message:Message,state:FSMContext):
    await state.clear()
    payload=message.text.split(maxsplit=1)[1] if message.text and len(message.text.split(maxsplit=1))>1 else ''
    if payload.startswith('order_'):
        try:
            claim=signing.loads(payload[6:],salt='shirin.deep-link',max_age=7*24*60*60)
            order=await sync_to_async(Order.objects.select_related('customer').get)(id=claim['order_id'],dedup_key=claim['dedup_key'])
            if order.telegram_id is None:
                order.telegram_id=message.from_user.id
                await sync_to_async(order.save)(update_fields=['telegram_id'])
            elif order.telegram_id!=message.from_user.id:
                await message.answer('Bu buyurtma boshqa Telegram hisobiga bog‘langan.');return
            await state.set_state(Checkout.receipt)
            await state.update_data(receipt_order_id=order.id)
            await message.answer(
                '🧾 To‘lov chekini yuboring\n\n'
                'Chek rasmini shu suhbatga yuboring. Rasm buyurtma bilan birga adminlar paneliga jonli yuboriladi.',
                reply_markup=ReplyKeyboardMarkup(keyboard=[],resize_keyboard=True))
            return
        except (signing.BadSignature,KeyError,TypeError,ValueError,Order.DoesNotExist):
            await message.answer('Buyurtma havolasi noto‘g‘ri yoki muddati o‘tgan.')
            return
    await message.answer(
        '🎂 ŞİRİN ga xuş keldiŋiz!\n'
        'Har bir ta\'mda — baxt bor!\n\n'
        'Premium şirinliklardan buyurtma beriş, savat va buyurtmalarni kuzatiş mumkin.',
        reply_markup=main_menu())


@dp.message(Command('catalog'))
@dp.message(F.text=='🍰 Katalog')
async def catalog(message:Message):
    categories=await sync_to_async(list)(Category.objects.order_by('name'))
    buttons=[[InlineKeyboardButton(text=f'📂 {c.name}',callback_data=f'cat_{c.id}')]
             for c in categories]
    buttons.append([InlineKeyboardButton(text='⬆ Narxi arzon',callback_data='sort_low'),
                    InlineKeyboardButton(text='⬇ Narxi qimmat',callback_data='sort_high')])
    buttons.append([InlineKeyboardButton(text='🔤 Nomi boyicha',callback_data='sort_name')])
    await message.answer('Kategoriya yoki saralashni tanlang:',reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.callback_query(F.data.startswith(('cat_','sort_')))
async def products(call:CallbackQuery):
    if call.data.startswith('cat_'):
        cat_id=int(call.data.split('_')[1])
        products=await sync_to_async(list)(Product.objects.filter(category_id=cat_id,available=True).order_by('name'))
        title='Mahsulotlar'
    else:
        mode=call.data
        ordering='price' if mode=='sort_low' else '-price' if mode=='sort_high' else 'name'
        products=await sync_to_async(list)(Product.objects.filter(available=True).order_by(ordering)[:30])
        title='Narxi arzonidan saralangan' if mode=='sort_low' else 'Narxi qimmatidan saralangan' if mode=='sort_high' else 'Nomi boyicha saralangan'
    buttons=[[InlineKeyboardButton(text=f'{p.name} — {int(p.price):,} söm'.replace(',',' '),callback_data=f'add_{p.id}')]
             for p in products]
    if not buttons:
        await call.message.edit_text('Bu kategoriya hozir boʻş.');return
    await call.message.edit_text(title,reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.callback_query(F.data.startswith('add_'))
async def add_product(call:CallbackQuery):
    pid=int(call.data.split('_')[1])
    product=await sync_to_async(Product.objects.get)(id=pid)
    uid=call.from_user.id
    carts.setdefault(uid,[])
    found=next((x for x in carts[uid] if x['id']==product.id),None)
    if found:
        found['qty']+=1
    else:
        carts[uid].append({'id':product.id,'name':product.name,'price':float(product.price),'qty':1})
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🛒 Savatni koʻriş',callback_data='cart')],
        [InlineKeyboardButton(text='🛍 Buyurtma beriş',callback_data='checkout')]])
    await call.answer('Savatga qöşildi',show_alert=False)
    await call.message.edit_text(f'{product.name} savatga qöşildi.',reply_markup=kb)


async def cart_text(uid):
    items=carts.get(uid,[])
    if not items:
        return 'Savat hozir boʻş.',[]
    lines=[f"• {x['name']} — {x['qty']} dona × {int(x['price']):,} söm".replace(',',' ') for x in items]
    total=sum(x['price']*x['qty'] for x in items)
    return '🛒 Savat\n\n'+'\n'.join(lines)+f'\n\nJami: {int(total):,} söm'.replace(',',' '),items,total


@dp.message(F.text=='🛒 Savat')
@dp.callback_query(F.data=='cart')
async def show_cart(event:Message|CallbackQuery):
    uid=event.from_user.id
    text,*_=await cart_text(uid)
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🛍 Buyurtma beriş',callback_data='checkout')],
        [InlineKeyboardButton(text='🗑 Savatni boʻşatiş',callback_data='clear_cart')]])
    if isinstance(event,CallbackQuery):
        await event.message.edit_text(text,reply_markup=kb)
    else:
        await event.answer(text,reply_markup=kb)


@dp.callback_query(F.data=='clear_cart')
async def clear_cart(call:CallbackQuery):
    carts[call.from_user.id]=[]
    await call.message.edit_text('Savat boʻşatildi.')


class Checkout(StatesGroup):
    name=State(); phone=State(); address=State(); note=State(); payment=State(); receipt=State()


@dp.callback_query(F.data=='checkout')
@dp.message(F.text=='Buyurtma beriş')
async def checkout(event:Message|CallbackQuery,state:FSMContext):
    uid=event.from_user.id
    items=carts.get(uid,[])
    if not items:
        if isinstance(event,CallbackQuery): await event.answer('Savat boʻş.',show_alert=True)
        else:
            await event.answer('Savat boʻş.')
        return
    target=event.message if isinstance(event,CallbackQuery) else event
    await target.answer('👤 Ismingiz va familiyangizni yuboring:',reply_markup=ReplyKeyboardMarkup(keyboard=[],resize_keyboard=True))
    await state.set_state(Checkout.name)


@dp.message(Checkout.name)
async def checkout_name(message:Message,state:FSMContext):
    await state.update_data(name=message.text.strip())
    kb=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='📞 Telefon raqamni yuboriş',request_contact=True)]],resize_keyboard=True)
    await message.answer('📞 Telefon raqamingizni yuboring:',reply_markup=kb)
    await state.set_state(Checkout.phone)


@dp.message(Checkout.phone, F.contact)
@dp.message(Checkout.phone)
async def checkout_phone(message:Message,state:FSMContext):
    phone=message.contact.phone_number if message.contact else message.text.strip()
    await state.update_data(phone=phone)
    kb=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='📍 Lokatsiyani yuboriş',request_location=True)]],resize_keyboard=True)
    await message.answer('📍 Yetkaziş manzilini yozing yoki lokatsiya yuboring:',reply_markup=kb)
    await state.set_state(Checkout.address)


@dp.message(Checkout.address, F.location)
@dp.message(Checkout.address)
async def checkout_address(message:Message,state:FSMContext):
    if message.location:
        address='Lokatsiya yuborildi'
        location=f'https://maps.google.com/?q={message.location.latitude:.6f},{message.location.longitude:.6f}'
    else:
        address=message.text.strip()
        location=''
    await state.update_data(address=address,location=location)
    await message.answer('📝 Buyurtma izohi (yoki “Yoʻq” deb yuboring):',reply_markup=ReplyKeyboardMarkup(keyboard=[],resize_keyboard=True))
    await state.set_state(Checkout.note)


@dp.message(Checkout.note)
async def checkout_note(message:Message,state:FSMContext):
    await state.update_data(note='' if message.text.strip().lower()=='yoq' else message.text.strip())
    kb=InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='💵 Naqd',callback_data='pay_cash'),
        InlineKeyboardButton(text='💳 Karta',callback_data='pay_card')]])
    await message.answer('💳 Toʻlov usulini tanlang:',reply_markup=kb)
    await state.set_state(Checkout.payment)


@dp.callback_query(Checkout.payment, F.data.startswith('pay_'))
async def finish_checkout(call:CallbackQuery,state:FSMContext):
    data=await state.get_data()
    uid=call.from_user.id
    items=carts.get(uid,[])
    if not items:
        await call.answer('Savat boʻş.',show_alert=True);return
    total=sum(x['price']*x['qty'] for x in items)
    customer,_=await sync_to_async(Customer.objects.get_or_create)(telegram_id=uid,defaults={'phone':data['phone'],'name':data['name']})
    if not customer.name:
        customer.name=data['name']
        await sync_to_async(customer.save)(update_fields=['name'])
    order=await sync_to_async(Order.objects.create)(
        dedup_key='bot-'+uuid.uuid4().hex,
        customer=customer,telegram_id=uid,items=items,total=total,
        payment='cash' if call.data=='pay_cash' else 'card',phone=data['phone'],
        address=data['address'],location=data.get('location',''),note=data['note'],status='new')
    carts[uid]=[]
    await state.clear()
    admin_text=order_details(order,call.from_user.username)
    try:
        await bot.send_message(ADMIN_ID,new_uzbek_alphabet(admin_text),
                               reply_markup=admin_order_keyboard(order.id),disable_web_page_preview=True)
        if order.payment=='card' and CARD_IMAGE.is_file():
            await bot.send_photo(ADMIN_ID,FSInputFile(CARD_IMAGE),
                                 caption=new_uzbek_alphabet(f'💳 Karta orqali to‘lov: {int(order.total):,} söm'.replace(',',' ')))
    except Exception:
        pass
    receipt=(f'✅ BUYURTMANGIZ QABUL QILINDI\n\n'
             f'📋 Buyurtma tafsiloti:\n'+ '\n'.join(
                 f"• {new_uzbek_alphabet(item['name'])} — {item['qty']} dona × {int(item['price']):,} söm = {int(item['price']*item['qty']):,} söm".replace(',',' ')
                 for item in items)+
             f'\n\n💰 Jami: {int(total):,} söm'.replace(',',' ')+
             f'\n📞 Telefon: {data["phone"]}\n📍 Manzil: {new_uzbek_alphabet(data["address"])}')
    map_link=order.location or (order.address if order.address.startswith('http') else f'https://maps.google.com/?q={quote_plus(order.address)}')
    receipt+=f'\n🗺 Xarita: {map_link}'
    await call.message.edit_text(new_uzbek_alphabet(receipt),disable_web_page_preview=True)
    if order.payment=='card':
        amount=f'{int(total):,} söm'.replace(',',' ')
        payment_text=(f'💳 Karta orqali to‘lov\n'
                      f'━━━━━━━━━━━━━━━━━━\n\n'
                      f'Quyidagi kartaga {amount} o‘tkazing 👇')
        await bot.send_message(uid,new_uzbek_alphabet(payment_text))
        if CARD_RECEIPT_IMAGE.is_file():
            await bot.send_photo(uid,FSInputFile(CARD_RECEIPT_IMAGE))
        elif CARD_IMAGE.is_file():
            await bot.send_photo(uid,FSInputFile(CARD_IMAGE),caption=new_uzbek_alphabet('To‘lovdan so‘ng chek rasmini shu botga yuboring.'))
        else:
            await bot.send_message(uid,new_uzbek_alphabet('To‘lovdan so‘ng chek rasmini shu botga yuboring.'))
        copy_keyboard=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text='📋 Karta raqamini nusxalash',copy_text=CopyTextButton(
                text=f'{CARD_NUMBER[:4]} {CARD_NUMBER[4:8]} {CARD_NUMBER[8:12]} {CARD_NUMBER[12:]}'))
        ]])
        await bot.send_message(uid,f'💳 {CARD_NUMBER[:4]} {CARD_NUMBER[4:8]} {CARD_NUMBER[8:12]} {CARD_NUMBER[12:]}\n👤 {CARD_OWNER}',reply_markup=copy_keyboard)
        keyboard=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text='✅ Tasdiqlash',callback_data=f'payment_done_{order.id}'),
            InlineKeyboardButton(text='❌ Bekor qilish',callback_data=f'payment_cancel_{order.id}')
        ]])
        await bot.send_message(uid,new_uzbek_alphabet('To‘lovni amalga oshirdingizmi?'),reply_markup=keyboard)


@dp.callback_query(F.data.startswith(('payment_done_','payment_cancel_')))
async def confirm_card_payment(call:CallbackQuery,state:FSMContext):
    _,action,order_id=call.data.rsplit('_',2)
    try:
        order=await sync_to_async(Order.objects.get)(pk=int(order_id))
    except (Order.DoesNotExist,ValueError):
        await call.answer('Buyurtma topilmadi.',show_alert=True)
        return
    if order.telegram_id!=call.from_user.id:
        await call.answer('Bu buyurtma sizga tegishli emas.',show_alert=True)
        return
    if action=='done':
        await call.message.edit_reply_markup(reply_markup=None)
        await state.set_state(Checkout.receipt)
        await state.update_data(receipt_order_id=order.id)
        await call.message.answer(new_uzbek_alphabet('🧾 To‘lov chekini rasm qilib shu yerga yuboring. Chek buyurtma bilan birga adminga boradi.'))
    else:
        order.status='cancelled'
        await sync_to_async(order.save)(update_fields=['status'])
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer('Buyurtmangiz bekor qilindi.')
        try:
            await notify_admin(f'❌ MIJOZ BUYURTMANI BEKOR QILDI\nID: {call.from_user.id}')
        except Exception:
            pass
    await call.answer()


@dp.callback_query(F.data.startswith(('admin_confirm_','admin_baking_','admin_delivery_','admin_done_','admin_cancel_','ok_','cancel_')))
async def admin_order_action(call:CallbackQuery):
    if call.from_user.id!=ADMIN_ID:
        await call.answer('Bu tugmalar faqat admin uchun.',show_alert=True)
        return
    action=call.data.rsplit('_',1)[0]
    order_id=int(call.data.rsplit('_',1)[1])
    transitions={
        'admin_confirm':('new','confirmed','👤 Buyurtma adminga tayinlandi!'),
        'ok':('new','confirmed','👤 Buyurtma adminga tayinlandi!'),
        'admin_baking':('confirmed','baking','👩‍🍳 Buyurtma tayyorlanmoqda.'),
        'admin_delivery':('baking','delivery','🚚 Buyurtma yetkazilmoqda.'),
        'admin_done':('delivery','done','✅ Buyurtma yetkazildi!'),
        'admin_cancel':(None,'cancelled','❌ Buyurtma bekor qilindi.'),
        'cancel':(None,'cancelled','❌ Buyurtma bekor qilindi.'),
    }
    expected_status,next_status,status_message=transitions[action]
    try:
        order=await sync_to_async(Order.objects.select_related('customer').get)(pk=order_id)
    except Order.DoesNotExist:
        await call.answer('Buyurtma topilmadi.',show_alert=True)
        return
    if expected_status and order.status!=expected_status:
        await call.answer('Buyurtma holati allaqachon yangilangan.',show_alert=True)
        return
    order.status=next_status
    await sync_to_async(order.save)(update_fields=['status'])
    original_text=call.message.text or call.message.caption or ''
    cleaned_text=re.sub(r'</?b>', '', original_text, flags=re.IGNORECASE)
    cleaned_text=re.sub(r'\s*№\s*\d+', '', cleaned_text)
    status_headings={
        'confirmed':'👤 BUYURTMA ADMINGA TAYINLANDI',
        'baking':'👩‍🍳 BUYURTMA TAYYORLANMOQDA',
        'delivery':'🚚 BUYURTMA YETKAZILMOQDA',
        'done':'✅ BUYURTMA YETKAZILDI',
        'cancelled':'❌ BUYURTMA BEKOR QILINDI',
    }
    lines=cleaned_text.splitlines()
    if lines:
        lines[0]=status_headings[next_status]
    else:
        lines=[status_headings[next_status]]
    cleaned_text='\n'.join(lines)
    try:
        next_keyboard=admin_order_keyboard(order.id,next_status) if next_status not in ('done','cancelled') else None
        await call.message.edit_text(new_uzbek_alphabet(cleaned_text),reply_markup=next_keyboard,disable_web_page_preview=True)
    except Exception:
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer(status_message)
    customer_id=order.telegram_id or (order.customer.telegram_id if order.customer else None)
    if customer_id:
        customer_messages={
            'confirmed':'👤 Buyurtmangiz adminga tayinlandi!',
            'baking':'👩‍🍳 Buyurtmangiz tayyorlanmoqda.',
            'delivery':'🚚 Buyurtmangiz yetkazilmoqda.',
            'done':'✅ Buyurtmangiz yetkazildi!',
            'cancelled':'❌ Buyurtmangiz bekor qilindi.',
        }
        try:
            await bot.send_message(customer_id,new_uzbek_alphabet(customer_messages[next_status]))
        except Exception:
            pass
    await call.answer()


@dp.message(Checkout.receipt, F.photo | F.document)
async def receive_payment_receipt(message:Message,state:FSMContext):
    data=await state.get_data()
    try:
        order=await sync_to_async(Order.objects.select_related('customer').get)(pk=int(data.get('receipt_order_id',0)),telegram_id=message.from_user.id)
    except (Order.DoesNotExist,TypeError,ValueError):
        await state.clear()
        await message.answer('Buyurtma topilmadi. Menyudan qayta boshlang.',reply_markup=main_menu())
        return
    if message.photo:
        uploaded_file_id=message.photo[-1].file_id
        media_kind='photo'
    elif message.document and (message.document.mime_type or '').startswith('image/'):
        uploaded_file_id=message.document.file_id
        media_kind='document'
    else:
        await message.answer('Iltimos, chekni rasm shaklida yuboring.')
        return
    proof_text=new_uzbek_alphabet(order_details(order,message.from_user.username)+'\n\n🧾 Foydalanuvchi chek rasmi. To‘lovni tekshiring.')
    keyboard=admin_order_keyboard(order.id,order.status)
    try:
        if media_kind=='photo':
            await bot.send_photo(ADMIN_ID,uploaded_file_id,caption=proof_text,reply_markup=keyboard)
        else:
            await bot.send_document(ADMIN_ID,uploaded_file_id,caption=proof_text,reply_markup=keyboard)
    except Exception:
        await message.answer('Chek rasmi adminga yuborilmadi. Iltimos, qayta yuboring.')
        return
    await state.clear()
    await message.answer('✅ Chekingiz adminga yuborildi. To‘lov tasdiqlanishini kuting.',reply_markup=main_menu())


@dp.message(Checkout.receipt)
async def ask_for_payment_receipt(message:Message,state:FSMContext):
    if message.text and message.text.strip().casefold() in {'bekor','bekor qilish'}:
        data=await state.get_data()
        try:
            order=await sync_to_async(Order.objects.get)(pk=int(data.get('receipt_order_id',0)),telegram_id=message.from_user.id)
            order.status='cancelled'
            await sync_to_async(order.save)(update_fields=['status'])
            await notify_admin(f'❌ MIJOZ BUYURTMANI BEKOR QILDI\nID: {message.from_user.id}')
            await message.answer('Buyurtmangiz bekor qilindi.',reply_markup=main_menu())
        except (Order.DoesNotExist,TypeError,ValueError):
            await message.answer('Buyurtma topilmadi.',reply_markup=main_menu())
        await state.clear()
        return
    await message.answer('Iltimos, to‘lov chekini rasm qilib yuboring. Bekor qilish uchun “bekor” deb yozing.')


@dp.message(Command('orders'))
@dp.message(F.text=='📦 Buyurtmalarim')
async def orders(message:Message):
    rows=await sync_to_async(list)(Order.objects.filter(telegram_id=message.from_user.id).order_by('-created_at')[:10])
    if not rows:
        await message.answer('Buyurtmalar hali yoʻq.',reply_markup=main_menu());return
    text='📦 Buyurtmalarim\n\n'+ '\n'.join(f'№{o.id} — {o.get_status_display()} — {int(o.total):,} söm'.replace(',',' ') for o in rows)
    await message.answer(text,reply_markup=main_menu())


@dp.message(Command('help'))
@dp.message(F.text=='❓ Yordam')
@dp.message(F.text=='📞 Aloqa')
async def help_message(message:Message):
    await message.answer('☎ ŞİRİN aloqa\n\n📞 +998 99 333 6815\n✈ @ShirinDessert_bot\n📢 Telegram kanal: https://t.me/shirinlik_00\n📍 Qarşi, Özbekiston',reply_markup=main_menu())


@dp.message(F.text=='📍 Manzil yuboriş')
async def location_menu(message:Message):
    kb=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='📍 Lokatsiyani yuboriş',request_location=True)]],resize_keyboard=True)
    await message.answer('Manzilni lokatsiya orqali yuboring:',reply_markup=kb)


@dp.message(Command('admin'))
async def admin(message:Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Bu boʻlim faqat ŞİRİN administratori uchun.');return
    await message.answer('🔐 Administrator paneli\n\n📦 Buyurtmalar:\nhttp://127.0.0.1:8001/admin/store/order/\n\nMahsulotlar:\nhttp://127.0.0.1:8001/admin/store/product/\n\nYangi buyurtmalar shu IDga Telegram orqali keladi.')


async def main():
    await bot.set_my_commands([
        BotCommand(command='start',description='Bosh menu'),BotCommand(command='catalog',description='Katalog'),
        BotCommand(command='orders',description='Buyurtmalarim'),BotCommand(command='help',description='Yordam'),
        BotCommand(command='admin',description='Administrator')])
    await dp.start_polling(bot)


if __name__=='__main__':
    asyncio.run(main())
