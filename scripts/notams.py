"""Fetch current NOTAMs for given ICAO locations from the FAA DINS public page.

Prints a JSON list of raw NOTAM texts. Prints nothing and exits 1 if the page
could not be read, so the workflow keeps the previous list.
"""
import html, json, re, sys, urllib.request

locs = sys.argv[1:] or ["LHBS"]
url = ("https://www.notams.faa.gov/dinsQueryWeb/queryRetrievalMapAction.do"
       "?reportType=Raw&actionType=notamRetrievalByICAOs&submit=View+NOTAMs"
       "&retrieveLocId=" + "+".join(locs))
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (FlyCoop flight sheet)"})
try:
    page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
except Exception as e:
    print(json.dumps({"notams": [], "info": f"fetch failed: {e}"})); sys.exit(0)

notams = []
for block in re.findall(r"<pre[^>]*>(.*?)</pre>", page, flags=re.S | re.I):
    text = html.unescape(re.sub(r"<[^>]+>", "", block)).strip()
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text)
    if text and any(l in text for l in locs) and text not in notams:
        notams.append(text)

snippet = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page))
i = snippet.find("LHBS")
info = f"{len(page)} bytes, {len(re.findall(r'<pre', page, flags=re.I))} pre blocks, {len(notams)} NOTAMs; near LHBS: {snippet[max(0,i-80):i+200] if i >= 0 else 'LHBS not found'}"
print(json.dumps({"notams": notams, "info": info[:600]}))
