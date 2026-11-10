# J.A Instalações — site (Netlify)

Site estático, sem build. Páginas (cada uma funciona como landing page):

| URL | Arquivo |
|---|---|
| `/` | `index.html` (institucional, leva às 3 áreas) |
| `/hidraulica/` | `hidraulica/index.html` |
| `/eletrica/` | `eletrica/index.html` |
| `/telhadista/` | `telhadista/index.html` |
| `/privacidade/` | `privacidade/index.html` |

- Visual: `assets/styles.css` · Comportamento (WhatsApp com captura de lead, Lead Hub, GTM, UTMs, carrossel, formulário Netlify): `assets/script.js`
- Textos/serviços: edite `tools/build.py` e rode `python3 tools/build.py` para regerar os HTML.
- Formulários aparecem no painel do Netlify como `contato-home`, `contato-hidraulica`, `contato-eletrica`, `contato-telhadista`.
- `netlify.toml` redireciona `hidraulica.jainstalacoes.com` → `jainstalacoes.com/hidraulica/`.
