"""Testovi determinističkog sloja i mehanizma kriterija.

Pokretanje:  python test_procjena.py
"""

from datetime import date

from izracuni import (
    bmi, cockcroft_gault, egfr_ckd_epi_2021, obradi_terapiju,
    stadij_ckd, trajanje_sedmica, acb_ukupno, duplikati_grupa,
)
from kriteriji import Profil, procijeni
from lijekovi import RJECNIK_LIJEKOVA

PROSLO = 0


def ok(uslov, poruka):
    global PROSLO
    assert uslov, poruka
    PROSLO += 1
    print(f"  ✓ {poruka}")


# --- izračuni ---
print("IZRAČUNI")
# Napomena: vodič uz primjer navodi "npr. 27.9", ali standardna C-G formula
# (identična kodu iz vodiča) za ove ulaze daje 31.2 ml/min.
crcl = cockcroft_gault(82, 68, 132, "Z")
ok(30 <= crcl <= 32, f"Cockcroft-Gault (82g, 68kg, 132µmol/L, Ž) = {crcl} ≈ 31.2")
egfr = egfr_ckd_epi_2021(132, 82, "Z")
ok(25 <= egfr <= 40, f"eGFR CKD-EPI 2021 = {egfr}")
ok(stadij_ckd(egfr) in ("G3b", "G4"), f"Stadij CKD = {stadij_ckd(egfr)}")
ok(bmi(68, 165) == 25.0, f"BMI 68kg/165cm = {bmi(68, 165)}")
ok(trajanje_sedmica(date(2026, 1, 5), date(2026, 7, 6)) == 26, "Trajanje 5.1.-6.7.2026 = 26 sedmica")

# --- rječnik i obrada terapije ---
print("TERAPIJA")
unosi = [
    {"inn": "Diazepam", "doza_dnevno_mg": 5, "trajanje_sedmica": 30, "indikacija": "nesanica"},
    {"inn": "diklofenak", "doza_dnevno_mg": 100, "trajanje_sedmica": 12, "indikacija": "bol u koljenu"},
    {"inn": "nepostojeci-lijek", "indikacija": "x"},
]
lijekovi, upozorenja = obradi_terapiju(unosi, RJECNIK_LIJEKOVA)
ok(len(lijekovi) == 3, "Obrađena 3 zapisa")
ok(lijekovi[0].atc == "N05BA01", "Diazepam mapiran na ATC N05BA01 (neosjetljivo na velika slova)")
ok("bzd" in lijekovi[0].grupe, "Diazepam u grupi bzd")
ok(len(upozorenja) == 1, "Neprepoznat lijek daje upozorenje")

l2, _ = obradi_terapiju([
    {"inn": "amitriptilin"}, {"inn": "solifenacin"}, {"inn": "kvetiapin"},
], RJECNIK_LIJEKOVA)
ok(acb_ukupno(l2) == 9, f"ACB zbir amitriptilin+solifenacin+kvetiapin = {acb_ukupno(l2)} (3+3+3)")

l3, _ = obradi_terapiju([{"inn": "ibuprofen"}, {"inn": "diklofenak"}], RJECNIK_LIJEKOVA)
ok(duplikati_grupa(l3) and duplikati_grupa(l3)[0][0] == "NSAID", "Dva NSAID-a detektovana kao duplikat")

# --- kriteriji: primjer iz vodiča (Dio 2 + 4.2) ---
print("KRITERIJI — primjer iz vodiča")
lij, _ = obradi_terapiju([
    {"inn": "diazepam", "doza_dnevno_mg": 5, "trajanje_sedmica": 30, "indikacija": "nesanica"},
    {"inn": "diklofenak", "doza_dnevno_mg": 100, "put": "per os", "trajanje_sedmica": 12, "indikacija": "bol u koljenu"},
], RJECNIK_LIJEKOVA)
profil = Profil(
    dob=82, spol="Z", masa_kg=68, crcl=27.9, egfr=31,
    dijagnoze={"atrijska_fibrilacija", "padovi", "ckd"},
    lijekovi=lij,
)
stopp, start, nije = procijeni(profil)
tekst_stopp = " | ".join(n.kriterij for n in stopp)

ok(any("Benzodiazepin duže od 4 sedmice" in n.kriterij for n in stopp),
   "STOPP: diazepam 30 sedmica → dugotrajni BZD")
ok(any("Dugodjelujući benzodiazepin" in n.kriterij for n in stopp),
   "STOPP: diazepam je dugodjelujući BZD")
ok(any("NSAID uz oslabljenu bubrežnu funkciju" in n.kriterij for n in stopp),
   "STOPP: diklofenak uz CrCl 27.9 → renalni kriterij")
ok(any("anamnezu pada" in n.kriterij for n in stopp),
   "STOPP: psihotrop uz anamnezu pada")
ok(any(n.lijek == "oralni antikoagulans" for n in start),
   "START: AF bez antikoagulansa → propušten OAK")

# --- START ne okida kad je lijek prisutan ---
lij2, _ = obradi_terapiju([
    {"inn": "apiksaban", "doza_dnevno_mg": 10, "trajanje_sedmica": 52, "indikacija": "AF"},
], RJECNIK_LIJEKOVA)
p2 = Profil(dob=80, spol="M", masa_kg=80, crcl=60, egfr=65,
            dijagnoze={"atrijska_fibrilacija"}, lijekovi=lij2)
_, start2, _ = procijeni(p2)
ok(not any(n.lijek == "oralni antikoagulans" for n in start2),
   "START: AF s NOAK-om ne prijavljuje propust")

# --- renalni prag NOAK ---
lij3, _ = obradi_terapiju([
    {"inn": "rivaroksaban", "doza_dnevno_mg": 20, "trajanje_sedmica": 10, "indikacija": "AF"},
], RJECNIK_LIJEKOVA)
p3 = Profil(dob=82, spol="Z", masa_kg=68, crcl=28, egfr=31,
            dijagnoze={"atrijska_fibrilacija"}, lijekovi=lij3)
s3, _, _ = procijeni(p3)
ok(any("NOAK uz CrCl 15-30" in n.kriterij for n in s3),
   "STOPP: rivaroksaban uz CrCl 28 → provjera doze (Beers kat. 5)")

# --- bez CrCl → 'nije provjereno' ---
p4 = Profil(dob=82, spol="Z", masa_kg=None, crcl=None, egfr=None,
            dijagnoze=set(), lijekovi=lij3)
_, _, nije4 = procijeni(p4)
ok(any("renalni kriteriji" in x.lower() for x in nije4),
   "Bez CrCl: renalni kriteriji označeni kao neprovjereni")

# --- hiponatremija + SSRI ---
lij5, _ = obradi_terapiju([{"inn": "sertralin", "trajanje_sedmica": 20, "indikacija": "depresija"}], RJECNIK_LIJEKOVA)
p5 = Profil(dob=75, spol="Z", masa_kg=60, crcl=55, egfr=60,
            dijagnoze={"depresija"}, lijekovi=lij5, natrij=127)
s5, _, _ = procijeni(p5)
ok(any("hiponatremijom" in n.kriterij for n in s5), "STOPP: SSRI uz Na=127")

# --- PPI >8 sedmica ---
lij6, _ = obradi_terapiju([{"inn": "pantoprazol", "doza_dnevno_mg": 40, "trajanje_sedmica": 30, "indikacija": ""}], RJECNIK_LIJEKOVA)
p6 = Profil(dob=70, spol="M", masa_kg=80, crcl=70, egfr=75, dijagnoze=set(), lijekovi=lij6)
s6, _, _ = procijeni(p6)
ok(any("PPI u punoj dozi duže od 8 sedmica" in n.kriterij for n in s6), "STOPP: PPI 30 sedmica bez indikacije")

# --- PDF ---
print("PDF")
from izvjestaj import generisi_pdf
pdf = generisi_pdf(profil, stopp, start, nije, "TEST-001")
ok(pdf[:4] == b"%PDF", f"PDF generisan ({len(pdf)} bajtova)")

print(f"\nSVIH {PROSLO} TESTOVA PROŠLO ✔")
