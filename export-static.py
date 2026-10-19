"""export-static.py — transforme le site Pépite (serveur Python) en HTML statique.

POURQUOI : Render exige une carte bancaire pour un nouveau service. GitHub Pages n'en
demande pas. Le site Pépite est du contenu : on le rend une fois en fichiers HTML et on
le publie tel quel.

Ce script démarre le serveur local, aspire chaque adresse, écrit les fichiers dans
`publication-static/`, puis arrête le serveur. Les liens absolus continuent de
fonctionner parce que le site est publié à la RACINE du domaine (dépôt Jos626.github.io).
"""

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "publication-static")
HOTE_LOCAL = "http://127.0.0.1"


def _port_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _aspirer(port, chemin):
    with urllib.request.urlopen(f"{HOTE_LOCAL}:{port}{chemin}", timeout=60) as r:
        return r.read()


def _ecrire(relatif, donnees):
    chemin = os.path.join(SORTIE, relatif)
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "wb") as f:
        f.write(donnees)


def main(domaine):
    if os.path.isdir(SORTIE):
        shutil.rmtree(SORTIE)
    os.makedirs(SORTIE)

    port = _port_libre()
    environ = dict(os.environ, PORT=str(port))
    serveur = subprocess.Popen([sys.executable, "-u", os.path.join(ICI, "serveur.py")],
                               cwd=ICI, env=environ,
                               stdout=open("/tmp/export-serveur.log","w"), stderr=subprocess.STDOUT)
    try:
        for _ in range(40):
            try:
                urllib.request.urlopen(f"{HOTE_LOCAL}:{port}/", timeout=2).read()
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise SystemExit("Le serveur local n'a pas démarré.")

        articles = []
        # Les slugs viennent du module `articles` lui-même : c'est lui qui fait foi (guides écrits
        # à la main + articles déposés en JSON). Lire seulement le dossier ratait le guide eFootball.
        try:
            import articles as _articles
            articles = list(_articles.ARTICLES.keys())
        except Exception as e:
            print("  (module articles illisible :", e, ")", flush=True)
        if not articles:
            dossier_articles = os.path.join(ICI, "articles-auto")
            if os.path.isdir(dossier_articles):
                for f in sorted(os.listdir(dossier_articles)):
                    if f.endswith(".json"):
                        with open(os.path.join(dossier_articles, f), encoding="utf-8") as fh:
                            articles.append(json.load(fh).get("slug"))

        pages = [("", "index.html"), ("/guides", "guides/index.html"),
                 ("/livre-blanc", "livre-blanc/index.html")]
        for slug in articles:
            if slug:
                pages.append((f"/guides/{slug}", f"guides/{slug}/index.html"))

        compte = 0
        for chemin, fichier in pages:
            donnees = _aspirer(port, chemin or "/")
            _ecrire(fichier, donnees)
            compte += 1
            print(f"  {chemin or '/'} -> {fichier}", flush=True)

        for chemin, fichier in [("/sitemap.xml", "sitemap.xml"), ("/robots.txt", "robots.txt"),
                                ("/manifeste.json", "manifeste.json")]:
            _ecrire(fichier, _aspirer(port, chemin))

        # Les articles retirés laissent des adresses mortes (partages, favoris). GitHub Pages sert
        # ce 404 sur toute URL inconnue : on y renvoie vers les guides plutôt qu'un écran d'erreur.
        _ecrire("404.html", """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="0; url=/guides/">
<title>Page introuvable — Guide VPN</title>
<style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#fffdf8;
color:#161513;font:17px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;text-align:center;padding:24px}
a{color:#8a6b00}</style></head><body><div>
<h1 style="font-family:Georgia,serif;font-size:28px">Cette page n'existe plus</h1>
<p>Le guide a été retiré. <a href="/guides/">Voir tous les guides</a>.</p>
</div></body></html>""".encode())

        for f in os.listdir(ICI):
            if f.startswith("icone-") and f.endswith(".png"):
                shutil.copy(os.path.join(ICI, f), os.path.join(SORTIE, f))

        # les illustrations des articles (téléchargées une fois, servies par le site)
        dossier_img = os.path.join(ICI, "img")
        if os.path.isdir(dossier_img):
            shutil.copytree(dossier_img, os.path.join(SORTIE, "img"))
    finally:
        serveur.terminate()
        try:
            serveur.wait(timeout=10)
        except Exception:
            serveur.kill()

    # ⚠️ LE DOMAINE : le serveur écrit « guide-vpn.onrender.com » partout. On le remplace
    # par le domaine réel, sinon canonical, sitemap et partages pointeraient dans le vide.
    motifs = 0
    for racine, _, fichiers in os.walk(SORTIE):
        for f in fichiers:
            if not f.endswith((".html", ".xml", ".txt", ".json")):
                continue
            p = os.path.join(racine, f)
            with open(p, encoding="utf-8", errors="ignore") as fh:
                t = fh.read()
            avant = t
            t = t.replace("guide-vpn.onrender.com", domaine)
            # la balise Admitad appartient au site Pari-Foot : elle n'a rien à faire ici
            t = re.sub(r'\s*<meta name="mitgo-verification"[^>]*>', "", t)
            if t != avant:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(t)
                motifs += 1

    print(f"✅ {compte} pages + sitemap/robots écrites dans {SORTIE} ({motifs} fichiers réécrits pour {domaine})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "jos626.github.io")
