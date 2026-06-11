"""W4+ 给 HN 热议补摘要：每条 story 抓 url 目标的 meta description / 第一段。
拿不到的留空（不编造）。失败的 URL 在最终页面上诚实标"无摘要"。"""
import json, re, urllib.request, sys

d=json.load(open("data/w3_sources.json"))
hot=(d.get("hn") or {}).get("hot_ai_stories") or []
ua="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 NorthStar/0.4"

META_DESC=re.compile(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', re.I)
OG_DESC=re.compile(r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']', re.I)
TWO_DESC=re.compile(r'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']description["\']', re.I)
FIRST_P=re.compile(r'<p[^>]*>([^<]{60,400})', re.I)
TITLE=re.compile(r'<title[^>]*>([^<]+)</title>', re.I)

out={}; ok=0; fail=0
for s in hot:
    url=s.get("url","").strip()
    if not url: out[url]={"sum":"","status":"no-url"}; continue
    try:
        req=urllib.request.Request(url, headers={"User-Agent":ua,"Accept":"text/html,*/*"})
        with urllib.request.urlopen(req, timeout=10) as r:
            ct=r.headers.get("Content-Type","").lower()
            if ct and "html" not in ct and "xml" not in ct:
                out[url]={"sum":"","status":f"non-html:{ct[:30]}"}; fail+=1; continue
            body=r.read(120_000).decode("utf-8","replace")
    except Exception as e:
        out[url]={"sum":"","status":f"FAIL:{type(e).__name__}:{str(e)[:60]}"}; fail+=1; continue
    # try multiple sources
    desc=""
    for rx in (OG_DESC, META_DESC, TWO_DESC):
        m=rx.search(body)
        if m: desc=m.group(1); break
    if not desc:
        m=FIRST_P.search(body)
        if m: desc=m.group(1)
    desc=re.sub(r"&amp;","&",desc); desc=re.sub(r"&lt;","<",desc); desc=re.sub(r"&gt;",">",desc)
    desc=re.sub(r"&[a-zA-Z]+;"," ",desc); desc=re.sub(r"\s+"," ",desc).strip()
    if len(desc)<25: out[url]={"sum":"","status":"too-short"}; fail+=1; continue
    out[url]={"sum":desc[:240],"status":"ok"}; ok+=1

json.dump({"collected_at":__import__("datetime").datetime.now().isoformat(timespec="seconds"),
          "by_url":out}, open("data/hn_summaries.json","w"), ensure_ascii=False, indent=1)
print(f"HN 摘要：{ok} 成功 / {fail} 失败 / 共 {len(hot)} 条")
for url,v in out.items():
    short=url[:55] if url else "(no url)"
    print(f"  {v['status']:<28} {short}")
