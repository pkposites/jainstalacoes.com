#!/usr/bin/env python3
"""Gera as páginas estáticas do site J.A Instalações.

Uso:  python3 tools/build.py
Edite os textos/dados abaixo e rode o script. Ele reescreve:
  - as landings (/, /hidraulica/, /eletrica/, /telhadista/), /sobre/, /faq/, /contato/,
    /areas-atendidas/, as páginas profundas de serviço, as páginas de região e de bairro, /privacidade/ e 404.html;
  - robots.txt, sitemap.xml e llms.txt.
Os estilos ficam em assets/styles.css e o comportamento (WhatsApp, formulário,
carrossel, Lead Hub, GTM) em assets/script.js. Imagens derivadas (favicon, OG, avatar do
hero) são geradas por tools/make_assets.py.
"""
import datetime
import html
import json
import re
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parent.parent
# Versão do CSS = hash do arquivo: muda sozinha a cada alteração e força o navegador a baixar de novo.
import hashlib
CSS_VERSION = hashlib.md5((ROOT / "assets" / "styles.css").read_bytes()).hexdigest()[:8]
SITE = "https://jainstalacoes.com"

# ============================================================================
# DADOS DO NEGÓCIO — fonte única (NAP, CNPJ, razão social, placeholders)
# ============================================================================
# NAP confirmado em 12/11/2026 (America/Sao_Paulo):
# - Telefone (11) 5092-2446: confirmado pelo Robson.
# - Endereço público (Perfil da Empresa no Google Maps, o mesmo que o site já usava):
#   Rua Arnaldo Magniccaro, 827 — Vila Gea, São Paulo — SP, 04691-060.
#   Coordenadas: -23.675082, -46.6903611.
# O cadastro do CNPJ traz outro endereço (Rua Pera Natal, 271 — Vila Natal, 04863-320,
# telefone (11) 3017-9054), tratado como endereço fiscal e NÃO usado no site.
BUSINESS = {
    "name": "J.A Instalações",
    # Razão social confirmada pelo Robson (12/11/2026): Instalação J.A — INSTALACAO J.A LTDA.
    "legal_name": "INSTALACAO J.A LTDA",
    "cnpj": "65.380.889/0001-25",
    "phone_digits": "551150922446",
    "phone_fmt": "(11) 5092-2446",
    "street": "Rua Arnaldo Magniccaro, 827",
    "neighborhood": "Vila Gea",
    "city": "São Paulo",
    "region": "SP",
    "postal_code": "04691-060",
    "country": "BR",
    "price_range": "$$",
    # Área confirmada pelo Robson (12/11/2026): toda a Grande São Paulo, com foco em bairros e
    # condomínios de alto padrão. Lista montada a partir de pesquisas públicas de mercado imobiliário
    # de alto padrão (2026) — ver AREA_NOBRE_SP e AREA_NOBRE_GRANDE_SP abaixo.
    "area_served": None,  # preenchido logo abaixo (AREA_SERVED)
    # Perfil da Empresa no Google Maps (conferido em 12/11/2026).
    "google_profile": "https://www.google.com/maps/place/J.A+Instala%C3%A7%C3%B5es/@-23.675082,-46.6903611,17z/data=!3m1!4b1!4m6!3m5!1s0x94ce509e2321c6c3:0xe11dfa2bc1c969b7!8m2!3d-23.675082!4d-46.6903611!16s%2Fg%2F11dfh2hs4f",
}

# Atendimento 24h confirmado pelo Robson (12/11/2026). Todos os dias, 00:00–23:59.
HORARIO = [{
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    ],
    "opens": "00:00",
    "closes": "23:59",
}]
# Coordenadas do Perfil da Empresa no Google Maps, 12/11/2026.
GEO = (-23.675082, -46.6903611)
# E-mail oficial confirmado pelo Robson (12/11/2026).
EMAIL = "J.a.tecnica@hotmail.com"

# Bairros nobres / de alto padrão da capital (referência: rankings públicos de alto padrão 2026).
AREA_NOBRE_SP = [
    "Jardim Europa", "Jardim América", "Jardim Paulista", "Jardim Paulistano", "Itaim Bibi",
    "Vila Nova Conceição", "Vila Olímpia", "Moema", "Brooklin", "Campo Belo", "Vila Mariana",
    "Morumbi", "Cidade Jardim", "Alto de Pinheiros", "Pinheiros", "Perdizes", "Higienópolis",
    "Pacaembu", "Chácara Santo Antônio", "Granja Julieta", "Alto da Boa Vista", "Santo Amaro",
]
# Cidades e polos de alto padrão da Grande São Paulo.
AREA_NOBRE_GRANDE_SP = [
    ("Alphaville", "Barueri e Santana de Parnaíba"), ("Tamboré", "Barueri e Santana de Parnaíba"),
    ("Aldeia da Serra", "Barueri e Santana de Parnaíba"), ("Granja Viana", "Cotia e Carapicuíba"),
    ("São Caetano do Sul", None), ("Santo André", None), ("São Bernardo do Campo", None),
]
AREA_SERVED = (
    [{"@type": "City", "name": "São Paulo"},
     {"@type": "AdministrativeArea", "name": "Grande São Paulo"}]
    + [{"@type": "Place", "name": f"{b}, São Paulo, SP"} for b in AREA_NOBRE_SP]
    + [{"@type": "Place", "name": f"{n}, {c}, SP" if c else f"{n}, SP"} for n, c in AREA_NOBRE_GRANDE_SP]
)
BUSINESS["area_served"] = AREA_SERVED
# TODO (Robson): redes sociais oficiais (Instagram, Facebook...) para sameAs (além do perfil do Google).
SAME_AS_EXTRA = []

# --- Nota/avaliações do Google (conferidas no Maps em 12/11/2026: 4,2 / 90) ---
# Usadas SÓ no texto visível, com link para o perfil. PUBLISH_RATING permanece False
# de propósito: AggregateRating no JSON-LD de um site da própria empresa NÃO gera as
# estrelas do Google (isso vem do Perfil da Empresa), e um número fixo no schema
# desatualiza quando a nota mudar. Não ligar sem uma decisão explícita e um processo
# de atualização.
PUBLISH_RATING = False
RATING_DISPLAY = "4,2"          # texto visível (pt-BR)
REVIEWS_COUNT_DISPLAY = "90"    # texto visível
RATING_AS_OF = "2026-11-12"     # data da conferência no Google Maps

# --- Constantes derivadas (nomes mantidos por compatibilidade) ---
PHONE = BUSINESS["phone_digits"]
PHONE_FMT = BUSINESS["phone_fmt"]
CNPJ = BUSINESS["cnpj"]
GOOGLE_PROFILE = BUSINESS["google_profile"]
ADDRESS = "Rua Arnaldo Magniccaro, 827 - Vila Gea, São Paulo - SP, 04691-060"
MAPS_Q = "Rua+Arnaldo+Magniccaro,+827+-+Vila+Gea,+S%C3%A3o+Paulo+-+SP,+04691-060"
# hasMap / links públicos: URL canônica do Perfil da Empresa (não a busca genérica).
MAPS_URL = BUSINESS["google_profile"]
MAPS_EMBED_Q = "-23.675082,-46.6903611"

GTM = "GTM-M7ZGPMRT"
LEADHUB_KEY = "pk_a7a9316b735740da9eaf41651eeba41a"
LEADHUB_PRIV = f"https://leadinghub.netlify.app/privacidade/{LEADHUB_KEY}"

OG_IMAGE = f"{SITE}/assets/og-cover.jpg"
OG_IMAGE_ALT = "J.A Instalações — elétrica, hidráulica e telhados em São Paulo"
BUILD_DATE = datetime.date.today().isoformat()

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

# Menu do cabeçalho: 3 verticais + Sobre (discreto). FAQ/Contato/Áreas ficam no rodapé.
NAV = [("/", "Início"), ("/hidraulica/", "Hidráulica"), ("/eletrica/", "Elétrica"), ("/telhadista/", "Telhados"), ("/sobre/", "Sobre")]
FOOTER_NAV = [("/", "Início"), ("/hidraulica/", "Hidráulica"), ("/eletrica/", "Elétrica"), ("/telhadista/", "Telhados"),
              ("/sobre/", "Sobre"), ("/faq/", "Perguntas frequentes"), ("/areas-atendidas/", "Áreas atendidas"),
              ("/contato/", "Contato"), ("/privacidade/", "Política de Privacidade")]

STEPS = [
    ("A gente escuta", "Você conta o que precisa pelo WhatsApp ou telefone. Entendemos o problema e orientamos sobre o serviço."),
    ("Tudo bem combinado", "Escopo, valores e agendamento alinhados antes de começar. Sem surpresas."),
    ("Cuidado do início ao fim", "Serviço com nota fiscal e garantia, e respeito pela sua casa ou pelo seu negócio."),
]

# Badge visível com a nota conferida, ligada ao perfil. Não entra no AggregateRating.
REVIEW_BADGE = ("link", f"⭐ {RATING_DISPLAY} / {REVIEWS_COUNT_DISPLAY} avaliações no Google", GOOGLE_PROFILE)

PAGES = {
    "home": {
        "path": "", "slug": "home", "body_class": "page-home",
        "title": "Eletricista, encanador e telhadista em São Paulo | J.A Instalações",
        "description": "Serviços elétricos, hidráulicos e de telhados em São Paulo, SP. Atendimento rápido para residências, prédios e comércios. Solicite seu orçamento pelo WhatsApp.",
        "schema_type": "HomeAndConstructionBusiness",
        "name": "Início",
        "eyebrow": "Elétrica · Hidráulica · Telhados",
        "h1": "Seu problema, nossa solução: elétrica, hidráulica e telhado em São Paulo",
        "sub": "Um só contato para cuidar da sua casa, prédio ou comércio. Atendimento rápido, nota fiscal e garantia.",
        "hero_img": True, "hero_icon": "",
        "badges": ["⚡ Atendimento 24h", "🧾 Nota fiscal e garantia", REVIEW_BADGE],
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
        "title": "Encanador em São Paulo | Desentupimento e caça-vazamento | J.A Instalações",
        "description": "J.A Instalações - Encanador profissional em São Paulo. Consertos urgentes, desentupimentos e detecção de vazamentos em residências e prédios. Atendimento via WhatsApp.",
        "schema_type": "Plumber",
        "name": "Hidráulica", "noun": "Encanador", "short": "hid",
        "eyebrow": "Encanador de confiança em São Paulo",
        "h1": "Encanador em São Paulo: desentupimento, consertos e detecção de vazamentos",
        "sub": "Atendimento rápido e serviço garantido. Custo de visita técnica sujeito a análise do caso e deslocamento.",
        "hero_img": True, "hero_icon": "",
        "badges": ["📍 Visita técnica sujeita a análise e deslocamento", "⚡ Atendimento urgente", REVIEW_BADGE],
        "marquee": "Atendimento rápido em toda grande São Paulo · Faça o seu orçamento hoje mesmo!",
        "wa_text": "Olá! Preciso de um encanador.",
        "greeting": "Olá! Gostaria de solicitar um atendimento.",
        "services": [
            ("🚨", "Encanador urgente", "Bombeiro hidráulico 24h para emergências", "Atendimento 24 horas para vazamentos, entupimentos e problemas hidráulicos que não podem esperar. Nossa equipe se desloca até residências e prédios em São Paulo para resolver o problema com agilidade e segurança."),
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
        "title": "Eletricista em São Paulo | Instalações e reparos | J.A Instalações",
        "description": "J.A Instalações - Eletricista profissional em São Paulo. Instalações e reparos elétricos, tomadas, iluminação, quadros e disjuntores em residências, prédios e comércios. Atendimento via WhatsApp.",
        "schema_type": "Electrician",
        "name": "Elétrica", "noun": "Eletricista", "short": "ele",
        "eyebrow": "Eletricista de confiança em São Paulo",
        "h1": "Eletricista em São Paulo: instalações e reparos elétricos com segurança para sua casa ou empresa",
        "sub": "Da tomada que parou de funcionar à instalação completa. Visita técnica sujeita a análise do caso e deslocamento.",
        "hero_img": False, "hero_icon": "⚡",
        "badges": ["📍 Visita técnica sujeita a análise e deslocamento", "⚡ Atendimento urgente", REVIEW_BADGE],
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
        "title": "Telhadista em São Paulo | Reparo de telhado, calhas e goteiras | J.A Instalações",
        "description": "J.A Instalações - Telhadista em São Paulo. Reparo e troca de telhas, manutenção de telhados, calhas, rufos e infiltrações em residências, prédios e comércios. Atendimento via WhatsApp.",
        "schema_type": "RoofingContractor",
        "name": "Telhados", "noun": "Telhadista", "short": "tel",
        "eyebrow": "Telhadista de confiança em São Paulo",
        "h1": "Telhadista em São Paulo: reparo e manutenção de telhados, calhas e infiltrações",
        "sub": "Um telhado bem cuidado protege tudo o que está embaixo dele. Visita técnica sujeita a análise do caso e deslocamento.",
        "hero_img": False, "hero_icon": "🏠",
        "badges": ["📍 Visita técnica sujeita a análise e deslocamento", "🌧️ Goteira? Atendimento rápido", REVIEW_BADGE],
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
VERTICALS = ["hidraulica", "eletrica", "telhadista"]
VERTICAL_ICON = {"hidraulica": "🚿", "eletrica": "⚡", "telhadista": "🏠"}

# ============================================================================
# FAQ (respostas só com fatos já publicados no site ou derivados deles)
# Respostas podem conter HTML simples (links); o JSON-LD usa a versão em texto puro.
# ============================================================================
FAQ_COMMON = [
    ("Como solicito um orçamento?",
     f"Pelo WhatsApp ou pelo telefone {PHONE_FMT}, ou preenchendo o formulário da <a href=\"/contato/\">página de contato</a>. Você conta o que precisa, entendemos o problema e alinhamos escopo, valores e agendamento antes de começar."),
    ("A visita técnica tem custo?",
     "O custo da visita técnica está sujeito à análise do caso e ao deslocamento. Informe o problema e a sua região pelo WhatsApp para receber a orientação antes de agendar."),
    ("Vocês emitem nota fiscal e dão garantia?",
     "Sim. Os serviços são feitos com nota fiscal e garantia. Os detalhes do serviço que você vai contratar são combinados com a gente antes de começar."),
    ("Quais regiões vocês atendem?",
     "Atendemos toda a Grande São Paulo, com atenção especial a bairros e condomínios de alto padrão, como Moema, Brooklin, Campo Belo, Itaim Bibi, Jardins, Vila Mariana, Morumbi, Alphaville e Granja Viana. Veja as <a href=\"/areas-atendidas/\">áreas atendidas</a>."),
    ("Qual é o horário de atendimento?",
     "O atendimento é 24 horas, todos os dias. Fale com a gente pelo WhatsApp ou pelo telefone " + PHONE_FMT + "."),
    ("Vocês atendem emergências?",
     "Sim. O atendimento é 24 horas para problemas hidráulicos, elétricos e de telhado que não podem esperar. Fale pelo WhatsApp ou pelo telefone " + PHONE_FMT + "."),
    ("Que tipos de imóvel vocês atendem?",
     "Residências, prédios e comércios, com serviços de elétrica, hidráulica e telhados."),
    ("Quais serviços a J.A Instalações oferece?",
     "<a href=\"/hidraulica/\">Hidráulica</a> (encanador, consertos, desentupimento e detecção de vazamentos), <a href=\"/eletrica/\">elétrica</a> (instalações, reparos, tomadas, iluminação, quadros e disjuntores) e <a href=\"/telhadista/\">telhados</a> (reparo e troca de telhas, manutenção, calhas, rufos, goteiras e infiltrações)."),
    ("Há pagamento facilitado?",
     "Sim, há pagamento facilitado. A forma de pagamento e as condições são combinadas junto com o orçamento."),
]

FAQ_VERTICAL = {
    "hidraulica": [
        ("O que fazer ao notar um vazamento enquanto o encanador não chega?",
         "Se souber onde fica, feche o registro do ponto afetado ou o registro geral para reduzir o desperdício e os danos. Se a água estiver perto de tomadas ou do quadro de energia, não toque e desligue a energia apenas se puder fazer isso com segurança. Depois, chame pelo WhatsApp e conte o que está acontecendo."),
        ("A detecção de vazamentos exige quebrar parede ou piso?",
         "O objetivo da detecção é localizar o vazamento com precisão para evitar quebra-quebra desnecessário. Se for preciso abrir algum ponto para o conserto, isso é combinado com você antes de começar. Veja mais em <a href=\"/hidraulica/deteccao-de-vazamentos/\">detecção de vazamentos</a>."),
        ("Quais pontos vocês desentopem?",
         "Pias, ralos, vasos sanitários, caixas de gordura e tubulações em geral, com equipamentos adequados para não danificar a estrutura hidráulica. Veja <a href=\"/hidraulica/desentupimento/\">desentupimento</a>."),
        ("Vocês atendem prédios e condomínios?",
         "Atendemos residências e prédios em São Paulo e Grande São Paulo. Informe o endereço aproximado e o tipo de imóvel pelo WhatsApp para alinharmos a visita."),
        ("Vocês atendem encanador de urgência?",
         "Sim, o atendimento de encanador urgente é 24 horas, para vazamentos e entupimentos que não podem esperar. Veja <a href=\"/hidraulica/encanador-urgente/\">encanador urgente</a>."),
    ],
    "eletrica": [
        ("O disjuntor desarma toda hora. O que pode ser?",
         "Pode ser sobrecarga do circuito, curto-circuito, algum equipamento com defeito ou o próprio disjuntor. Só a avaliação no local confirma a causa. Evite religar repetidamente e chame um eletricista. Veja <a href=\"/eletrica/quadros-e-disjuntores/\">quadros e disjuntores</a>."),
        ("Senti cheiro de queimado ou vi faíscas. O que fazer?",
         "Se for possível com segurança, desligue o disjuntor do circuito (ou o geral), não toque em fios ou tomadas danificadas e chame pelo WhatsApp para atendimento urgente. Em caso de fogo, acione imediatamente os bombeiros."),
        ("Vocês trocam chuveiro, tomadas, interruptores e luminárias?",
         "Sim: troca e instalação de tomadas, interruptores, chuveiros, luminárias, lustres e spots de LED. Veja <a href=\"/eletrica/instalacoes-e-reparos/\">instalações e reparos elétricos</a>."),
        ("Vocês montam ou trocam quadros de distribuição e DR?",
         "Sim, fazemos montagem e troca de quadros de distribuição, disjuntores e DR, além de balanceamento de circuitos e identificação correta."),
    ],
    "telhadista": [
        ("Minha goteira é caso de reparo ou de trocar telhas?",
         "Depende da causa: pode ser telha quebrada ou deslocada, cumeeira, rufo ou calha. A visita permite localizar a origem e indicar a correção. Veja <a href=\"/telhadista/goteiras-e-infiltracoes/\">goteiras e infiltrações</a>."),
        ("Vocês instalam e limpam calhas e rufos?",
         "Sim: instalação, troca, limpeza e vedação de calhas, rufos e condutores. Veja <a href=\"/telhadista/calhas-e-rufos/\">calhas e rufos</a>."),
        ("Vale a pena fazer manutenção preventiva do telhado?",
         "A revisão do telhado, a limpeza e a verificação da estrutura e das vedações ajudam a evitar problemas maiores e mais caros no futuro."),
        ("O que informar ao pedir atendimento de telhado?",
         "O bairro, o tipo de imóvel e onde aparece a goteira ou a mancha. Quanto mais claro o relato, mais fácil orientar a visita, que é sujeita à análise do caso e ao deslocamento."),
    ],
}

# ============================================================================
# PÁGINAS PROFUNDAS DE SERVIÇO
# ============================================================================
SERVICE_STD = ("A visita técnica tem custo sujeito à análise do caso e ao deslocamento. Escopo, valores e agendamento são "
               "alinhados antes de começar, e o serviço é feito com nota fiscal e garantia. Para pedir orçamento, chame pelo WhatsApp.")

SERVICE_PAGES = [
    {
        "vertical": "hidraulica", "slug": "desentupimento", "card": "Desentupimentos",
        "name": "Desentupimento", "icon": "🚿",
        "title": "Desentupimento em São Paulo | Pias, ralos e vasos | J.A Instalações",
        "description": "Desentupimento de pias, ralos, vasos sanitários, caixas de gordura e tubulações em São Paulo, para residências e prédios. Peça orçamento pelo WhatsApp.",
        "h1": "Desentupimento em São Paulo: pias, ralos, vasos e caixas de gordura",
        "eyebrow": "Encanador · Desentupimento",
        "sub": "Desobstrução de pias, ralos, vasos e tubulações em residências e prédios, com equipamentos adequados.",
        "wa_text": "Olá! Preciso de um desentupimento.",
        "intro": [
            "Desentupimento é a desobstrução de pias, ralos, vasos sanitários, caixas de gordura e tubulações em que a água deixou de escoar. A obstrução pode vir de gordura, restos de comida, papel, cabelo, areia ou de objetos que caíram no ralo — e, se não for tratada, pode causar mau cheiro, refluxo e até infiltrações.",
            "A J.A Instalações faz o desentupimento com equipamentos adequados ao tipo de obstrução, buscando resolver o problema sem danificar a estrutura hidráulica. Quando o entupimento volta com frequência, a visita ajuda a avaliar se há algo na instalação que precisa de atenção, além de desobstruir o ponto.",
        ],
        "when": [
            "A pia ou o ralo escoa devagar ou não escoa mais.",
            "A água volta pelo ralo ou há refluxo em outro ponto da casa.",
            "Mau cheiro persistente saindo de ralos ou caixas de gordura.",
            "O vaso sanitário entope com frequência ou transborda.",
            "A caixa de gordura está cheia ou transbordando.",
        ],
        "how": [
            "Pelo WhatsApp, conte qual ponto está entupido (pia da cozinha, ralo do banheiro, vaso, caixa de gordura), há quanto tempo isso acontece e em que bairro você está. Com essas informações orientamos o que pode ser feito e combinamos o atendimento.",
        ],
        "faq": [
            ("Quais pontos vocês desentopem?", "Pias, ralos, vasos sanitários, caixas de gordura e tubulações em geral, em residências e prédios."),
            ("O desentupimento pode danificar a tubulação?", "Usamos equipamentos adequados ao tipo de entupimento para resolver sem danificar a estrutura hidráulica. Se na avaliação notarmos outro problema na instalação, explicamos antes de seguir."),
            ("Quanto custa um desentupimento?", "O valor depende do ponto e do caso, por isso o orçamento é feito pelo WhatsApp. A visita técnica tem custo sujeito à análise do caso e ao deslocamento."),
        ],
        "related": ["deteccao-de-vazamentos", "encanador-urgente"],
    },
    {
        "vertical": "hidraulica", "slug": "deteccao-de-vazamentos", "card": "Detecção de vazamentos",
        "name": "Detecção de vazamentos", "icon": "💧",
        "title": "Detecção de vazamentos em São Paulo | J.A Instalações",
        "description": "Detecção de vazamentos ocultos em paredes, pisos e tubulações em São Paulo, sem quebra-quebra desnecessário. Fale com a J.A Instalações pelo WhatsApp.",
        "h1": "Detecção de vazamentos em São Paulo: localização precisa, sem quebra-quebra desnecessário",
        "eyebrow": "Encanador · Caça-vazamento",
        "sub": "Identificamos o ponto do vazamento antes de qualquer conserto, para poupar tempo, obra e dinheiro.",
        "wa_text": "Olá! Preciso de detecção de vazamento.",
        "intro": [
            "Um vazamento oculto costuma dar sinais: mancha ou mofo em parede, piso ou teto, tinta descascando, cheiro de umidade ou uma conta de água que sobe sem explicação. Quando o cano está dentro da parede ou sob o piso, tentar adivinhar o ponto pode significar abrir áreas inteiras sem necessidade.",
            "A detecção de vazamentos serve para localizar o problema com precisão antes do conserto, evitando quebra-quebra desnecessário e economizando tempo e dinheiro. Com o ponto identificado, o reparo fica mais direto e o acabamento do seu imóvel é preservado ao máximo.",
        ],
        "when": [
            "Mancha de umidade, mofo ou tinta soltando em parede, piso ou teto.",
            "Conta de água mais alta que o normal, sem mudança de consumo.",
            "Barulho de água correndo com todos os pontos fechados.",
            "Piso ou parede frios e úmidos em um ponto específico.",
            "Água aparecendo no teto do vizinho de baixo, em prédios.",
        ],
        "how": [
            "Atendemos residências e prédios em São Paulo e Grande São Paulo. Pelo WhatsApp, conte onde aparece a mancha ou o sinal de umidade e se a conta de água aumentou. Alinhamos a visita e o orçamento antes de começar.",
        ],
        "faq": [
            ("Como saber se tenho um vazamento oculto?", "Os sinais mais comuns são manchas e mofo, cheiro de umidade, tinta descascando, barulho de água com tudo fechado e conta de água acima do normal. Só a avaliação no local confirma e localiza o ponto."),
            ("Vai ser preciso quebrar parede ou piso?", "A detecção existe justamente para localizar o vazamento com precisão e evitar quebra-quebra desnecessário. Se for preciso abrir algum ponto para o conserto, isso é combinado antes de começar."),
            ("Vocês atendem prédios e condomínios?", "Sim, atendemos residências e prédios. Informe o endereço aproximado e o andar pelo WhatsApp."),
            ("Se eu achar um vazamento, o que faço antes de vocês chegarem?", "Se souber onde fica, feche o registro do ponto afetado ou o registro geral para reduzir o desperdício e os danos."),
        ],
        "related": ["desentupimento", "encanador-urgente"],
    },
    {
        "vertical": "hidraulica", "slug": "encanador-urgente", "card": "Encanador urgente",
        "name": "Encanador urgente", "icon": "🚨",
        "title": "Encanador urgente 24h em São Paulo | J.A Instalações",
        "description": "Encanador urgente 24 horas em São Paulo para vazamentos, entupimentos e problemas hidráulicos que não podem esperar. Peça atendimento pelo WhatsApp.",
        "h1": "Encanador urgente 24h em São Paulo: vazamentos e entupimentos que não podem esperar",
        "eyebrow": "Encanador · Atendimento 24 horas",
        "sub": "Atendimento 24 horas para problemas hidráulicos que não esperam. Chame pelo WhatsApp ou telefone.",
        "wa_text": "Olá! Preciso de um encanador urgente.",
        "intro": [
            "Algumas situações hidráulicas não podem esperar: cano estourado, vazamento forte, água jorrando, refluxo de esgoto ou entupimentos que impedem o uso de banheiros e cozinha. Quanto mais tempo passa, maior o risco de danos a pisos, paredes, móveis e à instalação elétrica.",
            "A J.A Instalações oferece atendimento 24 horas para esses casos em residências e prédios de São Paulo. O caminho mais rápido é chamar pelo WhatsApp ou ligar.",
        ],
        "when": [
            "Cano estourado ou vazamento forte que não para.",
            "Água atingindo tomadas, quadro de energia ou móveis.",
            "Refluxo de esgoto ou vaso/ralo transbordando.",
            "Falta de água causada por defeito na instalação.",
            "Vazamento em prédio afetando outras unidades.",
        ],
        "how": [
            "Enquanto o atendimento não chega: se souber onde fica, feche o registro do ponto afetado ou o registro geral; afaste móveis e objetos da área molhada; e, se houver água perto de tomadas ou do quadro de energia, não toque — desligue a energia apenas se puder fazer isso com segurança.",
            "Ao chamar, informe o endereço aproximado, o tipo de imóvel e o que está acontecendo. Assim a equipe entende a urgência e orienta os próximos passos.",
        ],
        "faq": [
            ("Vocês atendem 24 horas?", "Sim. O atendimento de encanador urgente é 24 horas, todos os dias. Fale pelo WhatsApp ou pelo telefone."),
            ("O que posso fazer antes de o encanador chegar?", "Feche o registro do ponto afetado ou o registro geral, se souber onde ficam, e afaste móveis da área molhada. Não toque em tomadas ou fios molhados."),
            ("Quanto custa o atendimento urgente?", "O valor depende do caso. A visita técnica tem custo sujeito à análise do caso e ao deslocamento; o orçamento é alinhado antes de começar o serviço."),
        ],
        "related": ["deteccao-de-vazamentos", "desentupimento"],
    },
    {
        "vertical": "eletrica", "slug": "quadros-e-disjuntores", "card": "Quadros e disjuntores",
        "name": "Quadros e disjuntores", "icon": "🧰",
        "title": "Quadro de luz e disjuntores em São Paulo | J.A Instalações",
        "description": "Montagem e troca de quadros de distribuição, disjuntores e DR em São Paulo, com balanceamento de circuitos. Eletricista para casas, prédios e comércios.",
        "h1": "Quadros de distribuição e disjuntores em São Paulo: montagem, troca e balanceamento",
        "eyebrow": "Eletricista · Quadros e disjuntores",
        "sub": "Mais segurança e menos desarmes: montagem, troca e identificação correta de circuitos.",
        "wa_text": "Olá! Preciso de ajuda com quadro de luz e disjuntores.",
        "intro": [
            "O quadro de distribuição (popularmente, o “quadro de luz”) reúne os disjuntores que protegem os circuitos de uma casa, prédio ou comércio. Ele organiza a energia que chega e desliga o circuito quando há sobrecarga ou curto-circuito, protegendo a fiação e os equipamentos.",
            "A J.A Instalações faz a montagem e a troca de quadros de distribuição, disjuntores e DR (dispositivo diferencial residual), o balanceamento de circuitos e a identificação correta de cada disjuntor. O resultado é uma instalação mais segura e com menos desarmes.",
        ],
        "when": [
            "O disjuntor desarma com frequência.",
            "O quadro é antigo, aquece, tem cheiro de queimado ou componentes danificados.",
            "Você ampliou ou reformou o imóvel e instalou novos equipamentos.",
            "Os circuitos não têm identificação e ninguém sabe o que cada disjuntor protege.",
            "Quer incluir um DR para mais proteção na instalação.",
        ],
        "how": [
            "Se o quadro estiver quente, com cheiro de queimado ou faíscas, não insista em religar: desligue o que for possível com segurança e chame pelo WhatsApp para atendimento urgente.",
            "Conte o tipo de imóvel (casa, apartamento, comércio), o que está acontecendo e o bairro. Assim alinhamos a visita e o orçamento.",
        ],
        "faq": [
            ("Por que meu disjuntor desarma?", "Pode ser sobrecarga do circuito, curto-circuito, equipamento com defeito ou o próprio disjuntor. Só a avaliação no local confirma a causa; evite religar repetidamente."),
            ("O que é o DR?", "O DR (dispositivo diferencial residual) é um dispositivo de proteção instalado no quadro que desliga o circuito quando identifica fuga de corrente, aumentando a segurança da instalação."),
            ("Vocês atendem comércios e prédios?", "Sim, atendemos residências, prédios e comércios em São Paulo e Grande São Paulo."),
        ],
        "related": ["instalacoes-e-reparos"],
    },
    {
        "vertical": "eletrica", "slug": "instalacoes-e-reparos", "card": "Instalações e reparos",
        "name": "Instalações e reparos elétricos", "icon": "🔌",
        "title": "Instalações e reparos elétricos em São Paulo | J.A Instalações",
        "description": "Instalações elétricas, troca de fiação, novos pontos de energia, tomadas, interruptores, chuveiros e luminárias em São Paulo. Peça orçamento pelo WhatsApp.",
        "h1": "Instalações e reparos elétricos em São Paulo: fiação, pontos novos, tomadas e iluminação",
        "eyebrow": "Eletricista · Instalações e reparos",
        "sub": "Da tomada que parou de funcionar à instalação completa, com material de qualidade e cuidado em cada conexão.",
        "wa_text": "Olá! Preciso de uma instalação ou reparo elétrico.",
        "intro": [
            "Instalações e reparos elétricos cobrem desde a troca de uma tomada ou interruptor até a instalação de pontos novos de energia, a substituição de fiação antiga e adequações para receber novos equipamentos. Em imóveis que passaram por reformas ou ampliações, é comum a instalação precisar ser revista.",
            "A J.A Instalações faz instalações novas, troca de fiação, novos pontos de energia e reparos em geral, além da troca e instalação de tomadas, interruptores, chuveiros, luminárias, lustres e spots de LED — sempre com material de qualidade e serviço limpo e bem acabado.",
        ],
        "when": [
            "Tomada ou interruptor que parou de funcionar, esquenta ou faísca.",
            "Fiação antiga que precisa ser trocada.",
            "Necessidade de novos pontos de energia ou de iluminação.",
            "Instalação de chuveiro, luminárias, lustres ou spots de LED.",
            "Falta de energia em parte do imóvel, disjuntor desarmando ou cheiro de queimado.",
        ],
        "how": [
            "Antes de começar, o escopo e os valores são combinados com você. Se houver cheiro de queimado, faíscas ou fios danificados, desligue o circuito apenas se puder fazer isso com segurança e chame pelo WhatsApp.",
        ],
        "faq": [
            ("Vocês instalam chuveiro, luminárias e spots de LED?", "Sim. Fazemos troca e instalação de chuveiros, luminárias, lustres, spots de LED, tomadas e interruptores."),
            ("Dá para criar novos pontos de energia?", "Sim, fazemos novos pontos de energia e adequações da instalação. A viabilidade é avaliada na visita."),
            ("Como funciona o orçamento?", "Você conta o que precisa pelo WhatsApp; a visita técnica tem custo sujeito à análise do caso e ao deslocamento, e o escopo e os valores são alinhados antes de começar."),
        ],
        "related": ["quadros-e-disjuntores"],
    },
    {
        "vertical": "telhadista", "slug": "calhas-e-rufos", "card": "Calhas e rufos",
        "name": "Calhas e rufos", "icon": "🪣",
        "title": "Calhas e rufos em São Paulo | Instalação e limpeza | J.A Instalações",
        "description": "Instalação, troca, limpeza e vedação de calhas, rufos e condutores em São Paulo, para evitar transbordamento e infiltração. Orçamento pelo WhatsApp.",
        "h1": "Calhas e rufos em São Paulo: instalação, troca, limpeza e vedação",
        "eyebrow": "Telhadista · Calhas e rufos",
        "sub": "A água da chuva escoando do jeito certo, sem transbordar nem infiltrar.",
        "wa_text": "Olá! Preciso de serviço de calhas e rufos.",
        "intro": [
            "As calhas recolhem a água da chuva que escorre pelo telhado e a conduzem até os condutores; os rufos fazem a vedação entre o telhado e paredes, platibandas ou outras estruturas. Quando algum desses elementos falha, a água transborda, escorre pela parede ou entra na construção.",
            "A J.A Instalações cuida da instalação, troca, limpeza e vedação de calhas, rufos e condutores, garantindo que a água seja escoada sem transbordar ou infiltrar. A limpeza é especialmente útil quando folhas e sujeira acumulam e entopem o caminho da água.",
        ],
        "when": [
            "A calha transborda em dias de chuva.",
            "Manchas ou umidade na parede, perto do encontro com o telhado.",
            "Rufo solto, trincado ou com falhas de vedação.",
            "Condutor entupido ou água caindo fora do lugar.",
            "Imóvel sem calha, em que a água escorre direto pela fachada ou pelo quintal.",
        ],
        "how": [
            "Para orientar a visita, informe pelo WhatsApp o bairro, o tipo de imóvel e onde percebe o problema (transbordo, mancha, goteira). A visita técnica é sujeita à análise do caso e ao deslocamento.",
        ],
        "faq": [
            ("Vocês instalam e limpam calhas?", "Sim: instalação, troca, limpeza e vedação de calhas, rufos e condutores."),
            ("Quando é um bom momento para revisar as calhas?", "Quando há acúmulo de folhas e sujeira, sinais de transbordo ou manchas na parede. A manutenção preventiva ajuda a evitar problemas maiores no futuro."),
            ("Calha e rufo resolvem goteira?", "Podem ser a causa de infiltrações, mas também há outras origens, como telhas deslocadas. A visita identifica o ponto. Veja <a href=\"/telhadista/goteiras-e-infiltracoes/\">goteiras e infiltrações</a>."),
        ],
        "related": ["goteiras-e-infiltracoes"],
    },
    {
        "vertical": "telhadista", "slug": "goteiras-e-infiltracoes", "card": "Goteiras e infiltrações",
        "name": "Goteiras e infiltrações", "icon": "🌧️",
        "title": "Goteiras e infiltrações no telhado em São Paulo | J.A Instalações",
        "description": "Localização e correção de goteiras e infiltrações vindas do telhado em São Paulo, evitando mofo e danos ao forro e às paredes. Peça orçamento pelo WhatsApp.",
        "h1": "Goteiras e infiltrações no telhado em São Paulo: localização e correção",
        "eyebrow": "Telhadista · Goteiras e infiltrações",
        "sub": "Atendimento rápido em dias de chuva para evitar manchas, mofo e danos ao forro, às paredes e aos móveis.",
        "wa_text": "Olá! Estou com goteira no telhado.",
        "intro": [
            "Goteiras e infiltrações raramente aparecem exatamente embaixo do ponto onde a água entra: ela pode escorrer por vigas e lajes antes de aparecer como mancha no forro ou na parede. Por isso, localizar a origem é o primeiro passo para uma correção que dure.",
            "A J.A Instalações faz a localização e a correção de goteiras e infiltrações vindas do telhado, evitando manchas, mofo e danos ao forro, às paredes e aos móveis. Dependendo da causa, a solução pode envolver telhas, cumeeira, rufos, calhas ou vedações.",
        ],
        "when": [
            "Pinga água dentro de casa quando chove.",
            "Manchas escuras ou bolhas de umidade no forro ou no teto.",
            "Mofo ou tinta descascando perto do telhado.",
            "Telhas quebradas, trincadas ou deslocadas visíveis do chão.",
            "Infiltração em lajes de cobertura ou em pontos de encontro entre telhado e parede.",
        ],
        "how": [
            "Pelo WhatsApp, conte onde aparece a goteira ou a mancha, o bairro e o tipo de imóvel. Se possível, envie fotos para ajudar na orientação. A visita técnica é sujeita à análise do caso e ao deslocamento, e o orçamento é alinhado antes de começar.",
        ],
        "faq": [
            ("Por que a goteira aparece longe de onde a água entra?", "A água pode correr por estruturas e lajes antes de aparecer. Por isso a visita busca a origem, que pode ser uma telha, a cumeeira, um rufo ou uma calha."),
            ("Atendem em dias de chuva?", "O atendimento a goteiras é pensado para quando elas aparecem. Chame pelo WhatsApp, descreva o que está acontecendo e avaliamos a urgência e como proceder."),
            ("Vocês trocam telhas?", "Sim, substituímos telhas quebradas, trincadas ou deslocadas e revisamos a cumeeira e o alinhamento."),
        ],
        "related": ["calhas-e-rufos"],
    },
]

# ============================================================================
# REGIÕES (páginas /{vertical}/{regiao}/)
# Regiões de São Paulo e Grande SP. Área confirmada (12/11/2026): toda a Grande SP, foco em alto padrão.
# ============================================================================
REGIONS = [
    {
        "slug": "zona-sul", "name": "Zona Sul", "in": "na Zona Sul de São Paulo",
        "examples": "Moema, Brooklin, Campo Belo, Vila Nova Conceição, Chácara Santo Antônio, Granja Julieta, Alto da Boa Vista, Santo Amaro e Vila Mariana",
        "travel": "A nossa base fica na Vila Gea, na própria Zona Sul, então é a região mais próxima de nós.",
        "hidraulica": {
            "lead": "Encanador com base na própria Zona Sul, para consertos, desentupimentos e vazamentos em casas e prédios.",
            "body": [
                "A Zona Sul reúne casas térreas e sobrados em bairros residenciais, condomínios de prédios e áreas comerciais movimentadas. Como a nossa base fica na Vila Gea, é a região que está mais perto de nós quando você precisa de um encanador.",
                "Em casas e sobrados, os problemas típicos envolvem torneiras e registros com defeito, caixas d'água e ralos entupidos; em prédios, vazamentos que aparecem no teto do vizinho de baixo ou em colunas de água. Conte o que está acontecendo e o endereço aproximado para orientarmos o melhor caminho.",
            ],
        },
        "eletrica": {
            "lead": "Eletricista para a Zona Sul de São Paulo: instalações, reparos, quadros e disjuntores.",
            "body": [
                "Na Zona Sul predominam imóveis residenciais, de casas com ampliações feitas ao longo dos anos a apartamentos em condomínios. Ampliações e reformas costumam sobrecarregar circuitos antigos, e é aí que surgem disjuntores que desarmam e tomadas que esquentam.",
                "Como saímos da Vila Gea, o deslocamento dentro da Zona Sul tende a ser mais curto. Mesmo assim, a visita técnica é sujeita à análise do caso e ao deslocamento, e o orçamento é alinhado antes de começar o serviço.",
            ],
        },
        "telhadista": {
            "lead": "Telhadista na Zona Sul: reparo de telhas, calhas, rufos e infiltrações.",
            "body": [
                "Casas com telhado de cerâmica ou fibrocimento, sobrados e comércios de rua são comuns na Zona Sul. Com as chuvas fortes do verão paulistano, telhas deslocadas, calhas entupidas e rufos mal vedados aparecem como goteiras e manchas no forro.",
                "Para orçar, informe pelo WhatsApp o bairro, o tipo de telha (se souber) e onde pinga. A partir da nossa base na Vila Gea atendemos a Zona Sul, com visita sujeita à análise do caso e ao deslocamento.",
            ],
        },
    },
    {
        "slug": "zona-oeste", "name": "Zona Oeste", "in": "na Zona Oeste de São Paulo",
        "examples": "Itaim Bibi, Jardim Europa, Jardim América, Vila Olímpia, Alto de Pinheiros, Pinheiros, Perdizes, Pacaembu, Morumbi e Cidade Jardim",
        "travel": "Saindo da nossa base na Vila Gea, o deslocamento até a Zona Oeste é avaliado junto com o caso.",
        "hidraulica": {
            "lead": "Encanador na Zona Oeste de São Paulo, para apartamentos, casas e imóveis comerciais.",
            "body": [
                "A Zona Oeste combina bairros muito verticalizados, como Pinheiros e Perdizes, com áreas de casas e vilas, como Lapa e Butantã. Prédios com muitos andares trazem questões típicas de hidráulica: colunas compartilhadas, registros por unidade e vazamentos que atingem vizinhos.",
                "Em imóveis mais antigos, tubulações embutidas nas paredes podem dificultar a localização de vazamentos, e é nesses casos que a detecção sem quebra-quebra desnecessário faz diferença. Informe o bairro e o tipo de imóvel pelo WhatsApp.",
            ],
        },
        "eletrica": {
            "lead": "Eletricista na Zona Oeste: apartamentos, casas e escritórios, com atenção a quadros e circuitos.",
            "body": [
                "Muitos imóveis da Zona Oeste são apartamentos e conjuntos comerciais, onde a instalação elétrica passa por regras do condomínio e por quadros de distribuição compartilhados. Em casas antigas de bairros tradicionais, a fiação original pode já não atender aos equipamentos de hoje.",
                "Troca de quadros, inclusão de DR, novos pontos de tomada e iluminação são serviços comuns nesse perfil de imóvel. Conte o que precisa e o tipo de imóvel para alinharmos a visita e o orçamento.",
            ],
        },
        "telhadista": {
            "lead": "Telhadista na Zona Oeste: telhados de casas e vilas, coberturas, calhas e rufos.",
            "body": [
                "Na Zona Oeste existem casas de telhado cerâmico, sobrados em vilas e prédios com coberturas e telhados de apoio. Cada tipo pede um cuidado diferente: acesso, vedação e escoamento da água.",
                "Em prédios e comércios, calhas e rufos entupidos por folhas e sujeira podem transbordar na chuva. Informe o bairro, o tipo de cobertura e onde aparece a infiltração; assim conseguimos orientar a visita.",
            ],
        },
    },
    {
        "slug": "zona-norte", "name": "Zona Norte", "in": "na Zona Norte de São Paulo",
        "examples": "Santana, Tucuruvi, Casa Verde, Freguesia do Ó e Jaçanã",
        "travel": "Como a nossa base fica na Vila Gea, na Zona Sul, o deslocamento até a Zona Norte é maior e entra na análise do caso.",
        "hidraulica": {
            "lead": "Encanador na Zona Norte de São Paulo, com visita sujeita a análise do caso e deslocamento.",
            "body": [
                "A Zona Norte tem bairros extensos, com muitas casas térreas e sobrados, além de áreas de prédios próximas às estações de metrô, como Santana e Tucuruvi. Residências com quintal costumam ter caixas de gordura, ralos externos e caixas d'água que pedem revisão periódica.",
                "Como a nossa base fica na Vila Gea, na Zona Sul, o deslocamento até a Zona Norte é maior, e por isso o custo da visita é avaliado caso a caso. Pelo WhatsApp você informa o bairro e o problema e confirmamos a disponibilidade antes de agendar.",
            ],
        },
        "eletrica": {
            "lead": "Eletricista na Zona Norte: casas, sobrados, prédios e comércios de rua.",
            "body": [
                "Comércios de rua, oficinas e casas com mais de um pavimento são frequentes na Zona Norte, e cada um tem uma demanda elétrica diferente: do quadro de um pequeno comércio ao ponto de energia de um chuveiro no segundo andar.",
                "Se o disjuntor desarma, a tomada esquenta ou há cheiro de queimado, desligue o que puder com segurança e chame pelo WhatsApp. Informe o bairro: confirmamos a disponibilidade para a sua região e combinamos o orçamento antes de começar.",
            ],
        },
        "telhadista": {
            "lead": "Telhadista na Zona Norte: telhas, calhas, rufos e infiltrações em casas, sobrados e galpões.",
            "body": [
                "Casas, sobrados e pequenos galpões comerciais são comuns na Zona Norte, muitos com coberturas de telha cerâmica ou de fibrocimento que sofrem com o tempo, o sol e a chuva forte.",
                "Se há goteira, mancha ou telha solta, conte pelo WhatsApp onde aparece e em qual bairro você está. A visita à Zona Norte é sujeita à análise do caso e ao deslocamento a partir da nossa base na Vila Gea.",
            ],
        },
    },
    {
        "slug": "zona-leste", "name": "Zona Leste", "in": "na Zona Leste de São Paulo",
        "examples": "Tatuapé, Mooca, Penha, Itaquera e São Mateus",
        "travel": "O deslocamento a partir da Vila Gea até a Zona Leste é maior, por isso a visita é sujeita à análise do caso e deslocamento.",
        "hidraulica": {
            "lead": "Encanador na Zona Leste de São Paulo, para casas, sobrados, prédios e comércios.",
            "body": [
                "A Zona Leste é uma das regiões mais extensas e populosas da capital e mistura bairros de prédios, como Tatuapé e Mooca, com grandes áreas residenciais de casas e sobrados, como Itaquera e São Mateus. A variedade de imóveis traz demandas diferentes de hidráulica.",
                "Em casas com caixa d'água no alto, entupimentos de ralos e vazamentos em registros são problemas típicos; em prédios, vazamentos em colunas. Fale pelo WhatsApp, informe o bairro e o problema, e confirmamos a disponibilidade antes de agendar.",
            ],
        },
        "eletrica": {
            "lead": "Eletricista na Zona Leste: instalações, reparos, tomadas, iluminação e quadros.",
            "body": [
                "Há na Zona Leste muitas casas que cresceram em etapas, com novos cômodos e novos andares. Quando a instalação não acompanha essas ampliações, aparecem sobrecargas, fios aquecendo e disjuntores desarmando.",
                "Adequar circuitos, trocar o quadro, instalar DR e criar novos pontos de energia são serviços que podemos avaliar. Envie o bairro e uma descrição do problema pelo WhatsApp; a visita é sujeita à análise do caso e ao deslocamento.",
            ],
        },
        "telhadista": {
            "lead": "Telhadista na Zona Leste: reparo de telhados, calhas, rufos e infiltrações.",
            "body": [
                "Na Zona Leste, casas com laje, sobrados e comércios de bairro convivem com prédios em regiões como Tatuapé e Mooca. Em cada um deles, a água da chuva precisa escoar bem pelo telhado, pelas calhas e pelos rufos.",
                "Se a goteira aparece só em chuva forte, a causa pode estar em uma telha deslocada, em um rufo ou em uma calha — só a visita permite confirmar. Informe o bairro e o ponto onde pinga para agendarmos a análise, sujeita a deslocamento.",
            ],
        },
    },
    {
        "slug": "centro", "name": "Centro", "in": "no Centro de São Paulo",
        "examples": "Higienópolis, Jardim Paulista, Bela Vista, Consolação e Santa Cecília",
        "travel": "Saindo da Vila Gea, o deslocamento até o Centro e as regras de acesso do prédio entram na combinação do atendimento.",
        "hidraulica": {
            "lead": "Encanador no Centro de São Paulo, para prédios antigos, apartamentos compactos e comércios.",
            "body": [
                "O Centro concentra prédios antigos, edifícios residenciais com muitas unidades, hotéis pequenos, lojas e escritórios. Tubulações mais antigas e colunas compartilhadas tornam o diagnóstico de vazamentos e entupimentos mais delicado.",
                "Em prédios, vale avisar a administração ou o zelador sobre o serviço. Pelo WhatsApp, informe o endereço aproximado, o andar e o que está acontecendo, para combinarmos o atendimento e o orçamento antes de começar.",
            ],
        },
        "eletrica": {
            "lead": "Eletricista no Centro de São Paulo: prédios antigos, lojas e escritórios.",
            "body": [
                "Prédios antigos do Centro foram projetados para uma demanda elétrica bem menor que a de hoje. Ar-condicionado, chuveiro elétrico e vários equipamentos no mesmo circuito podem sobrecarregar a instalação.",
                "Para lojas, escritórios e apartamentos, avaliamos quadros, disjuntores, fiação e pontos de tomada. A visita é sujeita à análise do caso e ao deslocamento a partir da Vila Gea; fale pelo WhatsApp para confirmar a disponibilidade e combinar o acesso ao prédio.",
            ],
        },
        "telhadista": {
            "lead": "Telhadista no Centro de São Paulo: coberturas, lajes, calhas e rufos de prédios e casarões.",
            "body": [
                "Coberturas de prédios antigos, casarões e galpões convivem no Centro com edifícios altos. Nesses imóveis, o acesso ao telhado costuma exigir combinação com a administração e cuidados extras de segurança.",
                "Infiltrações vindas de telhados, lajes de cobertura, calhas e rufos podem escorrer por vários andares antes de aparecer. Conte pelo WhatsApp onde a mancha surgiu e o tipo de edifício, para orientarmos a visita.",
            ],
        },
    },
    {
        "slug": "grande-sao-paulo", "name": "Grande São Paulo", "in": "na Grande São Paulo",
        "examples": "Alphaville e Tamboré (Barueri e Santana de Parnaíba), Aldeia da Serra, Granja Viana (Cotia), São Caetano do Sul, Santo André e São Bernardo do Campo",
        "travel": "Atendemos toda a Grande São Paulo a partir da nossa base na Vila Gea, com atenção especial a condomínios e bairros de alto padrão.",
        "hidraulica": {
            "lead": "Encanador na Grande São Paulo: Alphaville, Tamboré, Granja Viana, ABC e demais cidades da região metropolitana.",
            "body": [
                "A J.A Instalações atende toda a Grande São Paulo. Em condomínios horizontais como os de Alphaville, Tamboré e Granja Viana, são comuns casas grandes com vários banheiros, aquecimento central, piscina e caixas d'água de maior volume, o que pede diagnóstico cuidadoso de vazamentos e entupimentos.",
                "No ABC, em cidades como São Caetano do Sul e Santo André, atendemos prédios e casas, de colunas de água a desentupimentos. Informe pelo WhatsApp a cidade, o condomínio e o problema; a visita é sujeita à análise do caso e ao deslocamento, e combinamos com a portaria o acesso da equipe.",
            ],
        },
        "eletrica": {
            "lead": "Eletricista na Grande São Paulo: casas em condomínio, prédios e comércios em Alphaville, Granja Viana, ABC e região.",
            "body": [
                "Casas de alto padrão em condomínios fechados costumam ter muitos circuitos: iluminação de jardim, bombas de piscina, aquecedores, ar-condicionado e carregadores. Atendemos toda a Grande São Paulo com instalações, reparos, quadros e disjuntores para manter tudo seguro e organizado.",
                "Em Alphaville, Tamboré, Aldeia da Serra, Granja Viana e no ABC, conte pelo WhatsApp a cidade, o tipo de imóvel e o serviço. Alinhamos a visita, sujeita à análise do caso e ao deslocamento, e o orçamento antes de começar.",
            ],
        },
        "telhadista": {
            "lead": "Telhadista na Grande São Paulo: telhados, calhas e rufos em condomínios de Alphaville, Granja Viana, ABC e região.",
            "body": [
                "Casas grandes em condomínio têm telhados extensos, com muitas águas, calhas longas e rufos junto a platibandas. A J.A Instalações atende toda a Grande São Paulo com reparo e troca de telhas, manutenção preventiva, calhas, rufos e infiltrações.",
                "Em Alphaville, Tamboré, Granja Viana, São Caetano do Sul, Santo André e demais cidades da região, informe pelo WhatsApp o endereço, o tipo de telha e onde aparece a goteira. A visita é sujeita à análise do caso e ao deslocamento.",
            ],
        },
    },
]

# ============================================================================
# PÁGINAS DE BAIRRO (alto padrão) — no máximo 8, conteúdo próprio, sem prometer tempo de chegada.
# ============================================================================
NEIGHBORHOODS = [
    {
        "slug": "moema", "name": "Moema", "region": "zona-sul", "title_short": "Eletricista, encanador e telhadista em Moema",
        "context": "Moema fica ao lado do Parque Ibirapuera, na Zona Sul, e é vizinha da nossa região de base. O bairro reúne prédios residenciais de médio e alto padrão, muitos com apartamentos amplos, e ainda conserva casas e sobrados em ruas arborizadas, além de um comércio de rua movimentado.",
        "hid": "Em prédios de Moema, os chamados mais comuns são vazamentos que aparecem no teto do vizinho de baixo, registros e misturadores com defeito, aquecedores a gás e desentupimento de pias e ralos. Nas casas, entram também caixas d'água e tubulações antigas.",
        "ele": "Apartamentos reformados costumam ganhar cooktop, forno elétrico, ar-condicionado e iluminação embutida, o que pede revisão do quadro e dos circuitos. Fazemos troca de disjuntores e DR, novos pontos e adequações.",
        "tel": "Nas casas e sobrados do bairro, as chuvas de verão revelam telhas deslocadas, calhas entupidas por folhas das árvores e rufos sem vedação. Fazemos revisão, limpeza e reparo.",
        "tip": "Em condomínio, avise a administração e informe à equipe as regras de horário para obras e o acesso pela portaria.",
    },
    {
        "slug": "brooklin", "name": "Brooklin", "region": "zona-sul", "title_short": "Eletricista, encanador e telhadista no Brooklin",
        "context": "O Brooklin, na Zona Sul, mistura a área residencial de casas do Brooklin Velho com torres modernas perto da Berrini e da Avenida Roberto Marinho. É uma região próxima da nossa base na Vila Gea.",
        "hid": "Nas torres mais novas, atendemos registros, misturadores, aquecimento e vazamentos em shafts; nas casas do Brooklin Velho, tubulações antigas, caixas d'água e desentupimento de caixas de gordura.",
        "ele": "Escritórios e apartamentos com home office pedem mais tomadas, circuitos dedicados para ar-condicionado e iluminação. Nas casas antigas, a troca de fiação e do quadro de distribuição é frequente.",
        "tel": "As casas e sobrados do Brooklin Velho têm telhados de cerâmica com décadas de uso. Revisamos telhas, cumeeiras, calhas e rufos para eliminar goteiras e infiltrações.",
        "tip": "Para empresas e salas comerciais, combine com o condomínio o horário de serviço e informe se a obra precisa ser fora do expediente.",
    },
    {
        "slug": "campo-belo", "name": "Campo Belo", "region": "zona-sul", "title_short": "Eletricista, encanador e telhadista no Campo Belo",
        "context": "O Campo Belo, perto do Aeroporto de Congonhas e vizinho do Brooklin e de Moema, tem ruas residenciais com casas amplas e muitos prédios de alto padrão. Fica próximo da nossa base na Zona Sul.",
        "hid": "Casas grandes com vários banheiros, aquecimento central e piscina pedem diagnóstico cuidadoso de vazamentos e manutenção de registros e bombas. Também fazemos desentupimentos e consertos em apartamentos.",
        "ele": "Instalação de circuitos para aquecedores, bombas, ar-condicionado e iluminação externa, além de quadros, disjuntores e DR para mais segurança.",
        "tel": "Em casas com telhados extensos, calhas e rufos longos são pontos críticos. Fazemos limpeza, vedação e troca, além do reparo de telhas quebradas ou deslocadas.",
        "tip": "Se o imóvel tem piscina ou aquecimento solar, mencione isso no WhatsApp: ajuda a separar o material certo para a visita.",
    },
    {
        "slug": "vila-mariana", "name": "Vila Mariana", "region": "zona-sul", "title_short": "Eletricista, encanador e telhadista na Vila Mariana",
        "context": "A Vila Mariana, entre o Ibirapuera e o Paraíso, combina prédios de várias épocas com sobrados e casas de vila. É um bairro tradicional da Zona Sul, com metrô e comércio de bairro.",
        "hid": "Prédios mais antigos costumam ter colunas de água e tubulações de ferro galvanizado que corroem com o tempo. Atendemos vazamentos, trocas de trechos, registros e desentupimentos.",
        "ele": "Instalações elétricas antigas, com fiação subdimensionada e poucos circuitos, são comuns em casas e apartamentos do bairro. Fazemos troca de fiação, quadros e disjuntores e adequações para equipamentos atuais.",
        "tel": "Sobrados e casas de vila têm telhados com rufos encostados nas paredes vizinhas, ponto frequente de infiltração. Revisamos telhas, rufos e calhas.",
        "tip": "Em casas de vila ou geminadas, informe se o telhado é compartilhado com o vizinho, para alinharmos o acesso.",
    },
    {
        "slug": "itaim-bibi", "name": "Itaim Bibi", "region": "zona-oeste", "title_short": "Eletricista, encanador e telhadista no Itaim Bibi",
        "context": "O Itaim Bibi, perto da Faria Lima e da Vila Nova Conceição, é um dos bairros mais verticalizados de São Paulo, com torres residenciais de alto padrão, escritórios e restaurantes, além de ruas residenciais com casas.",
        "hid": "Em apartamentos de alto padrão, atendemos metais e misturadores, aquecedores, pressurizadores, vazamentos em shafts e desentupimentos, com cuidado com acabamentos de pedra e marcenaria.",
        "ele": "Reformas de apartamentos e escritórios pedem novos circuitos, iluminação embutida, automação simples e revisão do quadro. Fazemos instalações e reparos com acabamento limpo.",
        "tel": "Nas casas e coberturas do bairro, cuidamos de telhados, calhas e rufos, inclusive em áreas de terraço onde a água da chuva precisa escoar sem infiltrar.",
        "tip": "Em prédios comerciais e residenciais do Itaim, a portaria costuma exigir cadastro prévio da equipe: envie os dados do condomínio pelo WhatsApp.",
    },
    {
        "slug": "morumbi", "name": "Morumbi", "region": "zona-oeste", "title_short": "Eletricista, encanador e telhadista no Morumbi",
        "context": "O Morumbi, com a Cidade Jardim ao lado, reúne casas em lotes amplos, condomínios fechados e prédios de alto padrão, perto do Palácio dos Bandeirantes e do Parque Burle Marx.",
        "hid": "Casas grandes com muitos banheiros, piscina, aquecimento e sistemas de bombeamento pedem manutenção e diagnóstico de vazamentos ocultos. Atendemos também prédios e condomínios.",
        "ele": "Iluminação de jardim, portões automáticos, bombas, aquecedores e ar-condicionado exigem circuitos bem dimensionados. Fazemos instalações, reparos, quadros e disjuntores.",
        "tel": "Telhados extensos, com muitas águas e calhas longas, acumulam folhas das áreas verdes do bairro. Fazemos manutenção preventiva, limpeza de calhas e reparo de telhas e rufos.",
        "tip": "Em condomínios fechados, informe o nome do condomínio e as regras de acesso para a equipe.",
    },
    {
        "slug": "alphaville", "name": "Alphaville", "region": "grande-sao-paulo", "title_short": "Eletricista, encanador e telhadista em Alphaville",
        "context": "Alphaville, entre Barueri e Santana de Parnaíba, é formado por residenciais fechados com casas de médio e grande porte, além de um eixo de edifícios residenciais e empresariais. O Tamboré, ao lado, tem perfil semelhante.",
        "hid": "Casas em residenciais costumam ter vários banheiros, piscina, aquecimento solar ou a gás e reservatórios grandes. Atendemos vazamentos, registros, aquecimento, bombas e desentupimentos.",
        "ele": "Instalação e manutenção de circuitos para piscina, aquecedores, iluminação externa, portões e ar-condicionado, além de quadros, disjuntores e DR.",
        "tel": "Telhados amplos em residenciais pedem revisão periódica de telhas, calhas e rufos, principalmente antes da temporada de chuvas.",
        "tip": "Os residenciais de Alphaville e Tamboré exigem autorização de entrada para prestadores: informe o residencial e o nome do morador ao pedir o atendimento.",
    },
    {
        "slug": "granja-viana", "name": "Granja Viana", "region": "grande-sao-paulo", "title_short": "Eletricista, encanador e telhadista na Granja Viana",
        "context": "A Granja Viana, entre Cotia e Carapicuíba ao longo da Raposo Tavares, reúne condomínios fechados com casas grandes e muito verde, além de comércio e serviços próprios.",
        "hid": "Casas com poço, cisterna, bombas, aquecimento e piscina pedem cuidado especial com pressão de água, vazamentos e entupimentos. Atendemos consertos, detecção de vazamentos e desentupimentos.",
        "ele": "Em casas grandes, circuitos longos e muitos equipamentos externos exigem quadros bem organizados e proteção com DR. Fazemos instalações, reparos e adequações.",
        "tel": "A arborização abundante enche calhas de folhas e galhos, e telhados extensos sofrem com chuvas fortes. Fazemos limpeza de calhas, troca de telhas e vedação de rufos.",
        "tip": "Informe o condomínio e as regras de acesso de prestadores, e se a casa usa água de poço ou cisterna.",
    },
]

E = html.escape


def wa(text):
    return f"https://wa.me/{PHONE}?text={quote(text)}"


def plain(html_text):
    return html.unescape(re.sub(r"<[^>]+>", "", html_text))


# registro de páginas para o sitemap e o llms.txt: (path, título curto)
SITEMAP = []


def register(path, label):
    SITEMAP.append((path, label))


# ============================================================================
# JSON-LD
# ============================================================================
def jsonld(obj):
    data = json.dumps(obj, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{data}\n</script>'


def _business_core(schema_type):
    b = BUSINESS
    node = {
        "@type": schema_type,
        "@id": f"{SITE}/#negocio",
        "name": b["name"],
        "legalName": b["legal_name"],
        "taxID": b["cnpj"],
        "image": f"{SITE}/assets/logo.png",
        "logo": f"{SITE}/assets/logo.png",
        "telephone": f"+{b['phone_digits']}",
        "priceRange": b["price_range"],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": f'{b["street"]} - {b["neighborhood"]}',
            "addressLocality": b["city"],
            "addressRegion": b["region"],
            "postalCode": b["postal_code"],
            "addressCountry": b["country"],
        },
        "areaServed": b["area_served"],
        "hasMap": MAPS_URL,
        "sameAs": [b["google_profile"]] + SAME_AS_EXTRA,
    }
    if HORARIO:
        node["openingHoursSpecification"] = HORARIO
    if GEO:
        node["geo"] = {"@type": "GeoCoordinates", "latitude": GEO[0], "longitude": GEO[1]}
    if EMAIL:
        node["email"] = EMAIL
    # AggregateRating permanece desligado (PUBLISH_RATING = False). Ver comentário no topo.
    if PUBLISH_RATING and RATING_DISPLAY and REVIEWS_COUNT_DISPLAY:
        node["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": RATING_DISPLAY.replace(",", "."),
            "reviewCount": REVIEWS_COUNT_DISPLAY,
        }
    return node


def business_ld(schema_type, url, offers=None, reviews=None):
    node = {"@context": "https://schema.org"}
    node.update(_business_core(schema_type))
    node["url"] = url
    if offers:
        node["makesOffer"] = [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": n, "description": d}}
                              for n, d in offers]
    if reviews:
        node["review"] = [{"@type": "Review", "author": {"@type": "Person", "name": a}, "reviewBody": t,
                           "reviewRating": {"@type": "Rating", "ratingValue": "5", "bestRating": "5"}}
                          for t, a in reviews]
    return jsonld(node)


def service_ld(name, description, url, schema_type, area=None, service_type=None):
    node = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": name,
        "description": description,
        "url": url,
        "provider": {"@type": schema_type, "@id": f"{SITE}/#negocio", "name": BUSINESS["name"],
                     "telephone": f"+{PHONE}", "url": f"{SITE}/"},
        "areaServed": area if area else BUSINESS["area_served"],
    }
    if service_type:
        node["serviceType"] = service_type
    return jsonld(node)


def breadcrumb_ld(items):
    return jsonld({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [{"@type": "ListItem", "position": i, "name": n, "item": u}
                            for i, (n, u) in enumerate(items, 1)],
    })


def faq_ld(items):
    return jsonld({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": plain(a)}} for q, a in items],
    })


def webpage_ld(kind, name, url, description):
    return jsonld({"@context": "https://schema.org", "@type": kind, "name": name, "url": url,
                   "description": description, "inLanguage": "pt-BR",
                   "isPartOf": {"@type": "WebSite", "name": BUSINESS["name"], "url": f"{SITE}/"}})


# ============================================================================
# HTML
# ============================================================================
def head(p, canonical, title, description, schemas=(), robots=None):
    robots_tag = f'<meta name="robots" content="{robots}">\n' if robots else ""
    ld = "\n".join(schemas)
    ld = f"{ld}\n" if ld else ""
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{E(title)}</title>
<meta name="description" content="{E(description)}">
<link rel="canonical" href="{canonical}">
{robots_tag}<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="J.A Instalações">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{OG_IMAGE}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{E(OG_IMAGE_ALT)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{E(title)}">
<meta name="twitter:description" content="{E(description)}">
<meta name="twitter:image" content="{OG_IMAGE}">
<meta name="twitter:image:alt" content="{E(OG_IMAGE_ALT)}">
<meta name="theme-color" content="#0a2540">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="/assets/logo.png">
{ld}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/styles.css?v={CSS_VERSION}">
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


def header(current, contact_href="#contato", parent=None):
    def link(h, t):
        attr = ""
        if h == current:
            attr = ' aria-current="page"'
        elif h == parent:
            attr = ' aria-current="true"'
        return f'      <a href="{h}"{attr}>{E(t)}</a>'
    links = "\n".join(link(h, t) for h, t in NAV)
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


def breadcrumbs(items):
    """items: [(nome, url)] — o último é a página atual (sem link)."""
    parts = []
    for i, (n, u) in enumerate(items):
        if i == len(items) - 1:
            parts.append(f'<li aria-current="page">{E(n)}</li>')
        else:
            parts.append(f'<li><a href="{u}">{E(n)}</a></li>')
    return f"""
<nav class="breadcrumb" aria-label="Você está em">
  <div class="container">
    <ol>{"".join(parts)}</ol>
  </div>
</nav>
"""


def hero(p):
    visual = ('<img src="/assets/avatar-hero.webp" alt="Profissional da J.A Instalações com chave de grifo, fazendo sinal de positivo" class="hero-avatar" width="96" height="96">'
              if p["hero_img"] else f'<div class="hero-icon" aria-hidden="true">{p["hero_icon"]}</div>')

    def badge(b):
        if isinstance(b, tuple):
            return f'      <a class="badge badge-link" href="{E(b[2])}" target="_blank" rel="noopener">{E(b[1])}</a>'
        return f'      <span class="badge">{E(b)}</span>'
    badges = "\n".join(badge(b) for b in p["badges"])
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


def safe_short(short):
    """Resumo curto do serviço para schema e listagens (o texto 24h está confirmado)."""
    return short


def deep_for_card(key, card_title):
    for s in SERVICE_PAGES:
        if s["vertical"] == key and s["card"] == card_title:
            return s
    return None


def service_details_section(key, p):
    """Textos longos dos serviços no HTML visível (o modal continua funcionando via JS)."""
    items = []
    for ic, t, short, txt in p["services"]:
        deep = deep_for_card(key, t)
        more = (f' <a href="/{key}/{deep["slug"]}/">Saiba mais sobre {E(deep["name"].lower())} →</a>' if deep else "")
        wa_link = wa(f"Olá! Gostaria de solicitar o serviço: {t}")
        items.append(f"""      <article class="service-detail">
        <h3><span aria-hidden="true">{ic}</span> {E(t)}</h3>
        <p class="service-short">{E(short)}</p>
        <p>{E(txt)}</p>
        <p class="service-links"><a href="{E(wa_link)}" target="_blank" rel="noopener">Pedir orçamento no WhatsApp</a>{more}</p>
      </article>""")
    body = "\n".join(items)
    return f"""
<section class="section service-details" id="detalhes-servicos">
  <div class="container prose">
    <h2>Como funciona cada serviço de {E(p['name'].lower())}</h2>
    <p class="section-sub">Detalhes de cada serviço, sem precisar abrir nada</p>
{body}
  </div>
</section>
"""


def region_links_section(key, heading=None):
    p = PAGES[key]
    links = "\n".join(
        f'      <a href="/{key}/{r["slug"]}/">{E(p["noun"])} {E(r["in"])}</a>' for r in REGIONS)
    return f"""
<section class="section regions-links">
  <div class="container">
    <h2>{E(heading or "Atendimento por região")}</h2>
    <p class="section-sub">Atendemos toda a Grande São Paulo, com atenção especial a bairros e condomínios de alto padrão. Veja a página da sua região ou <a href="/areas-atendidas/">todas as áreas atendidas</a>.</p>
    <div class="cross-links">
{links}
    </div>
    <p class="section-sub regions-all"><a href="/areas-atendidas/">Ver todas as áreas atendidas →</a></p>
  </div>
</section>
"""


def faq_section(items, heading="Perguntas frequentes", sub=None, section_id="faq"):
    qs = "\n".join(f"""      <div class="faq-item">
        <h3>{E(q)}</h3>
        <p>{a}</p>
      </div>""" for q, a in items)
    sub_html = f'\n    <p class="section-sub">{E(sub)}</p>' if sub else ""
    return f"""
<section class="section faq" id="{section_id}">
  <div class="container prose">
    <h2>{E(heading)}</h2>{sub_html}
{qs}
  </div>
</section>
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


def home_info_section():
    """Bloco da home com serviços em texto + links para sobre, áreas e FAQ."""
    return f"""
<section class="section home-info">
  <div class="container prose">
    <h2>Eletricista, encanador e telhadista em São Paulo</h2>
    <p>A <strong>J.A Instalações</strong> é uma {E(PAGES['home']['about'])} que atende residências, prédios, condomínios e comércios em toda a Grande São Paulo, com atenção especial a bairros de alto padrão. Com um só contato você resolve problemas de <a href="/hidraulica/">hidráulica</a>, <a href="/eletrica/">elétrica</a> e <a href="/telhadista/">telhados</a>, com nota fiscal e garantia.</p>
    <p>Entre os serviços mais procurados estão <a href="/hidraulica/desentupimento/">desentupimento</a>, <a href="/hidraulica/deteccao-de-vazamentos/">detecção de vazamentos</a>, <a href="/eletrica/quadros-e-disjuntores/">quadros e disjuntores</a>, <a href="/telhadista/calhas-e-rufos/">calhas e rufos</a> e <a href="/telhadista/goteiras-e-infiltracoes/">goteiras e infiltrações</a>.</p>
    <div class="cross-links">
      <a href="/sobre/">Sobre a J.A Instalações</a>
      <a href="/areas-atendidas/">📍 Áreas atendidas</a>
      <a href="/faq/">Perguntas frequentes</a>
      <a href="/contato/">Contato</a>
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


def page_reviews(p):
    return REVIEWS_ALL if p["reviews"] == "all" else [r for r in REVIEWS_ALL if r[2] == "geral"]


def reviews_section(p):
    revs = page_reviews(p)
    items = "\n".join(f"""      <div class="review-item">
        <p class="review-stars">★★★★★</p>
        <p class="review-text">{E(t)}</p>
        <p class="review-author">{E(a)} · Google</p>
      </div>""" for t, a, _ in revs)
    visible = "\n".join(f"""      <div class="review-item">
        <p class="review-stars">★★★★★</p>
        <p class="review-text">{E(t)}</p>
        <p class="review-author">{E(a)} · Google</p>
      </div>""" for t, a, _ in revs[:3])
    # Nota visível (conferida em 12/11/2026), com link para o perfil. Sem AggregateRating no JSON-LD.
    summary = f"""<div class="review-summary">
      <span class="stars" aria-hidden="true">★★★★☆</span>
      <a class="review-google-link" href="{GOOGLE_PROFILE}" target="_blank" rel="noopener">{E(RATING_DISPLAY)} / {E(REVIEWS_COUNT_DISPLAY)} avaliações no Google</a>
    </div>"""
    return f"""
<section class="section reviews" id="avaliacoes">
  <div class="container">
    <h2>Avaliações</h2>
    {summary}
    <p class="section-sub">Clientes satisfeitos com nosso atendimento</p>
    <div class="review-cards">
{visible}
    </div>
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
    <a class="review-external-link" href="{GOOGLE_PROFILE}" target="_blank" rel="noopener">Ver todas as avaliações no Google Maps ↗</a>
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
        src="https://maps.google.com/maps?q={MAPS_EMBED_Q}&amp;output=embed"
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
    links = "\n".join(f'      <a href="{h}">{E(t)}</a>' for h, t in FOOTER_NAV)
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
    <div class="footer-contacts">
      <a class="footer-contact" href="https://wa.me/{PHONE}" target="_blank" rel="noopener">{WA_SVG.format(s=18)} WhatsApp {PHONE_FMT}</a>
      <a class="footer-contact" href="tel:+{PHONE}">📞 Ligar {PHONE_FMT}</a>
    </div>
    <nav class="footer-nav" aria-label="Rodapé">
{links}
    </nav>
    <p class="footer-meta">CNPJ: {CNPJ} · <a class="footer-email" href="mailto:{EMAIL}">{EMAIL}</a></p>
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


def write(path, out):
    target = ROOT / path / "index.html" if path else ROOT / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(out, encoding="utf-8")
    print("ok", target.relative_to(ROOT))


# ============================================================================
# Builders de página
# ============================================================================
def build_landing(key):
    p = PAGES[key]
    current = "/" + p["path"]
    canonical = f"{SITE}/{p['path']}"
    register(current, p["name"])

    schemas = []
    revs = [(t, a) for t, a, _ in page_reviews(p)]
    offers = [(t, safe_short(short)) for _, t, short, _ in p["services"]] if p["services"] else \
        [("Serviços hidráulicos", "Encanador, desentupimento e detecção de vazamentos"),
         ("Serviços elétricos", "Instalações, reparos, tomadas, iluminação, quadros e disjuntores"),
         ("Serviços de telhado", "Reparo e troca de telhas, manutenção, calhas, rufos e infiltrações")]
    schemas.append(business_ld(p["schema_type"], canonical, offers=offers, reviews=revs))
    faq = FAQ_VERTICAL.get(key)
    if key != "home":
        schemas.append(breadcrumb_ld([("Início", f"{SITE}/"), (p["name"], canonical)]))
    if faq:
        schemas.append(faq_ld(faq))

    out = head(p, canonical, p["title"], p["description"], schemas)
    out += header(current)
    if key != "home":
        out += breadcrumbs([("Início", "/"), (p["name"], current)])
    out += hero(p)
    if key == "home":
        out += areas_section() + steps_section() + home_info_section()
    else:
        out += services_section(p) + service_details_section(key, p) + steps_section()
        out += region_links_section(key)
        out += faq_section(faq, f"Perguntas frequentes sobre {p['name'].lower()}")
    out += lead_gate(p) + reviews_section(p) + contact_section(p)
    if key != "home":
        out += cross_section(current)
    out += location_section() + footer(p, current) + page_config(p)
    write(p["path"], out)


def inner_p(vertical, **over):
    """Dict de página para páginas internas (herda opções/greeting/slug da vertical ou da home)."""
    base = dict(PAGES[vertical] if vertical else PAGES["home"])
    base.update({"services": [], "hero_img": False, **over})
    return base


def prose_block(h2, paragraphs):
    ps = "\n".join(f"    <p>{E(t)}</p>" for t in paragraphs)
    return f"""
<section class="section prose-section">
  <div class="container prose">
    <h2>{E(h2)}</h2>
{ps}
  </div>
</section>
"""


def list_block(h2, items, intro=None):
    li = "\n".join(f"      <li>{E(i)}</li>" for i in items)
    intro_html = f"\n    <p>{E(intro)}</p>" if intro else ""
    return f"""
<section class="section prose-section">
  <div class="container prose">
    <h2>{E(h2)}</h2>{intro_html}
    <ul class="check-list">
{li}
    </ul>
  </div>
</section>
"""


def cta_row(wa_text):
    return f"""    <div class="cta-row">
      <a class="btn btn-primary btn-lg" href="{E(wa(wa_text))}" target="_blank" rel="noopener">{WA_SVG.format(s=20)} Pedir orçamento no WhatsApp</a>
      <a class="btn btn-outline btn-lg cta-call" href="tel:+{PHONE}">{TEL_SVG} Ligar: {PHONE_FMT}</a>
    </div>"""


def build_service_page(s):
    v = s["vertical"]
    vp = PAGES[v]
    path = f"{v}/{s['slug']}/"
    canonical = f"{SITE}/{path}"
    register("/" + path, s["name"])
    p = inner_p(v, body_class=f"page-{v}", title=s["title"], eyebrow=s["eyebrow"], h1=s["h1"], sub=s["sub"],
                hero_icon=s["icon"], wa_text=s["wa_text"],
                badges=["📍 Visita técnica sujeita a análise e deslocamento", "🧾 Nota fiscal e garantia", REVIEW_BADGE])
    crumbs = [("Início", "/"), (vp["name"], f"/{v}/"), (s["name"], "/" + path)]

    schemas = [
        business_ld(vp["schema_type"], f"{SITE}/", offers=[(s["name"], s["description"])]),
        service_ld(s["name"], s["description"], canonical, vp["schema_type"], service_type=s["name"]),
        breadcrumb_ld([(n, SITE + u) for n, u in crumbs]),
        faq_ld(s["faq"]),
    ]
    related = "\n".join(
        f'      <a href="/{v}/{r["slug"]}/">{E(r["name"])}</a>'
        for r in SERVICE_PAGES if r["vertical"] == v and r["slug"] in s["related"])
    related_block = f"""
<section class="section cross">
  <div class="container">
    <h2>Veja também</h2>
    <div class="cross-links">
{related}
      <a href="/{v}/">{E(vp['name'])}: todos os serviços</a>
      <a href="/faq/">Perguntas frequentes</a>
      <a href="/contato/">Contato</a>
    </div>
  </div>
</section>
"""
    how = "\n".join(f"    <p>{E(t)}</p>" for t in s["how"])
    how_block = f"""
<section class="section prose-section">
  <div class="container prose">
    <h2>Como a J.A Instalações atende</h2>
{how}
    <p>{E(SERVICE_STD)}</p>
{cta_row(s['wa_text'])}
  </div>
</section>
"""
    out = head(p, canonical, s["title"], s["description"], schemas)
    out += header("/" + path, parent=f"/{v}/") + breadcrumbs(crumbs) + hero(p)
    out += prose_block(f"{s['name']}: o que é e como funciona", s["intro"])
    out += list_block("Quando chamar", s["when"])
    out += how_block
    out += faq_section(s["faq"], "Perguntas frequentes", section_id="faq")
    out += region_links_section(v, f"{vp['noun']} por região")
    out += related_block
    out += lead_gate(p) + contact_section(p) + footer(p, "/" + path) + page_config(p)
    write(path, out)


def build_region_page(v, r):
    vp = PAGES[v]
    d = r[v]
    path = f"{v}/{r['slug']}/"
    canonical = f"{SITE}/{path}"
    register("/" + path, f"{vp['noun']} {r['in']}")
    noun = vp["noun"]
    h1 = f"{noun} {r['in']}"
    title = f"{h1} | J.A Instalações"
    _ex = [x.strip() for x in re.split(r",| e ", re.sub(r"\([^)]*\)", "", r["examples"])) if x.strip()]
    description = f"{noun} {r['in']}: atendimento em {', '.join(_ex[:3])} e região. Orçamento pelo WhatsApp com a J.A Instalações."
    if len(description) > 155:
        description = f"{noun} {r['in']}: atendimento em {', '.join(_ex[:2])} e região. Orçamento pelo WhatsApp."
    p = inner_p(v, body_class=f"page-{v}", title=title, eyebrow=f"{noun} · {r['name']}", h1=h1, sub=d["lead"],
                hero_icon=VERTICAL_ICON[v],
                badges=["📍 Visita técnica sujeita a análise e deslocamento", "🧾 Nota fiscal e garantia", REVIEW_BADGE],
                wa_text=f"Olá! Preciso de um {noun.lower()} {r['in']}.")
    crumbs = [("Início", "/"), (vp["name"], f"/{v}/"), (r["name"], "/" + path)]
    area = {"@type": "Place", "name": f"{r['name']}, São Paulo, SP" if r["slug"] != "grande-sao-paulo" else "Grande São Paulo, SP"}
    area = [area] + [{"@type": "Place", "name": x.strip()} for x in re.split(r",| e ", re.sub(r"\([^)]*\)", "", r["examples"])) if x.strip()]
    schemas = [
        business_ld(vp["schema_type"], f"{SITE}/", offers=[(f"{noun} {r['in']}", d["lead"])]),
        service_ld(h1, d["lead"], canonical, vp["schema_type"], area=area, service_type=vp["name"]),
        breadcrumb_ld([(n, SITE + u) for n, u in crumbs]),
    ]
    ref = (f"Atendemos bairros e cidades como {r['examples']}. Se o seu endereço não aparece aqui, "
           f"fale pelo WhatsApp: atendemos toda a Grande São Paulo.")
    body = "\n".join(f"    <p>{E(t)}</p>" for t in d["body"])
    svc_items = []
    for _, t, short, _ in vp["services"]:
        deep = deep_for_card(v, t)
        label = f'<a href="/{v}/{deep["slug"]}/">{E(t)}</a>' if deep else E(t)
        svc_items.append(f"      <li>{label} — {E(safe_short(short))}</li>")
    services = "\n".join(svc_items)
    others_zone = "\n".join(
        f'      <a href="/{rv}/{r["slug"]}/">{E(PAGES[rv]["noun"])} {E(r["in"])}</a>' for rv in VERTICALS if rv != v)
    other_regions = "\n".join(
        f'      <a href="/{v}/{o["slug"]}/">{E(noun)} {E(o["in"])}</a>' for o in REGIONS if o["slug"] != r["slug"])
    consulta_note = ""
    nb_links = [n for n in NEIGHBORHOODS if n["region"] == r["slug"]]
    if nb_links:
        consulta_note = "\n    <p>Páginas de bairro: " + ", ".join(
            f'<a href="/bairros/{n["slug"]}/">{E(n["name"])}</a>' for n in nb_links) + ".</p>"
    main = f"""
<section class="section prose-section">
  <div class="container prose">
    <h2>{E(noun)} {E(r['in'])}: como funciona o atendimento</h2>
{body}
    <p>{E(r['travel'])}</p>{consulta_note}
    <p class="note">{E(ref)}</p>
{cta_row(p['wa_text'])}
  </div>
</section>

<section class="section prose-section">
  <div class="container prose">
    <h2>Serviços de {E(vp['name'].lower())} que fazemos</h2>
    <ul class="check-list">
{services}
    </ul>
    <p>{E(SERVICE_STD)}</p>
    <p>Dúvidas comuns sobre o atendimento estão em <a href="/faq/">perguntas frequentes</a>; conheça também a <a href="/{v}/">página de {E(vp['name'].lower())}</a> e as <a href="/areas-atendidas/">áreas atendidas</a>.</p>
  </div>
</section>

<section class="section cross">
  <div class="container">
    <h2>Outros serviços {E(r['in'])}</h2>
    <div class="cross-links">
{others_zone}
    </div>
    <h2 class="h2-spaced">{E(noun)} em outras regiões</h2>
    <div class="cross-links">
{other_regions}
    </div>
  </div>
</section>
"""
    out = head(p, canonical, title, description, schemas)
    out += header("/" + path, parent=f"/{v}/") + breadcrumbs(crumbs) + hero(p) + main
    out += lead_gate(p) + contact_section(p) + footer(p, "/" + path) + page_config(p)
    write(path, out)


def build_neighborhood_page(n):
    path = f"bairros/{n['slug']}/"
    canonical = f"{SITE}/{path}"
    register("/" + path, n["title_short"])
    region = next(r for r in REGIONS if r["slug"] == n["region"])
    in_ = "na" if n["name"] in ("Vila Mariana", "Granja Viana") else ("no" if n["name"] in ("Brooklin", "Campo Belo", "Itaim Bibi", "Morumbi") else "em")
    h1 = f"Eletricista, encanador e telhadista {in_} {n['name']}"
    title = f"{h1} | J.A Instalações"
    description = (f"Hidráulica, elétrica e telhados {in_} {n['name']}: atendimento 24h para casas, prédios e condomínios "
                   f"de alto padrão, com nota fiscal e garantia. Peça orçamento pelo WhatsApp.")
    wa_text = f"Olá! Preciso de atendimento {in_} {n['name']}."
    p = inner_p(None, body_class="page-home", title=title, eyebrow=f"Bairros · {n['name']}", h1=h1,
                sub=f"Hidráulica, elétrica e telhados {in_} {n['name']}, com atendimento 24h, nota fiscal e garantia.",
                hero_icon="📍", wa_text=wa_text,
                badges=["⚡ Atendimento 24h", "🧾 Nota fiscal e garantia", REVIEW_BADGE], slug="home")
    crumbs = [("Início", "/"), ("Áreas atendidas", "/areas-atendidas/"), (n["name"], "/" + path)]
    area = {"@type": "Place", "name": f"{n['name']}, SP"}
    schemas = [
        business_ld("HomeAndConstructionBusiness", f"{SITE}/",
                    offers=[(f"Encanador {in_} {n['name']}", n["hid"]), (f"Eletricista {in_} {n['name']}", n["ele"]),
                            (f"Telhadista {in_} {n['name']}", n["tel"])]),
        service_ld(h1, n["context"], canonical, "HomeAndConstructionBusiness", area=area,
                   service_type="Elétrica, hidráulica e telhados"),
        breadcrumb_ld([(nm, SITE + u) for nm, u in crumbs]),
    ]
    others = "\n".join(f'      <a href="/bairros/{o["slug"]}/">{E(o["name"])}</a>' for o in NEIGHBORHOODS if o["slug"] != n["slug"])
    verts = "\n".join(f'      <a href="/{v}/{region["slug"]}/">{E(PAGES[v]["noun"])} {E(region["in"])}</a>' for v in VERTICALS)
    main = f"""
<section class="section prose-section">
  <div class="container prose">
    <h2>Atendimento {E(in_)} {E(n['name'])}</h2>
    <p>{E(n['context'])}</p>
    <p>A J.A Instalações atende {E(in_)} {E(n['name'])} 24 horas, todos os dias, para residências, prédios, condomínios e comércios. A visita técnica tem custo sujeito à análise do caso e ao deslocamento; escopo, valores e agendamento são combinados antes de começar, com nota fiscal, garantia e pagamento facilitado.</p>
{cta_row(wa_text)}
  </div>
</section>

<section class="section prose-section">
  <div class="container prose">
    <h2>Hidráulica {E(in_)} {E(n['name'])}</h2>
    <p>{E(n['hid'])} Veja <a href="/hidraulica/">encanador</a>, <a href="/hidraulica/deteccao-de-vazamentos/">detecção de vazamentos</a> e <a href="/hidraulica/desentupimento/">desentupimento</a>.</p>
    <h2>Elétrica {E(in_)} {E(n['name'])}</h2>
    <p>{E(n['ele'])} Veja <a href="/eletrica/">eletricista</a> e <a href="/eletrica/quadros-e-disjuntores/">quadros e disjuntores</a>.</p>
    <h2>Telhados {E(in_)} {E(n['name'])}</h2>
    <p>{E(n['tel'])} Veja <a href="/telhadista/">telhadista</a> e <a href="/telhadista/calhas-e-rufos/">calhas e rufos</a>.</p>
    <p class="note">{E(n['tip'])}</p>
  </div>
</section>

<section class="section cross">
  <div class="container">
    <h2>{E(region['name'])}</h2>
    <div class="cross-links">
{verts}
    </div>
    <h2 class="h2-spaced">Outros bairros atendidos</h2>
    <div class="cross-links">
{others}
      <a href="/areas-atendidas/">Todas as áreas</a>
    </div>
  </div>
</section>
"""
    out = head(p, canonical, title, description, schemas)
    out += header("/" + path, parent="/areas-atendidas/") + breadcrumbs(crumbs) + hero(p) + main
    out += lead_gate(p) + contact_section(p) + footer(p, "/" + path) + page_config(p)
    write(path, out)


def build_areas_page():
    path = "areas-atendidas/"
    canonical = f"{SITE}/{path}"
    register("/" + path, "Áreas atendidas")
    title = "Áreas atendidas em São Paulo e Grande SP | J.A Instalações"
    description = ("Hidráulica, elétrica e telhados 24h em toda a Grande São Paulo, com foco em bairros de alto "
                   "padrão como Moema, Itaim Bibi, Morumbi e Alphaville.")
    p = inner_p(None, body_class="page-home", title=title, eyebrow="Atendimento em toda a Grande São Paulo",
                h1="Áreas atendidas em São Paulo e Grande São Paulo",
                sub="Atendemos toda a Grande São Paulo, com atenção especial a bairros e condomínios de alto padrão.",
                hero_icon="📍", wa_text="Olá! Gostaria de um orçamento para o meu endereço.",
                badges=["⚡ Atendimento 24h", "🧾 Nota fiscal e garantia", REVIEW_BADGE],
                slug="areas")
    crumbs = [("Início", "/"), ("Áreas atendidas", "/" + path)]
    def _ex_html(r):
        parts, names = [], [n for n in NEIGHBORHOODS if n["region"] == r["slug"]]
        raw = r["examples"]
        # liga o nome do bairro quando há página própria
        for n in names:
            raw = raw.replace(n["name"], f'\x00{n["slug"]}\x00')
        # re.split conservando o texto em volta
        acc = raw
        for n in names:
            acc = acc.replace(f'\x00{n["slug"]}\x00', f'<a href="/bairros/{n["slug"]}/">{E(n["name"])}</a>')
        return acc
    cards = []
    for r in REGIONS:
        links = "\n".join(
            f'          <a href="/{v}/{r["slug"]}/">{E(PAGES[v]["noun"])} {E(r["in"])}</a>' for v in VERTICALS)
        cards.append(f"""      <article class="area-region">
        <h3>{E(r['name'])}</h3>
        <p>Atendemos bairros e cidades como {_ex_html(r)}.</p>
        <div class="cross-links cross-links-start">
{links}
        </div>
      </article>""")
    nb_cards = "\n".join(
        f"""      <article class="area-region">
        <h3><a href="/bairros/{n['slug']}/">{E(n['name'])}</a></h3>
        <p>{E(n['context'].split('.')[0] + '.')}</p>
        <p><a href="/bairros/{n['slug']}/">Ver página de {E(n['name'])} →</a></p>
      </article>""" for n in NEIGHBORHOODS)
    body = f"""
<section class="section prose-section">
  <div class="container prose">
    <h2>Atendemos toda a Grande São Paulo</h2>
    <p>A J.A Instalações atende residências, prédios, condomínios e comércios em toda a Grande São Paulo, com atenção especial a bairros e condomínios de alto padrão. A nossa base fica na Vila Gea, na Zona Sul da capital, e o atendimento é 24 horas, todos os dias, com nota fiscal, garantia e pagamento facilitado.</p>
    <p>Abaixo estão as regiões com página própria e os bairros de alto padrão com página dedicada. Se o seu endereço não aparece nesta lista, fale pelo WhatsApp ou pelo <a href="/contato/">formulário de contato</a>: atendemos toda a região metropolitana. A visita técnica tem custo sujeito à análise do caso e ao deslocamento.</p>
  </div>
</section>

<section class="section area-regions">
  <div class="container prose">
    <h2>Regiões</h2>
{chr(10).join(cards)}
  </div>
</section>

<section class="section area-regions">
  <div class="container prose">
    <h2>Bairros e condomínios de alto padrão</h2>
{nb_cards}
  </div>
</section>

<section class="section cross">
  <div class="container">
    <h2>Serviços</h2>
    <div class="cross-links">
      <a href="/hidraulica/">🚿 Hidráulica</a>
      <a href="/eletrica/">⚡ Elétrica</a>
      <a href="/telhadista/">🏠 Telhados</a>
      <a href="/faq/">Perguntas frequentes</a>
    </div>
  </div>
</section>
"""
    schemas = [business_ld("HomeAndConstructionBusiness", f"{SITE}/"),
               webpage_ld("CollectionPage", "Áreas atendidas", canonical, description),
               breadcrumb_ld([(n, SITE + u) for n, u in crumbs])]
    out = head(p, canonical, title, description, schemas)
    out += header("/" + path, "/contato/") + breadcrumbs(crumbs) + hero(p) + body
    out += lead_gate(p) + contact_section(p) + footer(p, "/" + path) + page_config(p)
    write(path, out)


def build_faq_page():
    path = "faq/"
    canonical = f"{SITE}/{path}"
    register("/" + path, "Perguntas frequentes")
    title = "Perguntas frequentes | Encanador, eletricista e telhadista | J.A Instalações"
    description = ("Dúvidas sobre orçamento, visita técnica, nota fiscal, garantia, áreas atendidas e serviços de "
                   "hidráulica, elétrica e telhados da J.A Instalações. Fale pelo WhatsApp.")
    p = inner_p(None, body_class="page-home", title=title, eyebrow="Perguntas frequentes",
                h1="Perguntas frequentes sobre os serviços da J.A Instalações",
                sub="Orçamento, visita técnica, nota fiscal, áreas atendidas e dúvidas de hidráulica, elétrica e telhados.",
                hero_icon="❓", wa_text="Olá! Tenho uma dúvida sobre os serviços.",
                badges=["📍 Visita técnica sujeita a análise e deslocamento", "🧾 Nota fiscal e garantia", REVIEW_BADGE],
                slug="faq")
    crumbs = [("Início", "/"), ("Perguntas frequentes", "/" + path)]
    all_items = list(FAQ_COMMON)
    body = faq_section(FAQ_COMMON, "Orçamento e atendimento", section_id="faq-geral")
    for v in VERTICALS:
        body += faq_section(FAQ_VERTICAL[v], f"Dúvidas sobre {PAGES[v]['name'].lower()}", section_id=f"faq-{v}")
        all_items += FAQ_VERTICAL[v]
    body += f"""
<section class="section cross">
  <div class="container">
    <h2>Não encontrou a sua dúvida?</h2>
    <p class="section-sub">Fale com a gente pelo WhatsApp ou pelo telefone {PHONE_FMT}.</p>
    <div class="cross-links">
      <a href="/contato/">Contato</a>
      <a href="/sobre/">Sobre a J.A</a>
      <a href="/areas-atendidas/">📍 Áreas atendidas</a>
    </div>
  </div>
</section>
"""
    schemas = [business_ld("HomeAndConstructionBusiness", f"{SITE}/"),
               faq_ld(all_items), breadcrumb_ld([(n, SITE + u) for n, u in crumbs])]
    out = head(p, canonical, title, description, schemas)
    out += header("/" + path, "/contato/") + breadcrumbs(crumbs) + hero(p) + body
    out += lead_gate(p) + contact_section(p) + footer(p, "/" + path) + page_config(p)
    write(path, out)


def build_about_page():
    path = "sobre/"
    canonical = f"{SITE}/{path}"
    register("/" + path, "Sobre")
    title = "Sobre a J.A Instalações | Elétrica, hidráulica e telhados em SP"
    description = ("Conheça a J.A Instalações: prestadora de serviços de elétrica, hidráulica e telhados em São Paulo "
                   "e Grande São Paulo, com nota fiscal e garantia. Fale pelo WhatsApp.")
    p = inner_p(None, body_class="page-home", title=title, eyebrow="Sobre a J.A Instalações",
                h1="Sobre a J.A Instalações: elétrica, hidráulica e telhados em São Paulo",
                sub="Um só contato para cuidar da sua casa, prédio ou comércio.",
                hero_icon="", hero_img=True, wa_text="Olá! Gostaria de saber mais sobre os serviços da J.A Instalações.",
                badges=["🧾 Nota fiscal e garantia", "⚡ Atendimento 24h", REVIEW_BADGE], slug="sobre")
    crumbs = [("Início", "/"), ("Sobre", "/" + path)]
    steps = "\n".join(f"""      <div class="step"><div class="step-num">{i}</div><h3>{E(t)}</h3><p>{E(d)}</p></div>"""
                      for i, (t, d) in enumerate(STEPS, 1))
    # NAP e dados da empresa: valores de BUSINESS (telefone, endereço e 24h já confirmados).
    body = f"""
<section class="section prose-section">
  <div class="container prose">
    <h2>Quem somos</h2>
    <p>A <strong>J.A Instalações</strong> é uma prestadora de serviços de elétrica, hidráulica e telhados que atende residências, prédios, condomínios e comércios em toda a Grande São Paulo, com atenção especial a bairros e condomínios de alto padrão. A ideia é simples: um só contato para resolver problemas da casa, do prédio ou do negócio, com atendimento rápido, nota fiscal e garantia.</p>
    <p>Atuamos em três frentes: <a href="/hidraulica/">hidráulica</a> (encanador, consertos, desentupimento e detecção de vazamentos), <a href="/eletrica/">elétrica</a> (instalações, reparos, tomadas, iluminação, quadros e disjuntores) e <a href="/telhadista/">telhados</a> (reparo e troca de telhas, manutenção, calhas, rufos, goteiras e infiltrações).</p>
  </div>
</section>

<section class="section prose-section">
  <div class="container prose">
    <h2>Dados da empresa</h2>
    <dl class="facts">
      <dt>Nome fantasia</dt><dd>{E(BUSINESS['name'])}</dd>
      <dt>Razão social</dt><dd>{E(BUSINESS['legal_name'])}</dd>
      <dt>CNPJ</dt><dd>{CNPJ}</dd>
      <dt>Endereço</dt><dd><a href="{E(MAPS_URL)}" target="_blank" rel="noopener">{E(ADDRESS)}</a></dd>
      <dt>Telefone e WhatsApp</dt><dd><a href="tel:+{PHONE}">{PHONE_FMT}</a></dd>
      <dt>E-mail</dt><dd><a href="mailto:{EMAIL}">{EMAIL}</a></dd>
      <dt>Horário</dt><dd>Atendimento 24 horas, todos os dias</dd>
      <dt>Área de atendimento</dt><dd>Toda a Grande São Paulo, com foco em bairros e condomínios de alto padrão (veja as <a href="/areas-atendidas/">áreas atendidas</a>)</dd>
    </dl>
  </div>
</section>

<section class="section">
  <div class="container">
    <h2>Como trabalhamos</h2>
    <p class="section-sub">Menos dor de cabeça, mais tranquilidade</p>
    <div class="steps">
{steps}
    </div>
  </div>
</section>

<section class="section prose-section">
  <div class="container prose">
    <h2>Nota fiscal e garantia</h2>
    <p>Os serviços da J.A Instalações são feitos com nota fiscal e garantia. A visita técnica tem custo sujeito à análise do caso e ao deslocamento, e o escopo, os valores e o agendamento são alinhados antes do início do serviço.</p>
    <h2>Fale com a gente</h2>
    <p>Você pode pedir orçamento pelo WhatsApp, pelo telefone {PHONE_FMT} ou pelo <a href="/contato/">formulário de contato</a>. Veja também as <a href="{GOOGLE_PROFILE}" target="_blank" rel="noopener">avaliações de clientes no Google</a> e as <a href="/faq/">perguntas frequentes</a>.</p>
{cta_row(p['wa_text'])}
  </div>
</section>
"""
    schemas = [business_ld("HomeAndConstructionBusiness", f"{SITE}/"),
               webpage_ld("AboutPage", "Sobre a J.A Instalações", canonical, description),
               breadcrumb_ld([(n, SITE + u) for n, u in crumbs])]
    out = head(p, canonical, title, description, schemas)
    out += header("/" + path, "/contato/") + breadcrumbs(crumbs) + hero(p) + body
    out += lead_gate(p) + contact_section(p) + footer(p, "/" + path) + page_config(p)
    write(path, out)


def build_contact_page():
    path = "contato/"
    canonical = f"{SITE}/{path}"
    register("/" + path, "Contato")
    title = "Contato e orçamento | Eletricista, encanador e telhadista | J.A Instalações"
    description = ("Fale com a J.A Instalações pelo WhatsApp, telefone ou formulário e peça seu orçamento de "
                   "elétrica, hidráulica ou telhados em São Paulo.")
    # Formulário próprio desta página: name="contato-pagina" (mesmos campos dos demais formulários).
    p = inner_p(None, body_class="page-home", title=title, eyebrow="Contato",
                h1="Contato e orçamento: fale com a J.A Instalações",
                sub="Peça seu orçamento pelo WhatsApp, pelo telefone ou pelo formulário abaixo.",
                hero_icon="", hero_img=True, wa_text="Olá! Gostaria de solicitar um orçamento.",
                badges=["📍 Visita técnica sujeita a análise e deslocamento", "🧾 Nota fiscal e garantia", REVIEW_BADGE],
                slug="pagina")
    p["greeting"] = PAGES["home"]["greeting"]
    crumbs = [("Início", "/"), ("Contato", "/" + path)]
    info = f"""
<section class="section prose-section">
  <div class="container prose">
    <h2>Como falar com a gente</h2>
    <dl class="facts">
      <dt>WhatsApp</dt><dd><a href="https://wa.me/{PHONE}" target="_blank" rel="noopener">{PHONE_FMT}</a></dd>
      <dt>Telefone</dt><dd><a href="tel:+{PHONE}">{PHONE_FMT}</a></dd>
      <dt>E-mail</dt><dd><a href="mailto:{EMAIL}">{EMAIL}</a></dd>
      <dt>Endereço</dt><dd><a href="{E(MAPS_URL)}" target="_blank" rel="noopener">{E(ADDRESS)}</a></dd>
      <dt>Horário</dt><dd>Atendimento 24 horas, todos os dias</dd>
      <dt>Área de atendimento</dt><dd>Toda a Grande São Paulo, com foco em bairros e condomínios de alto padrão (<a href="/areas-atendidas/">áreas atendidas</a>)</dd>
    </dl>
    <p>A visita técnica tem custo sujeito à análise do caso e ao deslocamento. Escopo, valores e agendamento são alinhados antes de começar. Dúvidas frequentes estão em <a href="/faq/">perguntas frequentes</a>.</p>
  </div>
</section>
"""
    schemas = [business_ld("HomeAndConstructionBusiness", f"{SITE}/"),
               webpage_ld("ContactPage", "Contato", canonical, description),
               breadcrumb_ld([(n, SITE + u) for n, u in crumbs])]
    out = head(p, canonical, title, description, schemas)
    out += header("/" + path) + breadcrumbs(crumbs) + hero(p) + info
    out += lead_gate(p) + contact_section(p) + location_section() + footer(p, "/" + path) + page_config(p)
    write(path, out)


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


def build_simple(path, title, description, body, robots=None, schemas=()):
    """Privacidade e 404: NÃO herdam schema de negócio nem AggregateRating."""
    p = {"body_class": "page-legal"}
    out = head(p, f"{SITE}/{path}", title, description, schemas, robots=robots)
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


# ============================================================================
# robots.txt, sitemap.xml, llms.txt
# ============================================================================
ROBOTS_BOTS = ["GPTBot", "ChatGPT-User", "ClaudeBot", "Anthropic-AI", "Google-Extended", "PerplexityBot", "Applebot-Extended"]


def build_robots():
    out = "User-agent: *\nAllow: /\n\n"
    for b in ROBOTS_BOTS:
        out += f"User-agent: {b}\nAllow: /\n\n"
    out += f"Sitemap: {SITE}/sitemap.xml\n"
    (ROOT / "robots.txt").write_text(out, encoding="utf-8")
    print("ok robots.txt")


def build_sitemap():
    rows = "\n".join(
        f"  <url>\n    <loc>{xml_escape(SITE + path)}</loc>\n    <lastmod>{BUILD_DATE}</lastmod>\n  </url>"
        for path, _ in SITEMAP)
    out = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}\n</urlset>\n'
    (ROOT / "sitemap.xml").write_text(out, encoding="utf-8")
    print("ok sitemap.xml", len(SITEMAP), "URLs")


def build_llms():
    def line(path, label):
        return f"- [{label}]({SITE}{path})"
    main = [("/", "Início"), ("/hidraulica/", "Hidráulica (encanador)"), ("/eletrica/", "Elétrica (eletricista)"),
            ("/telhadista/", "Telhados (telhadista)"), ("/sobre/", "Sobre a J.A Instalações"),
            ("/faq/", "Perguntas frequentes"), ("/contato/", "Contato e orçamento"),
            ("/areas-atendidas/", "Áreas atendidas"), ("/privacidade/", "Política de Privacidade")]
    deep = [(f"/{s['vertical']}/{s['slug']}/", s["name"]) for s in SERVICE_PAGES]
    out = f"""# {BUSINESS['name']}

> {BUSINESS['name']} é uma prestadora de serviços de elétrica, hidráulica e telhados que atende residências, prédios, condomínios e comércios em toda a Grande São Paulo, com atenção especial a bairros e condomínios de alto padrão.

## Dados da empresa

- Nome fantasia: {BUSINESS['name']}
- Razão social: {BUSINESS['legal_name']}
- CNPJ: {CNPJ}
- Endereço: {ADDRESS}
- Telefone e WhatsApp: {PHONE_FMT}
- E-mail: {EMAIL}
- Horário: atendimento 24 horas, todos os dias
- Área de atendimento: toda a Grande São Paulo, com foco em bairros e condomínios de alto padrão ({", ".join(AREA_NOBRE_SP)}; {", ".join(n for n, _ in AREA_NOBRE_GRANDE_SP)})
- Formas de pagamento: pagamento facilitado, combinado junto com o orçamento

## Serviços

- Hidráulica (encanador): consertos, desentupimento de pias, ralos, vasos e tubulações, detecção de vazamentos e atendimento urgente.
- Elétrica (eletricista): instalações e reparos, tomadas, interruptores, iluminação, quadros de distribuição, disjuntores e DR.
- Telhados (telhadista): reparo e troca de telhas, manutenção de telhados, calhas, rufos, goteiras e infiltrações.

## Como pedir orçamento

- WhatsApp ou telefone: {PHONE_FMT}
- Formulário na página de contato: {SITE}/contato/
- A visita técnica tem custo sujeito à análise do caso e ao deslocamento. Escopo, valores e agendamento são alinhados antes de começar. Serviços com nota fiscal e garantia.

## Páginas principais

{chr(10).join(line(*m) for m in main)}

## Serviços em detalhe

{chr(10).join(line(*d) for d in deep)}

## Regiões

{chr(10).join(line(f"/{v}/{r['slug']}/", f"{PAGES[v]['noun']} {r['in']}") for r in REGIONS for v in VERTICALS)}

## Bairros

{chr(10).join(line(f"/bairros/{n['slug']}/", n['title_short']) for n in NEIGHBORHOODS)}

## Privacidade

A política de privacidade está em {SITE}/privacidade/.
"""
    (ROOT / "llms.txt").write_text(out, encoding="utf-8")
    print("ok llms.txt")


if __name__ == "__main__":
    for k in PAGES:
        build_landing(k)
    build_about_page()
    build_faq_page()
    build_contact_page()
    build_areas_page()
    for s in SERVICE_PAGES:
        build_service_page(s)
    for r in REGIONS:
        for v in VERTICALS:
            build_region_page(v, r)
    for n in NEIGHBORHOODS:
        build_neighborhood_page(n)
    register("/privacidade/", "Política de Privacidade")
    build_simple("privacidade/", "Política de Privacidade | J.A Instalações",
                 "Política de Privacidade da J.A Instalações, conforme a LGPD.", PRIVACY_BODY,
                 schemas=[webpage_ld("WebPage", "Política de Privacidade", f"{SITE}/privacidade/",
                                     "Política de Privacidade da J.A Instalações, conforme a LGPD.")])
    build_simple("", "Página não encontrada | J.A Instalações",
                 "Página não encontrada.", NOT_FOUND, robots="noindex")
    build_robots()
    build_sitemap()
    build_llms()
