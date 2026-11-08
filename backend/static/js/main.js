const loader = document.getElementById('loader');
document.querySelectorAll('.nav-links a').forEach(link => {
  const target = `${link.getAttribute('href') || ''} ${link.textContent || ''}`.toLowerCase();
  if (target.includes('studio') || target.includes('tracking') || target.includes('kuzatuv') || target.includes('/admin/') || target.includes('tort atelyeri')) {
    link.remove();
  }
});
document.querySelectorAll('.hero-actions button,.hero-actions a').forEach(button => {
  const label = (button.textContent || '').toLocaleLowerCase('uz');
  if (button.dataset.scroll === 'studio' || label.includes('tortni bezash')) button.remove();
});
document.querySelectorAll('.studio-section,.studio-modal').forEach(section => section.remove());
const hideLoader = () => setTimeout(() => loader?.classList.add('hidden'), 350);
window.addEventListener('load', hideLoader);
document.addEventListener('DOMContentLoaded', () => setTimeout(() => {
  if (document.readyState === 'complete') hideLoader();
}, 1000));
setTimeout(hideLoader, 2500);

const cursor = document.getElementById('cursor');
window.addEventListener('mousemove', event => {
  if (!cursor) return;
  cursor.style.left = `${event.clientX}px`;
  cursor.style.top = `${event.clientY}px`;
});
document.querySelectorAll('button,a,.product-card').forEach(element => {
  element.addEventListener('mouseenter', () => cursor?.classList.add('active'));
  element.addEventListener('mouseleave', () => cursor?.classList.remove('active'));
});
document.querySelectorAll('.product-image img').forEach(image => {
  const showFallback = () => {
    if (image.dataset.fallbackApplied) return;
    image.dataset.fallbackApplied = 'true';
    image.src = 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=900&q=85';
  };
  image.addEventListener('error', showFallback);
  if (image.complete && image.naturalWidth === 0) showFallback();
});

const navToggle = document.querySelector('.nav-toggle');
const navLinks = document.querySelector('.nav-links');
navToggle?.addEventListener('click', () => navLinks?.classList.toggle('open'));

let cart = [];
try {
  cart = JSON.parse(localStorage.getItem('shirin_cart') || '[]');
  if (!Array.isArray(cart)) cart = [];
} catch {
  cart = [];
}
const money = value => `${Number(value || 0).toLocaleString('uz-UZ')} söm`;
const parsePrice = value => {
  if (typeof value === 'number') return Number.isFinite(value) ? value : 0;
  const raw = String(value || '').trim().replace(/\s/g, '').replace(',', '.');
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : 0;
};
const newAlphabet = value => String(value || '')
  .replace(/o['’‘ʻ]/gi, letter => letter[0] === letter[0].toUpperCase() ? 'Ö' : 'ö')
  .replace(/g['’‘ʻ]/gi, letter => letter[0] === letter[0].toUpperCase() ? 'Ğ' : 'ğ')
  .replace(/sh/gi, letters => letters[0] === letters[0].toUpperCase() ? 'Ş' : 'ş')
  .replace(/ch/gi, letters => letters[0] === letters[0].toUpperCase() ? 'Ç' : 'ç');
function translateVisibleText(root = document.body) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    if (node.parentElement.closest('script,style,noscript')) continue;
    node.nodeValue = newAlphabet(node.nodeValue);
  }
  root.querySelectorAll('[placeholder],[aria-label],[title],[alt]').forEach(element => {
    ['placeholder','aria-label','title','alt'].forEach(attribute => {
      if (element.hasAttribute(attribute)) element.setAttribute(attribute,newAlphabet(element.getAttribute(attribute)));
    });
  });
  const title = document.querySelector('title');
  if (title) title.textContent = newAlphabet(title.textContent);
}
translateVisibleText();
const normalizeProductName = value => String(value || '').toLocaleLowerCase('uz')
  .replace(/[oö]/g, 'o').replace(/[gğ]/g, 'g')
  .replace(/[ş]/g, 'sh').replace(/[ç]/g, 'ch')
  .replace(/[ʻʼ’‘`´']/g, '').replace(/[^\p{L}\p{N}]/gu, '');
const cartProductName = item => item.name || item.product_name || item.title || item.product?.name || '';
const cartProductId = item => item.id ?? item.product_id ?? item.productId ?? item.product?.id;
const findCartProduct = (products, item) => {
  const name = normalizeProductName(cartProductName(item));
  const productByName = name && products.find(entry => normalizeProductName(entry.name) === name);
  if (productByName) return productByName;
  const id = cartProductId(item);
  return id == null ? undefined : products.find(entry => String(entry.id) === String(id));
};
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, character => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[character]));

function restorePricesFromPage() {
  cart.forEach(item => {
    const cards = [...document.querySelectorAll('.product-card')];
    const name = normalizeProductName(cartProductName(item));
    const id = cartProductId(item);
    const card = cards.find(product => name && normalizeProductName(product.dataset.name) === name)
      || cards.find(product => id != null && String(product.dataset.id) === String(id));
    if (!card) return;
    item.id = card.dataset.id;
    item.name = card.dataset.name;
    item.price = parsePrice(card.dataset.price);
  });
}

function restorePricesFromEmbeddedCatalog() {
  const data = document.getElementById('cart-products-data');
  if (!data) return;
  try {
    const products = JSON.parse(data.textContent || '[]');
    cart.forEach(item => {
      const product = findCartProduct(products, item);
      if (!product) return;
      item.id = product.id;
      item.name = newAlphabet(product.name);
      item.price = parsePrice(product.price);
    });
  } catch (error) {
    console.warn('Mahsulot narxlarini sahifadan o‘qib bo‘lmadi.', error);
  }
}

async function restorePricesFromCatalog() {
  if (!cart.length) return;
  try {
    const response = await fetch('/api/products/');
    if (!response.ok) return;
    const products = await response.json();
    cart.forEach(item => {
      const product = findCartProduct(products, item);
      if (!product) return;
      item.id = product.id;
      item.name = newAlphabet(product.name);
      item.price = parsePrice(product.price);
    });
    saveCart();
  } catch {
    renderCart();
  }
}

function renderCart() {
  restorePricesFromEmbeddedCatalog();
  restorePricesFromPage();
  const count = cart.reduce((sum, item) => sum + Number(item.qty || 0), 0);
  document.getElementById('cartCount').textContent = count;
  const items = document.getElementById('cartItems');
  items.innerHTML = cart.length ? cart.map((item, index) => `
    <div class="cart-item">
      <div><strong>${escapeHtml(newAlphabet(item.name))}</strong>
        <small>${parsePrice(item.price) > 0 ? `${money(item.price)} × ${item.qty} = <b>${money(parsePrice(item.price) * Number(item.qty))}</b>` : 'Narx aniqlanmoqda…'}</small>
      </div>
      <div class="cart-qty">
        <button aria-label="Kamaytiriş" data-minus="${index}">−</button>
        <strong>${item.qty}</strong>
        <button aria-label="Köpaytiriş" data-plus="${index}">+</button>
        <button aria-label="Öçiriş" class="cart-remove" data-remove="${index}">×</button>
      </div>
    </div>`).join('') : '<p class="cart-empty">Savat hozir boş.</p>';
  const pricesReady = cart.every(item => parsePrice(item.price) > 0);
  const total = cart.reduce((sum, item) => sum + parsePrice(item.price) * Number(item.qty), 0);
  document.getElementById('cartTotal').textContent = pricesReady ? money(total) : 'Hisoblanmoqda…';
  document.getElementById('checkoutButton').disabled = !cart.length || !pricesReady;
}

function saveCart() {
  localStorage.setItem('shirin_cart', JSON.stringify(cart));
  renderCart();
}

restorePricesFromEmbeddedCatalog();
restorePricesFromPage();
renderCart();
restorePricesFromCatalog();

document.addEventListener('click', event => {
  const addButton = event.target.closest('.add-cart');
  if (addButton) {
    const card = addButton.closest('.product-card');
    const existing = cart.find(item => String(item.id) === String(card.dataset.id));
    if (existing) existing.qty = Number(existing.qty) + 1;
    else cart.push({ id: card.dataset.id, product_id: card.dataset.id, name: card.dataset.name, price: parsePrice(card.dataset.price), qty: 1 });
    saveCart();
    addButton.textContent = 'Qöşildi ✓';
    setTimeout(() => addButton.textContent = 'Savatga qöşish', 900);
    return;
  }
  const removeButton = event.target.closest('[data-remove]');
  if (removeButton) {
    cart.splice(Number(removeButton.dataset.remove), 1);
    saveCart();
  }
  const minusButton = event.target.closest('[data-minus]');
  if (minusButton) {
    const index = Number(minusButton.dataset.minus);
    if (cart[index].qty > 1) cart[index].qty -= 1;
    else cart.splice(index, 1);
    saveCart();
  }
  const plusButton = event.target.closest('[data-plus]');
  if (plusButton) {
    cart[Number(plusButton.dataset.plus)].qty += 1;
    saveCart();
  }
});

const drawer = document.getElementById('cartDrawer');
document.getElementById('cartButton')?.addEventListener('click', () => drawer.classList.add('open'));
document.getElementById('cartClose')?.addEventListener('click', () => drawer.classList.remove('open'));
const modal = document.getElementById('checkoutModal');
const checkoutForm = document.getElementById('checkoutForm');
document.getElementById('checkoutButton')?.addEventListener('click', () => {
  if (checkoutForm.hidden) {
    checkoutForm.hidden = false;
    checkoutForm.reset();
    document.getElementById('checkoutResult').innerHTML = '';
    modal.querySelector('h2').textContent = 'Yetkaziş manzili';
  }
  modal.classList.add('open');
});
document.querySelector('.modal-close')?.addEventListener('click', () => modal.classList.remove('open'));
modal?.addEventListener('click', event => {
  if (event.target === modal) modal.classList.remove('open');
});

function csrfToken() {
  return document.cookie.split('; ').find(value => value.startsWith('csrftoken='))?.split('=')[1] || '';
}

const cardPayment = document.getElementById('cardPayment');
document.querySelectorAll('#checkoutForm input[name="payment"]').forEach(radio => {
  radio.addEventListener('change', () => cardPayment?.classList.toggle('visible', radio.value === 'card' && radio.checked));
});
document.getElementById('getLocation')?.addEventListener('click', () => {
  const status = document.getElementById('locationStatus');
  if (!navigator.geolocation) {
    status.textContent = 'Qurilmangiz joylashuvni aniqlay olmadi.';
    return;
  }
  status.textContent = 'Joylashuv aniqlanmoqda…';
  navigator.geolocation.getCurrentPosition(({ coords }) => {
    const link = `https://maps.google.com/?q=${coords.latitude.toFixed(6)},${coords.longitude.toFixed(6)}`;
    checkoutForm.elements.namedItem('location').value = link;
    status.innerHTML = `<a href="${link}" target="_blank" rel="noopener">Joylashuv xaritada aniqlandi — ko‘rish ↗</a>`;
  }, () => {
    status.textContent = 'Joylashuv olinmadi. Manzilni qo‘lda kiriting.';
  }, { enableHighAccuracy: true, timeout: 12000 });
});

document.addEventListener('click', async event => {
  const button = event.target.closest('.copy-card');
  if (!button) return;
  const number = button.dataset.card || '';
  try {
    await navigator.clipboard.writeText(number);
  } catch {
    const input = document.createElement('textarea');
    input.value = number;
    document.body.appendChild(input);
    input.select();
    document.execCommand('copy');
    input.remove();
  }
  const label = button.querySelector('span');
  if (label) {
    label.textContent = 'Nusxa olindi ✓';
    setTimeout(() => label.textContent = 'Nusxa oliş', 1500);
  }
});

document.getElementById('checkoutForm')?.addEventListener('submit', async event => {
  event.preventDefault();
  const formElement = event.currentTarget;
  const form = new FormData(formElement);
  const total = cart.reduce((sum, item) => sum + parsePrice(item.price) * Number(item.qty), 0);
  const payload = {
    dedup_key: crypto.randomUUID(), items: cart, total,
    name: form.get('name'), phone: form.get('phone'), address: form.get('address'),
    location: form.get('location') || `https://maps.google.com/?q=${encodeURIComponent(form.get('address'))}`,
    delivery_time: form.get('delivery_time'),
    note: form.get('note'), payment: form.get('payment')
  };
  const result = document.getElementById('checkoutResult');
  const submit = formElement.querySelector('[type="submit"]');
  submit.disabled = true;
  result.textContent = 'Buyurtmangiz yuborilmoqda…';
  try {
    const response = await fetch('/api/orders/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Buyurtma yuborilmadi');
    localStorage.setItem('shirin_last_order', data.dedup_key);
    const receiptItems = (data.items || cart).map(item => `
      <li><span>${escapeHtml(newAlphabet(item.name))} <small>× ${item.qty}</small></span>
      <strong>${money(parsePrice(item.price) * Number(item.qty))}</strong></li>`).join('');
    const cardInstructions = payload.payment === 'card' ? `
      <div class="receipt-card-payment">
        <p>💳 Karta orqali tölov</p>
        <img src="/static/img/payment-card.png" alt="I. Suhrob kartasi">
        <p>Karta egasi: <strong>I. Suhrob</strong></p>
        <p>Ötkazma summasi: <strong>${money(data.total || total)}</strong></p>
        <button class="copy-card" type="button" data-card="5614956265656968">
          5614 9562 6565 6968 <span>Nusxa oliş</span>
        </button>
        <p>Tölovdan söng chekni <a href="https://t.me/ShirinUzBot" target="_blank" rel="noopener">Telegram botimizga yuboring ↗</a>.</p>
      </div>` : '';
    result.innerHTML = `
      <section class="order-receipt">
        <div class="receipt-heading"><span class="receipt-check">✓</span><div>
          <p>Buyurtmangiz qabul qilindi</p>
        </div></div>
        <ul>${receiptItems}</ul>
        <div class="receipt-total"><span>Jami tölov</span><strong>${money(data.total || total)}</strong></div>
        <p class="receipt-address"><b>Yetkaziş manzili</b><br>${escapeHtml(payload.address)}</p>
        ${payload.location ? `<a class="receipt-map" href="${escapeHtml(payload.location)}" target="_blank" rel="noopener">📍 Xarita manzilini köriş ↗</a>` : ''}
        ${cardInstructions}
        <p class="receipt-notice">${data.admin_notified ? 'ŞİRİN administratori buyurtmangizdan xabardor qilindi.' : 'Buyurtmangiz qabul qilindi. Tez orada siz bilan boğlanamiz.'}</p>
        <a class="tracking-link" href="/tracking/?key=${encodeURIComponent(data.dedup_key)}">Buyurtma holatini kuzatiş →</a>
      </section>`;
    cart = [];
    saveCart();
    formElement.reset();
    formElement.hidden = true;
    modal.querySelector('h2').textContent = 'Rahmat!';
  } catch (error) {
    result.textContent = error.message;
  } finally {
    submit.disabled = false;
  }
});

document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('[data-filter]').forEach(item => item.classList.remove('active'));
  button.classList.add('active');
  document.querySelectorAll('.product-card').forEach(card => {
    card.style.display = button.dataset.filter === 'all' || card.dataset.category === button.dataset.filter ? 'block' : 'none';
  });
}));

const trackingForm = document.getElementById('trackingForm');
let trackingRefreshTimer;
let activeTrackingKey = '';
const refreshOrderTracking = async key => {
  const statusText = document.getElementById('trackingStatus');
  try {
    const response = await fetch(`/api/orders/${encodeURIComponent(key)}/`);
    const data = await response.json();
    if (!response.ok) {
      statusText.textContent = newAlphabet(data.error || 'Buyurtma topilmadi.');
      return;
    }
    const statuses = ['new', 'confirmed', 'baking', 'delivery', 'done'];
    const current = statuses.indexOf(data.status);
    document.querySelectorAll('.steps li').forEach((item, index) => {
      item.classList.toggle('active', current >= 0 && index <= current);
      if (index === current) item.setAttribute('aria-current', 'step');
      else item.removeAttribute('aria-current');
    });
    statusText.textContent = data.status === 'cancelled'
      ? '❌ Buyurtma bekor qilindi.'
      : `Buyurtma holati: ${newAlphabet(data.status_label || data.status)}`;
  } catch {
    statusText.textContent = 'Holatni yangilab bo‘lmadi. Qayta urinib ko‘ring.';
  }
};
trackingForm?.addEventListener('submit', async event => {
  event.preventDefault();
  const key = document.getElementById('dedupKey').value;
  activeTrackingKey = key.trim();
  if (trackingRefreshTimer) clearInterval(trackingRefreshTimer);
  await refreshOrderTracking(activeTrackingKey);
  trackingRefreshTimer = setInterval(() => refreshOrderTracking(activeTrackingKey), 10000);
});
const query = new URLSearchParams(location.search);
if (query.get('key')) {
  document.getElementById('dedupKey').value = query.get('key');
  trackingForm?.requestSubmit();
}

if (window.gsap) {
  gsap.registerPlugin(ScrollTrigger);
  gsap.from('.hero-copy>*', { y: 40, opacity: 0, stagger: .12, duration: 1, ease: 'power3.out', delay: .6 });
  gsap.to('.cake-orbit', { y: -20, duration: 3, yoyo: true, repeat: -1, ease: 'sine.inOut' });
  gsap.utils.toArray('.product-card').forEach(card => gsap.from(card, {
    scrollTrigger: { trigger: card, start: 'top 85%' }, y: 80, opacity: 0, duration: .8
  }));
}
