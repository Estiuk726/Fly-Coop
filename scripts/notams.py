"""Fetch current NOTAMs for given ICAO locations.

Tries the FAA NOTAM Search backend (notams.aim.faa.gov), then the old DINS page.
Prints {"notams": [...], "info": "..."} as JSON.
"""
import html, json, re, sys, urllib.parse, urllib.request

locs = sys.argv[1:] or ["LHBS"]
UA = {"User-Agent": "Mozilla/5.0 (FlyCoop flight sheet)"}
notes = []

def faa_search():
    data = urllib.parse.urlencode({
        "searchType": 0, "designatorsForLocation": ",".join(locs), "designatorForAccountable": "",
        "latDegrees": "", "latMinutes": 0, "latSeconds": 0, "longDegrees": "", "longMinutes": 0, "longSeconds": 0,
        "radius": 10, "sortColumns": "5 false", "sortDirection": True, "designatorForNotamNumberSearch": "",
        "notamNumber": "", "radiusSearchOnDesignator": False, "radiusSearchDesignator": "",
        "latitudeDirection": "N", "longitudeDirection": "W", "freeFormText": "", "flightPathText": "",
        "flightPathDivertAirfields": "", "flightPathBuffer": 4, "flightPathIncludeNavaids": True,
        "flightPathIncludeArtcc": False, "flightPathIncludeTfr": True, "flightPathIncludeRegulatory": False,
        "flightPathResultsType": "All NOTAMs", "archiveDate": "", "archiveDesignator": "", "offset": 0,
        "notamsOnly": False, "filters": "", "minRunwayLength": "", "minRunwayWidth": "",
        "runwaySurfaceTypes": "", "predefinedAbbreviationsAndCategories": "", "notamType": ""}).encode()
    req = urllib.request.Request("https://notams.aim.faa.gov/notamSearch/search", data=data,
                                 headers={**UA, "Content-Type": "application/x-www-form-urlencoded"})
    j = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace"))
    out = []
    for n in j.get("notamList", []):
        t = (n.get("icaoMessage") or n.get("traditionalMessageFrom4thWord") or n.get("traditionalMessage") or "").strip()
        if t:
            out.append(re.sub(r"\s*\n\s*", "\n", t))
    return out, f"FAA search: {j.get('totalNotamCount', len(out))} total"

def dins():
    url = ("https://www.notams.faa.gov/dinsQueryWeb/queryRetrievalMapAction.do"
           "?reportType=Raw&actionType=notamRetrievalByICAOs&submit=View+NOTAMs&retrieveLocId=" + "+".join(locs))
    page = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "replace")
    out = []
    for block in re.findall(r"<pre[^>]*>(.*?)</pre>", page, flags=re.S | re.I):
        t = html.unescape(re.sub(r"<[^>]+>", "", block)).strip()
        t = re.sub(r"[ \t]+", " ", re.sub(r"\s*\n\s*", "\n", t))
        if t and any(l in t for l in locs):
            out.append(t)
    return out, f"DINS: {len(page)} bytes"

for src in (faa_search, dins):
    try:
        found, info = src()
        notams = list(dict.fromkeys(found))
        print(json.dumps({"notams": notams, "info": f"{info}, {len(notams)} kept"}))
        sys.exit(0)
    except Exception as e:
        notes.append(f"{src.__name__} failed: {e}")
print(json.dumps({"notams": [], "info": "fetch failed: " + "; ".join(notes)}))
