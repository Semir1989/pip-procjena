"""Deterministički sloj — svi izračuni se rade u kodu, nikada u jezičkom modelu.

Prema Dijelu 3 vodiča: Cockcroft-Gault, CKD-EPI 2021, BMI, trajanje terapije,
antiholinergičko opterećenje (ACB) i detekcija duplikata terapijske grupe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


# ------------------------------------------------------------------
# Bubrežna funkcija
# ------------------------------------------------------------------

def cockcroft_gault(dob: int, masa_kg: float, kreatinin_umol_l: float, spol: str) -> float:
    """Klirens kreatinina (ml/min). Kreatinin u µmol/L. Spol: 'M' ili 'Z'."""
    kreatinin_mg_dl = kreatinin_umol_l / 88.42
    crcl = ((140 - dob) * masa_kg) / (72 * kreatinin_mg_dl)
    if spol.upper() in ("Z", "Ž", "F"):
        crcl *= 0.85
    return round(crcl, 1)


def egfr_ckd_epi_2021(kreatinin_umol_l: float, dob: int, spol: str) -> float:
    """eGFR po CKD-EPI 2021 (bez rase), ml/min/1.73 m2."""
    scr = kreatinin_umol_l / 88.42  # mg/dL
    zena = spol.upper() in ("Z", "Ž", "F")
    kappa = 0.7 if zena else 0.9
    alfa = -0.241 if zena else -0.302
    egfr = 142 * (min(scr / kappa, 1) ** alfa) * (max(scr / kappa, 1) ** -1.200) * (0.9938 ** dob)
    if zena:
        egfr *= 1.012
    return round(egfr, 1)


def stadij_ckd(egfr: float) -> str:
    """Stadij hronične bubrežne bolesti iz eGFR."""
    if egfr >= 90:
        return "G1"
    if egfr >= 60:
        return "G2"
    if egfr >= 45:
        return "G3a"
    if egfr >= 30:
        return "G3b"
    if egfr >= 15:
        return "G4"
    return "G5"


# ------------------------------------------------------------------
# Antropometrija
# ------------------------------------------------------------------

def bmi(masa_kg: float, visina_cm: float) -> float:
    v = visina_cm / 100
    return round(masa_kg / (v * v), 1)


def idealna_masa(visina_cm: float, spol: str) -> float:
    """Devine formula, kg."""
    inca_preko_5ft = max(0.0, (visina_cm - 152.4) / 2.54)
    baza = 45.5 if spol.upper() in ("Z", "Ž", "F") else 50.0
    return round(baza + 2.3 * inca_preko_5ft, 1)


# ------------------------------------------------------------------
# Trajanje terapije
# ------------------------------------------------------------------

def trajanje_sedmica(datum_pocetka: date, danas: date | None = None) -> int:
    danas = danas or date.today()
    return max(0, (danas - datum_pocetka).days // 7)


# ------------------------------------------------------------------
# Zapis lijeka i obrada terapije
# ------------------------------------------------------------------

@dataclass
class Lijek:
    inn: str
    doza_dnevno_mg: float | None = None
    frekvencija: str = ""            # "redovno" ili "PRN"
    put: str = "per os"
    trajanje_sedmica: int | None = None
    indikacija: str = ""
    atc: str = ""
    grupe: set[str] = field(default_factory=set)
    acb: int = 0


def obradi_terapiju(unosi: list[dict], rjecnik: dict) -> tuple[list[Lijek], list[str]]:
    """Normalizuje unesene lijekove preko lokalnog rječnika (INN -> ATC/grupe/ACB).

    Vraća (lista Lijek objekata, lista upozorenja o neprepoznatim lijekovima).
    """
    lijekovi: list[Lijek] = []
    upozorenja: list[str] = []
    for u in unosi:
        ime = (u.get("inn") or "").strip().lower()
        if not ime:
            continue
        info = rjecnik.get(ime)
        lij = Lijek(
            inn=ime,
            doza_dnevno_mg=u.get("doza_dnevno_mg"),
            frekvencija=u.get("frekvencija", ""),
            put=u.get("put", "per os"),
            trajanje_sedmica=u.get("trajanje_sedmica"),
            indikacija=(u.get("indikacija") or "").strip(),
        )
        if info:
            lij.atc = info.get("atc", "")
            lij.grupe = set(info.get("grupe", []))
            lij.acb = info.get("acb", 0)
        else:
            upozorenja.append(
                f"Lijek „{ime}“ nije u lokalnom rječniku — ATC grupisanje i "
                f"antiholinergičko opterećenje nisu provjereni za taj lijek."
            )
        lijekovi.append(lij)
    return lijekovi, upozorenja


def acb_ukupno(lijekovi: list[Lijek]) -> int:
    """Zbir antiholinergičkog opterećenja (ACB skala) — samo sistemski putevi."""
    return sum(l.acb for l in lijekovi if not _je_topikalni(l))


def _je_topikalni(l: Lijek) -> bool:
    return l.put.lower() in ("topikalno", "lokalno", "gel", "mast", "kapi za oko")


def duplikati_grupa(lijekovi: list[Lijek]) -> list[tuple[str, list[str]]]:
    """Detekcija >=2 sistemska lijeka iz iste terapijske grupe."""
    provjeri = {
        "nsaid": "NSAID",
        "bzd": "benzodiazepin",
        "z-lijek": "Z-lijek (hipnotik)",
        "ssri": "SSRI",
        "acei": "ACE inhibitor",
        "arb": "ARB (sartan)",
        "diuretik_petlje": "diuretik Henleove petlje",
        "opioid": "opioid",
        "antipsihotik": "antipsihotik",
        "sulfonilureja": "sulfonilureja",
    }
    nalazi = []
    for kljuc, naziv in provjeri.items():
        clanovi = [l.inn for l in lijekovi if kljuc in l.grupe and not _je_topikalni(l)]
        if len(clanovi) >= 2:
            nalazi.append((naziv, clanovi))
    return nalazi
