import json
import hmac
import os
import re
import secrets
import time
import unicodedata
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

import bleach
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from markupsafe import Markup
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
# In local dev: app.py lives in niblo_site/, static files in niblo_site/landing-page-niblo/
# On Vercel/production: app.py and static files are both at repo root
_landing_subdir = BASE_DIR / "landing-page-niblo"
SITE_DIR = _landing_subdir if _landing_subdir.is_dir() else BASE_DIR
# On Vercel the filesystem is read-only except /tmp; seed committed data/ on first boot
_IS_VERCEL = bool(os.environ.get("VERCEL"))
_COMMITTED_DATA = BASE_DIR / "data"
DATA_DIR = Path("/tmp/niblo-data") if _IS_VERCEL else _COMMITTED_DATA
POSTS_FILE = DATA_DIR / "posts.json"
SITE_CONTENT_FILE = DATA_DIR / "site_content.json"
IMAGES_DIR = SITE_DIR / "images"
IS_PRODUCTION = bool(os.environ.get("VERCEL") or os.environ.get("NIBLO_ENV") == "production" or os.environ.get("FLASK_ENV") == "production")
ADMIN_USERNAME = os.environ.get("NIBLO_ADMIN_USERNAME", "niblo")
ADMIN_PASSWORD_HASH = os.environ.get(
    "NIBLO_ADMIN_PASSWORD_HASH",
    "scrypt:32768:8:1$PXwfhLtXiWiHpJnT$20fff7e890bc7d6031f6253df2985feea04cee876712f445b334ceda2eef96750c0e309a5ea9fa4eb3fd3e8409f391aee8a1ed27256fcb04d7f6e37269246d1b",
)
ADMIN_PASSWORD_LEGACY = os.environ.get("NIBLO_ADMIN_PASSWORD", "") if not IS_PRODUCTION else ""
ADMIN_SLUG = "acesso-interno-cloud-2026"
ALLOWED_MEDIA_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".mp4",
    ".webm",
    ".avif",
}
ALLOWED_MEDIA_MIME_TYPES = {
    ".png": {"image/png"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".webp": {"image/webp"},
    ".gif": {"image/gif"},
    ".avif": {"image/avif"},
    ".mp4": {"video/mp4"},
    ".webm": {"video/webm"},
}
ALLOWED_HTML_TAGS = {
    "a", "blockquote", "br", "code", "div", "em", "figcaption", "figure",
    "h1", "h2", "h3", "h4", "hr", "img", "li", "ol", "p", "pre", "span",
    "strong", "u", "ul",
}
ALLOWED_HTML_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "div": ["class"],
    "figure": ["class"],
    "figcaption": ["class"],
    "h1": ["class"],
    "h2": ["class"],
    "h3": ["class"],
    "h4": ["class"],
    "img": ["src", "alt", "title", "loading"],
    "li": ["class"],
    "ol": ["class"],
    "p": ["class"],
    "pre": ["class"],
    "span": ["class"],
    "ul": ["class"],
}
ALLOWED_HTML_PROTOCOLS = {"http", "https", "mailto"}
LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60
FAILED_LOGIN_ATTEMPTS = {}

SITE_CONTENT_SCHEMA = {
    "common": {
        "label": "Textos globais",
        "description": "Elementos reutilizados em várias páginas, como WhatsApp e popup de saída.",
        "preview_path": "/",
        "fields": [
            {"key": "whatsapp_title", "label": "Título do WhatsApp", "default": "💬 Fale com a Niblo", "mode": "text"},
            {"key": "whatsapp_support_title", "label": "Título do suporte", "default": "Suporte Técnico", "mode": "text"},
            {"key": "whatsapp_support_subtitle", "label": "Subtítulo do suporte", "default": "Abertura de chamados", "mode": "text"},
            {"key": "whatsapp_sales_title", "label": "Título comercial", "default": "Time Comercial", "mode": "text"},
            {"key": "whatsapp_sales_subtitle", "label": "Subtítulo comercial", "default": "Planos e propostas", "mode": "text"},
            {"key": "exit_title_html", "label": "Título do popup de saída", "default": "Antes de ir, que tal<br><span class=\"exit-highlight\">economizar de verdade?</span>", "mode": "html"},
            {"key": "exit_text", "label": "Texto do popup de saída", "default": "Fale com nosso time e descubra quanto você pode economizar migrando para a Niblo Cloud.", "mode": "text"},
            {"key": "exit_cta", "label": "Botão principal do popup", "default": "Falar com especialista", "mode": "text"},
            {"key": "exit_dismiss", "label": "Botão secundário do popup", "default": "Agora não", "mode": "text"},
        ],
    },
    "home": {
        "label": "Home page",
        "description": "Mensagens principais da página inicial.",
        "preview_path": "/",
        "fields": [
            {"key": "hero_title_html", "label": "Título principal", "default": "Não é sobre estar nas nuvens é sobre ter a sua cloud <span class=\"highlight-dark\">sob medida.</span><br>Flexibilidade real para negócios que nasceram para ser <span class=\"highlight-dark\">disruptivos.</span>", "mode": "html"},
            {"key": "hero_primary_cta", "label": "CTA principal", "default": "Migrar para Niblo →", "mode": "text"},
            {"key": "hero_secondary_cta", "label": "CTA secundário", "default": "Ver soluções", "mode": "text"},
            {"key": "stats_title", "label": "Título dos números", "default": "Números que demonstram nossa capacidade", "mode": "text"},
            {"key": "partners_tag", "label": "Tag da seção parceiros", "default": "Parceiros", "mode": "text"},
            {"key": "partners_title", "label": "Título da seção parceiros", "default": "Parceiros que completam, soluções que evoluem", "mode": "text"},
            {"key": "partners_points_html", "label": "Bloco de pontos de parceiros", "default": "<div class=\"parceiros-point\"><div class=\"point-dot\"></div><p>Somos mais do que uma cloud somos o elemento estratégico que faltava para destravar o crescimento do seu negócio.</p></div><div class=\"parceiros-point\"><div class=\"point-dot\"></div><p>Enquanto você foca no que faz de melhor, nós garantimos a infraestrutura que sustenta sua evolução. Atuamos como um parceiro de verdade, permitindo que você amplie sua oferta de serviços, gere novas receitas e entregue ainda mais valor aos seus clientes sem aumentar a complexidade operacional.</p></div><div class=\"parceiros-point\"><div class=\"point-dot\"></div><p>Com nossa cloud, sua marca ganha força, sua proposta se torna mais competitiva e suas oportunidades se expandem de forma consistente.</p></div><div class=\"parceiros-point\"><div class=\"point-dot\"></div><p>Oferecemos performance, segurança e confiabilidade para que você incorpore nossa solução ao seu portfólio com tranquilidade, transformando tecnologia em vantagem competitiva.</p></div><div class=\"parceiros-point\"><div class=\"point-dot\"></div><p>Sua expertise cria possibilidades. Nossa cloud torna tudo viável.</p></div>", "mode": "html"},
            {"key": "partners_cta", "label": "CTA de parceiros", "default": "Seja nosso parceiro →", "mode": "text"},
            {"key": "news_tag", "label": "Tag da seção notícias", "default": "Últimas notícias", "mode": "text"},
            {"key": "news_title", "label": "Título da seção notícias", "default": "Esteja por dentro do mundo cloud", "mode": "text"},
        ],
    },
    "solucoes": {
        "label": "Soluções",
        "description": "Blocos textuais da página de soluções.",
        "preview_path": "/solucoes.html",
        "fields": [
            {"key": "intro_tag", "label": "Tag de abertura", "default": "Soluções", "mode": "text"},
            {"key": "intro_title", "label": "Título de abertura", "default": "Você sabe o quanto pode economizar migrando para a Niblo Cloud?", "mode": "text"},
            {"key": "intro_desc_html", "label": "Descrição de abertura", "default": "Migrar para a cloud certa vai muito além de reduzir custos — é sobre ganhar controle, eficiência e tranquilidade no dia a dia. Modelos em nuvem eliminam investimentos em infraestrutura própria, manutenção e energia, além de permitir pagar apenas pelo que é utilizado, tornando os gastos mais previsíveis e fáceis de planejar.<br><br>Com a Niblo Cloud, você transforma tecnologia em vantagem competitiva.", "mode": "html"},
            {"key": "intro_cta", "label": "CTA de abertura", "default": "Falar com um especialista →", "mode": "text"},
            {"key": "features_html", "label": "Lista de diferenciais", "default": "<li class=\"feature-item reveal\"><div class=\"feature-icon\"></div><div class=\"feature-text\"><h4>Segurança de verdade</h4><p>Infraestrutura robusta com monitoramento constante e recursos avançados de proteção de dados.</p></div></li><li class=\"feature-item reveal\"><div class=\"feature-icon\"></div><div class=\"feature-text\"><h4>Atendimento facilitado e rápido</h4><p>Suporte próximo, ágil e preparado para resolver demandas com velocidade, mantendo sua operação sempre disponível.</p></div></li><li class=\"feature-item reveal\"><div class=\"feature-icon\"></div><div class=\"feature-text\"><h4>Preços acessíveis</h4><p>Reduza custos com hardware, manutenção e equipe dedicada. Modelo mais econômico e eficiente.</p></div></li><li class=\"feature-item reveal\"><div class=\"feature-icon\"></div><div class=\"feature-text\"><h4>Previsibilidade de custos</h4><p>Modelo transparente e escalável — você sabe exatamente quanto vai investir, sem surpresas no orçamento.</p></div></li>", "mode": "html"},
            {"key": "multicloud_tag", "label": "Tag da seção Multi-Cloud", "default": "Multi-Cloud", "mode": "text"},
            {"key": "multicloud_title", "label": "Título da seção Multi-Cloud", "default": "Nos conectamos com as clouds públicas", "mode": "text"},
            {"key": "multicloud_subtitle", "label": "Subtítulo da seção Multi-Cloud", "default": "Integração de dados, escalabilidade e segurança no seu ambiente", "mode": "text"},
            {"key": "infra_tag", "label": "Tag de certificações infra", "default": "Certificações", "mode": "text"},
            {"key": "infra_title", "label": "Título de certificações infra", "default": "Nossa Infraestrutura: Garantia de Continuidade e Segurança", "mode": "text"},
            {"key": "infra_intro", "label": "Texto de certificações infra", "default": "Operamos sob os mais rígidos padrões internacionais para garantir que sua operação nunca pare. Nossas certificações atestam o compromisso com a resiliência e a proteção de dados:", "mode": "text"},
            {"key": "esg_tag", "label": "Tag ESG", "default": "ESG", "mode": "text"},
            {"key": "esg_title", "label": "Título ESG", "default": "Compromisso com o Futuro: Nossa Jornada ESG", "mode": "text"},
            {"key": "esg_intro", "label": "Texto ESG", "default": "Mais do que uma tendência, o ESG é o pilar que sustenta nossa operação. Nossas certificações e práticas de gestão refletem um compromisso genuíno com a ética e a preservação do planeta:", "mode": "text"},
        ],
    },
    "sobre": {
        "label": "Sobre",
        "description": "Conteúdo institucional da página sobre.",
        "preview_path": "/sobre.html",
        "fields": [
            {"key": "hero_tag", "label": "Tag inicial", "default": "Sobre nós", "mode": "text"},
            {"key": "hero_title", "label": "Título inicial", "default": "Missão, Visão e Valores", "mode": "text"},
            {"key": "hero_intro", "label": "Texto inicial", "default": "Passe o mouse sobre os cards para conhecer o que nos move.", "mode": "text"},
            {"key": "mission_html", "label": "Texto de missão", "default": "Prover a liberdade digital através de uma <strong>Cloud flexível</strong>, personalizada e segura, que se adapta à estratégia de cada operação.", "mode": "html"},
            {"key": "vision_html", "label": "Texto de visão", "default": "Ser reconhecida como a Cloud que rompe o padrão do mercado, tornando-se referência em soluções <strong>sob medida e disruptivas</strong>, onde cada empresa da nossa rede encontra flexibilidade real para evoluir com autonomia, previsibilidade e alta performance.", "mode": "html"},
            {"key": "values_html", "label": "Lista de valores", "default": "<li>• <strong>Conexão estratégica</strong></li><li>• <strong>Flexibilidade verdadeira</strong></li><li>• <strong>Personalização</strong></li><li>• <strong>Inovação com impacto</strong></li><li>• <strong>Proximidade ativa</strong></li><li>• <strong>Excelência operacional</strong></li><li>• <strong>Evolução permanente</strong></li>", "mode": "html"},
            {"key": "who_tag", "label": "Tag de quem somos", "default": "Quem somos", "mode": "text"},
            {"key": "who_title", "label": "Título de quem somos", "default": "Uma cloud que é parceira do seu negócio", "mode": "text"},
            {"key": "who_body_html", "label": "Bloco de quem somos", "default": "<p class=\"section-desc\">Há 24 anos, um grupo de profissionais visionários uniu experiência e paixão por tecnologia para acelerar a jornada digital das empresas. Dessa trajetória de evolução constante e compreensão profunda das necessidades do mercado nasce a:</p><p class=\"section-desc\"><strong>NIBLO</strong> uma marca de identidade jovem, mas sustentada por mais de duas décadas de solidez técnica.</p><p class=\"section-desc\">Carregamos a maturidade de quem acompanhou a transformação digital desde o início e a energia de quem continua inovando todos os dias, transformando 24 anos de história em soluções de Cloud que atendem organizações de diversos portes com eficiência e confiabilidade.</p><p class=\"section-desc\">Nossa atuação vai além da entrega de infraestrutura; somos parceiros estratégicos que oferecem consultoria especializada, suporte próximo e soluções que permitem escalar operações com segurança, performance e previsibilidade de custos. Acreditamos que a tecnologia cumpre seu papel quando simplifica processos e potencializa resultados reais. Por isso, mantemos padrões rigorosos de qualidade em toda a nossa operação, seguindo comprometidos com o propósito de ajudar empresas a crescer com confiança e construir, junto aos nossos clientes, o futuro digital que já começou.</p>", "mode": "html"},
            {"key": "coverage_tag", "label": "Tag de cobertura", "default": "Cobertura", "mode": "text"},
            {"key": "coverage_title", "label": "Título de cobertura", "default": "Onde atendemos", "mode": "text"},
            {"key": "coverage_body_html", "label": "Bloco de cobertura", "default": "Nossa infraestrutura já está em <strong>São Paulo e Fortaleza</strong>, garantindo performance, segurança e disponibilidade para operações críticas.<br><br>Agora, damos mais um passo em nossa evolução: <strong>em breve estaremos também nos Estados Unidos</strong>, ampliando nossa presença e aproximando ainda mais nossos serviços de clientes e parceiros internacionais. Mais presença, mais conectividade, mais possibilidades para o seu negócio.<br><br>E os nossos planos não param por aí, em 2028 desembarcaremos na <strong>Europa</strong>. Um novo horizonte de conectividade para romper fronteiras e impulsionar o crescimento da sua empresa em escala mundial.", "mode": "html"},
        ],
    },
    "parceiros": {
        "label": "Parceiros",
        "description": "Apresentação do programa de parceiros.",
        "preview_path": "/parceiros.html",
        "fields": [
            {"key": "hero_tag", "label": "Tag inicial", "default": "Seja parceiro", "mode": "text"},
            {"key": "hero_title", "label": "Título inicial", "default": "Seja nosso parceiro comercial", "mode": "text"},
            {"key": "hero_intro", "label": "Texto inicial", "default": "Preencha o formulário e nossa equipe de marketing entrará em contato para apresentar as oportunidades de parceria.", "mode": "text"},
        ],
    },
    "contato": {
        "label": "Contato",
        "description": "Textos de entrada da página de contato.",
        "preview_path": "/contato.html",
        "fields": [
            {"key": "hero_tag", "label": "Tag inicial", "default": "Contato", "mode": "text"},
            {"key": "hero_title", "label": "Título inicial", "default": "Entre em contato com nosso time", "mode": "text"},
            {"key": "hero_intro", "label": "Texto inicial", "default": "Preencha o formulário e nossa equipe retornará em até 24 horas úteis para entender como podemos ajudar.", "mode": "text"},
        ],
    },
    "blog": {
        "label": "Blog",
        "description": "Textos de apresentação da página do blog.",
        "preview_path": "/blog.html",
        "fields": [
            {"key": "hero_tag", "label": "Tag inicial", "default": "Blog", "mode": "text"},
            {"key": "hero_title", "label": "Título inicial", "default": "Esteja por dentro das últimas notícias", "mode": "text"},
        ],
    },
}


app = Flask(__name__, static_folder=str(SITE_DIR), static_url_path="")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.environ.get("NIBLO_ADMIN_SECRET") or os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = bool(_truthy := os.environ.get("NIBLO_SESSION_COOKIE_SECURE")) and _truthy.lower() in {"1", "true", "yes", "on"}
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)


def should_use_secure_cookies():
    return app.config["SESSION_COOKIE_SECURE"] or IS_PRODUCTION


app.config["SESSION_COOKIE_SECURE"] = should_use_secure_cookies()


def slugify(value):
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return cleaned or f"post-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def ensure_storage():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    # On Vercel: copy committed JSON files to /tmp on first boot so reads work
    if _IS_VERCEL and _COMMITTED_DATA.is_dir():
        for src in _COMMITTED_DATA.glob("*.json"):
            dst = DATA_DIR / src.name
            if not dst.exists():
                import shutil
                shutil.copy2(src, dst)


def deep_copy_data(value):
    return json.loads(json.dumps(value))


def parse_br_date(value):
    try:
        return datetime.strptime(value, "%d/%m/%Y")
    except ValueError:
        return datetime.min


def strip_html(value):
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", text).strip()


def extract_excerpt(html, limit=180):
    text = strip_html(html)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def format_date_br(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return value


app.jinja_env.filters["date_br"] = format_date_br


def client_ip():
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"


def get_rate_limit_key(username):
    return f"{client_ip()}::{username.lower()}"


def prune_login_attempts(now=None):
    current_time = now or time.time()
    expired_keys = [
        key for key, state in FAILED_LOGIN_ATTEMPTS.items()
        if current_time - state.get("last_attempt", 0) > LOGIN_WINDOW_SECONDS
    ]
    for key in expired_keys:
        FAILED_LOGIN_ATTEMPTS.pop(key, None)


def login_is_locked(username):
    prune_login_attempts()
    state = FAILED_LOGIN_ATTEMPTS.get(get_rate_limit_key(username))
    if not state:
        return False
    return time.time() < state.get("locked_until", 0)


def register_failed_login(username):
    now = time.time()
    key = get_rate_limit_key(username)
    state = FAILED_LOGIN_ATTEMPTS.get(key, {"count": 0, "last_attempt": 0, "locked_until": 0})
    if now - state.get("last_attempt", 0) > LOGIN_WINDOW_SECONDS:
        state = {"count": 0, "last_attempt": now, "locked_until": 0}
    state["count"] += 1
    state["last_attempt"] = now
    if state["count"] >= LOGIN_MAX_ATTEMPTS:
        state["locked_until"] = now + LOGIN_LOCKOUT_SECONDS
    FAILED_LOGIN_ATTEMPTS[key] = state


def clear_failed_login(username):
    FAILED_LOGIN_ATTEMPTS.pop(get_rate_limit_key(username), None)


def verify_admin_password(password):
    if ADMIN_PASSWORD_HASH:
        return check_password_hash(ADMIN_PASSWORD_HASH, password)
    return bool(ADMIN_PASSWORD_LEGACY) and hmac.compare_digest(password, ADMIN_PASSWORD_LEGACY)


def admin_login_enabled():
    return bool(ADMIN_PASSWORD_HASH or ADMIN_PASSWORD_LEGACY)


def get_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def csrf_input():
    return Markup(f'<input type="hidden" name="csrf_token" value="{get_csrf_token()}">')


def validate_csrf():
    expected = session.get("csrf_token")
    provided = request.form.get("csrf_token", "")
    return bool(expected and provided and hmac.compare_digest(expected, provided))


def sanitize_html_fragment(value):
    cleaned = bleach.clean(
        value or "",
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        protocols=ALLOWED_HTML_PROTOCOLS,
        strip=True,
    )
    return re.sub(r"\s+rel=(['\"])(?![^>]*noopener)([^'\"]*)(['\"])", r" rel=\1noopener noreferrer\3", cleaned)


def normalize_media_path(value, fallback="images/logo1.png"):
    raw_value = (value or "").strip().replace("\\", "/")
    if not raw_value:
        return fallback
    raw_value = raw_value.lstrip("/")
    if not raw_value.startswith("images/"):
        return fallback
    filename = Path(raw_value).name
    if secure_filename(filename) != filename or not allowed_media(filename):
        return fallback
    return f"images/{filename}"


def sanitize_site_content_payload(content):
    sanitized = build_default_site_content()
    for page_key, config in SITE_CONTENT_SCHEMA.items():
        source_page = content.get(page_key, {}) if isinstance(content, dict) else {}
        if not isinstance(source_page, dict):
            source_page = {}
        page_payload = {}
        for field in config["fields"]:
            raw_value = (source_page.get(field["key"], field.get("default", "")) or "").strip()
            if field.get("mode") == "html":
                page_payload[field["key"]] = sanitize_html_fragment(raw_value)
            else:
                page_payload[field["key"]] = raw_value
        sanitized[page_key] = page_payload
    return sanitized


def sanitize_post_payload(post):
    sanitized = dict(post)
    sanitized["title"] = (sanitized.get("title") or "").strip()
    sanitized["excerpt"] = strip_html((sanitized.get("excerpt") or "").strip())
    sanitized["content"] = sanitize_html_fragment((sanitized.get("content") or "").strip())
    sanitized["author"] = (sanitized.get("author") or "Niblo Cloud").strip() or "Niblo Cloud"
    sanitized["cover_image"] = normalize_media_path(sanitized.get("cover_image"), fallback="images/logo1.png")
    sanitized["slug"] = slugify(sanitized.get("slug") or sanitized["title"])
    return sanitized


app.jinja_env.globals["csrf_input"] = csrf_input


SHORT_LABELS = {
    "common": "Globais",
    "home": "Home",
    "solucoes": "Soluções",
    "sobre": "Sobre",
    "parceiros": "Parceiros",
    "contato": "Contato",
    "blog": "Blog",
}


@app.context_processor
def inject_globals():
    return {
        "current_year": datetime.now().year,
        "sidebar_content_pages": list_site_pages(include_common=True),
        "current_content_page": (request.view_args or {}).get("page_key"),
        "csrf_token": get_csrf_token,
    }


def build_default_site_content():
    payload = {}
    for page_key, config in SITE_CONTENT_SCHEMA.items():
        payload[page_key] = {field["key"]: field.get("default", "") for field in config["fields"]}
    return payload


def bootstrap_site_content():
    ensure_storage()
    defaults = build_default_site_content()
    if SITE_CONTENT_FILE.exists():
        try:
            with SITE_CONTENT_FILE.open("r", encoding="utf-8") as handle:
                existing = json.load(handle)
        except (json.JSONDecodeError, OSError):
            existing = {}
    else:
        existing = {}

    updated = deep_copy_data(defaults)
    for page_key, page_values in existing.items():
        if page_key not in updated or not isinstance(page_values, dict):
            continue
        updated[page_key].update(page_values)

    with SITE_CONTENT_FILE.open("w", encoding="utf-8") as handle:
        json.dump(updated, handle, ensure_ascii=False, indent=2)


def read_site_content():
    bootstrap_site_content()
    with SITE_CONTENT_FILE.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    sanitized = sanitize_site_content_payload(data)
    if sanitized != data:
        write_site_content(sanitized)
    return sanitized


def write_site_content(content):
    ensure_storage()
    merged = sanitize_site_content_payload(content)
    with SITE_CONTENT_FILE.open("w", encoding="utf-8") as handle:
        json.dump(merged, handle, ensure_ascii=False, indent=2)


def get_site_page_config(page_key):
    config = SITE_CONTENT_SCHEMA.get(page_key)
    if not config:
        abort(404)
    return config


def get_public_site_content(page_key):
    content = read_site_content()
    page_content = {}
    page_content.update(content.get("common", {}))
    page_content.update(content.get(page_key, {}))
    return page_content


def list_site_pages(include_common=False):
    items = []
    for page_key, config in SITE_CONTENT_SCHEMA.items():
        if not include_common and page_key == "common":
            continue
        items.append(
            {
                "key": page_key,
                "label": config["label"],
                "label_short": SHORT_LABELS.get(page_key, config["label"]),
                "description": config["description"],
                "preview_path": config["preview_path"],
                "field_count": len(config["fields"]),
            }
        )
    return items


def read_posts():
    bootstrap_posts()
    if not POSTS_FILE.exists():
        return []
    with POSTS_FILE.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    sanitized = [sanitize_post_payload(item) for item in data if isinstance(item, dict)]
    if sanitized != data:
        write_posts(sanitized)
    return sort_posts(sanitized)


def write_posts(posts):
    ensure_storage()
    sanitized_posts = [sanitize_post_payload(item) for item in posts if isinstance(item, dict)]
    with POSTS_FILE.open("w", encoding="utf-8") as handle:
        json.dump(sort_posts(sanitized_posts), handle, ensure_ascii=False, indent=2)


def sort_posts(posts):
    return sorted(posts, key=lambda item: (item.get("published_at", ""), item.get("updated_at", "")), reverse=True)


def bootstrap_posts():
    ensure_storage()
    if POSTS_FILE.exists():
        try:
            with POSTS_FILE.open("r", encoding="utf-8") as handle:
                existing = json.load(handle)
            if existing:
                return
        except (json.JSONDecodeError, OSError):
            pass

    migrated_posts = []
    pattern = re.compile(r"blog(\d+)\.html$")
    for file_path in sorted(SITE_DIR.glob("blog[1-9]*.html")):
        match = pattern.search(file_path.name)
        if not match:
            continue
        html = file_path.read_text(encoding="utf-8")
        title_match = re.search(r'<div class="blog-post-title"(?:[^>]*)>(.*?)</div>', html, re.S)
        meta_match = re.search(r'<div class="blog-post-meta">(.*?)</div>', html, re.S)
        content_match = re.search(r'<div class="blog-post-content">(.*?)</div>\s*<div class="blog-post-footer">', html, re.S)
        if not title_match or not meta_match or not content_match:
            continue

        title = re.sub(r"\s+", " ", title_match.group(1)).strip()
        meta_text = re.sub(r"\s+", " ", meta_match.group(1)).strip()
        content = content_match.group(1).strip()
        date_match = re.search(r"Publicado em\s+([0-9]{2}/[0-9]{2}/[0-9]{4})", meta_text)
        author_match = re.search(r"Autor:\s*(.*)$", meta_text)
        cover_image = f"images/blog{match.group(1)}.png"
        published_at = "2026-01-01"
        if date_match:
            published_at = parse_br_date(date_match.group(1)).strftime("%Y-%m-%d")
        migrated_posts.append(
            {
                "id": file_path.stem,
                "slug": slugify(title),
                "title": title,
                "excerpt": extract_excerpt(content),
                "content": content,
                "cover_image": cover_image,
                "author": author_match.group(1).strip() if author_match else "Niblo Cloud",
                "published_at": published_at,
                "created_at": published_at,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_published": True,
                "legacy_path": file_path.name,
            }
        )

    write_posts(migrated_posts)


def get_post_or_404(slug):
    for post in read_posts():
        if post.get("slug") == slug:
            return post
    abort(404)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped


def allowed_media(filename):
    return Path(filename).suffix.lower() in ALLOWED_MEDIA_EXTENSIONS


def allowed_media_upload(file_storage, filename):
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_MEDIA_MIME_TYPES:
        return False
    mimetype = (file_storage.mimetype or "").lower()
    return mimetype in ALLOWED_MEDIA_MIME_TYPES[extension]


def save_media_upload(file_storage, replace_target=None, prefix="media"):
    if not file_storage or not file_storage.filename:
        return None

    original_name = secure_filename(file_storage.filename)
    if not original_name or not allowed_media(original_name) or not allowed_media_upload(file_storage, original_name):
        return None

    if replace_target:
        safe_name = secure_filename(Path(replace_target).name)
        if not safe_name or not allowed_media(safe_name):
            return None
    else:
        stem = slugify(Path(original_name).stem)
        extension = Path(original_name).suffix.lower()
        safe_name = f"{prefix}-{stem}{extension}"
        counter = 1
        while (IMAGES_DIR / safe_name).exists():
            safe_name = f"{prefix}-{stem}-{counter}{extension}"
            counter += 1

    destination = IMAGES_DIR / safe_name
    file_storage.save(destination)
    return f"images/{safe_name}"


def list_media_files():
    ensure_storage()
    files = []
    for file_path in sorted(IMAGES_DIR.iterdir(), key=lambda item: item.name.lower()):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in ALLOWED_MEDIA_EXTENSIONS:
            continue
        files.append(
            {
                "name": file_path.name,
                "path": f"images/{file_path.name}",
                "suffix": file_path.suffix.lower(),
                "updated_at": datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%d/%m/%Y %H:%M"),
            }
        )
    return files


@app.before_request
def enforce_csrf_for_admin():
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return None
    if not request.path.startswith(f"/{ADMIN_SLUG}"):
        return None
    if not validate_csrf():
        abort(400)
    return None


@app.after_request
def secure_admin_routes(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.is_secure:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
    if request.path.startswith(f"/{ADMIN_SLUG}"):
        response.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def home():
    return send_from_directory(SITE_DIR, "index.html")


@app.route("/blog.html")
def blog_index():
    posts = [post for post in read_posts() if post.get("is_published")]
    return render_template("blog_list.html", posts=posts)


@app.route("/blog/<slug>")
def blog_post(slug):
    post = get_post_or_404(slug)
    if not post.get("is_published") and not session.get("admin_logged_in"):
        abort(404)
    return render_template("blog_post.html", post=post)


@app.route("/blog<int:legacy_id>.html")
def legacy_blog_post(legacy_id):
    legacy_path = f"blog{legacy_id}.html"
    for post in read_posts():
        if post.get("legacy_path") == legacy_path:
            return redirect(url_for("blog_post", slug=post["slug"]), code=302)
    abort(404)


@app.route("/api/public/posts")
def public_posts_api():
    limit = request.args.get("limit", default=4, type=int)
    posts = [post for post in read_posts() if post.get("is_published")][: min(max(limit, 1), 12)]
    payload = [
        {
            "title": post["title"],
            "excerpt": post.get("excerpt", ""),
            "cover_image": url_for("static", filename=post.get("cover_image", "images/logo1.png")),
            "url": url_for("blog_post", slug=post["slug"]),
            "published_at": format_date_br(post.get("published_at", "")),
        }
        for post in posts
    ]
    return jsonify(payload)


@app.route("/api/public/site-content/<page_key>")
def public_site_content_api(page_key):
    get_site_page_config(page_key)
    return jsonify({"page": page_key, "content": get_public_site_content(page_key)})


@app.route(f"/{ADMIN_SLUG}", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not admin_login_enabled():
            abort(503)
        if login_is_locked(username):
            flash("Muitas tentativas. Aguarde alguns minutos e tente novamente.", "error")
        elif hmac.compare_digest(username, ADMIN_USERNAME) and verify_admin_password(password):
            clear_failed_login(username)
            session.clear()
            session["admin_logged_in"] = True
            session["csrf_token"] = secrets.token_urlsafe(32)
            session.permanent = True
            return redirect(url_for("admin_dashboard"))
        else:
            register_failed_login(username)
            flash("Credenciais inválidas.", "error")

    return render_template("admin_login.html", admin_path=f"/{ADMIN_SLUG}")


@app.route(f"/{ADMIN_SLUG}/logout", methods=["POST"])
@login_required
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route(f"/{ADMIN_SLUG}/dashboard")
@login_required
def admin_dashboard():
    posts = read_posts()
    return render_template(
        "admin_dashboard.html",
        posts=posts,
        media_count=len(list_media_files()),
        content_pages=list_site_pages(include_common=True),
        admin_path=f"/{ADMIN_SLUG}",
    )


@app.route(f"/{ADMIN_SLUG}/posts")
@login_required
def admin_posts():
    return render_template(
        "admin_posts.html",
        posts=read_posts(),
        admin_path=f"/{ADMIN_SLUG}",
    )


@app.route(f"/{ADMIN_SLUG}/media")
@login_required
def admin_media_page():
    return render_template(
        "admin_media.html",
        media_files=list_media_files(),
        admin_path=f"/{ADMIN_SLUG}",
    )


@app.route(f"/{ADMIN_SLUG}/content/<page_key>", methods=["GET", "POST"])
@login_required
def admin_edit_site_content(page_key):
    config = get_site_page_config(page_key)
    content = read_site_content()

    if request.method == "POST":
        updated_page = {}
        for field in config["fields"]:
            field_value = request.form.get(field["key"], "").strip()
            if field.get("mode") == "html":
                updated_page[field["key"]] = sanitize_html_fragment(field_value)
            else:
                updated_page[field["key"]] = field_value
        content[page_key] = updated_page
        write_site_content(content)
        flash(f"Conteúdo de {config['label']} atualizado com sucesso.", "success")
        return redirect(url_for("admin_edit_site_content", page_key=page_key))

    page_content = content.get(page_key, {})
    return render_template(
        "admin_site_content_form.html",
        page_key=page_key,
        page_config=config,
        page_content=page_content,
        admin_path=f"/{ADMIN_SLUG}",
    )


def upsert_post(existing_slug=None):
    posts = read_posts()
    current_post = None
    if existing_slug:
        current_post = next((item for item in posts if item.get("slug") == existing_slug), None)
        if not current_post:
            abort(404)

    title = request.form.get("title", "").strip()
    if not title:
        flash("O título do post é obrigatório.", "error")
        return None

    requested_slug = request.form.get("slug", "").strip()
    new_slug = slugify(requested_slug or title)
    if any(item.get("slug") == new_slug and item.get("slug") != existing_slug for item in posts):
        flash("Já existe um post com esse slug.", "error")
        return None

    cover_image = normalize_media_path(
        request.form.get("cover_image", "").strip() or (current_post or {}).get("cover_image"),
        fallback="images/logo1.png",
    )
    uploaded_cover = save_media_upload(request.files.get("cover_upload"), prefix="blog")
    if uploaded_cover:
        cover_image = uploaded_cover

    published_at = request.form.get("published_at", "").strip() or datetime.now().strftime("%Y-%m-%d")
    payload = {
        "id": (current_post or {}).get("id") or f"post-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "slug": new_slug,
        "title": title,
        "excerpt": request.form.get("excerpt", "").strip() or extract_excerpt(request.form.get("content", "")),
        "content": sanitize_html_fragment(request.form.get("content", "").strip()),
        "cover_image": cover_image,
        "author": request.form.get("author", "").strip() or "Niblo Cloud",
        "published_at": published_at,
        "created_at": (current_post or {}).get("created_at") or published_at,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "is_published": request.form.get("is_published") == "on",
        "legacy_path": (current_post or {}).get("legacy_path"),
    }

    updated_posts = [item for item in posts if item.get("slug") != existing_slug]
    updated_posts.append(payload)
    write_posts(updated_posts)
    return payload


@app.route(f"/{ADMIN_SLUG}/posts/new", methods=["GET", "POST"])
@login_required
def admin_new_post():
    if request.method == "POST":
        post = upsert_post()
        if post:
            flash("Post criado com sucesso.", "success")
            return redirect(url_for("admin_edit_post", slug=post["slug"]))

    empty_post = {
        "title": "",
        "slug": "",
        "excerpt": "",
        "content": "",
        "cover_image": "",
        "author": "Niblo Cloud",
        "published_at": datetime.now().strftime("%Y-%m-%d"),
        "is_published": True,
    }
    return render_template(
        "admin_post_form.html",
        post=empty_post,
        form_title="Novo post",
        submit_label="Criar post",
        admin_path=f"/{ADMIN_SLUG}",
    )


@app.route(f"/{ADMIN_SLUG}/posts/<slug>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_post(slug):
    if request.method == "POST":
        post = upsert_post(existing_slug=slug)
        if post:
            flash("Post atualizado com sucesso.", "success")
            return redirect(url_for("admin_edit_post", slug=post["slug"]))

    post = get_post_or_404(slug)
    return render_template(
        "admin_post_form.html",
        post=post,
        form_title="Editar post",
        submit_label="Salvar alterações",
        admin_path=f"/{ADMIN_SLUG}",
    )


@app.route(f"/{ADMIN_SLUG}/posts/<slug>/delete", methods=["POST"])
@login_required
def admin_delete_post(slug):
    posts = [item for item in read_posts() if item.get("slug") != slug]
    write_posts(posts)
    flash("Post removido.", "success")
    return redirect(url_for("admin_posts"))


@app.route(f"/{ADMIN_SLUG}/media/upload", methods=["POST"])
@login_required
def admin_upload_media():
    media_file = request.files.get("media_file")
    replace_target = request.form.get("replace_target", "").strip() or None
    saved_path = save_media_upload(media_file, replace_target=replace_target, prefix="site")
    if saved_path:
        flash(f"Arquivo salvo em {saved_path}.", "success")
    else:
        flash("Envie um arquivo permitido para substituir ou adicionar mídia.", "error")
    return redirect(url_for("admin_media_page"))


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(IMAGES_DIR, "logo1.png")


if __name__ == "__main__":
    bootstrap_posts()
    bootstrap_site_content()
    app.run(
        debug=os.environ.get("FLASK_DEBUG") == "1",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
    )