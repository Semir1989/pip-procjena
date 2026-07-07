"""Mehanizam kriterija — parafrazirani skup pravila izveden iz:

  - AGS 2023 Updated Beers Criteria (J Am Geriatr Soc 2023;71(7):2052-2081)
  - O'Mahony et al., STOPP/START criteria version 3 (Eur Geriatr Med 2023;14:625-632)

Pravila su uslovna i deterministički se provjeravaju u Pythonu (Dio 3 vodiča).
Svaki nalaz nosi izvor, klinički rizik, preporuku i nivo pouzdanosti.
Alat je podrška odlučivanju — konačnu odluku donosi farmaceut/ljekar.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from izracuni import Lijek, acb_ukupno, duplikati_grupa


@dataclass
class Nalaz:
    tip: str                 # "STOPP" ili "START"
    lijek: str               # lijek (STOPP) ili propušteni lijek (START)
    kriterij: str
    izvor: str               # "Beers 2023", "STOPP v3", "START v3", ...
    klinicki_rizik: str
    preporuka: str
    nivo_pouzdanosti: str    # "visok" | "srednji" | "nizak"


@dataclass
class Profil:
    """Obrađeni profil pacijenta — sve izračunato u izracuni.py prije procjene."""
    dob: int
    spol: str
    masa_kg: float | None = None
    crcl: float | None = None
    egfr: float | None = None
    dijagnoze: set[str] = field(default_factory=set)   # šifre stanja, vidi STANJA u app.py
    lijekovi: list[Lijek] = field(default_factory=list)
    # laboratorij
    natrij: float | None = None
    kalij: float | None = None
    hba1c: float | None = None
    inr: float | None = None
    hemoglobin: float | None = None
    qtc: float | None = None
    # vitalni / funkcionalni
    sistolni: float | None = None
    frekvencija_srca: float | None = None
    ogranicen_zivotni_vijek: bool = False


# ------------------------------------------------------------------
# pomoćne funkcije
# ------------------------------------------------------------------

def _ima(profil: Profil, *grupe: str) -> list[Lijek]:
    """Lijekovi koji pripadaju bilo kojoj od navedenih grupa (sistemski)."""
    rez = []
    for l in profil.lijekovi:
        if l.put.lower() in ("topikalno", "lokalno", "gel", "mast"):
            continue
        if any(g in l.grupe for g in grupe):
            rez.append(l)
    return rez


def _dg(profil: Profil, *stanja: str) -> bool:
    return any(s in profil.dijagnoze for s in stanja)


def _dugotrajno(l: Lijek, sedmica: int) -> bool:
    return l.trajanje_sedmica is not None and l.trajanje_sedmica > sedmica


# ------------------------------------------------------------------
# glavna procjena
# ------------------------------------------------------------------

def procijeni(profil: Profil) -> tuple[list[Nalaz], list[Nalaz], list[str]]:
    """Vraća (stopp_nalazi, start_nalazi, nije_provjereno)."""
    stopp: list[Nalaz] = []
    start: list[Nalaz] = []
    nije: list[str] = []

    _stopp_sedativi(profil, stopp)
    _stopp_antiholinergici(profil, stopp)
    _stopp_nsaid(profil, stopp, nije)
    _stopp_gi(profil, stopp)
    _stopp_kardio(profil, stopp, nije)
    _stopp_renalno(profil, stopp, nije)
    _stopp_endokrino(profil, stopp, nije)
    _stopp_cns(profil, stopp)
    _stopp_padovi(profil, stopp)
    _stopp_duplikati(profil, stopp)
    _stopp_bez_indikacije(profil, stopp)

    _start_kriteriji(profil, start)

    _nedostajuci_podaci(profil, nije)

    return stopp, start, nije


# ------------------------------------------------------------------
# STOPP / Beers — sedativi i hipnotici
# ------------------------------------------------------------------

def _stopp_sedativi(p: Profil, out: list[Nalaz]):
    for l in _ima(p, "bzd"):
        if _dugotrajno(l, 4):
            out.append(Nalaz(
                "STOPP", l.inn,
                f"Benzodiazepin duže od 4 sedmice (uneseno: {l.trajanje_sedmica} sedm.)",
                "STOPP v3 (D5) / Beers 2023",
                "Sedacija, kognitivni pad, delirij, padovi i prijelomi, zavisnost.",
                "Postupna obustava (taper); nefarmakološke mjere za nesanicu/anksioznost.",
                "visok"))
        elif l.trajanje_sedmica is None:
            out.append(Nalaz(
                "STOPP", l.inn,
                "Benzodiazepin kod starijih — trajanje nije uneseno",
                "Beers 2023 / STOPP v3",
                "BZD kod ≥65 g. povećavaju rizik pada, prijeloma i kognitivnog pada.",
                "Unijeti trajanje terapije; ako >4 sedmice, planirati postupnu obustavu.",
                "srednji"))
        else:
            out.append(Nalaz(
                "STOPP", l.inn,
                "Benzodiazepin kod starijih (kratkotrajno)",
                "Beers 2023",
                "I kratkotrajna primjena povećava rizik sedacije i pada.",
                "Preispitati potrebu; najniža doza, najkraće trajanje.",
                "srednji"))
        if "bzd_dugodjelujuci" in l.grupe:
            out.append(Nalaz(
                "STOPP", l.inn,
                "Dugodjelujući benzodiazepin kod starijih",
                "Beers 2023",
                "Produžen poluvijek eliminacije kod starijih — akumulacija, produžena sedacija.",
                "Ako je BZD neophodan, preferirati kratkodjelujući (npr. oksazepam, lorazepam) u minimalnoj dozi.",
                "visok"))

    for l in _ima(p, "z-lijek"):
        out.append(Nalaz(
            "STOPP", l.inn,
            "Z-lijek (hipnotik) kod starijih"
            + (f" — trajanje {l.trajanje_sedmica} sedm." if l.trajanje_sedmica else ""),
            "Beers 2023 / STOPP v3",
            "Slično BZD: padovi, prijelomi, kognitivno oštećenje; minimalna korist za san.",
            "Postupna obustava; higijena spavanja, nefarmakološke mjere.",
            "visok"))

    opioidi = _ima(p, "opioid")
    bzd_ili_z = _ima(p, "bzd", "z-lijek")
    if opioidi and bzd_ili_z:
        out.append(Nalaz(
            "STOPP", f"{opioidi[0].inn} + {bzd_ili_z[0].inn}",
            "Istovremena primjena opioida i benzodiazepina/Z-lijeka",
            "Beers 2023",
            "Aditivna depresija CNS-a i disanja; znatno povećan rizik predoziranja.",
            "Izbjegavati kombinaciju; ako je neizbježna, minimalne doze uz nadzor.",
            "visok"))

    if opioidi and not _ima(p, "laksativ"):
        out.append(Nalaz(
            "START", "laksativ",
            "Opioid u redovnoj terapiji bez profilaktičkog laksativa",
            "START v3",
            "Opioidima izazvana konstipacija je gotovo univerzalna kod starijih.",
            "Razmotriti osmotski laksativ (npr. makrogol, laktuloza) uz redovni opioid.",
            "visok"))


# ------------------------------------------------------------------
# antiholinergici
# ------------------------------------------------------------------

def _stopp_antiholinergici(p: Profil, out: list[Nalaz]):
    ukupno = acb_ukupno(p.lijekovi)
    if ukupno >= 3:
        nosioci = [l.inn for l in p.lijekovi if l.acb >= 1]
        out.append(Nalaz(
            "STOPP", ", ".join(nosioci),
            f"Visoko antiholinergičko opterećenje (ACB zbir = {ukupno})",
            "Beers 2023 / STOPP v3",
            "Kumulativni antiholinergički efekat: kognitivni pad, delirij, padovi, "
            "retencija urina, konstipacija.",
            "Smanjiti broj antiholinergika; zamijeniti nosioce ACB skora alternativama.",
            "visok"))

    jaki = [l for l in p.lijekovi if l.acb >= 3]
    for l in jaki:
        if _dg(p, "demencija", "delirij"):
            out.append(Nalaz(
                "STOPP", l.inn,
                "Jak antiholinergik kod demencije/anamneze delirija",
                "Beers 2023 (drug-disease) / STOPP v3",
                "Pogoršanje kognicije, precipitacija delirija.",
                "Obustaviti ili zamijeniti lijekom bez antiholinergičkog djelovanja.",
                "visok"))
        if _dg(p, "glaukom"):
            out.append(Nalaz(
                "STOPP", l.inn,
                "Antiholinergik kod uskougaonog glaukoma",
                "Beers 2023 / STOPP v3",
                "Precipitacija akutnog napada glaukoma.",
                "Obustaviti; konsultovati oftalmologa.",
                "visok"))
        if _dg(p, "bph_retencija"):
            out.append(Nalaz(
                "STOPP", l.inn,
                "Antiholinergik kod BPH/urinarne retencije",
                "Beers 2023 / STOPP v3",
                "Akutna retencija urina.",
                "Obustaviti ili zamijeniti.",
                "visok"))
        if _dg(p, "konstipacija"):
            out.append(Nalaz(
                "STOPP", l.inn,
                "Antiholinergik kod hronične konstipacije",
                "STOPP v3",
                "Pogoršanje konstipacije, rizik ileusa.",
                "Zamijeniti lijekom bez antiholinergičkog djelovanja.",
                "srednji"))

    for l in _ima(p, "antihistaminik_1g"):
        out.append(Nalaz(
            "STOPP", l.inn,
            "Antihistaminik 1. generacije kod starijih",
            "Beers 2023",
            "Izražena sedacija i antiholinergički efekti; padovi, konfuzija.",
            "Zamijeniti antihistaminikom 2. generacije (npr. loratadin).",
            "visok"))


# ------------------------------------------------------------------
# NSAID
# ------------------------------------------------------------------

def _stopp_nsaid(p: Profil, out: list[Nalaz], nije: list[str]):
    nsaidi = _ima(p, "nsaid")
    for l in nsaidi:
        bubr = p.crcl if p.crcl is not None else p.egfr
        if bubr is not None and bubr < 50:
            out.append(Nalaz(
                "STOPP", l.inn,
                f"NSAID uz oslabljenu bubrežnu funkciju (CrCl/eGFR ≈ {bubr} ml/min)",
                "STOPP v3 / Beers 2023 (kat. 5)",
                "Pogoršanje bubrežne funkcije, retencija tečnosti, hiperkalemija.",
                "Paracetamol 1. linija; topikalni NSAID gel za lokaliziranu bol; obustaviti sistemski NSAID.",
                "visok"))
        if _dg(p, "ulkus_gi_krvarenje") and not _ima(p, "ppi"):
            out.append(Nalaz(
                "STOPP", l.inn,
                "NSAID uz anamnezu peptičkog ulkusa/GI krvarenja bez PPI zaštite",
                "STOPP v3",
                "Recidiv ulkusa i GI krvarenja.",
                "Obustaviti NSAID; ako je nužan, dodati PPI i koristiti najkraće moguće.",
                "visok"))
        if _dg(p, "srcana_insuficijencija"):
            out.append(Nalaz(
                "STOPP", l.inn,
                "NSAID kod srčane insuficijencije",
                "STOPP v3 / Beers 2023",
                "Retencija tečnosti i pogoršanje srčane insuficijencije.",
                "Obustaviti; paracetamol ili topikalne alternative.",
                "visok"))
        if _dg(p, "hipertenzija"):
            out.append(Nalaz(
                "STOPP", l.inn,
                "Dugotrajniji NSAID kod hipertenzije",
                "STOPP v3",
                "Povišenje krvnog pritiska, antagonizacija antihipertenziva.",
                "Preispitati potrebu; preferirati paracetamol/topikalno.",
                "srednji"))
        if _dugotrajno(l, 12):
            out.append(Nalaz(
                "STOPP", l.inn,
                f"Dugotrajna sistemska primjena NSAID ({l.trajanje_sedmica} sedm.)",
                "Beers 2023 / STOPP v3",
                "Kumulativni GI, renalni i kardiovaskularni rizik.",
                "Preispitati indikaciju; deprescribing ili prelazak na alternativu uz PPI ako je nužan.",
                "visok"))
        if l.trajanje_sedmica is None:
            nije.append(f"Trajanje terapije za {l.inn} nije uneseno — trajanje-zavisni NSAID kriteriji nisu u potpunosti provjereni.")
        if "beers_izbjegavati" in l.grupe:
            out.append(Nalaz(
                "STOPP", l.inn,
                "NSAID koji Beers izričito navodi za izbjegavanje (indometacin/piroksikam)",
                "Beers 2023",
                "Najveći CNS/GI rizik u klasi.",
                "Zamijeniti sigurnijom alternativom.",
                "visok"))

    aspirin = [l for l in p.lijekovi if "aspirin" in l.grupe]
    for l in aspirin:
        kardio_ind = _dg(p, "koronarna_bolest", "cvi_tia", "periferna_arterijska")
        if not kardio_ind and p.dob >= 70:
            out.append(Nalaz(
                "STOPP", l.inn,
                "Aspirin u primarnoj prevenciji kod ≥70 godina (bez dokazane KV bolesti)",
                "Beers 2023 / STOPP v3",
                "Rizik krvarenja nadmašuje korist u primarnoj prevenciji kod starijih.",
                "Razmotriti obustavu ako nema sekundarne kardiovaskularne indikacije.",
                "srednji"))


# ------------------------------------------------------------------
# GI
# ------------------------------------------------------------------

def _stopp_gi(p: Profil, out: list[Nalaz]):
    for l in _ima(p, "ppi"):
        ind = l.indikacija.lower()
        opravdano = any(k in ind for k in ("barrett", "zollinger", "ezofagitis", "krvarenj", "ulkus"))
        if _dugotrajno(l, 8) and not opravdano:
            out.append(Nalaz(
                "STOPP", l.inn,
                f"PPI u punoj dozi duže od 8 sedmica bez jasne indikacije ({l.trajanje_sedmica} sedm.; indikacija: „{l.indikacija or 'nije unesena'}“)",
                "STOPP v3 (F2)",
                "Hipomagnezijemija, C. difficile, prijelomi, deficit B12 uz dugotrajnu primjenu.",
                "Smanjiti na dozu održavanja, prijeći na PRN ili postupno obustaviti.",
                "visok"))
        if not l.indikacija:
            out.append(Nalaz(
                "STOPP", l.inn,
                "PPI bez unesene indikacije",
                "STOPP v3 (lijek bez indikacije)",
                "Nepotrebna dugotrajna supresija kiseline.",
                "Utvrditi indikaciju; ako je nema, planirati obustavu.",
                "srednji"))

    for l in _ima(p, "prokinetik"):
        if _dg(p, "parkinson"):
            out.append(Nalaz(
                "STOPP", l.inn,
                "Metoklopramid kod Parkinsonove bolesti",
                "Beers 2023 / STOPP v3",
                "Pogoršanje ekstrapiramidnih simptoma (antagonist dopamina).",
                "Zamijeniti domperidonom ili obustaviti.",
                "visok"))
        else:
            out.append(Nalaz(
                "STOPP", l.inn,
                "Metoklopramid kod starijih (osim kratkotrajno)",
                "Beers 2023",
                "Ekstrapiramidni efekti, tardivna diskinezija.",
                "Ograničiti na najkraće trajanje; preispitati potrebu.",
                "srednji"))


# ------------------------------------------------------------------
# kardiovaskularni
# ------------------------------------------------------------------

def _stopp_kardio(p: Profil, out: list[Nalaz], nije: list[str]):
    for l in _ima(p, "digoksin"):
        if l.doza_dnevno_mg is not None and l.doza_dnevno_mg > 0.125:
            out.append(Nalaz(
                "STOPP", l.inn,
                f"Digoksin > 0,125 mg/dan kod starijih ({l.doza_dnevno_mg} mg/dan)",
                "Beers 2023 / STOPP v3",
                "Toksičnost digoksina (smanjen renalni klirens kod starijih).",
                "Smanjiti dozu na ≤0,125 mg/dan; kontrolisati digoksinemiju i bubrežnu funkciju.",
                "visok"))
        bubr = p.crcl if p.crcl is not None else p.egfr
        if bubr is not None and bubr < 30 and (l.doza_dnevno_mg or 0) > 0.125:
            out.append(Nalaz(
                "STOPP", l.inn,
                f"Digoksin u punoj dozi uz CrCl/eGFR < 30 ml/min",
                "STOPP v3",
                "Akumulacija i toksičnost.",
                "Redukcija doze uz praćenje koncentracije.",
                "visok"))

    if _dg(p, "srcana_insuficijencija"):
        for l in _ima(p, "ccb_nondhp"):
            out.append(Nalaz(
                "STOPP", l.inn,
                "Verapamil/diltiazem kod srčane insuficijencije (HFrEF)",
                "STOPP v3 / Beers 2023",
                "Negativan inotropni efekat — pogoršanje insuficijencije.",
                "Obustaviti; alternativa prema indikaciji (npr. beta-blokator).",
                "visok"))

    if p.frekvencija_srca is not None and p.frekvencija_srca < 50:
        bradikardni = _ima(p, "bb", "ccb_nondhp", "digoksin")
        for l in bradikardni:
            out.append(Nalaz(
                "STOPP", l.inn,
                f"Lijek koji usporava frekvenciju uz bradikardiju ({p.frekvencija_srca:.0f}/min)",
                "STOPP v3",
                "Simptomatska bradikardija, sinkopa, blok provodjenja.",
                "Preispitati dozu/potrebu; EKG kontrola.",
                "visok"))

    if _dg(p, "ortostatska_hipotenzija", "sinkopa"):
        for l in _ima(p, "alfa_blokator", "centralni_antihipertenziv", "nitrat"):
            out.append(Nalaz(
                "STOPP", l.inn,
                "Vazodilatator/alfa-blokator uz ortostatsku hipotenziju ili sinkope",
                "STOPP v3 / Beers 2023",
                "Ortostatski pad pritiska — padovi i sinkope.",
                "Preispitati antihipertenzivnu shemu; izbjegavati alfa-blokatore kao antihipertenzive.",
                "visok"))

    for l in _ima(p, "beers_izbjegavati_htn"):
        out.append(Nalaz(
            "STOPP", l.inn,
            "Periferni alfa-blokator kao antihipertenziv kod starijih",
            "Beers 2023",
            "Ortostatska hipotenzija; postoje sigurnije alternative.",
            "Zamijeniti drugim antihipertenzivom (ACEi/ARB, CCB, tiazid).",
            "srednji"))

    if p.kalij is not None and p.kalij > 5.0:
        rizicni = _ima(p, "acei", "arb", "k_stedeci", "hiperkalemija_rizik")
        for l in rizicni:
            out.append(Nalaz(
                "STOPP", l.inn,
                f"Lijek koji povisuje kalij uz hiperkalemiju (K = {p.kalij} mmol/L)",
                "STOPP v3",
                "Životno ugrožavajuća hiperkalemija, aritmije.",
                "Korekcija kalija; preispitati kombinaciju i doze; kontrola elektrolita.",
                "visok"))

    acei_arb = _ima(p, "acei") + _ima(p, "arb")
    spiro = _ima(p, "spironolakton")
    if acei_arb and spiro and p.kalij is None:
        nije.append("Kalij nije unesen — kombinacija ACEi/ARB + spironolakton zahtijeva kontrolu kalemije (kriterij nije provjeren).")

    if _ima(p, "acei") and _ima(p, "arb"):
        out.append(Nalaz(
            "STOPP", "ACEi + ARB",
            "Istovremena primjena ACE inhibitora i sartana",
            "STOPP v3",
            "Hiperkalemija, hipotenzija, pogoršanje bubrežne funkcije — bez dodatne koristi.",
            "Zadržati samo jedan blokator RAAS-a.",
            "visok"))

    if p.natrij is not None and p.natrij < 130:
        for l in _ima(p, "ssri", "snri", "diuretik", "hiponatremija_rizik"):
            out.append(Nalaz(
                "STOPP", l.inn,
                f"Lijek povezan s hiponatremijom uz Na = {p.natrij} mmol/L",
                "STOPP v3 / Beers 2023",
                "Pogoršanje hiponatremije: konfuzija, padovi, napadi.",
                "Korekcija natrija; preispitati uzročni lijek (SSRI, tiazid, karbamazepin).",
                "visok"))

    if p.qtc is not None and p.qtc > 470:
        qt_lijekovi = _ima(p, "qt_rizik")
        for l in qt_lijekovi:
            out.append(Nalaz(
                "STOPP", l.inn,
                f"Lijek koji produžava QT uz QTc = {p.qtc:.0f} ms",
                "STOPP v3",
                "Torsades de pointes, iznenadna srčana smrt.",
                "Obustaviti/zamijeniti; EKG i elektroliti.",
                "visok"))
    elif p.qtc is None and len(_ima(p, "qt_rizik")) >= 2:
        out.append(Nalaz(
            "STOPP", ", ".join(l.inn for l in _ima(p, "qt_rizik")),
            "Kombinacija ≥2 lijeka koji produžavaju QT interval (QTc nije dostupan)",
            "STOPP v3",
            "Aditivno produženje QT — rizik torsades de pointes.",
            "Snimiti EKG (QTc); preispitati kombinaciju.",
            "srednji"))


# ------------------------------------------------------------------
# renalni pragovi (Beers kategorija 5)
# ------------------------------------------------------------------

def _stopp_renalno(p: Profil, out: list[Nalaz], nije: list[str]):
    bubr = p.crcl if p.crcl is not None else p.egfr
    if bubr is None:
        if p.lijekovi:
            nije.append("CrCl/eGFR nije dostupan (nedostaje kreatinin ili masa) — renalni kriteriji (Beers kat. 5) NISU provjereni.")
        return

    for l in _ima(p, "nitrofurantoin"):
        if bubr < 30:
            out.append(Nalaz(
                "STOPP", l.inn,
                f"Nitrofurantoin uz CrCl < 30 ml/min ({bubr} ml/min)",
                "Beers 2023 (kat. 5) / STOPP v3",
                "Neefikasan u urinu i rizik plućne/hepatalne toksičnosti i neuropatije.",
                "Zamijeniti drugim uroantiseptikom/antibiotikom prema antibiogramu.",
                "visok"))
        if _dugotrajno(l, 4):
            out.append(Nalaz(
                "STOPP", l.inn,
                "Dugotrajna profilaksa nitrofurantoinom",
                "Beers 2023",
                "Plućna fibroza, hepatotoksičnost, periferna neuropatija.",
                "Preispitati potrebu dugotrajne profilakse.",
                "srednji"))

    for l in _ima(p, "metformin"):
        if bubr < 30:
            out.append(Nalaz(
                "STOPP", l.inn,
                f"Metformin uz eGFR/CrCl < 30 ml/min ({bubr} ml/min)",
                "sažetak karakteristika lijeka / STOPP v3",
                "Laktatna acidoza.",
                "Obustaviti; prelazak na drugi antidijabetik prilagođen bubrežnoj funkciji.",
                "visok"))
        elif bubr < 45:
            out.append(Nalaz(
                "STOPP", l.inn,
                f"Metformin uz eGFR/CrCl 30-45 ml/min ({bubr} ml/min)",
                "sažetak karakteristika lijeka",
                "Povećan rizik laktatne acidoze.",
                "Redukcija doze (max ~1000 mg/dan) i češće praćenje bubrežne funkcije.",
                "srednji"))

    noaci = _ima(p, "noak")
    for l in noaci:
        if bubr < 15:
            out.append(Nalaz(
                "STOPP", l.inn,
                f"NOAK uz CrCl < 15 ml/min ({bubr} ml/min)",
                "Beers 2023 (kat. 5)",
                "Akumulacija — veliko krvarenje.",
                "Kontraindikovano; konsultovati hematologa/kardiologa za alternativu.",
                "visok"))
        elif l.inn == "dabigatran" and bubr < 30:
            out.append(Nalaz(
                "STOPP", l.inn,
                f"Dabigatran uz CrCl < 30 ml/min ({bubr} ml/min)",
                "Beers 2023 (kat. 5)",
                "Pretežno renalna eliminacija — rizik krvarenja.",
                "Izbjegavati; razmotriti apiksaban uz redukciju doze ili varfarin.",
                "visok"))
        elif bubr < 30:
            out.append(Nalaz(
                "STOPP", l.inn,
                f"NOAK uz CrCl 15-30 ml/min ({bubr} ml/min) — provjeriti dozu",
                "Beers 2023 (kat. 5) / SmPC",
                "Rizik krvarenja bez redukcije doze.",
                "Provjeriti da li je doza reducirana prema SmPC (npr. rivaroksaban 15 mg).",
                "visok"))
        elif bubr < 50 and l.inn == "rivaroksaban":
            if l.doza_dnevno_mg is not None and l.doza_dnevno_mg > 15:
                out.append(Nalaz(
                    "STOPP", l.inn,
                    f"Rivaroksaban {l.doza_dnevno_mg:.0f} mg/dan uz CrCl {bubr} ml/min (potrebno 15 mg)",
                    "SmPC / Beers 2023",
                    "Povećan rizik krvarenja bez redukcije doze.",
                    "Redukcija na 15 mg jednom dnevno (indikacija AF).",
                    "visok"))

    for l in _ima(p, "gabapentinoid"):
        if bubr < 60 and l.doza_dnevno_mg and (
            (l.inn == "gabapentin" and l.doza_dnevno_mg > 1800) or
            (l.inn == "pregabalin" and l.doza_dnevno_mg > 300)
        ):
            out.append(Nalaz(
                "STOPP", l.inn,
                f"Gabapentinoid u visokoj dozi uz CrCl {bubr} ml/min",
                "Beers 2023 (kat. 5)",
                "Sedacija, ataksija, padovi — potrebna renalna prilagodba doze.",
                "Reducirati dozu prema klirensu.",
                "visok"))

    if _dg(p, "ckd") or (p.egfr is not None and p.egfr < 45):
        pass  # NSAID kod CKD pokriven u _stopp_nsaid preko praga <50


# ------------------------------------------------------------------
# endokrini
# ------------------------------------------------------------------

def _stopp_endokrino(p: Profil, out: list[Nalaz], nije: list[str]):
    for l in _ima(p, "sulfonilureja_dugodjelujuca"):
        out.append(Nalaz(
            "STOPP", l.inn,
            "Dugodjelujuća sulfonilureja (glibenklamid/glimepirid) kod starijih",
            "Beers 2023 / STOPP v3",
            "Produžena hipoglikemija — padovi, kardiovaskularni događaji.",
            "Zamijeniti gliklazidom, DPP-4 inhibitorom ili drugim antidijabetikom.",
            "visok"))

    if p.hba1c is not None and p.hba1c < 6.5 and _ima(p, "sulfonilureja", "inzulin"):
        out.append(Nalaz(
            "STOPP", ", ".join(l.inn for l in _ima(p, "sulfonilureja", "inzulin")),
            f"Preintenzivna glikemijska kontrola (HbA1c = {p.hba1c}%) uz lijekove koji izazivaju hipoglikemiju",
            "STOPP v3 / Beers 2023",
            "Hipoglikemija kod starijih: padovi, konfuzija, aritmije.",
            "Relaksirati cilj HbA1c (7-8% kod krhkih); deintenzifikacija terapije.",
            "visok"))

    if _dg(p, "dijabetes") and _ima(p, "sulfonilureja", "inzulin") and p.hba1c is None:
        nije.append("HbA1c nije unesen — kriterij preintenzivne glikemijske kontrole nije provjeren.")

    for l in _ima(p, "estrogen"):
        if l.put.lower() not in ("vaginalno", "topikalno", "lokalno"):
            out.append(Nalaz(
                "STOPP", l.inn,
                "Sistemski estrogen kod starijih žena",
                "Beers 2023",
                "Karcinogeni potencijal (dojka, endometrij), VTE, bez kardioprotekcije.",
                "Obustaviti sistemsku primjenu; za urogenitalnu atrofiju niskodozna vaginalna forma.",
                "visok"))

    kortiko = [l for l in _ima(p, "kortikosteroid_sistemski") if _dugotrajno(l, 12)]
    if kortiko and not _ima(p, "bisfosfonat", "antiresorptiv"):
        out.append(Nalaz(
            "START", "bisfosfonat + vitamin D/kalcij",
            f"Dugotrajni sistemski kortikosteroid ({kortiko[0].inn}) bez zaštite kostiju",
            "START v3",
            "Glukokortikoidima izazvana osteoporoza i prijelomi.",
            "Uvesti vitamin D + kalcij i razmotriti bisfosfonat uz procjenu rizika prijeloma.",
            "visok"))


# ------------------------------------------------------------------
# CNS
# ------------------------------------------------------------------

def _stopp_cns(p: Profil, out: list[Nalaz]):
    antipsihotici = _ima(p, "antipsihotik")
    if _dg(p, "demencija") and antipsihotici:
        for l in antipsihotici:
            out.append(Nalaz(
                "STOPP", l.inn,
                "Antipsihotik kod demencije (BPSD) — osim kod teške psihoze/agresije",
                "Beers 2023 / STOPP v3",
                "Povećan mortalitet i rizik CVI kod dementnih pacijenata.",
                "Nefarmakološke mjere 1. linija; ako je nužan — najniža doza, najkraće trajanje, redovna revizija.",
                "visok"))
    if _dg(p, "parkinson", "lewy"):
        for l in antipsihotici:
            if l.inn not in ("kvetiapin", "klozapin"):
                out.append(Nalaz(
                    "STOPP", l.inn,
                    "Antipsihotik (osim kvetiapina/klozapina) kod Parkinsona/Lewy demencije",
                    "Beers 2023 / STOPP v3",
                    "Teško pogoršanje motorike; kod Lewy demencije teška neuroleptička senzitivnost.",
                    "Obustaviti; ako je neophodan — kvetiapin ili klozapin u minimalnoj dozi.",
                    "visok"))

    for l in _ima(p, "tca"):
        out.append(Nalaz(
            "STOPP", l.inn,
            "Triciklički antidepresiv kod starijih",
            "Beers 2023 / STOPP v3",
            "Jaka antiholinergička i sedativna svojstva; ortostatska hipotenzija, aritmije.",
            "Zamijeniti SSRI/SNRI (uz oprez na hiponatremiju).",
            "visok"))

    if _dg(p, "epilepsija"):
        for l in _ima(p, "snizava_prag_napada"):
            out.append(Nalaz(
                "STOPP", l.inn,
                "Lijek koji snižava prag napada kod epilepsije (tramadol)",
                "STOPP v3",
                "Provokacija epileptičkih napada.",
                "Zamijeniti drugim analgetikom.",
                "srednji"))

    for l in _ima(p, "vertigo"):
        if "beers_izbjegavati" in l.grupe and _dugotrajno(l, 4):
            out.append(Nalaz(
                "STOPP", l.inn,
                "Dugotrajna primjena cinarizina kod starijih",
                "STOPP v3",
                "Ekstrapiramidni simptomi, depresija, sedacija.",
                "Preispitati indikaciju; ograničiti trajanje.",
                "srednji"))

    for l in _ima(p, "teofilin"):
        if _dg(p, "kopb") and not _ima(p, "inhalacioni"):
            out.append(Nalaz(
                "STOPP", l.inn,
                "Teofilin kao monoterapija KOPB-a",
                "STOPP v3",
                "Uzak terapijski indeks, interakcije; sigurnije i efikasnije inhalacione alternative.",
                "Prelazak na inhalacionu terapiju (LAMA/LABA).",
                "visok"))


# ------------------------------------------------------------------
# padovi — zaseban blok (veže veliki broj kriterija)
# ------------------------------------------------------------------

def _stopp_padovi(p: Profil, out: list[Nalaz]):
    if not _dg(p, "padovi"):
        return
    rizicni = _ima(p, "bzd", "z-lijek", "antipsihotik", "tca", "sedativ", "opioid")
    vidjeni = set()
    for l in rizicni:
        if l.inn in vidjeni:
            continue
        vidjeni.add(l.inn)
        out.append(Nalaz(
            "STOPP", l.inn,
            "Psihotropni lijek uz anamnezu pada u zadnjih 12 mjeseci",
            "STOPP v3 (sekcija K) / Beers 2023",
            "Sedacija/psihomotorno usporenje — ponovni pad, prijelom kuka.",
            "Deprescribing psihotropa je najefikasnija pojedinačna intervencija za prevenciju pada.",
            "visok"))
    # antihipertenzivi + ortostatska
    if _dg(p, "ortostatska_hipotenzija"):
        for l in _ima(p, "alfa_blokator", "centralni_antihipertenziv", "diuretik_petlje"):
            out.append(Nalaz(
                "STOPP", l.inn,
                "Hipotenzivni lijek uz padove i ortostatsku hipotenziju",
                "STOPP v3 (K)",
                "Ortostaza — padovi.",
                "Revizija antihipertenzivne sheme, mjerenje ortostatskog pritiska.",
                "visok"))


# ------------------------------------------------------------------
# duplikati i lijekovi bez indikacije
# ------------------------------------------------------------------

def _stopp_duplikati(p: Profil, out: list[Nalaz]):
    for naziv, clanovi in duplikati_grupa(p.lijekovi):
        out.append(Nalaz(
            "STOPP", " + ".join(clanovi),
            f"Duplikat terapijske grupe: dva lijeka iz grupe „{naziv}“",
            "STOPP v3 (A3)",
            "Aditivna toksičnost bez dodatne koristi.",
            "Zadržati jedan lijek iz grupe; optimizovati monoterapiju prije zamjene klase.",
            "visok"))


def _stopp_bez_indikacije(p: Profil, out: list[Nalaz]):
    for l in p.lijekovi:
        if not l.indikacija and "ppi" not in l.grupe:  # PPI već pokriven
            out.append(Nalaz(
                "STOPP", l.inn,
                "Lijek bez unesene indikacije",
                "STOPP v3 (A1 — lijek bez indikacije zasnovane na dokazima)",
                "Nepotrebna polifarmacija; nemoguće procijeniti omjer koristi i rizika.",
                "Utvrditi/dokumentovati indikaciju; ako je nema — kandidat za deprescribing.",
                "nizak"))


# ------------------------------------------------------------------
# START — propušteni indicirani lijekovi
# ------------------------------------------------------------------

def _start_kriteriji(p: Profil, out: list[Nalaz]):
    preventiva_ok = not p.ogranicen_zivotni_vijek

    if _dg(p, "atrijska_fibrilacija") and not _ima(p, "antikoagulans"):
        out.append(Nalaz(
            "START", "oralni antikoagulans",
            "Atrijska fibrilacija bez antikoagulantne terapije",
            "START v3 (A1)",
            "Ishemijski moždani udar — AF nosi ~5x veći rizik.",
            "Razmotriti NOAK (ili varfarin) uz procjenu CHA2DS2-VASc i rizika krvarenja (HAS-BLED).",
            "visok"))

    if _dg(p, "koronarna_bolest", "cvi_tia", "periferna_arterijska"):
        if not _ima(p, "antiagregans", "antikoagulans"):
            out.append(Nalaz(
                "START", "antiagregans (ASK/klopidogrel)",
                "Dokazana aterosklerotska bolest bez antitrombotske terapije",
                "START v3 (A3)",
                "Recidiv kardiovaskularnog/cerebrovaskularnog događaja.",
                "Uvesti antiagregans u sekundarnoj prevenciji.",
                "visok"))
        if not _ima(p, "statin") and preventiva_ok:
            out.append(Nalaz(
                "START", "statin",
                "Dokazana aterosklerotska bolest bez statina",
                "START v3 (A5)",
                "Recidiv KV događaja — statin je standard sekundarne prevencije.",
                "Uvesti statin osim ako je kontraindikovan ili je životni vijek ograničen.",
                "visok"))

    if _dg(p, "koronarna_bolest") and not _ima(p, "bb"):
        out.append(Nalaz(
            "START", "beta-blokator",
            "Ishemijska bolest srca bez beta-blokatora",
            "START v3 (A7)",
            "Simptomi angine, reinfarkt.",
            "Razmotriti beta-blokator ako nema kontraindikacija (bradikardija, blok).",
            "srednji"))

    if _dg(p, "srcana_insuficijencija"):
        if not _ima(p, "acei", "arb"):
            out.append(Nalaz(
                "START", "ACE inhibitor / ARB",
                "Srčana insuficijencija bez ACEi/ARB",
                "START v3 (A6)",
                "Progresija insuficijencije, hospitalizacije, mortalitet.",
                "Uvesti ACEi (ili ARB kod netolerancije) titrirano.",
                "visok"))
        if not _ima(p, "bb"):
            out.append(Nalaz(
                "START", "beta-blokator (bisoprolol/karvedilol/nebivolol)",
                "Srčana insuficijencija (HFrEF) bez beta-blokatora",
                "START v3",
                "Mortalitet i hospitalizacije.",
                "Uvesti beta-blokator s dokazom u HF, titrirati postepeno.",
                "visok"))

    if _dg(p, "osteoporoza"):
        if not _ima(p, "bisfosfonat", "antiresorptiv") and preventiva_ok:
            out.append(Nalaz(
                "START", "bisfosfonat/denosumab",
                "Osteoporoza (ili fragilni prijelom) bez antiresorptivne terapije",
                "START v3 (E)",
                "Osteoporotski prijelomi (kuk, kičma).",
                "Uvesti bisfosfonat uz vitamin D i kalcij, uz provjeru bubrežne funkcije.",
                "visok"))
        if not _ima(p, "vitamin_d"):
            out.append(Nalaz(
                "START", "vitamin D (± kalcij)",
                "Osteoporoza bez suplementacije vitaminom D",
                "START v3 (E)",
                "Suboptimalan efekat antiresorptivne terapije; rizik pada.",
                "Uvesti holekalciferol (uz kalcij prema unosu).",
                "visok"))

    if _dg(p, "padovi") and not _ima(p, "vitamin_d") and preventiva_ok:
        out.append(Nalaz(
            "START", "vitamin D",
            "Ponavljani padovi bez suplementacije vitaminom D",
            "START v3",
            "Mišićna slabost i rizik ponovnog pada uz deficit vitamina D.",
            "Razmotriti vitamin D uz procjenu statusa.",
            "srednji"))

    if _dg(p, "dijabetes"):
        if not _ima(p, "antidijabetik"):
            out.append(Nalaz(
                "START", "metformin (ili drugi antidijabetik)",
                "Šećerna bolest tip 2 bez ikakve antihiperglikemijske terapije",
                "START v3 (F)",
                "Hronične komplikacije dijabetesa.",
                "Metformin 1. linija ako bubrežna funkcija dozvoljava; individualizovati cilj.",
                "srednji"))
        if _dg(p, "ckd", "proteinurija") and not _ima(p, "acei", "arb"):
            out.append(Nalaz(
                "START", "ACE inhibitor / ARB",
                "Dijabetes s bubrežnim oštećenjem/proteinurijom bez RAAS blokade",
                "START v3 (F)",
                "Progresija dijabetičke nefropatije.",
                "Uvesti ACEi/ARB uz kontrolu kalija i kreatinina.",
                "visok"))

    if _dg(p, "kopb") and not _ima(p, "inhalacioni"):
        out.append(Nalaz(
            "START", "inhalacioni bronhodilatator (LAMA/LABA)",
            "KOPB bez inhalacione terapije",
            "START v3 (G)",
            "Simptomi, egzacerbacije, hospitalizacije.",
            "Uvesti dugodjelujući bronhodilatator uz obuku tehnike inhalacije.",
            "visok"))

    if _dg(p, "depresija") and not _ima(p, "ssri", "snri", "tca", "antidepresiv_ostali"):
        out.append(Nalaz(
            "START", "antidepresiv (SSRI 1. linija)",
            "Umjerena/teška depresija bez antidepresiva",
            "START v3",
            "Neliječena depresija: funkcionalni pad, suicidalni rizik.",
            "Razmotriti SSRI uz praćenje natrija i rizika pada.",
            "srednji"))

    if _dg(p, "demencija") and not _ima(p, "antidementiv"):
        out.append(Nalaz(
            "START", "inhibitor acetilholinesteraze / memantin",
            "Demencija (Alzheimer) bez antidementivne terapije",
            "START v3",
            "Brži kognitivni i funkcionalni pad.",
            "Razmotriti donepezil/rivastigmin (blaga-umjerena) ili memantin (umjerena-teška).",
            "nizak"))

    if p.ogranicen_zivotni_vijek:
        out.append(Nalaz(
            "START", "—",
            "Napomena: ograničen životni vijek / palijativni cilj njege",
            "START v3 (princip)",
            "Preventivne START preporuke (statin, bisfosfonat) gube smisao kod kratkog očekivanog vijeka.",
            "Fokus na simptomatsku terapiju i kvalitet života; preventivu preispitati.",
            "visok"))


# ------------------------------------------------------------------
# transparentnost — šta NIJE provjereno
# ------------------------------------------------------------------

def _nedostajuci_podaci(p: Profil, nije: list[str]):
    if p.natrij is None and _ima(p, "ssri", "snri", "diuretik", "hiponatremija_rizik"):
        nije.append("Natrij nije unesen — kriteriji hiponatremije (SSRI/diuretici/karbamazepin) nisu provjereni.")
    if p.kalij is None and _ima(p, "acei", "arb", "k_stedeci"):
        nije.append("Kalij nije unesen — kriteriji hiperkalemije nisu provjereni.")
    if p.qtc is None and _ima(p, "qt_rizik"):
        nije.append("QTc nije dostupan — kriteriji produženja QT intervala nisu u potpunosti evaluirani.")
    if p.inr is None and _ima(p, "varfarin"):
        nije.append("INR nije unesen — sigurnost varfarina nije provjerena.")
    for l in p.lijekovi:
        if l.trajanje_sedmica is None and any(
            g in l.grupe for g in ("bzd", "z-lijek", "ppi", "opioid", "kortikosteroid_sistemski")
        ):
            nije.append(f"Trajanje za {l.inn} nije uneseno — trajanje-zavisni kriteriji za taj lijek nisu provjereni.")
