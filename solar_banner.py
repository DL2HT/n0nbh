#!/usr/bin/env python3
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont

XML_URL = "https://www.hamqsl.com/solarxml.php"
OUTFILE = "solartext.png"

def safe_get(parent, tag, default=""):
    el = parent.find(tag)
    if el is None or el.text is None:
        return default
    return el.text.strip()

def classify_sfi(sfi):
    if sfi < 80:
        return ("schwache obere KW-Baender", "weak upper HF bands")
    elif sfi < 120:
        return ("gute 20-15m Bedingungen", "good 20-15m conditions")
    elif sfi < 160:
        return ("sehr gute 20-10m Bedingungen", "very good 20-10m conditions")
    else:
        return ("exzellente 20-10m Bedingungen", "excellent 20-10m conditions")

def classify_k(k):
    if k <= 1:
        return ("Magnetfeld ruhig", "geomagnetic field quiet")
    elif k <= 3:
        return ("Magnetfeld leicht unruhig", "geomagnetic field unsettled")
    elif k == 4:
        return ("Magnetfeld gestoert", "geomagnetic field active")
    elif k <= 5:
        return ("geomagnetischer Sturm (K>=5)", "minor geomagnetic storm (K>=5)")
    else:
        return ("starker geomagnetischer Sturm", "major geomagnetic storm")

def classify_aurora(a):
    if a < 5:
        return ("Aurora-DX unwahrscheinlich", "Aurora DX unlikely")
    elif a < 7:
        return ("moegliche Aurora-Aktivitaet", "possible auroral activity")
    else:
        return ("hohe Aurora-Wahrscheinlichkeit", "high auroral probability")

def classify_xray(xray_str):
    if not xray_str:
        return ("X-Ray Hintergrund ruhig", "low X-ray background")
    level = xray_str[0].upper()
    if level in ("A", "B"):
        return ("X-Ray Hintergrund ruhig", "low X-ray background")
    elif level == "C":
        return ("C-Flare Aktivitaet", "C-flare activity")
    elif level == "M":
        return ("M-Flare - kurzzeitige HF-Daempfung moeglich", "M-flare - short HF fade possible")
    else:
        return ("X-Flare - HF-Blackouts moeglich", "X-flare - HF blackouts possible")

def main():
    resp = requests.get(XML_URL, timeout=15)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    item = root.find("./channel/item/solardata")
    if item is None:
        item = root.find("./channel/item")
    if item is None:
        raise SystemExit("Konnte solardata-Element nicht finden")

    sfi = float(safe_get(item, "solarflux", "0") or 0)
    sn = safe_get(item, "sunspots", "?")
    a = int(float(safe_get(item, "aindex", "0") or 0))
    k = int(float(safe_get(item, "kindex", "0") or 0))
    xray = safe_get(item, "xray", "")
    aurora = float(safe_get(item, "aurora", "0") or 0)
    geomag = safe_get(item, "geomagfield", "NoRpt")
    sig_noise = safe_get(item, "signalnoise", "?")

    sfi_de, sfi_en = classify_sfi(sfi)
    k_de, k_en = classify_k(k)
    aur_de, aur_en = classify_aurora(aurora)
    xr_de, xr_en = classify_xray(xray)

    now_utc = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

    lines_de = [
        f"DL2HT Solarbericht - {now_utc}",
        f"SFI {int(sfi)} / SN {sn} - {sfi_de}",
        f"A={a}, K={k} - {k_de}",
        f"Aurora-Index {aurora:.1f} - {aur_de}",
        f"X-Ray {xray or 'n/a'} - {xr_de}",
        f"Geomag: {geomag}, Rauschpegel: {sig_noise}",
    ]

    lines_en = [
        f"DL2HT Solar Report - {now_utc}",
        f"SFI {int(sfi)} / SSN {sn} - {sfi_en}",
        f"A={a}, K={k} - {k_en}",
        f"Aurora index {aurora:.1f} - {aur_en}",
        f"X-ray {xray or 'n/a'} - {xr_en}",
        f"Geomag: {geomag}, Noise level: {sig_noise}",
    ]

    width, height = 640, 300
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_big = ImageFont.truetype("arial.ttf", 18)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    y = 8
    draw.text((10, y), "Solar / HF Bedingungen - DL2HT (JO43VK)", font=font_big, fill=(0, 0, 0))
    y += 26

    for line in lines_de:
        draw.text((10, y), line, font=font_small, fill=(0, 0, 0))
        y += 18

    y += 4
    draw.line((10, y, width - 10, y), fill=(0, 0, 0))
    y += 8

    for line in lines_en:
        draw.text((10, y), line, font=font_small, fill=(0, 0, 0))
        y += 18

    footer = "Data source: hamqsl.com / N0NBH"
    fw, fh = draw.textsize(footer, font=font_small)
    draw.text((width - fw - 10, height - fh - 4), footer, font=font_small, fill=(0, 0, 0))

    img.save(OUTFILE)

if __name__ == "__main__":
    main()
