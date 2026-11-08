# ŞİRİN

Premium şirinliklar ekotizimi: Django, DRF, PostgreSQL, Redis, Celery, aiogram 3, GSAP va Three.js.

## Tez ishga tushuriş

```bash
cd shirin
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python backend/manage.py migrate
python backend/manage.py seed
python backend/manage.py createsuperuser
python backend/manage.py runserver 0.0.0.0:8000
```

Boshqa terminalda botni ishga tushuring:

```bash
cd shirin
source .venv/bin/activate
python bot/main.py
```

Docker bilan:

```bash
cd shirin
docker compose up --build
```

Sayt: http://localhost
Admin: http://localhost/admin/
API: http://localhost/api/products/

Bot tokeni faqat `.env` ichida saqlanadi. `.env` Gitga qo‘yilmaydi.
