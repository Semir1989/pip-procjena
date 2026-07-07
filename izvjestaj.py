"""Izlazni izvještaj (Dio 5 vodiča) — brendiran PDF spreman za štampu.

Struktura: zaglavlje s anonimnom oznakom slučaja, sažetak profila, STOPP tabela,
START tabela, lista "nije provjereno" i odricanje odgovornosti. Nalazi visoke
pouzdanosti su vizuelno odvojeni bojom od nesigurnih.
"""

from __future__ import annotations

import io
import os
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from kriteriji import Nalaz, Profil

# boje pouzdanosti (hex stringovi za <font color=...>)
_BOJA = {
    "visok": "#c0392b",
    "srednji": "#e67e22",
    "nizak": "#7f8c8d",
}
_START_BOJA = colors.HexColor("#1e6f42")


def _registruj_fontove() -> tuple[str, str]:
    """Registruje TTF font s podrškom za dijakritike (č, ć, ž, š, đ)."""
    kandidati = [
        (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
        (r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\segoeuib.ttf"),
    ]
    for reg, bold in kandidati:
        if os.path.exists(reg) and os.path.exists(bold):
            pdfmetrics.registerFont(TTFont("Osnovni", reg))
            pdfmetrics.registerFont(TTFont("Osnovni-Bold", bold))
            return "Osnovni", "Osnovni-Bold"
    return "Helvetica", "Helvetica-Bold"


def generisi_pdf(profil: Profil, stopp: list[Nalaz], start: list[Nalaz],
                 nije_provjereno: list[str], oznaka_slucaja: str = "") -> bytes:
    font, font_b = _registruj_fontove()

    st_naslov = ParagraphStyle("naslov", fontName=font_b, fontSize=15, spaceAfter=2 * mm)
    st_pod = ParagraphStyle("pod", fontName=font, fontSize=9, textColor=colors.HexColor("#555555"))
    st_h2 = ParagraphStyle("h2", fontName=font_b, fontSize=12, spaceBefore=5 * mm, spaceAfter=2 * mm)
    st_cel = ParagraphStyle("cel", fontName=font, fontSize=8, leading=10)
    st_cel_b = ParagraphStyle("celb", fontName=font_b, fontSize=8, leading=10)
    st_mali = ParagraphStyle("mali", fontName=font, fontSize=8, textColor=colors.HexColor("#666666"), leading=10)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm, bottomMargin=15 * mm,
        title="Procjena potencijalno neadekvatnog propisivanja",
    )
    el = []

    # --- zaglavlje ---
    el.append(Paragraph("Procjena potencijalno neadekvatnog propisivanja", st_naslov))
    el.append(Paragraph(
        f"Beers 2023 · STOPP/START v3 &nbsp;|&nbsp; Datum: {date.today().strftime('%d.%m.%Y.')}"
        + (f" &nbsp;|&nbsp; Oznaka slučaja: {oznaka_slucaja}" if oznaka_slucaja else ""),
        st_pod))
    el.append(Spacer(1, 4 * mm))

    # --- sažetak profila ---
    bubr = []
    if profil.crcl is not None:
        bubr.append(f"CrCl {profil.crcl} ml/min")
    if profil.egfr is not None:
        bubr.append(f"eGFR {profil.egfr} ml/min/1,73m²")
    sazetak = (
        f"<b>Dob:</b> {profil.dob} g. &nbsp; <b>Spol:</b> {profil.spol} &nbsp; "
        + (f"<b>Bubrežna funkcija:</b> {', '.join(bubr)} &nbsp; " if bubr else "<b>Bubrežna funkcija:</b> nije dostupna &nbsp; ")
        + f"<b>Broj lijekova:</b> {len(profil.lijekovi)} &nbsp; "
        + f"<b>Dijagnoze:</b> {len(profil.dijagnoze)}"
    )
    el.append(Paragraph(sazetak, st_cel))
    el.append(Spacer(1, 3 * mm))

    def tabela(nalazi: list[Nalaz], naslov: str, boja_zaglavlja):
        el.append(Paragraph(naslov, st_h2))
        if not nalazi:
            el.append(Paragraph("Nema detektovanih nalaza.", st_mali))
            return
        podaci = [[
            Paragraph("<b>Lijek / indikacija</b>", st_cel_b),
            Paragraph("<b>Kriterij (izvor)</b>", st_cel_b),
            Paragraph("<b>Klinički rizik</b>", st_cel_b),
            Paragraph("<b>Preporučena akcija</b>", st_cel_b),
            Paragraph("<b>Pouzd.</b>", st_cel_b),
        ]]
        for n in nalazi:
            boja = _BOJA.get(n.nivo_pouzdanosti, "#000000")
            podaci.append([
                Paragraph(n.lijek, st_cel_b),
                Paragraph(f"{n.kriterij}<br/><i>{n.izvor}</i>", st_cel),
                Paragraph(n.klinicki_rizik, st_cel),
                Paragraph(n.preporuka, st_cel),
                Paragraph(f'<font color="{boja}"><b>{n.nivo_pouzdanosti}</b></font>', st_cel),
            ])
        t = Table(podaci, colWidths=[30 * mm, 48 * mm, 38 * mm, 48 * mm, 14 * mm], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), boja_zaglavlja),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        el.append(t)

    tabela(stopp, "STOPP / Beers — potencijalno neadekvatni lijekovi", colors.HexColor("#8e2f22"))
    tabela(start, "START — propušteni, a indicirani lijekovi", _START_BOJA)

    # --- nije provjereno ---
    el.append(Paragraph("Nije provjereno — nedostajući podaci", st_h2))
    if nije_provjereno:
        for stavka in nije_provjereno:
            el.append(Paragraph(f"• {stavka}", st_mali))
    else:
        el.append(Paragraph("Svi ključni podaci za aktivirane kriterije bili su dostupni.", st_mali))

    # --- odricanje odgovornosti ---
    el.append(Spacer(1, 6 * mm))
    el.append(Paragraph(
        "<b>Odricanje odgovornosti:</b> Ovaj izvještaj je podrška kliničkom odlučivanju i "
        "edukaciji, a ne medicinsko sredstvo niti zamjena za prosudbu zdravstvenog radnika. "
        "Nijedna preporuka se ne primjenjuje bez provjere farmaceuta/ljekara. Kriteriji: "
        "AGS 2023 Updated Beers Criteria; O'Mahony i sar., STOPP/START v3 (2023) — "
        "parafrazirani skup pravila uz citiranje izvora.",
        st_mali))

    doc.build(el)
    return buf.getvalue()
