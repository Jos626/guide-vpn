"""Guide VPN — l'application des pronostics de José Ledanite.

CE QUE C'EST. La face visible du bot de football : les analyses du jour et la montante, dans une
application qu'on installe sur son téléphone (menu ⋮ du navigateur → « Ajouter à l'écran d'accueil »).

D'OÙ VIENNENT LES CHIFFRES, ET POURQUOI CE SERVEUR NE CALCULE RIEN. Les cotes viennent de
m.betclic.ci, un site ivoirien : la récolte et le calcul se font sur le téléphone de José, là où ça
fonctionne. Cette application ne fait qu'AFFICHER un instantané (publication.json) fabriqué là-bas.
Séparer les deux, c'est ce qui permet à l'application d'être simple, rapide et impossible à casser
depuis l'extérieur : elle n'a aucun accès, aucune clé, aucune donnée personnelle.

⚠️ AUCUNE DONNÉE DE CLIENT ICI. On publie des matchs, des pourcentages et des cotes. Jamais un nom,
jamais un identifiant Telegram, jamais une mise. Un instantané publié doit pouvoir être lu par
n'importe qui sans rien révéler de qui que ce soit.
"""
import html
import json
import os
import re
import sys
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import articles  # les GUIDES écrits (contenu SEO), avec leur lien d'affiliation en un seul endroit
import trafic    # le compteur de visites (sobre : sans cookie, sans adresse IP)

ICI = os.path.dirname(os.path.abspath(__file__))
LECTURE_VERTE, LECTURE_VERTE_FORTE = "#16a34a", "#15803d"

STYLE = """:root{
  --ink:#161513; --muted:#6d6a63; --line:#e7e1d5; --bg:#fffdf8; --card:#ffffff;
  --accent:#d9a900; --accent-soft:#fff4cc;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font:17px/1.68 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
img{max-width:100%;display:block}
a{color:var(--ink)}
.wrap{max-width:748px;margin:0 auto;padding:0 20px}

/* ── en-tête ───────────────────────────────────────────── */
header.site{position:sticky;top:0;z-index:10;background:rgba(255,253,248,.92);
  backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
header.site .wrap{display:flex;align-items:center;justify-content:space-between;height:62px}
.marque{font-family:Georgia,"Times New Roman",serif;font-size:22px;font-weight:700;
  letter-spacing:-.02em;text-decoration:none}
.marque span{color:var(--muted);font-weight:400}
header.site nav a{color:var(--muted);text-decoration:none;font-size:14px;margin-left:20px}
header.site nav a:hover{color:var(--ink)}

/* ── une du blog ───────────────────────────────────────── */
.une{display:block;text-decoration:none;margin:34px 0 10px}
.une .visuel{position:relative;border-radius:14px;overflow:hidden;background:#efe9dc;aspect-ratio:16/9}
.une .visuel img{width:100%;height:100%;object-fit:cover}
.etiquette{display:inline-block;background:var(--accent-soft);color:#6b5200;font-size:12px;
  font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:6px 10px;border-radius:999px}
.une h2{font-family:Georgia,"Times New Roman",serif;font-size:clamp(26px,6vw,38px);line-height:1.15;
  letter-spacing:-.02em;margin:14px 0 8px}
.une p{color:var(--muted);margin:0 0 10px}
.meta{font-size:13.5px;color:var(--muted)}
.meta b{color:var(--ink);font-weight:600}

/* ── liste des articles ────────────────────────────────── */
.titre-section{display:flex;align-items:center;gap:14px;margin:42px 0 6px}
.titre-section h2{font-family:Georgia,serif;font-size:15px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted);font-weight:700;margin:0;white-space:nowrap}
.titre-section i{flex:1;height:1px;background:var(--line)}
.liste{display:flex;flex-direction:column}
.carte{display:flex;gap:18px;padding:22px 0;border-bottom:1px solid var(--line);text-decoration:none}
.carte:last-child{border-bottom:0}
.carte .vignette{flex:0 0 132px;height:96px;border-radius:10px;overflow:hidden;background:#efe9dc}
.carte .vignette img{width:100%;height:100%;object-fit:cover}
.carte h3{font-family:Georgia,serif;font-size:19px;line-height:1.25;margin:0 0 6px;letter-spacing:-.01em}
.carte p{color:var(--muted);font-size:14.5px;margin:0 0 8px;display:-webkit-box;
  -webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.carte:hover h3{text-decoration:underline;text-underline-offset:3px}

/* ── article ───────────────────────────────────────────── */
.fil{font-size:13px;color:var(--muted);margin:22px 0 0}
.fil a{color:var(--muted);text-decoration:none}
.article h1{font-family:Georgia,"Times New Roman",serif;font-size:clamp(29px,7vw,44px);
  line-height:1.12;letter-spacing:-.025em;margin:14px 0 12px}
.article .chapeau{font-size:19.5px;line-height:1.5;color:#3d3a35;margin:0 0 18px}
.article .entete-meta{display:flex;align-items:center;gap:10px;padding:14px 0;border-top:1px solid var(--line);
  border-bottom:1px solid var(--line);margin-bottom:26px}
.article .entete-meta img{width:34px;height:34px;border-radius:50%;object-fit:cover}
.article .entete-meta span{font-size:13.5px;color:var(--muted)}
.article .hero{border-radius:14px;overflow:hidden;margin:0 0 30px;background:#efe9dc}
.article .hero img{width:100%;height:auto}
.article h2{font-family:Georgia,serif;font-size:26px;line-height:1.25;letter-spacing:-.015em;margin:38px 0 12px}
.article h3{font-size:19px;margin:26px 0 8px}
.article p{margin:0 0 18px}
.article ul,.article ol{margin:0 0 20px;padding-left:22px}
.article li{margin:0 0 9px}
.article a.lien-affilie,.article a{color:#8a6b00;text-decoration:underline;text-underline-offset:2px}
.article .divulgation{background:#f6f2e6;border-left:3px solid var(--accent);padding:14px 16px;
  font-size:14px;color:#4a463d;border-radius:0 8px 8px 0;margin:0 0 24px}
.article blockquote{margin:26px 0;padding:4px 0 4px 20px;border-left:3px solid var(--line);
  font-family:Georgia,serif;font-size:20px;color:#3d3a35}
.article table{width:100%;border-collapse:collapse;margin:0 0 22px;font-size:15px}
.article th,.article td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line)}

/* ── encart auteur / partage ───────────────────────────── */
.encart{display:flex;gap:16px;align-items:flex-start;background:var(--card);border:1px solid var(--line);
  border-radius:14px;padding:20px;margin:40px 0 26px}
.encart img{width:56px;height:56px;border-radius:50%;object-fit:cover;flex:0 0 auto}
.encart b{display:block;font-size:15px}
.encart p{font-size:14.5px;color:var(--muted);margin:4px 0 0}
.partage{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:18px 0;border-top:1px solid var(--line)}
.partage span{font-size:13px;color:var(--muted);margin-right:4px}
.partage a,.partage button{font-size:13.5px;text-decoration:none;color:var(--ink);border:1px solid var(--line);
  background:var(--card);padding:8px 13px;border-radius:999px;cursor:pointer;font-family:inherit}
.partage a:hover,.partage button:hover{border-color:var(--ink)}

/* ── pied ──────────────────────────────────────────────── */
footer.pied{margin-top:50px;border-top:1px solid var(--line);padding:28px 0 42px;
  font-size:14px;color:var(--muted)}
footer.pied .wrap{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}
footer.pied a{color:var(--muted)}


/* ── couverture 3D du livre blanc ──────────────────────── */
.ebook{perspective:1100px;display:flex;justify-content:center;margin:14px 0 30px}
.ebook .livre{position:relative;width:212px;height:292px;padding:22px 18px 18px;
  transform:rotateY(-21deg) rotateX(4deg);transform-style:preserve-3d;
  background:linear-gradient(135deg,#0f2b46 0%,#1e5f8a 52%,#0b1f33 100%);
  color:#fff;border-radius:3px 8px 8px 3px;
  box-shadow:26px 24px 44px -18px rgba(10,25,40,.55), 0 2px 0 rgba(255,255,255,.15) inset;
  display:flex;flex-direction:column;justify-content:space-between}
.ebook .livre::before{content:"";position:absolute;left:0;top:0;bottom:0;width:15px;
  background:linear-gradient(90deg,rgba(0,0,0,.5),rgba(255,255,255,.14));border-radius:3px 0 0 3px}
.ebook .livre::after{content:"";position:absolute;right:-7px;top:4px;bottom:4px;width:7px;
  background:linear-gradient(90deg,#e8eef5,#c9d3de);transform:rotateY(90deg);transform-origin:left}
.ebook .haut small{font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;opacity:.8}
.ebook .haut h3{font-family:Georgia,serif;font-size:24px;line-height:1.14;margin:10px 0 0;letter-spacing:-.02em}
.ebook .bas{font-size:11.5px;opacity:.85;border-top:1px solid rgba(255,255,255,.25);padding-top:9px}
.ebook .badge-3d{position:absolute;top:10px;right:10px}

/* ── formulaire de capture ─────────────────────────────── */
.capture{display:flex;gap:10px;flex-wrap:wrap;margin:6px 0 10px}
.capture input[type=email]{flex:1 1 220px;padding:13px 15px;border:1px solid var(--line);
  border-radius:10px;font:inherit;background:#fff}
.capture input[type=email]:focus{outline:2px solid var(--accent);outline-offset:1px}
.capture button{flex:0 0 auto;padding:13px 20px;border:0;border-radius:10px;cursor:pointer;
  background:var(--ink);color:#fff;font:inherit;font-weight:600}
.capture button:hover{background:#000}
.capture-note{font-size:12.5px;color:var(--muted);margin:0 0 22px}

@media (max-width:520px){
  .carte{gap:14px}
  .carte .vignette{flex-basis:96px;height:80px}
  .carte h3{font-size:17px}
  .carte p{display:none}
}
"""


def lire_publication():
    try:
        with open(os.path.join(ICI, "publication.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _joli(texte):
    """Le texte du bot -> du HTML lisible. On ÉCHAPPE d'abord, on met en forme ensuite.

    ⚠️ L'ÉCHAPPEMENT D'ABORD N'EST PAS UN DÉTAIL : les analyses contiennent des noms d'équipes et de
    compétitions qui viennent de sources extérieures. Un « < » non échappé casserait la page.
    """
    protege = html.escape(str(texte or ""))
    protege = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", protege)
    protege = re.sub(r"(━━+)", r'<span class="trait">\1</span>', protege)
    return protege


def _quand_ou_direct(fiche):
    """L'heure du coup d'envoi, ou la mention « en direct ».

    ⚠️ POURQUOI C'EST ICI : José a demandé « ce sont les matchs à venir pour aujourd'hui ? ». La
    réponse est oui — le bot refuse d'analyser un match commencé — mais le montrer vaut mieux que le
    dire. Et si un match a commencé entre-temps, autant l'écrire franchement.
    """
    if fiche.get("en_direct"):
        return "🔴 En direct en ce moment — trop tard pour ce match"
    brut = fiche.get("coup_envoi") or ""
    if not brut:
        return ""
    try:
        quand = datetime.fromisoformat(brut)
        return "🕐 Coup d'envoi à " + quand.astimezone().strftime("%Hh%M")
    except (ValueError, TypeError):
        return ""


def _carte_message(m):
    """UNE CARTE = LE MESSAGE DU BOT, MOT POUR MOT.

    ⛔ LEÇON DU 10/10/2026. José : « Je veux que ce soit exactement comme avec le bot. Et je veux pas
    l'histoire des analyses. Non ! Fais comme exactement avec le bot. » Avant, cette fonction
    reconstruisait un joli résumé à partir d'un fichier intermédiaire : d'autres mots, un autre ordre,
    une section « pour le plaisir » qu'il n'avait jamais demandée, et PAS les scores les plus
    probables que le bot donne toujours. C'était une deuxième vérité avec les mêmes chiffres.
    Maintenant on affiche le texte que le moteur du bot a produit. Il ne peut plus y avoir d'écart.
    """
    quand = _quand_ou_direct(m)
    pied = f'<p class="quand2">{quand}</p>' if quand else ""
    return f'<div class="message">{_joli(m.get("message"))}{pied}</div>' 


def _coherent(paris):
    """⛔ LA RÈGLE DE JOSÉ : jamais un « plus de buts » ET un « under » sur le MÊME match.

    Quand les deux sortent, on garde l'under seul (décision du propriétaire, appliquée aussi dans le
    bot). Sans ce filtre, l'application afficherait un conseil qui se contredit lui-même.
    """
    a_under = any("UNDER" in (p.get("libelle") or "").upper() for p in paris)
    if not a_under:
        return paris
    return [p for p in paris
            if "UNDER" in (p.get("libelle") or "").upper()
            or not any(mot in (p.get("libelle") or "").upper()
                       for mot in ("PLUS DE", "+1,5", "+2,5", "PLUS DE BUTS"))]


def _carte_match(m):
    paris = _coherent(m.get("paris") or [])
    lignes = []
    for p in paris:
        pc = p.get("pourcent")
        largeur = max(2, min(100, int(pc))) if isinstance(pc, (int, float)) else 0
        lignes.append(
            f'<div class="pari"><span class="nom">{html.escape(str(p.get("libelle", "")))}</span>'
            f'<span class="barre"><i style="width:{largeur}%"></i></span>'
            f'<span class="pc">{pc:g} %</span>' if isinstance(pc, (int, float)) else
            f'<div class="pari"><span class="nom">{html.escape(str(p.get("libelle", "")))}</span>')
        # la pastille, telle que le bot la donne
        if p.get("pastille"):
            lignes[-1] += f'<span class="pas">{p["pastille"]}</span>'
        lignes[-1] += "</div>"
    plaisir = m.get("plaisir") or []
    bas = ""
    if plaisir:
        jolis = " · ".join(f'{html.escape(str(p.get("libelle")))} {p.get("pourcent"):g} %'
                           for p in plaisir if isinstance(p.get("pourcent"), (int, float)))
        if jolis:
            bas = f'<p class="plaisir">Pour le plaisir (sans pastille) : {jolis}</p>'
    return (f'<div class="match"><h3>{html.escape(str(m.get("match", "")))}</h3>'
            f'{"".join(lignes)}{bas}</div>')


def _carte_montante(v):
    quand = ""
    brut = v.get("coup_envoi") or ""
    if brut:
        try:
            h, minute = brut[11:13], brut[14:16]
            quand = f"Coup d\'envoi à {h}h{minute}"
        except Exception:
            quand = ""
    cotes = v.get("cotes") or {}
    detail = " · ".join(f"{k} : {val}" for k, val in cotes.items() if val)
    return (f'<div class="mont"><span class="badge">🌱 LA MONTANTE</span>'
            f'<div class="haut"><h3>{html.escape(str(v.get("match", "")))}</h3>'
            f'<span class="cote">{v.get("cote", "")}</span></div>'
            f'<p class="quoi">{html.escape(str(v.get("libelle", "")))}'
            + (f' — cotes {html.escape(detail)}' if detail else '') + '</p>'
            f'<p class="quand">{quand}</p></div>')


def _base():
    """L'adresse publique du site (celle qui sert dans les liens de partage et le sitemap)."""
    return os.environ.get("URL_PUBLIQUE", "https://jos626.github.io").rstrip("/")


def _compteur():
    """Le script de mesure des visites (GoatCounter). Le code du compte est celui du site."""
    code = os.environ.get("GOATCOUNTER_CODE", "guide-vpn").strip()
    if not code:
        return ""
    return (f'\n<script data-goatcounter="https://{code}.goatcounter.com/count" '
            f'async src="//gc.zgo.at/count.js"></script>')


def _image(slug, variante=0):
    """Une illustration stable pour un article : le même slug rend toujours la même image.

    ⛔ La somme des codes de caractères donnait des collisions (deux articles de la une avec la
    MÊME photo). Un vrai condensé disperse correctement.
    """
    import hashlib
    empreinte = int(hashlib.md5((slug or "").encode()).hexdigest()[:8], 16)
    n = (empreinte + variante) % 8 + 1
    return f"/img/p{n}.jpg"


def _temps_lecture(corps):
    """Minutes de lecture, arrondies — un repère que les blogs affichent et que les gens aiment."""
    mots = len(re.sub(r"<[^>]+>", " ", corps or "").split())
    return max(3, round(mots / 200))


MARQUES = [("nordvpn", "NordVPN"), ("cyberghost", "CyberGhost"),
           ("expressvpn", "ExpressVPN"), ("surfshark", "Surfshark")]


def _maj(texte):
    """Un titre de blog : première lettre en capitale, et les sigles écrits correctement."""
    texte = (texte or "").strip()
    if not texte:
        return texte
    texte = re.sub(r"\bvpn\b", "VPN", texte, flags=re.IGNORECASE)
    for fautif, juste in MARQUES:
        texte = re.sub(r"\b" + fautif + r"\b", juste, texte, flags=re.IGNORECASE)
    return texte[:1].upper() + texte[1:]


def _date_fr(texte):
    """« 12 octobre 2026 » à partir de ce que le site stocke déjà."""
    return (texte or "").strip() or "—"


def _page(titre, contenu, actif, titre_onglet=None, description=None):
    """La coquille du blog : en-tête collant, contenu, pied. Une seule balise <title> par page."""
    titre_final = titre_onglet or "Guide VPN — comparatifs et guides pour Android, TV et streaming"
    balise_desc = (f'\n<meta name="description" content="{html.escape(description)}">'
                   if description else "")
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="google-site-verification" content="_xgT2NROIIzNXS7Iw1Mv0V15aetbsBWr-EBJqHR9nus">
<title>{titre_final}</title>{balise_desc}
<link rel="manifest" href="/manifeste.json">
<meta name="theme-color" content="#fffdf8">
<meta name="mobile-web-app-capable" content="yes">
<link rel="apple-touch-icon" href="/icone-apple-180.png">
<link rel="icon" type="image/png" href="/icone-192.png">
<style>{STYLE}</style></head><body>
<header class="site"><div class="wrap">
<a class="marque" href="/">Guide<span>VPN</span></a>
<nav><a href="/">Accueil</a><a href="/guides/">Tous les guides</a></nav>
</div></header>
<main class="wrap">{contenu}</main>
<footer class="pied"><div class="wrap">
<p><b>Guide VPN</b> — des comparatifs honnêtes : ce qui marche, ce qui ne marche pas, et pourquoi.</p>
<p>Écrit par José Ledanite · <a href="/sitemap.xml">Plan du site</a></p>
</div></footer>
{_compteur()}
</body></html>"""


def page_guides():
    """La une du blog : un article mis en avant, puis la liste des derniers guides."""
    entrees = list(articles.ARTICLES.items())
    if not entrees:
        corps = ('<div class="une"><h2>Les guides arrivent</h2>'
                 '<p>Aucun article publié pour le moment. Reviens dans quelques jours.</p></div>')
        return _page("Guides", corps, "guides", titre_onglet="Guide VPN — comparatifs et guides",
                     description="Comparatifs et guides VPN pour Android, TV et streaming.")

    # L'article le plus récent occupe la une ; les autres suivent en liste.
    slug_une, a_une = entrees[-1]
    reste = list(reversed(entrees[:-1]))
    corps = (
        f'<a class="une" href="/guides/{slug_une}">'
        f'<div class="visuel"><img src="{_image(slug_une)}" alt="{html.escape(a_une["h1"])}" '
        f'loading="eager" width="1200" height="675"></div>'
        f'<span class="etiquette">À la une</span>'
        f'<h2>{html.escape(_maj(a_une["titre_onglet"]))}</h2>'
        f'<p>{html.escape(a_une["description"])}</p>'
        f'<p class="meta"><b>José Ledanite</b> · {html.escape(_date_fr(a_une["publie_le"]))} · '
        f'{_temps_lecture(a_une["corps"])} min de lecture</p>'
        f'</a>'
    )
    if reste:
        cartes = "".join(
            f'<a class="carte" href="/guides/{slug}/">'
            f'<div class="vignette"><img src="{_image(slug)}" alt="" loading="lazy" '
            f'width="264" height="192"></div>'
            f'<div><h3>{html.escape(_maj(a["titre_onglet"]))}</h3>'
            f'<p>{html.escape(a["description"])}</p>'
            f'<span class="meta">{html.escape(_date_fr(a["publie_le"]))} · '
            f'{_temps_lecture(a["corps"])} min</span></div></a>'
            for slug, a in reste)
        corps += ('<div class="titre-section"><h2>Derniers guides</h2><i></i></div>'
                  f'<div class="liste">{cartes}</div>')
    return _page("Guides", corps, "guides", titre_onglet="Guide VPN — comparatifs et guides",
                 description="Des guides VPN honnêtes pour Android, TV et streaming : ce qui marche, "
                             "ce qui ne marche pas, et combien ça coûte vraiment.")


def page_tous_guides():
    """L'archive : TOUS les guides, y compris celui de la une. C'est la page que le menu ouvre —
    sans elle, « Les guides » renvoyait vers l'accueil et le clic ne produisait rien de visible."""
    entrees = list(reversed(list(articles.ARTICLES.items())))
    if not entrees:
        corps = '<div class="article"><h1>Tous les guides</h1><p class="chapeau">Rien encore.</p></div>'
        return _page("Tous les guides", corps, "guides")
    cartes = "".join(
        f'<a class="carte" href="/guides/{slug}/">'
        f'<div class="vignette"><img src="{_image(slug)}" alt="" loading="lazy" width="264" height="192"></div>'
        f'<div><h3>{html.escape(_maj(a["titre_onglet"]))}</h3>'
        f'<p>{html.escape(a["description"])}</p>'
        f'<span class="meta">{html.escape(_date_fr(a["publie_le"]))} · {_temps_lecture(a["corps"])} min</span></div></a>'
        for slug, a in entrees)
    corps = (f'<div class="article" style="margin-top:26px"><h1>Tous les guides</h1>'
             f'<p class="chapeau">{len(entrees)} guides : ce qui marche vraiment, ce qui ne marche pas, '
             f'et combien ça coûte.</p></div>'
             f'<div class="liste">{cartes}</div>')
    return _page("Tous les guides", corps, "guides",
                 titre_onglet="Tous les guides VPN — Guide VPN",
                 description="La liste complète des guides VPN : installation, streaming, sport en ligne, "
                             "prix réels et pièges à éviter.")


def page_article(slug):
    """Un guide, présenté comme un article de blog : visuel, signature, partage, suite à lire."""
    a = articles.ARTICLES.get(slug)
    if not a:
        return None
    url = f"{_base()}/guides/{slug}/"
    titre = a["titre_onglet"]
    partage = (
        f'<a href="https://wa.me/?text={urllib.parse.quote(titre + " " + url)}" rel="nofollow">WhatsApp</a>'
        f'<a href="https://www.facebook.com/sharer/sharer.php?u={urllib.parse.quote(url)}" rel="nofollow">Facebook</a>'
        f'<a href="https://twitter.com/intent/tweet?text={urllib.parse.quote(titre)}&url={urllib.parse.quote(url)}" rel="nofollow">X</a>'
        f'<button type="button" onclick="navigator.clipboard.writeText(\'{url}\');this.textContent=\'Lien copié\'">Copier le lien</button>'
    )
    autres = [(s, x) for s, x in articles.ARTICLES.items() if s != slug][:3]
    suite = "".join(
        f'<a class="carte" href="/guides/{s}/"><div class="vignette">'
        f'<img src="{_image(s)}" alt="" loading="lazy" width="264" height="192"></div>'
        f'<div><h3>{html.escape(_maj(x["titre_onglet"]))}</h3>'
        f'<span class="meta">{_temps_lecture(x["corps"])} min de lecture</span></div></a>'
        for s, x in autres)
    corps = (
        f'<div class="article">'
        f'<p class="fil"><a href="/">Accueil</a> › <a href="/guides/">Guides</a> › {html.escape(titre)}</p>'
        f'<h1>{html.escape(_maj(a["h1"]))}</h1>'
        f'<p class="chapeau">{html.escape(a["chapeau"])}</p>'
        f'<div class="entete-meta"><img src="/img/auteur.jpg" alt="José Ledanite" width="34" height="34">'
        f'<span><b>José Ledanite</b> · {html.escape(_date_fr(a["publie_le"]))} · '
        f'{_temps_lecture(a["corps"])} min de lecture</span></div>'
        f'<div class="hero"><img src="{_image(slug)}" alt="{html.escape(titre)}" '
        f'width="1200" height="675"></div>'
        f'{a["corps"]}'
        f'<div class="encart" style="border-color:#d9a900;background:#fffaf0">'
        f'<img src="/img/auteur.jpg" alt="" width="56" height="56">'
        f'<div><b>📘 Le guide VPN 2026 — gratuit</b>'
        f'<p>Six sections pour choisir, installer et ne pas se faire avoir. '
        f'<a href="/livre-blanc/"><b>Recevoir le guide</b></a> — par email, sans spam.</p></div></div>'
        f'{FORMULAIRE}'
        f'<div class="encart"><img src="/img/auteur.jpg" alt="José Ledanite" width="56" height="56">'
        f'<div><b>Cet article t’a été utile ?</b><p>Je publie un guide par jour sur les VPN, '
        f'le streaming et le foot en ligne. Le plus simple : garde le site en favori.</p></div></div>'
        f'<div class="partage"><span>Partager</span>{partage}</div>'
        f'</div>'
    )
    if suite:
        corps += ('<div class="titre-section"><h2>À lire ensuite</h2><i></i></div>'
                  f'<div class="liste">{suite}</div>')
    return _page(a["h1"], corps, "guides", titre_onglet=titre, description=a["description"])


LIVRE_BLANC = """
<h2>1. Gratuit ou payant : le vrai calcul</h2>
<p>Un VPN gratuit n'est pas un VPN moins cher : c'est un VPN payé autrement. Trois modèles existent,
et un seul est honnête.</p>
<ul>
<li><b>La version bridée</b> — 2 Go par mois, trois serveurs, une seule connexion. Suffisant pour
essayer, insuffisant pour regarder une chaîne en continu : une heure de streaming consomme 1 à 3 Go.</li>
<li><b>La revente de données</b> — le service se finance en observant ce que tu fais. C'est le modèle
économique, pas un accident.</li>
<li><b>Le faux VPN</b> — l'application affiche « connecté » et ne chiffre rien. Le test : coupe le
Wi-Fi, garde la 4G, et vérifie que ton adresse IP publique change réellement.</li>
</ul>
<p>Un abonnement correct coûte entre 2 et 4 euros par mois sur deux ans. C'est le prix d'un café par
mois — et c'est ce qui permet au service de ne pas vendre tes données.</p>

<h2>2. Installer sur une TV Android</h2>
<p>Trois chemins, du plus simple au plus manuel :</p>
<ul>
<li><b>Play Store présent</b> — installation directe, cinq minutes, c'est réglé.</li>
<li><b>Play Store absent</b> — télécharge l'APK sur le site officiel de l'éditeur, jamais sur un dépôt
tiers. Autorise l'installation depuis une source inconnue, installe, puis <b>désactive à nouveau</b>
cette autorisation.</li>
<li><b>TV sans Android</b> — le VPN se met sur le routeur, ou sur le partage de connexion du téléphone.
Toute la maison passe alors par le tunnel.</li>
</ul>

<h2>3. Pourquoi ça rame (ce n'est presque jamais le VPN)</h2>
<p>Trois causes, dans l'ordre de fréquence :</p>
<ul>
<li><b>Le serveur est trop loin</b> — prends le pays le plus proche qui débloque le service visé,
pas celui qui a le plus joli drapeau.</li>
<li><b>Le protocole</b> — WireGuard (ou NordLynx) bat OpenVPN sur une connexion mobile. C'est un
réglage, pas un changement d'abonnement.</li>
<li><b>Le Wi-Fi lui-même</b> — teste en 4G avant d'accuser le VPN. Sur une connexion à 2 Mb/s, aucun
VPN ne fera de miracle.</li>
</ul>

<h2>4. Streaming et sport : ce qui marche vraiment</h2>
<p>La réponse honnête : ça dépend du service, et ça change. Ce qui fonctionne le plus souvent :
un serveur dans le pays d'origine du compte, un protocole rapide, et surtout pas de changement de
pays toutes les cinq minutes — les plateformes repèrent les allers-retours.</p>
<p>Ce qui ne fonctionne pas : les services qui bloquent les plages d'adresses des hébergeurs. Là,
aucun VPN ne peut promettre. Un essai de 30 jours est donc plus utile que n'importe quel comparatif.</p>

<h2>5. Le prix réel sur un an</h2>
<p>Trois lignes à regarder avant de payer :</p>
<ul>
<li>le prix <b>au mois sur la durée totale</b>, pas la première année ;</li>
<li>le <b>renouvellement</b>, souvent au tarif plein ;</li>
<li>la <b>garantie de remboursement</b> — 30 jours changent tout si le service ne débloque rien.</li>
</ul>

<h2>6. La seule question qui décide de tout</h2>
<p>« Qu'est-ce que je veux débloquer, exactement ? »</p>
<ul>
<li>La TV d'un pays précis → il faut un serveur dans ce pays.</li>
<li>La sécurité sur un Wi-Fi public → n'importe quel serveur proche suffit.</li>
<li>Le sport en streaming → la vitesse et la stabilité comptent plus que le nombre de serveurs.</li>
</ul>
<p>Réponds à cette question et tu n'as plus besoin de comparatif.</p>
"""


# ⛔ LE FORMULAIRE DE CAPTURE. Pas de compte, pas de service tiers : il poste vers FormSubmit,
# qui relaie chaque inscription par email dans la boîte de José. Pépite lit ensuite cette boîte
# (IMAP) et envoie la séquence. C'est le seul chemin qui ne demande AUCUNE vérification.
FORMULAIRE = """
<form class="capture" action="https://formsubmit.co/chrismotivation21@gmail.com" method="POST">
  <input type="hidden" name="_subject" value="Nouvelle inscription — Guide VPN">
  <input type="hidden" name="_captcha" value="false">
  <input type="hidden" name="_template" value="table">
  <input type="hidden" name="_next" value="https://jos626.github.io/livre-blanc/merci/">
  <input type="email" name="email" required placeholder="ton@email.com" aria-label="Ton adresse email">
  <button type="submit">Recevoir le guide</button>
</form>
<p class="capture-note">Le guide arrive tout de suite. Ensuite, un email utile de temps en temps —
jamais de spam, désinscription en un clic.</p>
"""

COUVERTURE = """
<div class="ebook"><div class="livre">
  <div class="haut"><small>Livre blanc · édition 2026</small>
    <h3>Le guide VPN 2026</h3></div>
  <div class="bas">Choisir · Installer · Ne pas se faire avoir<br>José Ledanite</div>
</div></div>
"""


def page_livre_blanc():
    """Le livre blanc : une page qu'on peut lire en ligne et imprimer en PDF (Ctrl+P)."""
    corps = ('<div class="article" style="margin-top:26px">'
             '<p class="fil"><a href="/">Accueil</a> › Livre blanc</p>'
             '<h1>Le guide VPN 2026</h1>'
             '<p class="chapeau">Choisir, installer, ne pas se faire avoir : ce que les comparatifs '
             'ne disent pas, en six sections.</p>'
             + COUVERTURE + FORMULAIRE +
             '<div class="entete-meta"><img src="/img/auteur.jpg" alt="José Ledanite" width="34" height="34">'
             '<span><b>José Ledanite</b> · édition 2026 · 9 min de lecture</span></div>'
             + LIVRE_BLANC +
             '<div class="encart"><img src="/img/auteur.jpg" alt="José Ledanite" width="56" height="56">'
             '<div><b>Tu veux le recevoir par email ?</b>'
             '<p>Donne ton adresse et je te l\'envoie — puis un guide utile par mois, jamais de spam.</p>'
             '</div></div>'
             '<div class="partage"><span>Partager</span>'
             f'<a href="https://wa.me/?text={urllib.parse.quote("Le guide VPN 2026 — " + _base() + "/livre-blanc")}" rel="nofollow">WhatsApp</a>'
             f'<a href="https://www.facebook.com/sharer/sharer.php?u={urllib.parse.quote(_base() + "/livre-blanc")}" rel="nofollow">Facebook</a>'
             '</div></div>')
    return _page("Le guide VPN 2026", corps, "guides",
                 titre_onglet="Le guide VPN 2026 — livre blanc gratuit",
                 description="Gratuit ou payant, installation sur TV Android, vitesse, streaming, prix "
                             "réel : le guide complet en six sections, par José Ledanite.")


def page_merci():
    corps = ('<div class="article" style="margin-top:40px;text-align:left">'
             '<h1>C\'est envoyé.</h1>'
             '<p class="chapeau">Le guide part dans ta boîte dans la minute. S\'il n\'arrive pas, '
             'regarde dans les spams et marque-le comme « non spam » — c\'est le premier email, '
             'les suivants passeront ensuite.</p>'
             '<p><a href="/guides/"><b>Lire les guides en attendant →</b></a></p></div>')
    return _page("C'est envoyé", corps, "guides", titre_onglet="Guide envoyé — Guide VPN")


def sitemap():
    """LA CARTE DU SITE — indispensable : sans elle, Google met des semaines à trouver les guides.
    Le domaine est celui du déploiement ; si José change d'adresse, cette ligne suit."""
    base = os.environ.get("URL_PUBLIQUE", "https://guide-vpn.onrender.com").rstrip("/")
    pages = ["/", "/guides/", "/livre-blanc"] + [f"/guides/{s}/" for s in articles.ARTICLES]
    urls = "".join(f"<url><loc>{base}{p}</loc></url>" for p in pages)
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + "</urlset>")


def robots():
    base = os.environ.get("URL_PUBLIQUE", "https://guide-vpn.onrender.com").rstrip("/")
    return f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n"


MANIFESTE = """{
 "name": "Guide VPN", "short_name": "Guide VPN", "lang": "fr",
 "start_url": "/", "scope": "/", "display": "standalone",
 "background_color": "#f7f9fc", "theme_color": "#f7f9fc",
 "description": "Comparatifs et guides VPN pour Android, TV et streaming — par José Ledanite.",
 "icons": [
  {"src": "/icone-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
  {"src": "/icone-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
  {"src": "/icone-masquable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
 ]
}"""

SERVICE_WORKER = """self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {});   // rien en cache : un pronostic périmé est un mensonge
"""

FICHIERS = {"manifeste.json": ("application/manifest+json; charset=utf-8", MANIFESTE),
            "sw.js": ("text/javascript; charset=utf-8", SERVICE_WORKER)}
ICONES = ("icone-192.png", "icone-512.png", "icone-masquable-512.png",
          "icone-apple-180.png", "iparv.png")


def fabriquer_serveur(port=8080):
    class Traitement(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _envoyer(self, donnees, type_mime, code=200):
            if isinstance(donnees, str):
                donnees = donnees.encode()
            self.send_response(code)
            self.send_header("Content-Type", type_mime)
            self.send_header("Content-Length", str(len(donnees)))
            self.end_headers()
            self.wfile.write(donnees)

        def do_GET(self):
            chemin = self.path.split("?")[0]

            # ⚠️ ON COMPTE LES PAGES AFFICHÉES, PAS LES FICHIERS. Une icône ou un fichier JSON n'est
            # pas une visite : les compter gonflerait les chiffres sans rien dire de vrai. On garde
            # aussi le détail par page — « 40 visites » ne dit pas quoi corriger, « 40 visites dont
            # 31 sur le guide VPN » le dit.
            if not chemin.startswith(("/icone", "/manifeste", "/publication.json", "/trafic.json",
                                      "/sitemap", "/robots")):
                trafic.compter(chemin, self.headers.get("Referer") or "",
                               self.headers.get("User-Agent") or "")

            if chemin == "/trafic.json":
                import json as _json
                self._envoyer(_json.dumps(trafic.instantane(), ensure_ascii=False).encode(),
                              "application/json; charset=utf-8")
                return

            # ⚠️ DIAGNOSTIC TEMPORAIRE — POSÉ PUIS RETIRÉ LE MÊME JOUR (10/10/2026).
            # Question de José : « Quand je prendrai l'abonnement OVH, mon téléphone devra-t-il toujours
            # garder la récolte des cotes ? » Le test a été fait DEPUIS FRANCFORT — un vrai serveur, pas
            # une supposition : m.betclic.ci répond 403 Forbidden, la page du football comme la racine.
            # Betclic Côte d'Ivoire refuse les serveurs européens.
            # ✅ CONCLUSION RETENUE : la RÉCOLTE DES COTES RESTE SUR LE TÉLÉPHONE, quoi qu'il arrive.
            # Le reste (analyses, montante, application) peut partir sur OVH.
# ⛔ On ne réactive pas ce genre de route en ligne : une adresse écrite en dur est la règle,
            # et un diagnostic public qui va chercher des pages est exactement ce qu'on ne garde pas.

            if chemin in ("/", "/index.html"):
                self._envoyer(page_guides(), "text/html; charset=utf-8")
                return
            # ── LES GUIDES (le contenu qui se référence). José, 10/10/2026 : « on va passer au SEO
            # de pari foot ». Sans ces pages, il n'y a rien à référencer : une application sans
            # texte ne se classe pas sur Google.
            if chemin in ("/livre-blanc/merci", "/livre-blanc/merci/"):
                self._envoyer(page_merci(), "text/html; charset=utf-8")
                return
            if chemin == "/livre-blanc":
                self._envoyer(page_livre_blanc(), "text/html; charset=utf-8")
                return
            if chemin == "/guides":
                self._envoyer(page_tous_guides(), "text/html; charset=utf-8")
                return
            if chemin.startswith("/guides/"):
                page = page_article(chemin[len("/guides/"):].strip("/"))
                if page:
                    self._envoyer(page, "text/html; charset=utf-8")
                else:
                    self._envoyer("<h1>Page introuvable</h1>", "text/html; charset=utf-8", 404)
                return
            # La carte du site : elle dit à Google quelles pages existent. Sans elle, un site neuf
            # peut rester des semaines sans être exploré.
            if chemin == "/sitemap.xml":
                self._envoyer(sitemap(), "application/xml; charset=utf-8")
                return
            if chemin == "/robots.txt":
                self._envoyer(robots(), "text/plain; charset=utf-8")
                return
            if chemin == "/publication.json":
                self._envoyer(json.dumps(lire_publication() or {},
                                         ensure_ascii=False).encode(),
                              "application/json; charset=utf-8")
                return
            if chemin.lstrip("/") in FICHIERS:
                type_mime, texte = FICHIERS[chemin.lstrip("/")]
                self._envoyer(texte, type_mime)
                return
            if chemin.lstrip("/") in ICONES:
                try:
                    with open(os.path.join(ICI, chemin.lstrip("/")), "rb") as f:
                        self._envoyer(f.read(), "image/png")
                except OSError:
                    self._envoyer("introuvable", "text/plain", 404)
                return
            self._envoyer("<h1>Page introuvable</h1>", "text/html; charset=utf-8", 404)

    return ThreadingHTTPServer(("0.0.0.0", port), Traitement)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"Guide VPN écoute sur le port {port}", flush=True)
    fabriquer_serveur(port).serve_forever()
