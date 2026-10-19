def _base():
    """L'adresse publique du site (celle qui sert dans les liens de partage et le sitemap)."""
    return os.environ.get("URL_PUBLIQUE", "https://jos626.github.io").rstrip("/")


def _image(slug, variante=0):
    """Une illustration stable pour un article : le même slug rend toujours la même image."""
    n = (sum(ord(c) for c in (slug or "")) + variante) % 5 + 1
    return f"/img/p{n}.jpg"


def _temps_lecture(corps):
    """Minutes de lecture, arrondies — un repère que les blogs affichent et que les gens aiment."""
    mots = len(re.sub(r"<[^>]+>", " ", corps or "").split())
    return max(3, round(mots / 200))


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
<title>{titre_final}</title>{balise_desc}
<link rel="manifest" href="/manifeste.json">
<meta name="theme-color" content="#fffdf8">
<meta name="mobile-web-app-capable" content="yes">
<link rel="apple-touch-icon" href="/icone-apple-180.png">
<link rel="icon" type="image/png" href="/icone-192.png">
<style>{STYLE}</style></head><body>
<header class="site"><div class="wrap">
<a class="marque" href="/">Guide<span>VPN</span></a>
<nav><a href="/">Les guides</a><a href="/sitemap.xml">Plan</a></nav>
</div></header>
<main class="wrap">{contenu}</main>
<footer class="pied"><div class="wrap">
<p><b>Guide VPN</b> — des comparatifs honnêtes : ce qui marche, ce qui ne marche pas, et pourquoi.</p>
<p>Écrit par José Ledanite · <a href="/sitemap.xml">Plan du site</a></p>
</div></footer>
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
        f'<h2>{html.escape(a_une["titre_onglet"])}</h2>'
        f'<p>{html.escape(a_une["description"])}</p>'
        f'<p class="meta"><b>José Ledanite</b> · {html.escape(_date_fr(a_une["publie_le"]))} · '
        f'{_temps_lecture(a_une["corps"])} min de lecture</p>'
        f'</a>'
    )
    if reste:
        cartes = "".join(
            f'<a class="carte" href="/guides/{slug}">'
            f'<div class="vignette"><img src="{_image(slug)}" alt="" loading="lazy" '
            f'width="264" height="192"></div>'
            f'<div><h3>{html.escape(a["titre_onglet"])}</h3>'
            f'<p>{html.escape(a["description"])}</p>'
            f'<span class="meta">{html.escape(_date_fr(a["publie_le"]))} · '
            f'{_temps_lecture(a["corps"])} min</span></div></a>'
            for slug, a in reste)
        corps += ('<div class="titre-section"><h2>Derniers guides</h2><i></i></div>'
                  f'<div class="liste">{cartes}</div>')
    return _page("Guides", corps, "guides", titre_onglet="Guide VPN — comparatifs et guides",
                 description="Des guides VPN honnêtes pour Android, TV et streaming : ce qui marche, "
                             "ce qui ne marche pas, et combien ça coûte vraiment.")


def page_article(slug):
    """Un guide, présenté comme un article de blog : visuel, signature, partage, suite à lire."""
    a = articles.ARTICLES.get(slug)
    if not a:
        return None
    url = f"{_base()}/guides/{slug}"
    titre = a["titre_onglet"]
    partage = (
        f'<a href="https://wa.me/?text={urllib.parse.quote(titre + " " + url)}" rel="nofollow">WhatsApp</a>'
        f'<a href="https://www.facebook.com/sharer/sharer.php?u={urllib.parse.quote(url)}" rel="nofollow">Facebook</a>'
        f'<a href="https://twitter.com/intent/tweet?text={urllib.parse.quote(titre)}&url={urllib.parse.quote(url)}" rel="nofollow">X</a>'
        f'<button type="button" onclick="navigator.clipboard.writeText(\'{url}\');this.textContent=\'Lien copié\'">Copier le lien</button>'
    )
    autres = [(s, x) for s, x in articles.ARTICLES.items() if s != slug][:3]
    suite = "".join(
        f'<a class="carte" href="/guides/{s}"><div class="vignette">'
        f'<img src="{_image(s)}" alt="" loading="lazy" width="264" height="192"></div>'
        f'<div><h3>{html.escape(x["titre_onglet"])}</h3>'
        f'<span class="meta">{_temps_lecture(x["corps"])} min de lecture</span></div></a>'
        for s, x in autres)
    corps = (
        f'<div class="article">'
        f'<p class="fil"><a href="/">Les guides</a> › {html.escape(titre)}</p>'
        f'<h1>{html.escape(a["h1"])}</h1>'
        f'<p class="chapeau">{html.escape(a["chapeau"])}</p>'
        f'<div class="entete-meta"><img src="/img/auteur.jpg" alt="José Ledanite" width="34" height="34">'
        f'<span><b>José Ledanite</b> · {html.escape(_date_fr(a["publie_le"]))} · '
        f'{_temps_lecture(a["corps"])} min de lecture</span></div>'
        f'<div class="hero"><img src="{_image(slug)}" alt="{html.escape(titre)}" '
        f'width="1200" height="675"></div>'
        f'{a["corps"]}'
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
