#!/usr/bin/env python3
"""Gera as páginas estáticas do site J.A Instalações.

Uso:  python3 tools/build.py
Edite os textos em PAGES abaixo e rode o script; os arquivos index.html de cada
pasta são reescritos. Os estilos ficam em assets/styles.css e o comportamento
(WhatsApp, formulário, carrossel, Lead Hub, GTM) em assets/script.js.
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://jainstalacoes.com"
PHONE = "551150922446"
PHONE_FMT = "(11) 5092-2446"
GTM = "GTM-M7ZGPMRT"
LEADHUB_KEY = "pk_a7a9316b735740da9eaf41651eeba41a"
LEADHUB_PRIV = f"https://leadinghub.netlify.app/privacidade/{LEADHUB_KEY}"
ADDRESS = "Rua Arnaldo Magniccaro, 827 - Vila Gea, São Paulo - SP, 04691-060"
MAPS_Q = "Rua+Arnaldo+Magniccaro,+827+-+Vila+Gea,+S%C3%A3o+Paulo+-+SP,+04691-060"
CNPJ = "65.380.889/0001-25"
RATING, REVIEWS_COUNT = "4.1", "87"

WA_SVG = '<svg viewBox="0 0 24 24" width="{s}" height="{s}" fill="currentColor" aria-hidden="true"><path d="M12.04 2c-5.5 0-9.96 4.46-9.96 9.96 0 1.76.46 3.48 1.34 5L2 22l5.2-1.36a9.94 9.94 0 0 0 4.84 1.23h.01c5.5 0 9.96-4.46 9.96-9.96S17.54 2 12.04 2zm5.83 14.24c-.24.68-1.4 1.3-1.93 1.38-.5.08-1.11.11-1.79-.11a15.7 15.7 0 0 1-1.6-.6c-2.82-1.22-4.65-4.06-4.79-4.25-.14-.19-1.15-1.53-1.15-2.92 0-1.39.73-2.07.99-2.35.26-.28.56-.35.75-.35h.55c.18 0 .42-.07.65.5.24.58.82 2 .89 2.14.07.14.12.31.02.5-.09.19-.14.31-.28.47-.14.16-.29.36-.42.48-.14.14-.28.29-.12.57.16.28.71 1.17 1.53 1.9 1.05.94 1.94 1.23 2.22 1.37.28.14.44.12.6-.07.16-.19.68-.79.86-1.06.18-.28.36-.23.6-.14.24.09 1.55.73 1.81.86.26.14.44.2.5.32.07.12.07.68-.17 1.36z"/></svg>'
TEL_SVG = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.4 0 .8-.3 1.1l-2.2 2.1z"/></svg>'

# Avaliações reais do Google Maps (perfil da empresa).
REVIEWS_ALL = [
    ("O atendimento do caça vazamentos foi excelente! O técnico foi muito educado e profissional. Resolveu o problema, cobrou o acordado! Recomendo a empresa!", "Pablo Mozer", "hid"),
    ("Atendimento rápido e prático, gostei muito e recomendo... o técnico é gente boa demais.", "Luiz Carlos Gomes Silva", "geral"),
    ("Meu marceneiro furou o cano da água quente do meu prédio, tivemos que fechar todos os registros e meus encanadores não conseguiram achar ninguém. Recorri ao Google e a J.A prontamente me atendeu, em duas horas tinha resolvido o problema. Ótimo serviço.", "Jose Ulisses de Almeida", "hid"),
    ("Vieram na mesma hora e foram extremamente educados desde o início, no atendimento telefônico quanto no presencial. Serviço limpo e eficiente. Valeu pelo valor cobrado. Mais do que recomendo.", "Daniel Jones", "geral"),
    ("Uma ótima pessoa. Execução do serviço ótima. A empresa tem um ótimo ser humano.", "Antonio Cunha", "geral"),
]

NAV = [("/", "Início"), ("/hidraulica/", "Hidráulica"), ("/eletrica/", "Elétrica"), ("/telhadista/", "Telhados")]

STEPS = [
    ("A gente escuta", "Você conta o que precisa pelo WhatsApp ou telefone. Entendemos o problema e orientamos sobre o serviço."),
    ("Tudo bem combinado", "Escopo, valores e agendamento alinhados antes de começar. Sem surpresas."),
    ("Cuidado do início ao fim", "Serviço com nota fiscal e garantia, e respeito pela sua casa ou pelo seu negócio."),
]

PAGES = {
    "home": {
        "path": "", "slug": "home", "body_class": "page-home",
        "title": "J.A Instalações | Eletricistas, encanadores e telhadistas em São Paulo",
        "description": "Serviços elétricos, hidráulicos e de telhados em São Paulo, SP. Atendimento rápido para residências, prédios e comércios. Solicite seu orçamento pelo WhatsApp.",
        "schema_type": "HomeAndConstructionBusiness",
        "eyebrow": "Elétrica · Hidráulica · Telhados",
        "h1": "Seu problema, nossa solução: elétrica, hidráulica e telhado em São Paulo",
        "sub": "Um só contato para cuidar da sua casa, prédio ou comércio. Atendimento rápido, nota fiscal e garantia.",
        "hero_img": True, "hero_icon": "",
        "badges": ["⚡ Atendimento urgente", "🧾 Nota fiscal e garantia", f"⭐ {RATING} no Google ({REVIEWS_COUNT} avaliações)"],
        "marquee": "Elétrica, hidráulica e telhados em toda grande São Paulo · Faça o seu orçamento hoje mesmo!",
        "wa_text": "Olá! Gostaria de solicitar um orçamento.",
        "greeting": "Olá! Gostaria de solicitar um orçamento.",
        "services": [],
        "options": ["Hidráulica / Encanador", "Elétrica / Eletricista", "Telhado / Telhadista", "Mais de um serviço"],
        "reviews": "all",
        "footer_tag": "Elétrica, hidráulica e telhados • Residências, prédios e comércios • São Paulo - SP",
        "about": "prestadora de serviços de elétrica, hidráulica e telhados",
    },
    "hidraulica": {
        "path": "hidraulica/", "slug": "hidraulica", "body_class": "page-hidraulica",
        "title": "J.A Instalações | Encanador em São Paulo",
        "description": "J.A Instalações - Encanador profissional em São Paulo. Consertos urgentes, desentupimentos e detecção de vazamentos em residências e prédios. Atendimento via WhatsApp.",
        "schema_type": "Plumber",
        "eyebrow": "Encanador de confiança em São Paulo",
        "h1": "Manutenção e conserto hidráulico para residências e prédios",
        "sub": "Atendimento rápido e serviço garantido. Custo de visita técnica sujeito a análise do caso e deslocamento.",
        "hero_img": True, "hero_icon": "",
        "badges": ["📍 Visita técnica sujeita a análise e deslocamento", "⚡ Atendimento urgente", f"⭐ {RATING} no Google ({REVIEWS_COUNT} avaliações)"],
        "marquee": "Atendimento rápido em toda grande São Paulo · Faça o seu orçamento hoje mesmo!",
        "wa_text": "Olá! Preciso de um encanador.",
        "greeting": "Olá! Gostaria de solicitar um atendimento.",
        "services": [
            ("🚨", "Encanador urgente", "Bombeiro hidráulico 24h para emergências", "Atendimento de emergência para vazamentos, entupimentos e problemas hidráulicos que não podem esperar. Nossa equipe se desloca rapidamente até residências e prédios em São Paulo para resolver o problema com agilidade e segurança."),
            ("🔧", "Consertos urgentes", "Reparos rápidos e eficientes", "Reparos em torneiras, registros, caixas d'água, aquecedores e tubulações. Diagnóstico rápido e conserto feito com peças de qualidade, evitando retrabalho e novos problemas no futuro."),
            ("🚿", "Desentupimentos", "Pias, ralos, vasos e tubulações", "Desentupimento de pias, ralos, vasos sanitários, caixas de gordura e tubulações em geral. Usamos equipamentos adequados para resolver o entupimento sem danificar a estrutura hidráulica."),
            ("💧", "Detecção de vazamentos", "Identificação precisa sem quebra-quebra", "Localização precisa de vazamentos ocultos em paredes, pisos e tubulações, sem necessidade de quebra-quebra desnecessário. Economize tempo e dinheiro com um diagnóstico certeiro."),
        ],
        "options": ["Encanador urgente", "Consertos urgentes", "Desentupimento", "Detecção de vazamentos", "Outro"],
        "reviews": "all",
        "footer_tag": "Encanador profissional • Residências e prédios • São Paulo - SP",
    },
    "eletrica": {
        "path": "eletrica/", "slug": "eletrica", "body_class": "page-eletrica",
        "title": "J.A Instalações | Eletricista em São Paulo",
        "description": "J.A Instalações - Eletricista profissional em São Paulo. Instalações e reparos elétricos, tomadas, iluminação, quadros e disjuntores em residências, prédios e comércios. Atendimento via WhatsApp.",
        "schema_type": "Electrician",
        "eyebrow": "Eletricista de confiança em São Paulo",
        "h1": "Instalações e reparos elétricos com segurança para sua casa ou empresa",
        "sub": "Da tomada que parou de funcionar à instalação completa. Visita técnica sujeita a análise do caso e deslocamento.",
        "hero_img": False, "hero_icon": "⚡",
        "badges": ["📍 Visita técnica sujeita a análise e deslocamento", "⚡ Atendimento urgente", f"⭐ {RATING} no Google ({REVIEWS_COUNT} avaliações)"],
        "marquee": "Eletricista em toda grande São Paulo · Faça o seu orçamento hoje mesmo!",
        "wa_text": "Olá! Preciso de um eletricista.",
        "greeting": "Olá! Gostaria de solicitar um atendimento de elétrica.",
        "services": [
            ("🚨", "Eletricista urgente", "Queda de energia e curto-circuito", "Atendimento rápido para falta de energia, disjuntor que desarma, cheiro de queimado ou curto-circuito. Diagnóstico seguro para resolver o problema e proteger sua família e seu imóvel."),
            ("🔌", "Instalações e reparos", "Fiação, pontos novos e adequações", "Instalações elétricas novas, troca de fiação antiga, novos pontos de energia e reparos em geral, sempre com material de qualidade e cuidado em cada conexão."),
            ("💡", "Tomadas e iluminação", "Tomadas, interruptores e luminárias", "Troca e instalação de tomadas, interruptores, chuveiros, luminárias, lustres e spots de LED. Serviço limpo, rápido e bem acabado."),
            ("🧰", "Quadros e disjuntores", "Montagem, troca e balanceamento", "Montagem e troca de quadros de distribuição, disjuntores e DR, balanceamento de circuitos e identificação correta, para mais segurança e menos desarmes."),
        ],
        "options": ["Eletricista urgente", "Instalações e reparos", "Tomadas e iluminação", "Quadros e disjuntores", "Outro"],
        "reviews": "geral",
        "footer_tag": "Eletricista profissional • Residências, prédios e comércios • São Paulo - SP",
    },
    "telhadista": {
        "path": "telhadista/", "slug": "telhadista", "body_class": "page-telhadista",
        "title": "J.A Instalações | Telhadista em São Paulo",
        "description": "J.A Instalações - Telhadista em São Paulo. Reparo e troca de telhas, manutenção de telhados, calhas, rufos e infiltrações em residências, prédios e comércios. Atendimento via WhatsApp.",
        "schema_type": "RoofingContractor",
        "eyebrow": "Telhadista de confiança em São Paulo",
        "h1": "Reparo e manutenção de telhados, calhas e infiltrações",
        "sub": "Um telhado bem cuidado protege tudo o que está embaixo dele. Visita técnica sujeita a análise do caso e deslocamento.",
        "hero_img": False, "hero_icon": "🏠",
        "badges": ["📍 Visita técnica sujeita a análise e deslocamento", "🌧️ Goteira? Atendimento rápido", f"⭐ {RATING} no Google ({REVIEWS_COUNT} avaliações)"],
        "marquee": "Telhadista em toda grande São Paulo · Faça o seu orçamento hoje mesmo!",
        "wa_text": "Olá! Preciso de um telhadista.",
        "greeting": "Olá! Gostaria de solicitar um atendimento de telhado.",
        "services": [
            ("🌧️", "Goteiras e infiltrações", "Atendimento rápido em dias de chuva", "Localização e correção de goteiras e infiltrações vindas do telhado, evitando manchas, mofo e danos ao forro, às paredes e aos móveis."),
            ("🏠", "Reparo e troca de telhas", "Telhas quebradas, soltas ou deslocadas", "Substituição de telhas quebradas, trincadas ou deslocadas, revisão da cumeeira e ajuste do alinhamento para o telhado voltar a escoar a água corretamente."),
            ("🛠️", "Manutenção de telhados", "Revisão preventiva e limpeza", "Revisão completa do telhado, limpeza, verificação da estrutura e das vedações. A manutenção preventiva evita problemas maiores e caros no futuro."),
            ("🪣", "Calhas e rufos", "Instalação, limpeza e vedação", "Instalação, troca, limpeza e vedação de calhas, rufos e condutores, garantindo que a água da chuva seja escoada sem transbordar ou infiltrar."),
        ],
        "options": ["Goteiras e infiltrações", "Reparo e troca de telhas", "Manutenção de telhados", "Calhas e rufos", "Outro"],
        "reviews": "geral",
        "footer_tag": "Telhadista profissional • Residências, prédios e comércios • São Paulo - SP",
    },
}

E = html.escape


def wa(text):
    from urllib.parse import quote
    return f"https://wa.me/{PHONE}?text={quote(text)}"


def head(p, canonical, title, description):
    schema = {
        "@context": "https://schema.org",
        "@type": p.get("schema_type", "HomeAndConstructionBusiness"),
        "name": "J.A Instalações",
        "image": f"{SITE}/assets/logo.png",
        "telephone": f"+{PHONE}",
        "priceRange": "$$",
        "url": canonical,
        "address": {"@type": "PostalAddress", "streetAddress": "Rua Arnaldo Magniccaro, 827",
                    "addressLocality": "São Paulo", "addressRegion": "SP",
                    "postalCode": "04691-060", "addressCountry": "BR"},
        "areaServed": "São Paulo, SP",
        "aggregateRating": {"@type": "AggregateRating", "ratingValue": RATING, "reviewCount": REVIEWS_COUNT},
    }
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{E(title)}</title>
<meta name="description" content="{E(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/assets/avatar.png">
<meta name="theme-color" content="#0a2540">
<link rel="icon" type="image/png" href="/assets/logo.png">
<script type="application/ld+json">
{json.dumps(schema, ensure_ascii=False, indent=2)}
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/styles.css">
<!-- Google Consent Mode (default: negado até aceite) -->
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('consent', 'default', {{
  ad_storage: 'denied',
  analytics_storage: 'denied',
  ad_user_data: 'denied',
  ad_personalization: 'denied'
}});
</script>
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{GTM}');</script>
<!-- End Google Tag Manager -->
<!-- Lead Hub -->
<script src="https://leadinghub.netlify.app/tracker.js" data-key="{LEADHUB_KEY}" data-consent="banner" async></script>
<!-- End Lead Hub -->
</head>
<body class="{p['body_class']}">
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
"""


def header(current, contact_href="#contato"):
    links = "\n".join(
        f'      <a href="{h}"{" aria-current=\"page\"" if h == current else ""}>{E(t)}</a>' for h, t in NAV)
    return f"""
<header class="site-header">
  <div class="container header-inner">
    <a class="logo" href="/">
      <img src="/assets/logo.png" alt="J.A Instalações" class="logo-badge" width="38" height="38">
      <span class="logo-text">J.A Instalações</span>
    </a>
    <nav class="main-nav" aria-label="Navegação principal">
{links}
    </nav>
    <a href="{contact_href}" class="btn btn-header">Solicitar orçamento</a>
  </div>
  <nav class="subnav" aria-label="Serviços">
{links}
  </nav>
</header>
"""


def hero(p):
    visual = ('<img src="/assets/avatar.png" alt="Profissional J.A Instalações" class="hero-avatar" width="96" height="96">'
              if p["hero_img"] else f'<div class="hero-icon" aria-hidden="true">{p["hero_icon"]}</div>')
    badges = "\n".join(f'      <span class="badge">{E(b)}</span>' for b in p["badges"])
    m = E(p["marquee"])
    return f"""
<section class="hero">
  <div class="container hero-inner">
    {visual}
    <p class="eyebrow">{E(p['eyebrow'])}</p>
    <h1>{E(p['h1'])}</h1>
    <p class="hero-sub">{E(p['sub'])}</p>
    <div class="hero-actions">
      <a class="btn btn-primary btn-lg" href="{E(wa(p['wa_text']))}" target="_blank" rel="noopener">
        {WA_SVG.format(s=20)}
        WhatsApp
      </a>
      <a class="btn btn-outline btn-lg" href="tel:+{PHONE}">
        {TEL_SVG}
        Ligar agora
      </a>
    </div>
    <div class="hero-badges">
{badges}
    </div>
  </div>
  <div class="hero-marquee">
    <div class="hero-marquee-track">
      <span>{m}</span>
      <span aria-hidden="true">{m}</span>
    </div>
  </div>
</section>
<div class="hero-accent-bar" aria-hidden="true"></div>
"""


def services_section(p):
    cards = "\n".join(f"""        <div class="card" data-service="{i}" role="button" tabindex="0">
          <div class="card-icon">{ic}</div>
          <h3>{E(t)}</h3>
          <p>{E(short)}</p>
        </div>""" for i, (ic, t, short, _) in enumerate(p["services"]))
    return f"""
<section class="section services" id="servicos">
  <div class="container">
    <h2>Nossos serviços</h2>
    <p class="section-sub">Toque em um serviço para ver detalhes</p>

    <div class="carousel-wrap">
      <button class="car-nav car-prev" aria-label="Anterior">‹</button>
      <div class="carousel" id="carousel">
{cards}
      </div>
      <button class="car-nav car-next" aria-label="Próximo">›</button>
    </div>
    <div class="dots" id="dots"></div>
  </div>
</section>

<div class="modal-overlay" id="modalOverlay">
  <div class="modal" role="dialog" aria-modal="true">
    <button class="modal-close" id="modalClose" aria-label="Fechar">×</button>
    <div class="modal-icon" id="modalIcon"></div>
    <h3 id="modalTitle"></h3>
    <p id="modalText"></p>
    <a class="btn btn-primary" id="modalCta" target="_blank" rel="noopener">Falar no WhatsApp</a>
  </div>
</div>
"""


def areas_section():
    return """
<section class="section" id="servicos">
  <div class="container">
    <h2>Um só contato. Várias soluções.</h2>
    <p class="section-sub">Escolha o serviço que o seu espaço precisa</p>
    <div class="areas">
      <a class="area-card area-hid" href="/hidraulica/">
        <div class="area-top"><div class="area-emoji">🚿</div><div><p class="area-kicker">Tudo no seu fluxo</p><h3>Encanadores</h3></div></div>
        <div class="area-body">
          <p>Vazamentos e imprevistos têm solução. Mais tranquilidade para a sua rotina.</p>
          <ul><li>Encanador urgente</li><li>Desentupimentos</li><li>Detecção de vazamentos</li></ul>
          <span class="area-link">Ver serviços de hidráulica →</span>
        </div>
      </a>
      <a class="area-card area-ele" href="/eletrica/">
        <div class="area-top"><div class="area-emoji">⚡</div><div><p class="area-kicker">Energia com segurança</p><h3>Eletricistas</h3></div></div>
        <div class="area-body">
          <p>Da tomada que parou de funcionar à instalação elétrica. Cuidado em cada conexão.</p>
          <ul><li>Instalações e reparos elétricos</li><li>Tomadas, interruptores e iluminação</li><li>Quadros e disjuntores</li></ul>
          <span class="area-link">Ver serviços de elétrica →</span>
        </div>
      </a>
      <a class="area-card area-tel" href="/telhadista/">
        <div class="area-top"><div class="area-emoji">🏠</div><div><p class="area-kicker">Proteção de cima a baixo</p><h3>Telhadistas</h3></div></div>
        <div class="area-body">
          <p>Um telhado bem cuidado faz toda a diferença. Proteja o que é importante para você.</p>
          <ul><li>Reparos e troca de telhas</li><li>Manutenção de telhados</li><li>Calhas, rufos e infiltrações</li></ul>
          <span class="area-link">Ver serviços de telhado →</span>
        </div>
      </a>
    </div>
  </div>
</section>
"""


def steps_section():
    items = "\n".join(f"""      <div class="step"><div class="step-num">{i}</div><h3>{E(t)}</h3><p>{E(d)}</p></div>"""
                      for i, (t, d) in enumerate(STEPS, 1))
    return f"""
<section class="section">
  <div class="container">
    <h2>Como funciona</h2>
    <p class="section-sub">Menos dor de cabeça, mais tranquilidade</p>
    <div class="steps">
{items}
    </div>
  </div>
</section>
"""


def reviews_section(p):
    revs = REVIEWS_ALL if p["reviews"] == "all" else [r for r in REVIEWS_ALL if r[2] == "geral"]
    items = "\n".join(f"""      <div class="review-item">
        <p class="review-stars">★★★★★</p>
        <p class="review-text">{E(t)}</p>
        <p class="review-author">{E(a)} · Google</p>
      </div>""" for t, a, _ in revs)
    summary = f"""<div class="review-summary">
      <span class="stars">★★★★☆</span>
      <span class="review-score">{RATING}</span>
      <span class="review-source">Google Maps · {REVIEWS_COUNT} avaliações</span>
    </div>"""
    return f"""
<section class="section reviews">
  <div class="container">
    <h2>Avaliações</h2>
    {summary}
    <p class="section-sub">Clientes satisfeitos com nosso atendimento</p>
    <button class="btn btn-outline" id="openReviews">Ver avaliações</button>
  </div>
</section>

<div class="modal-overlay" id="reviewsOverlay">
  <div class="modal modal-reviews" role="dialog" aria-modal="true">
    <button class="modal-close" id="reviewsClose" aria-label="Fechar">×</button>
    {summary}
    <div class="review-list">
{items}
    </div>
    <a class="btn btn-primary btn-lg btn-block" href="{E(wa('Olá! Vi as avaliações e gostaria de solicitar um atendimento.'))}" target="_blank" rel="noopener" id="reviewsCta">Falar no WhatsApp</a>
    <a class="review-external-link" href="https://share.google/j6rluZMPSI7rXktm3" target="_blank" rel="noopener">Ver todas as avaliações no Google Maps ↗</a>
  </div>
</div>
"""


def options_html(opts):
    return "\n".join(f'          <option value="{E(o)}">{E(o)}</option>' for o in opts)


def lead_gate(p):
    return f"""
<div class="modal-overlay" id="leadGateOverlay">
  <div class="modal" role="dialog" aria-modal="true">
    <button class="modal-close" id="leadGateClose" aria-label="Fechar">×</button>
    <div class="online-badge"><span class="online-dot"></span> Atendimento online agora</div>
    <div class="modal-icon">💬</div>
    <h3>Fale agora com nossa equipe sobre o seu problema!</h3>
    <p class="trust-line">✔️ Serviços com nota fiscal e garantia, pagamento facilitado</p>
    <form id="leadGateForm" class="form" style="text-align:left;">
      <label>
        O que você está precisando?
        <select id="leadService" required>
          <option value="" disabled selected>Selecione um serviço</option>
{options_html(p['options'])}
        </select>
      </label>
      <label>
        Nome
        <input type="text" id="leadName" required placeholder="Seu nome" autocomplete="name">
      </label>
      <label>
        WhatsApp com DDD
        <input type="tel" id="leadPhone" required placeholder="(11) 91234-5678" inputmode="numeric" autocomplete="tel">
      </label>
      <button type="submit" class="btn btn-primary btn-lg btn-block">Continuar para o WhatsApp</button>
      <p class="lead-consent">Ao continuar, você concorda em ser contatado pelo WhatsApp. Veja a <a href="/privacidade/">Política de privacidade</a>.</p>
    </form>
  </div>
</div>
"""


def contact_section(p):
    return f"""
<section class="section contact" id="contato">
  <div class="container">
    <h2>Solicite seu atendimento</h2>
    <p class="section-sub">Preencha o formulário e fale conosco pelo WhatsApp</p>

    <form class="form" id="contactForm" method="POST" name="contato-{p['slug']}" data-netlify="true" netlify-honeypot="bot-field">
      <input type="hidden" name="form-name" value="contato-{p['slug']}">
      <p class="hp-field"><label>Não preencher: <input name="bot-field"></label></p>
      <label>
        Nome
        <input type="text" id="fname" name="fname" required placeholder="Seu nome completo" autocomplete="name">
      </label>
      <label>
        Telefone / WhatsApp para retorno
        <input type="tel" id="fphone" name="fphone" required placeholder="(11) 90000-0000" autocomplete="tel">
      </label>
      <label>
        Tipo de serviço
        <select id="fservice" name="fservice" required>
          <option value="" disabled selected>Selecione um serviço</option>
{options_html(p['options'])}
        </select>
      </label>
      <label>
        Região de SP
        <input type="text" id="fregion" name="fregion" required placeholder="Ex: Zona Sul, Moema, etc.">
      </label>
      <button type="submit" class="btn btn-primary btn-lg btn-block">
        {WA_SVG.format(s=20)}
        Enviar via WhatsApp
      </button>
    </form>

    <div class="direct-contacts">
      <a href="https://wa.me/{PHONE}" target="_blank" rel="noopener">📱 WhatsApp: {PHONE_FMT}</a>
      <a href="tel:+{PHONE}">☎️ Telefone: {PHONE_FMT}</a>
    </div>
  </div>
</section>
"""


def cross_section(current):
    links = [("/hidraulica/", "🚿 Hidráulica"), ("/eletrica/", "⚡ Elétrica"), ("/telhadista/", "🏠 Telhados")]
    items = "\n".join(f'      <a href="{h}">{t}</a>' for h, t in links if h != current)
    return f"""
<section class="section cross">
  <div class="container">
    <h2>Precisa de outro serviço?</h2>
    <p class="section-sub">A J.A Instalações também cuida de</p>
    <div class="cross-links">
{items}
    </div>
  </div>
</section>
"""


def location_section():
    return f"""
<section class="section location">
  <div class="container">
    <h2>Onde estamos</h2>
    <p class="section-sub">{E(ADDRESS)}</p>
    <div class="map-embed">
      <iframe
        src="https://maps.google.com/maps?q={MAPS_Q}&amp;output=embed"
        width="100%"
        height="300"
        style="border:0;"
        allowfullscreen=""
        loading="lazy"
        referrerpolicy="no-referrer-when-downgrade"
        title="Localização J.A Instalações no Google Maps">
      </iframe>
    </div>
  </div>
</section>
"""


def footer(p, current):
    links = "\n".join(f'      <a href="{h}">{E(t)}</a>' for h, t in NAV + [("/privacidade/", "Política de Privacidade")])
    fab = "" if p is None else f"""
<a class="fab-whatsapp" href="{E(wa(p['wa_text']))}" target="_blank" rel="noopener" aria-label="Falar no WhatsApp">
  {WA_SVG.format(s=28)}
</a>
"""
    tag = p["footer_tag"] if p else PAGES["home"]["footer_tag"]
    return f"""
<footer class="site-footer">
  <div class="container">
    <div class="logo footer-logo">
      <img src="/assets/logo.png" alt="J.A Instalações" class="logo-badge" width="38" height="38">
      <span class="logo-text">J.A Instalações</span>
    </div>
    <p>{E(tag)}</p>
    <nav class="footer-nav" aria-label="Rodapé">
{links}
    </nav>
    <p class="footer-meta">CNPJ: {CNPJ}</p>
    <p class="footer-meta">
      <a href="https://www.google.com/maps/search/?api=1&amp;query={MAPS_Q}" target="_blank" rel="noopener">📍 {E(ADDRESS)}</a>
    </p>
    <p class="footer-meta">
      <a href="{LEADHUB_PRIV}" target="_blank" rel="noopener">Privacidade do Lead Hub</a>
    </p>
    <p class="footer-copy">© <span id="year"></span> J.A Instalações. Todos os direitos reservados.</p>
  </div>
</footer>
{fab}"""


def page_config(p):
    cfg = {"slug": p["slug"], "greeting": p["greeting"],
           "services": [{"icon": ic, "title": t, "text": txt} for ic, t, _, txt in p["services"]]}
    return f"<script>window.JA_PAGE = {json.dumps(cfg, ensure_ascii=False)};</script>\n<script src=\"/assets/script.js\"></script>\n</body>\n</html>\n"


def build_landing(key):
    p = PAGES[key]
    current = "/" + p["path"]
    canonical = f"{SITE}/{p['path']}"
    out = head(p, canonical, p["title"], p["description"]) + header(current) + hero(p)
    if key == "home":
        out += areas_section() + steps_section()
    else:
        out += services_section(p) + steps_section()
    out += lead_gate(p) + reviews_section(p) + contact_section(p)
    if key != "home":
        out += cross_section(current)
    out += location_section() + footer(p, current) + page_config(p)
    target = ROOT / p["path"] / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(out, encoding="utf-8")
    print("ok", target.relative_to(ROOT))


PRIVACY_BODY = f"""
<section class="section legal">
  <div class="container legal-content">
    <h1>Política de Privacidade</h1>
    <p class="legal-updated">Última atualização: 10 de novembro de 2026</p>

    <p>A <strong>J.A Instalações</strong> (CNPJ {CNPJ}) respeita a sua privacidade e está comprometida em proteger os dados pessoais dos visitantes deste site. Esta Política de Privacidade explica quais informações coletamos, como as utilizamos e quais são os seus direitos, em conformidade com a Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018).</p>

    <h2>1. Quem somos</h2>
    <p>Somos uma empresa prestadora de serviços de hidráulica (encanamento), elétrica e telhados, atendendo residências, prédios e comércios na cidade de São Paulo - SP.</p>

    <h2>2. Quais dados coletamos</h2>
    <p>Ao utilizar nosso site, podemos coletar os seguintes dados:</p>
    <ul>
      <li><strong>Dados fornecidos por você:</strong> nome, telefone/WhatsApp, tipo de serviço solicitado e região de atendimento, informados voluntariamente nos formulários de contato.</li>
      <li><strong>Dados de navegação:</strong> páginas visitadas, cliques em botões (como WhatsApp e telefone), tipo de dispositivo, navegador e origem do acesso (por exemplo, um anúncio do Google Ads ou do Meta Ads), coletados de forma automática por meio de cookies e ferramentas de análise.</li>
    </ul>

    <h2>3. Como usamos seus dados</h2>
    <p>Utilizamos os dados coletados para:</p>
    <ul>
      <li>Responder às suas solicitações de orçamento e atendimento via WhatsApp ou telefone;</li>
      <li>Entender como os visitantes utilizam o site, para melhorá-lo continuamente;</li>
      <li>Medir a efetividade das nossas campanhas de anúncios, identificando quais cliques resultaram em contato.</li>
    </ul>
    <p>Não vendemos, alugamos ou compartilhamos seus dados pessoais com terceiros para fins de marketing de terceiros.</p>

    <h2>4. Cookies e ferramentas de terceiros</h2>
    <p>Este site utiliza o <strong>Google Tag Manager</strong> e pode utilizar o <strong>Google Ads</strong> e o <strong>Meta Ads</strong> para:</p>
    <ul>
      <li>Registrar quando um visitante clica no botão de WhatsApp, telefone ou envia o formulário de contato (conversões);</li>
      <li>Medir a origem dos visitantes que chegam por meio de anúncios pagos.</li>
    </ul>
    <p>Essas ferramentas podem utilizar cookies e identificadores para associar seu acesso a uma campanha publicitária. Você pode desativar cookies diretamente nas configurações do seu navegador, embora isso possa afetar a experiência de navegação no site.</p>

    <h2>5. Compartilhamento de dados</h2>
    <p>Seus dados podem ser processados pelas seguintes ferramentas, que atuam como operadoras de dados:</p>
    <ul>
      <li>Google (Google Tag Manager e Google Ads) — para fins de mensuração e publicidade;</li>
      <li>Netlify — hospedagem do site e recebimento dos formulários de contato;</li>
      <li>Lead Hub — ferramenta própria de registro de contatos, que grava seu nome e WhatsApp somente após o seu aceite de cookies, junto com a origem do anúncio que trouxe você até o site. Veja a <a href="{LEADHUB_PRIV}" target="_blank" rel="noopener">política de privacidade do Lead Hub</a>;</li>
      <li>WhatsApp (Meta) — quando você opta por entrar em contato pelo botão de WhatsApp, a conversa passa a ser regida pela política de privacidade do próprio WhatsApp.</li>
    </ul>

    <h2>6. Armazenamento e segurança</h2>
    <p>Adotamos medidas razoáveis para proteger os dados coletados contra acesso não autorizado, perda ou uso indevido. Os dados do formulário são utilizados apenas para o atendimento solicitado.</p>

    <h2>7. Seus direitos</h2>
    <p>De acordo com a LGPD, você tem direito a:</p>
    <ul>
      <li>Confirmar a existência de tratamento dos seus dados;</li>
      <li>Acessar, corrigir ou solicitar a exclusão dos seus dados;</li>
      <li>Revogar o consentimento dado anteriormente;</li>
      <li>Solicitar informações sobre com quem compartilhamos seus dados.</li>
    </ul>
    <p>Para exercer qualquer um desses direitos, entre em contato conosco pelos canais abaixo.</p>

    <h2>8. Contato</h2>
    <ul>
      <li>WhatsApp: <a href="https://wa.me/{PHONE}">{PHONE_FMT}</a></li>
      <li>Telefone: <a href="tel:+{PHONE}">{PHONE_FMT}</a></li>
    </ul>

    <h2>9. Alterações desta política</h2>
    <p>Esta Política de Privacidade pode ser atualizada periodicamente para refletir mudanças em nossas práticas ou por exigências legais. Recomendamos que você a revise de tempos em tempos.</p>

    <p><a class="btn btn-outline" href="/" style="margin-top: 20px;">← Voltar ao site</a></p>
  </div>
</section>
"""


def build_simple(path, title, description, body, robots=None):
    p = {"body_class": "page-legal", "schema_type": "HomeAndConstructionBusiness"}
    out = head(p, f"{SITE}/{path}", title, description)
    if robots:
        out = out.replace('<meta name="theme-color"', f'<meta name="robots" content="{robots}">\n<meta name="theme-color"')
    out += header(None, "/#contato") + body + footer(None, None)
    out += '<script src="/assets/script.js"></script>\n</body>\n</html>\n'
    target = ROOT / path / "index.html" if path else ROOT / "404.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(out, encoding="utf-8")
    print("ok", target.relative_to(ROOT))


NOT_FOUND = """
<section class="section legal">
  <div class="container legal-content" style="text-align:center;">
    <h1>Página não encontrada</h1>
    <p class="legal-updated">O endereço que você acessou não existe ou mudou de lugar.</p>
    <div class="cross-links" style="margin-top:24px;">
      <a href="/">🏠 Página inicial</a>
      <a href="/hidraulica/">🚿 Hidráulica</a>
      <a href="/eletrica/">⚡ Elétrica</a>
      <a href="/telhadista/">🏠 Telhados</a>
    </div>
  </div>
</section>
"""

if __name__ == "__main__":
    for k in PAGES:
        build_landing(k)
    build_simple("privacidade/", "Política de Privacidade | J.A Instalações",
                 "Política de Privacidade da J.A Instalações, conforme a LGPD.", PRIVACY_BODY)
    build_simple("", "Página não encontrada | J.A Instalações",
                 "Página não encontrada.", NOT_FOUND, robots="noindex")
