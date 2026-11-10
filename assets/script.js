const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

window.dataLayer = window.dataLayer || [];

const WHATSAPP_NUMBER = '551150922446';

function trackConversion(eventName, extra) {
  window.dataLayer.push(Object.assign({ event: eventName }, extra || {}));
}

// Captura de origem do lead: UTMs + parâmetros dinâmicos do Meta Ads/Google Ads.
// Gravados em sessionStorage assim que aparecem na URL, pra não perder a
// origem se o usuário navegar pela página antes de preencher o formulário.
const LEAD_SOURCE_STORAGE_KEY = 'ja_lead_source';
const LEAD_SOURCE_PARAMS = [
  'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
  'campaign_name', 'campaign_id', 'adset_name', 'adset_id', 'ad_name', 'ad_id',
  'fbclid', 'gclid'
];

function captureLeadSource() {
  try {
    const stored = JSON.parse(sessionStorage.getItem(LEAD_SOURCE_STORAGE_KEY) || '{}');
    const params = new URLSearchParams(window.location.search);
    let changed = false;
    LEAD_SOURCE_PARAMS.forEach((key) => {
      const value = params.get(key);
      if (value) { stored[key] = value; changed = true; }
    });
    if (changed) sessionStorage.setItem(LEAD_SOURCE_STORAGE_KEY, JSON.stringify(stored));
    return stored;
  } catch (e) {
    return {};
  }
}

function getLeadSource() {
  const fromUrl = captureLeadSource();
  if (Object.keys(fromUrl).length > 0) return fromUrl;
  try {
    return JSON.parse(sessionStorage.getItem(LEAD_SOURCE_STORAGE_KEY) || '{}');
  } catch (e) {
    return {};
  }
}

// Monta o bloco "Origem do lead:" pra mensagem do WhatsApp/CRM, mostrando
// só as linhas que tiverem valor.
function buildLeadSourceBlock(source) {
  const lines = [];
  if (source.utm_source || source.utm_medium) {
    lines.push(`Canal: ${[source.utm_source, source.utm_medium].filter(Boolean).join(' / ')}`);
  }
  const campaign = source.campaign_name || source.utm_campaign;
  if (campaign) lines.push(`Campanha: ${campaign}`);
  if (source.adset_name) lines.push(`Conjunto de anúncios: ${source.adset_name}`);
  const ad = source.ad_name || source.utm_content;
  if (ad) lines.push(`Anúncio: ${ad}`);
  if (source.utm_term) lines.push(`Termo/Público: ${source.utm_term}`);
  if (source.fbclid) lines.push('Origem: Meta Ads (Facebook/Instagram)');
  if (source.gclid) lines.push('Origem: Google Ads');

  if (lines.length === 0) return '';
  return `\n\nOrigem do lead:\n${lines.join('\n')}`;
}

const leadSource = getLeadSource();

document.querySelectorAll('a[href^="tel:"]').forEach(link => {
  link.addEventListener('click', () => trackConversion('phone_click', { link_location: link.closest('section, header')?.id || link.className }));
});

// Cada página define seus serviços em window.JA_PAGE (ver <script> inline no HTML).
const PAGE = window.JA_PAGE || { services: [], greeting: 'Olá! Gostaria de solicitar um atendimento.' };
const services = PAGE.services || [];

const carousel = document.getElementById('carousel');
const dotsWrap = document.getElementById('dots');

if (carousel) {
  const cards = Array.from(carousel.querySelectorAll('.card'));

  cards.forEach((_, i) => {
    const dot = document.createElement('span');
    dot.className = 'dot' + (i === 0 ? ' active' : '');
    dot.addEventListener('click', () => {
      cards[i].scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
    });
    dotsWrap.appendChild(dot);
  });
  const dots = Array.from(dotsWrap.children);

  function updateActiveDot() {
    const center = carousel.scrollLeft + carousel.offsetWidth / 2;
    let closest = 0;
    let minDist = Infinity;
    cards.forEach((card, i) => {
      const dist = Math.abs((card.offsetLeft + card.offsetWidth / 2) - center);
      if (dist < minDist) { minDist = dist; closest = i; }
    });
    dots.forEach((d, i) => d.classList.toggle('active', i === closest));
  }
  carousel.addEventListener('scroll', () => {
    window.requestAnimationFrame(updateActiveDot);
  });

  document.querySelector('.car-prev').addEventListener('click', () => {
    carousel.scrollBy({ left: -280, behavior: 'smooth' });
  });
  document.querySelector('.car-next').addEventListener('click', () => {
    carousel.scrollBy({ left: 280, behavior: 'smooth' });
  });

  const modalOverlay = document.getElementById('modalOverlay');
  const modalIcon = document.getElementById('modalIcon');
  const modalTitle = document.getElementById('modalTitle');
  const modalText = document.getElementById('modalText');
  const modalCta = document.getElementById('modalCta');

  function openModal(index) {
    const s = services[index];
    modalIcon.textContent = s.icon;
    modalTitle.textContent = s.title;
    modalText.textContent = s.text;
    const msg = encodeURIComponent(`Olá! Gostaria de solicitar o serviço: ${s.title}`);
    modalCta.href = `https://wa.me/${WHATSAPP_NUMBER}?text=${msg}`;
    modalOverlay.classList.add('open');
    trackConversion('service_modal_open', { service_name: s.title });
  }
  function closeModal() {
    modalOverlay.classList.remove('open');
  }

  cards.forEach(card => {
    card.addEventListener('click', () => openModal(Number(card.dataset.service)));
  });
  document.getElementById('modalClose').addEventListener('click', closeModal);
  modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) closeModal();
  });
}

const reviewsOverlay = document.getElementById('reviewsOverlay');
if (reviewsOverlay) {
  document.getElementById('openReviews').addEventListener('click', () => {
    reviewsOverlay.classList.add('open');
    trackConversion('reviews_modal_open');
  });
  document.getElementById('reviewsClose').addEventListener('click', () => reviewsOverlay.classList.remove('open'));
  reviewsOverlay.addEventListener('click', (e) => {
    if (e.target === reviewsOverlay) reviewsOverlay.classList.remove('open');
  });
}

// Lead Hub: captura serviço + nome + WhatsApp antes de abrir a conversa, em todo link de WhatsApp
const leadGateOverlay = document.getElementById('leadGateOverlay');
const leadGateForm = document.getElementById('leadGateForm');
const leadService = document.getElementById('leadService');
const leadName = document.getElementById('leadName');
const leadPhone = document.getElementById('leadPhone');
let pendingWhatsApp = null;

function maskPhone(value) {
  const digits = value.replace(/\D/g, '').slice(0, 11);
  if (digits.length <= 2) return digits;
  if (digits.length <= 7) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
}
if (leadPhone) leadPhone.addEventListener('input', () => {
  leadPhone.value = maskPhone(leadPhone.value);
});

function openLeadGate(url, location) {
  pendingWhatsApp = { url, location };
  leadGateOverlay.classList.add('open');
}
function closeLeadGate() {
  leadGateOverlay.classList.remove('open');
}
if (leadGateOverlay) {
  document.getElementById('leadGateClose').addEventListener('click', closeLeadGate);
  leadGateOverlay.addEventListener('click', (e) => {
    if (e.target === leadGateOverlay) closeLeadGate();
  });
}

if (leadGateForm) leadGateForm.addEventListener('submit', (e) => {
  e.preventDefault();
  if (!pendingWhatsApp) return;
  const service = leadService.value;
  const name = leadName.value.trim();
  const phone = leadPhone.value.trim();
  if (!service || !name || !phone) return;

  const message = `${PAGE.greeting}\n\nServiço: ${service}\nNome: ${name}\nWhatsApp: ${phone}`;
  const baseUrl = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`;

  window.LeadHub?.set({ 'Serviço': service });
  window.LeadHub?.identify({ name, phone });
  const destino = window.LeadHub ? window.LeadHub.whatsappUrl(baseUrl) : baseUrl;

  trackConversion('whatsapp_click', { link_location: pendingWhatsApp.location, service_type: service, page: PAGE.slug });

  window.open(destino, '_blank', 'noopener');
  closeLeadGate();
  leadGateForm.reset();
  pendingWhatsApp = null;
});

document.querySelectorAll('a[href*="wa.me"]').forEach(link => {
  if (!leadGateOverlay) return;
  link.addEventListener('click', (e) => {
    e.preventDefault();
    const location = link.closest('section, header, .fab-whatsapp')?.id || link.className;
    openLeadGate(link.href, location);
  });
});

function encodeFormData(data) {
  return Object.keys(data)
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(data[key])}`)
    .join('&');
}

const form = document.getElementById('contactForm');
if (form) {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('fname').value.trim();
    const phone = document.getElementById('fphone').value.trim();
    const service = document.getElementById('fservice').value;
    const region = document.getElementById('fregion').value.trim();

    // Envia os dados para o Netlify Forms, para consulta rápida no painel do Netlify
    fetch('/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: encodeFormData({ 'form-name': form.getAttribute('name'), fname: name, fphone: phone, fservice: service, fregion: region })
    }).catch(() => {});

    const source = getLeadSource();
    const message = `${PAGE.greeting}\n\nNome: ${name}\nTelefone: ${phone}\nServiço: ${service}\nRegião: ${region}${buildLeadSourceBlock(source)}`;
    const url = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`;

    window.LeadHub?.identify({ name, phone });
    const destino = window.LeadHub ? window.LeadHub.whatsappUrl(url) : url;

    trackConversion('form_submit', { service_type: service, region: region, page: PAGE.slug });

    // Se houver Meta Pixel instalado nesta LP, dispara o Lead com a
    // campanha/anúncio detectados na URL/sessão.
    if (typeof fbq === 'function') {
      fbq('track', 'Lead', {
        content_name: source.campaign_name || source.utm_campaign || 'Formulário de contato',
        ad_name: source.ad_name || source.utm_content || undefined
      });
    }

    window.open(destino, '_blank', 'noopener');
  });
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
});
