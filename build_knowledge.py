#!/usr/bin/env python3
"""Bouwt Doofinder AI Knowledge Base-documenten uit ALLE Shopify-blogartikelen.
Per blog-categorie 1+ tekstdocument (gesplitst op <34000 tekens, de KB-limiet),
met titel + ruimere body-excerpt + link. Output: knowledge/<slug>_<n>.txt"""
import os, sys, json, re, time, urllib.request, collections

STORE = re.sub(r'^https?://|/$', '', os.environ.get('SHOPIFY_STORE_URL',''))
TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN')
API = os.environ.get('SHOPIFY_API_VERSION','2026-01')
BASE='https://vijvercentrum.nl'
URL=f'https://{STORE}/admin/api/{API}/graphql.json'
Q="""query($c:String){ articles(first:100, after:$c, sortKey:PUBLISHED_AT, reverse:true){
 pageInfo{hasNextPage endCursor}
 nodes{ id title handle summary body publishedAt tags blog{handle title} } } }"""
TAG=re.compile(r'<[^>]+>'); WS=re.compile(r'\s+')
def strip(h,n):
    if not h: return ''
    t=TAG.sub(' ',h)
    for a,b in [('&nbsp;',' '),('&amp;','&'),('&lt;','<'),('&gt;','>'),('&#39;',"'"),('&quot;','"')]:
        t=t.replace(a,b)
    return WS.sub(' ',t).strip()[:n]
def gql(c):
    body=json.dumps({'query':Q,'variables':{'c':c}}).encode()
    req=urllib.request.Request(URL,data=body,method='POST',headers={'Content-Type':'application/json','X-Shopify-Access-Token':TOKEN})
    with urllib.request.urlopen(req,timeout=30) as r: d=json.loads(r.read().decode())
    if d.get('errors'): raise RuntimeError(d['errors'])
    return d['data']['articles']

def slug(s): return re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')

items, c = [], None
while True:
    a=gql(c)
    for n in a['nodes']:
        bh=(n.get('blog') or {}).get('handle','')
        items.append({
            'blog':(n.get('blog') or {}).get('title','Overig'),
            'title':n.get('title',''),
            'link':f"{BASE}/blogs/{bh}/{n['handle']}" if bh else '',
            'text':strip(n.get('body') or n.get('summary',''),440),
        })
    if not a['pageInfo']['hasNextPage']: break
    c=a['pageInfo']['endCursor']; time.sleep(0.5)

groups=collections.OrderedDict()
for it in items: groups.setdefault(it['blog'],[]).append(it)

os.makedirs('knowledge',exist_ok=True)
for f in os.listdir('knowledge'): os.remove(os.path.join('knowledge',f))
LIMIT=34000
manifest=[]
for blog, arts in groups.items():
    header=f"VIJVERCENTRUM KENNISBANK - {blog}\nDit zijn samenvattingen van onze blogartikelen over '{blog}'. Gebruik deze kennis om klanten van Vijvercentrum (vijver- en koispecialist) accuraat te adviseren. Verwijs voor het volledige artikel naar de link.\n\n"
    chunks=[]; cur=header; n=1
    for it in arts:
        block=f"### {it['title']}\n{it['text']}\nVolledig artikel: {it['link']}\n\n"
        if len(cur)+len(block)>LIMIT:
            chunks.append(cur); cur=header+block
        else:
            cur+=block
    chunks.append(cur)
    for i,ch in enumerate(chunks,1):
        name=f"{slug(blog)}_{i}.txt" if len(chunks)>1 else f"{slug(blog)}.txt"
        open(os.path.join('knowledge',name),'w',encoding='utf-8').write(ch)
        manifest.append((name,len(ch),len(arts) if len(chunks)==1 else '~'))
print(f"{len(items)} artikelen, {len(groups)} thema's")
for name,sz,_ in manifest: print(f"  {sz:6d}  knowledge/{name}")
