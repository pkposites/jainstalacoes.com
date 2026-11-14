const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

window.dataLayer = window.dataLayer || [];

const WHATSAPP_NUMBER = '551150922446';

function trackConversion(eventName, extra) {
  const src = (typeof leadSource === 'object' && leadSource) || {};
  window.dataLayer.push(Object.assign({ event: eventName, lead_channel: src.channel, lead_source: src.source, lead_medium: src.medium }, extra || {}));
  if (typeof window.clarity === 'function') {
    try { window.clarity('event', eventName); window.clarity('upgrade', eventName); } catch (e) {}
  }
}

// ===================== Origem do tráfego (atribuição) =====================
// Captura tudo o que dá para saber de onde veio o visitante:
// - parâmetros UTM e IDs de clique de todas as plataformas de anúncio;
// - parâmetros dinâmicos do Meta Ads e do Google Ads (ValueTrack);
// - o site de onde a pessoa veio (busca orgânica, rede social, IA, e-mail…);
// - primeiro contato (first touch) e último contato (last touch), página de
//   entrada, páginas vistas e número da visita.
// Sem consentimento de cookies tudo fica só na aba (sessionStorage). Com o
// consentimento aceito no banner, o primeiro contato passa a ser lembrado no
// aparelho (localStorage), para atribuir quem volta dias depois.
const LEAD_SOURCE_STORAGE_KEY = 'ja_lead_source';      // último contato (sessão)
const FIRST_TOUCH_KEY = 'ja_first_touch';              // primeiro contato
const SESSION_KEY = 'ja_session';                      // entrada e páginas vistas
const VISITS_KEY = 'ja_visits';

const UTM_PARAMS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'utm_id',
  'utm_source_platform', 'utm_creative_format', 'utm_marketing_tactic'];
// Meta Ads (parâmetros de URL dinâmicos) e Google Ads (ValueTrack)
const AD_PARAMS = ['campaign_name', 'campaign_id', 'adset_name', 'adset_id', 'ad_name', 'ad_id', 'placement',
  'site_source_name', 'gad_source', 'gad_campaignid', 'campaignid', 'adgroupid', 'keyword', 'matchtype',
  'network', 'device', 'creative', 'targetid', 'loc_physical_ms', 'loc_interest_ms', 'ref', 'src'];
const CLICK_IDS = {
  gclid: 'Google Ads', gbraid: 'Google Ads', wbraid: 'Google Ads', dclid: 'Google Display & Video 360',
  fbclid: 'Meta (Facebook/Instagram)', msclkid: 'Microsoft Ads (Bing)', ttclid: 'TikTok Ads',
  li_fat_id: 'LinkedIn Ads', twclid: 'X (Twitter) Ads', epik: 'Pinterest Ads', sccid: 'Snapchat Ads',
  yclid: 'Yandex Ads', srsltid: 'Google (resultado orgânico)'
};
const LEAD_SOURCE_PARAMS = UTM_PARAMS.concat(AD_PARAMS, Object.keys(CLICK_IDS));

const REFERRER_RULES = [
  // [canal, nome, regex do domínio]
  ['IA (assistente)', 'ChatGPT', /(^|\.)(chatgpt\.com|chat\.openai\.com|openai\.com)$/],
  ['IA (assistente)', 'Perplexity', /(^|\.)perplexity\.ai$/],
  ['IA (assistente)', 'Claude', /(^|\.)claude\.ai$/],
  ['IA (assistente)', 'Gemini', /^(gemini|bard)\.google\.com$/],
  ['IA (assistente)', 'Copilot', /^copilot\.microsoft\.com$/],
  ['IA (assistente)', 'Meta AI', /(^|\.)meta\.ai$/],
  ['IA (assistente)', 'DeepSeek', /(^|\.)deepseek\.com$/],
  ['IA (assistente)', 'Grok', /(^|\.)(grok\.com|x\.ai)$/],
  ['IA (assistente)', 'Poe/You.com', /(^|\.)(poe\.com|you\.com)$/],
  ['E-mail', 'Gmail', /^mail\.google\.com$/],
  ['E-mail', 'Outlook', /(^|\.)(outlook\.live\.com|outlook\.office\.com|outlook\.office365\.com)$/],
  ['E-mail', 'Yahoo Mail', /^mail\.yahoo\./],
  ['Google Maps', 'Google Maps', /^maps\.google\./],
  ['Busca orgânica', 'Google', /(^|\.)google\.[a-z.]+$/],
  ['Busca orgânica', 'Bing', /(^|\.)bing\.com$/],
  ['Busca orgânica', 'Yahoo', /(^|\.)yahoo\.[a-z.]+$/],
  ['Busca orgânica', 'DuckDuckGo', /(^|\.)duckduckgo\.com$/],
  ['Busca orgânica', 'Ecosia', /(^|\.)ecosia\.org$/],
  ['Busca orgânica', 'Brave Search', /^search\.brave\.com$/],
  ['Busca orgânica', 'Yandex', /(^|\.)yandex\./],
  ['Busca orgânica', 'Baidu', /(^|\.)baidu\.com$/],
  ['Rede social', 'Facebook', /(^|\.)(facebook\.com|fb\.com|fb\.me)$/],
  ['Rede social', 'Instagram', /(^|\.)instagram\.com$/],
  ['Rede social', 'WhatsApp', /(^|\.)(whatsapp\.com|wa\.me)$/],
  ['Rede social', 'YouTube', /(^|\.)(youtube\.com|youtu\.be)$/],
  ['Rede social', 'TikTok', /(^|\.)tiktok\.com$/],
  ['Rede social', 'LinkedIn', /(^|\.)(linkedin\.com|lnkd\.in)$/],
  ['Rede social', 'X (Twitter)', /(^|\.)(t\.co|twitter\.com|x\.com)$/],
  ['Rede social', 'Pinterest', /(^|\.)pinterest\.[a-z.]+$/],
  ['Rede social', 'Threads', /(^|\.)threads\.(net|com)$/],
  ['Rede social', 'Reddit', /(^|\.)reddit\.com$/],
  ['Rede social', 'Telegram', /(^|\.)(t\.me|telegram\.org)$/],
  ['Rede social', 'Kwai', /(^|\.)kwai\./]
];
const PAID_MEDIUM = /^(cpc|ppc|paid|paidsearch|paid_search|paid[-_ ]?social|cpm|cpv|display|ads?|anuncio|retargeting|remarketing)$/i;

function consentGranted() {
  try { return !!(window.LeadHub && window.LeadHub.consentStatus && window.LeadHub.consentStatus() === 'granted'); }
  catch (e) { return false; }
}
function readJSON(key) {
  try {
    return JSON.parse(sessionStorage.getItem(key) || localStorage.getItem(key) || 'null');
  } catch (e) { return null; }
}
function writeJSON(key, value) {
  try { sessionStorage.setItem(key, JSON.stringify(value)); } catch (e) {}
  if (consentGranted()) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) {} }
}

function refererHost() {
  try {
    if (!document.referrer) return '';
    const host = new URL(document.referrer).hostname.replace(/^www\./, '');
    const own = location.hostname.replace(/^www\./, '');
    return host === own || host.endsWith('.' + own) || host.endsWith('jainstalacoes.com') ? '' : host;
  } catch (e) { return ''; }
}

// Classifica a visita atual. Devolve null se for navegação interna sem nada novo.
function classifyTouch(params) {
  const host = refererHost();
  const touch = { ts: new Date().toISOString(), landing_page: location.pathname, referrer: host || '' };
  LEAD_SOURCE_PARAMS.forEach((k) => { const v = params.get(k); if (v) touch[k] = v.slice(0, 200); });
  const clickKey = Object.keys(CLICK_IDS).find((k) => touch[k]);

  if (touch.utm_source) {
    touch.source = touch.utm_source;
    touch.medium = touch.utm_medium || '(não informado)';
    touch.channel = PAID_MEDIUM.test(touch.medium) || (clickKey && clickKey !== 'srsltid') ? 'Anúncio pago'
      : /e-?mail|newsletter/i.test(touch.medium) ? 'E-mail'
      : /social/i.test(touch.medium) ? 'Rede social'
      : /gmb|gbp|google[-_ ]?business|maps|local/i.test(touch.source + ' ' + touch.medium) ? 'Google Maps'
      : /qr|offline|panfleto|adesivo|carro|cartao/i.test(touch.source + ' ' + touch.medium) ? 'Offline (QR/impresso)'
      : 'Campanha (UTM)';
  } else if (clickKey && clickKey !== 'srsltid') {
    touch.channel = 'Anúncio pago';
    touch.source = CLICK_IDS[clickKey];
    touch.medium = 'cpc';
  } else if (host) {
    const rule = REFERRER_RULES.find((r) => r[2].test(host));
    touch.channel = rule ? rule[0] : 'Indicação (outro site)';
    touch.source = rule ? rule[1] : host;
    touch.medium = rule ? ({ 'Busca orgânica': 'organic', 'Rede social': 'social', 'E-mail': 'email', 'IA (assistente)': 'ai', 'Google Maps': 'maps' }[rule[0]]) : 'referral';
    if (rule && rule[1] === 'Instagram' && params.get('igshid')) touch.medium = 'social (link compartilhado)';
  } else if (clickKey === 'srsltid') {
    touch.channel = 'Busca orgânica'; touch.source = 'Google'; touch.medium = 'organic';
  } else {
    return null; // direto ou navegação interna: não sobrescreve a origem já conhecida
  }
  if (clickKey) touch.click_id_type = clickKey;
  return touch;
}

function deviceType() {
  const ua = navigator.userAgent || '';
  if (/iPad|Tablet/i.test(ua)) return 'tablet';
  return /Mobi|Android|iPhone/i.test(ua) ? 'celular' : 'computador';
}

function captureLeadSource() {
  try {
    const params = new URLSearchParams(window.location.search);
    const touch = classifyTouch(params);

    // Sessão: página de entrada, páginas vistas
    let session = readJSON(SESSION_KEY);
    try { session = JSON.parse(sessionStorage.getItem(SESSION_KEY) || 'null'); } catch (e) {}
    if (!session) {
      session = { started: new Date().toISOString(), entry_page: location.pathname, pages: 0 };
      let visits = 0;
      try { visits = parseInt(localStorage.getItem(VISITS_KEY) || '0', 10) || 0; } catch (e) {}
      session.visit_number = visits + 1;
      if (consentGranted()) { try { localStorage.setItem(VISITS_KEY, String(session.visit_number)); } catch (e) {} }
    }
    if (!captureLeadSource.counted) { session.pages += 1; captureLeadSource.counted = true; }
    try { sessionStorage.setItem(SESSION_KEY, JSON.stringify(session)); } catch (e) {}

    let last = readJSON(LEAD_SOURCE_STORAGE_KEY);
    try { last = JSON.parse(sessionStorage.getItem(LEAD_SOURCE_STORAGE_KEY) || 'null') || last; } catch (e) {}
    if (touch) { last = touch; writeJSON(LEAD_SOURCE_STORAGE_KEY, last); }
    if (!last) {
      last = { channel: 'Direto', source: '(direto)', medium: '(nenhum)', landing_page: session.entry_page, ts: session.started };
    }

    let first = readJSON(FIRST_TOUCH_KEY);
    if (!first) { first = last; writeJSON(FIRST_TOUCH_KEY, first); }
    else if (consentGranted()) { writeJSON(FIRST_TOUCH_KEY, first); }

    return Object.assign({}, last, {
      session_entry_page: session.entry_page,
      pages_viewed: session.pages,
      visit_number: session.visit_number,
      device_type: deviceType(),
      first_channel: first.channel, first_source: first.source, first_medium: first.medium,
      first_campaign: first.utm_campaign || first.campaign_name || '',
      first_landing_page: first.landing_page, first_ts: first.ts
    });
  } catch (e) {
    return {};
  }
}

function getLeadSource() {
  return captureLeadSource();
}

function sourceCampaign(s) { return s.campaign_name || s.utm_campaign || s.gad_campaignid || s.campaignid || ''; }
function sourceAd(s) { return s.ad_name || s.utm_content || s.creative || s.ad_id || ''; }

// Monta o bloco "Origem do lead:" pra mensagem do WhatsApp/CRM, mostrando
// só as linhas que tiverem valor.
function buildLeadSourceBlock(source) {
  if (!source || !source.channel) return '';
  const lines = [];
  lines.push(`Canal: ${source.channel}${source.source && source.source !== '(direto)' ? ` (${[source.source, source.medium].filter(Boolean).join(' / ')})` : ''}`);
  const campaign = sourceCampaign(source);
  if (campaign) lines.push(`Campanha: ${campaign}`);
  if (source.adset_name) lines.push(`Conjunto de anúncios: ${source.adset_name}`);
  const ad = sourceAd(source);
  if (ad) lines.push(`Anúncio: ${ad}`);
  const term = source.utm_term || source.keyword;
  if (term) lines.push(`Termo/Palavra-chave: ${term}${source.matchtype ? ` (${source.matchtype})` : ''}`);
  if (source.placement || source.site_source_name) lines.push(`Posicionamento: ${[source.site_source_name, source.placement].filter(Boolean).join(' / ')}`);
  if (source.landing_page) lines.push(`Página de entrada: ${source.landing_page}`);
  if (source.first_channel && (source.first_channel !== source.channel || source.first_source !== source.source)) {
    lines.push(`Primeiro contato: ${source.first_channel} (${source.first_source || '-'})`);
  }
  return `\n\nOrigem do lead:\n${lines.join('\n')}`;
}

// Campos achatados para o Netlify Forms (precisam existir como <input hidden> no HTML).
function leadSourceFields(s) {
  const clickKey = s.click_id_type;
  return {
    origem_canal: s.channel || '',
    origem_fonte: s.source || '',
    origem_midia: s.medium || '',
    origem_campanha: sourceCampaign(s),
    origem_anuncio: sourceAd(s),
    origem_termo: s.utm_term || s.keyword || '',
    origem_click_id: clickKey ? `${clickKey}=${s[clickKey]}` : '',
    origem_referrer: s.referrer || '',
    origem_entrada: s.landing_page || '',
    origem_primeiro_contato: s.first_channel ? `${s.first_channel} | ${s.first_source || ''} | ${s.first_medium || ''} | ${s.first_campaign || ''} | ${s.first_landing_page || ''} | ${s.first_ts || ''}` : '',
    origem_sessao: `visita ${s.visit_number || 1} | ${s.pages_viewed || 1} página(s) | ${s.device_type || ''}`,
    origem_detalhes: JSON.stringify(s).slice(0, 1800)
  };
}

// Microsoft Clarity: etiquetas de origem para filtrar gravações e mapas de calor.
function clarityCall() {
  if (typeof window.clarity === 'function') { try { window.clarity.apply(null, arguments); } catch (e) {} }
}
function tagClarity(s) {
  clarityCall('set', 'canal', s.channel || '');
  clarityCall('set', 'fonte', s.source || '');
  clarityCall('set', 'midia', s.medium || '');
  if (sourceCampaign(s)) clarityCall('set', 'campanha', sourceCampaign(s));
  if (sourceAd(s)) clarityCall('set', 'anuncio', sourceAd(s));
  if (s.utm_term || s.keyword) clarityCall('set', 'termo', s.utm_term || s.keyword);
  if (s.click_id_type) clarityCall('set', 'click_id', s.click_id_type);
  clarityCall('set', 'primeiro_canal', s.first_channel || '');
  clarityCall('set', 'pagina_entrada', s.landing_page || '');
  clarityCall('set', 'visita', String(s.visit_number || 1));
  clarityCall('set', 'pagina_tipo', (window.JA_PAGE && window.JA_PAGE.slug) || location.pathname.split('/')[1] || 'home');
}

// Consentimento do Clarity segue o banner do Lead Hub (o mesmo que libera o GTM).
function syncClarityConsent() {
  let st = 'pending';
  try { st = window.LeadHub && window.LeadHub.consentStatus ? window.LeadHub.consentStatus() : 'pending'; } catch (e) {}
  if (st === syncClarityConsent.last) return;
  syncClarityConsent.last = st;
  if (st === 'granted') {
    clarityCall('consentv2', { ad_Storage: 'granted', analytics_Storage: 'granted' });
    captureLeadSource(); // grava o primeiro contato no aparelho agora que é permitido
  } else if (st === 'denied') {
    clarityCall('consentv2', { ad_Storage: 'denied', analytics_Storage: 'denied' });
  }
}
document.addEventListener('click', (e) => {
  if (e.target.closest && e.target.closest('[data-leadhub-consent] button')) setTimeout(syncClarityConsent, 0);
}, true);
[300, 1500, 4000].forEach((ms) => setTimeout(syncClarityConsent, ms));

const leadSource = getLeadSource();
tagClarity(leadSource);
window.dataLayer.push(Object.assign({ event: 'lead_source_ready' }, {
  lead_channel: leadSource.channel, lead_source: leadSource.source, lead_medium: leadSource.medium,
  lead_campaign: sourceCampaign(leadSource), lead_ad: sourceAd(leadSource), lead_term: leadSource.utm_term || leadSource.keyword || '',
  lead_click_id_type: leadSource.click_id_type || '', lead_referrer: leadSource.referrer || '',
  lead_landing_page: leadSource.landing_page || '', lead_first_channel: leadSource.first_channel || '',
  lead_first_source: leadSource.first_source || '', lead_visit_number: leadSource.visit_number || 1
}));

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

  const message = `${PAGE.greeting}\n\nServiço: ${service}\nNome: ${name}\nWhatsApp: ${phone}${buildLeadSourceBlock(getLeadSource())}`;
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
    // Envia para o Netlify Forms. O WhatsApp abre em seguida de qualquer jeito;
    // se o registro no site falhar, avisamos e oferecemos o WhatsApp de novo.
    const netlifyRequest = fetch('/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: encodeFormData(Object.assign({ 'form-name': form.getAttribute('name'), fname: name, fphone: phone, fservice: service, fregion: region }, leadSourceFields(getLeadSource())))
    }).then((res) => {
      if (!res.ok) throw new Error('HTTP ' + res.status);
    });

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

    netlifyRequest.then(() => {
      showFormStatus('ok', 'Pedido recebido! Se o WhatsApp não abriu, toque no botão abaixo para continuar a conversa.', destino);
    }).catch((err) => {
      trackConversion('form_error', { page: PAGE.slug, error: String(err && err.message || err) });
      showFormStatus('error', 'Não conseguimos registrar seu pedido pelo site agora. Fale com a gente direto pelo WhatsApp que atendemos na hora.', destino);
    });
  });
}

function showFormStatus(kind, text, waUrl) {
  if (!form) return;
  let box = document.getElementById('formStatus');
  if (!box) {
    box = document.createElement('div');
    box.id = 'formStatus';
    box.setAttribute('role', 'status');
    box.setAttribute('aria-live', 'polite');
    form.insertAdjacentElement('afterend', box);
  }
  box.className = 'form-status form-status-' + kind;
  box.textContent = '';
  const p = document.createElement('p');
  p.textContent = text;
  const a = document.createElement('a');
  a.className = 'btn btn-primary btn-block';
  a.href = waUrl;
  a.target = '_blank';
  a.rel = 'noopener';
  a.textContent = 'Abrir o WhatsApp';
  box.appendChild(p);
  box.appendChild(a);
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
});
