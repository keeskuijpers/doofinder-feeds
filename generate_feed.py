#!/usr/bin/env python3
"""Genereert een Doofinder-JSON-feed van ALLE Shopify-blogartikelen (Vijvercentrum)."""
import os, sys, json, re, time, urllib.request

STORE = re.sub(r'^https?://|/$', '', os.environ.get('SHOPIFY_STORE_URL', ''))
TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN')
API = os.environ.get('SHOPIFY_API_VERSION', '2026-01')
BASE = 'https://vijvercentrum.nl'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'blog_feed.json')
URL = f'https://{STORE}/admin/api/{API}/graphql.json'
Q = """query($c:String){ articles(first:100, after:$c, sortKey:PUBLISHED_AT, reverse:true){
 pageInfo{hasNextPage endCursor}
 nodes{ id title handle summary body publishedAt tags image{url} blog{handle title} } } }"""
TAGRE = re.compile(r'<[^>]+>'); WSRE = re.compile(r'\s+')

def strip(h, n=600):
    if not h: return ''
    t = TAGRE.sub(' ', h)
    for a,b in [('&nbsp;',' '),('&amp;','&'),('&lt;','<'),('&gt;','>'),('&#39;',"'"),('&quot;','"')]:
        t = t.replace(a,b)
    return WSRE.sub(' ', t).strip()[:n]

def gql(c):
    body = json.dumps({'query':Q,'variables':{'c':c}}).encode()
    req = urllib.request.Request(URL, data=body, method='POST',
        headers={'Content-Type':'application/json','X-Shopify-Access-Token':TOKEN})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())
    if d.get('errors'): raise RuntimeError(d['errors'])
    return d['data']['articles']

def main():
    if not (STORE and TOKEN): sys.exit('Missing SHOPIFY_STORE_URL / SHOPIFY_ACCESS_TOKEN')
    items, c = [], None
    while True:
        a = gql(c)
        for n in a['nodes']:
            bh = (n.get('blog') or {}).get('handle','')
            items.append({
                'id': 'article_'+n['id'].split('/')[-1],
                'title': n.get('title',''),
                'link': f"{BASE}/blogs/{bh}/{n['handle']}" if bh else '',
                'description': strip(n.get('summary') or n.get('body','')),
                'image_link': (n.get('image') or {}).get('url',''),
                'blog': (n.get('blog') or {}).get('title',''),
                'tags': n.get('tags',[]),
                'date': n.get('publishedAt',''),
                'df_grouping_id': 'article',
            })
        if not a['pageInfo']['hasNextPage']: break
        c = a['pageInfo']['endCursor']; time.sleep(0.5)
    with open(OUT,'w',encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    print(f'OK {len(items)} artikelen -> {OUT}')

if __name__ == '__main__':
    main()
