"""PIP Procjena — provjera potencijalno neadekvatnog propisivanja lijekova
(Beers 2023 · STOPP/START v3) kod starijih pacijenata.

Pokretanje:  streamlit run app.py
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from izracuni import (
    bmi, cockcroft_gault, egfr_ckd_epi_2021, obradi_terapiju,
    stadij_ckd, trajanje_sedmica, acb_ukupno,
)
from izvjestaj import generisi_pdf
from kriteriji import Nalaz, Profil, procijeni
from lijekovi import RJECNIK_LIJEKOVA, SVI_INN

st.set_page_config(page_title="PIP Procjena — Beers · STOPP/START", page_icon="💊", layout="wide")

# ------------------------------------------------------------------
# vizuelni sloj — medicinska paleta (teal/tirkizna), kartice, mobilni prikaz
# ------------------------------------------------------------------
st.markdown("""
<style>
:root {
    --pip-teal: #0F766E;
    --pip-teal-dark: #115E59;
    --pip-teal-light: #CCECE9;
    --pip-ink: #16323E;
    --pip-muted: #5B7684;
    --pip-card: #FFFFFF;
    --pip-border: #DCE9E7;
    --pip-stopp: #B4232A;
    --pip-start: #1B7A3D;
}

/* tipografija i osnovni razmaci */
html, body, [class*="css"] { font-family: "Segoe UI", system-ui, -apple-system, sans-serif; }
.block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1200px; }

/* sakrij Streamlit meni i futer — čišći, profesionalan izgled */
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }

/* zaglavlje aplikacije */
.pip-banner {
    background: linear-gradient(135deg, #0F766E 0%, #0E7490 60%, #155E75 100%);
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    color: #FFFFFF;
    margin-bottom: 1.2rem;
    box-shadow: 0 6px 18px rgba(15, 118, 110, 0.25);
}
.pip-banner h1 {
    margin: 0 0 .3rem 0;
    font-size: 1.9rem;
    font-weight: 700;
    letter-spacing: -.02em;
    color: #FFFFFF;
}
.pip-banner p { margin: 0; opacity: .92; font-size: .95rem; line-height: 1.45; }
.pip-banner .pip-badges { margin-top: .7rem; display: flex; flex-wrap: wrap; gap: .4rem; }
.pip-badge {
    display: inline-block;
    background: rgba(255,255,255,.16);
    border: 1px solid rgba(255,255,255,.35);
    border-radius: 999px;
    padding: .15rem .7rem;
    font-size: .78rem;
    font-weight: 600;
    letter-spacing: .02em;
}

/* naslovi sekcija */
h2 {
    color: var(--pip-teal-dark) !important;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    border-bottom: 2px solid var(--pip-teal-light);
    padding-bottom: .35rem !important;
    margin-top: 1.6rem !important;
}
h3 { color: var(--pip-ink) !important; font-size: 1.05rem !important; }

/* metrike kao kliničke kartice */
[data-testid="stMetric"] {
    background: var(--pip-card);
    border: 1px solid var(--pip-border);
    border-left: 4px solid var(--pip-teal);
    border-radius: 12px;
    padding: .8rem 1rem;
    box-shadow: 0 2px 6px rgba(22, 50, 62, 0.06);
}
[data-testid="stMetricLabel"] { color: var(--pip-muted); font-size: .8rem; }
[data-testid="stMetricValue"] { color: var(--pip-ink); font-weight: 700; }

/* expanderi (nalazi) kao kartice */
[data-testid="stExpander"] {
    background: var(--pip-card);
    border: 1px solid var(--pip-border);
    border-radius: 12px;
    margin-bottom: .5rem;
    box-shadow: 0 1px 4px rgba(22, 50, 62, 0.05);
    overflow: hidden;
}
[data-testid="stExpander"] summary { font-size: .92rem; }

/* glavno dugme */
.stButton > button[kind="primary"], [data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, var(--pip-teal) 0%, #0E7490 100%);
    color: #FFFFFF;
    border: none;
    border-radius: 12px;
    padding: .7rem 1.2rem;
    font-weight: 700;
    font-size: 1rem;
    box-shadow: 0 4px 12px rgba(15, 118, 110, 0.30);
    transition: transform .12s ease, box-shadow .12s ease;
}
.stButton > button[kind="primary"]:hover, [data-testid="stDownloadButton"] > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(15, 118, 110, 0.38);
    color: #FFFFFF;
}

/* checkbox blokovi — kompaktnije */
[data-testid="stCheckbox"] { margin-bottom: -.35rem; }
[data-testid="stCheckbox"] p { font-size: .88rem; }

/* upozorenja i info blokovi — mekši uglovi */
[data-testid="stAlert"] { border-radius: 12px; }

/* tabela lijekova */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    border: 1px solid var(--pip-border);
    border-radius: 12px;
    overflow: hidden;
}

/* mobilni prikaz */
@media (max-width: 740px) {
    .block-container { padding-left: .9rem; padding-right: .9rem; }
    .pip-banner { padding: 1.1rem 1.2rem; border-radius: 12px; }
    .pip-banner h1 { font-size: 1.35rem; }
    .pip-banner p { font-size: .85rem; }
    h2 { font-size: 1.1rem !important; }
    [data-testid="stMetric"] { padding: .6rem .8rem; }
    .stButton > button[kind="primary"] { width: 100%; }
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# šifrarnik stanja (Dio 1.4 vodiča) — potvrdne kućice, ne slobodan tekst
# ------------------------------------------------------------------
STANJA: dict[str, list[tuple[str, str]]] = {
    "Kardiovaskularni": [
        ("srcana_insuficijencija", "Srčana insuficijencija"),
        ("atrijska_fibrilacija", "Atrijska fibrilacija"),
        ("koronarna_bolest", "Koronarna (ishemijska) bolest srca"),
        ("hipertenzija", "Hipertenzija"),
        ("sinkopa", "Sinkopa"),
        ("ortostatska_hipotenzija", "Ortostatska hipotenzija"),
        ("bradikardija", "Bradikardija"),
        ("periferna_arterijska", "Periferna arterijska bolest"),
    ],
    "CNS i psiha": [
        ("demencija", "Demencija / kognitivni pad"),
        ("delirij", "Anamneza delirija"),
        ("parkinson", "Parkinsonova bolest"),
        ("lewy", "Demencija s Lewyjevim tijelima"),
        ("epilepsija", "Epilepsija / napadi"),
        ("depresija", "Depresija"),
        ("anksioznost", "Anksioznost"),
        ("nesanica", "Nesanica"),
        ("cvi_tia", "Anamneza CVI / TIA"),
    ],
    "Padovi (zaseban blok)": [
        ("padovi", "≥1 pad u zadnjih 12 mjeseci"),
    ],
    "Gastrointestinalni": [
        ("ulkus_gi_krvarenje", "Anamneza peptičkog ulkusa / GI krvarenja"),
        ("konstipacija", "Hronična konstipacija"),
        ("gerb", "GERB"),
    ],
    "Urološki": [
        ("bph_retencija", "BPH / urinarna retencija"),
        ("inkontinencija", "Urinarna inkontinencija"),
    ],
    "Endokrini / metabolički": [
        ("dijabetes", "Šećerna bolest (tip 2)"),
        ("osteoporoza", "Osteoporoza / fragilni prijelom"),
        ("giht", "Giht"),
        ("ckd", "Hronična bubrežna bolest (poznata)"),
        ("proteinurija", "Proteinurija / albuminurija"),
    ],
    "Respiratorni": [
        ("kopb", "KOPB"),
        ("astma", "Astma"),
    ],
    "Ostalo": [
        ("glaukom", "Uskougaoni glaukom"),
        ("vte", "Anamneza VTE"),
        ("malignitet", "Aktivni malignitet"),
    ],
}

POUZDANOST_IKONA = {"visok": "🔴", "srednji": "🟠", "nizak": "⚪"}

# ------------------------------------------------------------------
st.markdown("""
<div class="pip-banner">
  <h1>💊 PIP Procjena</h1>
  <p>Provjera potencijalno neadekvatnog propisivanja lijekova kod starijih pacijenata.
     Alat je podrška odlučivanju i edukaciji — konačnu odluku donosi farmaceut/ljekar.</p>
  <div class="pip-badges">
    <span class="pip-badge">AGS Beers 2023</span>
    <span class="pip-badge">STOPP v3</span>
    <span class="pip-badge">START v3</span>
    <span class="pip-badge">Radi bez interneta i API-ja</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ================= 1. demografija i bubrežna funkcija =================
st.header("1 · Pacijent")
c1, c2, c3, c4, c5 = st.columns(5)
dob = c1.number_input("Dob (godine) *", 18, 120, 75)
spol = c2.selectbox("Spol *", ["Ž", "M"])
masa = c3.number_input("Tjelesna masa (kg) *", 0.0, 250.0, 70.0, step=0.5)
visina = c4.number_input("Visina (cm)", 0.0, 230.0, 165.0, step=0.5)
kreatinin = c5.number_input("Serum kreatinin (µmol/L) *", 0.0, 1500.0, 0.0, step=1.0,
                            help="0 = nije dostupan. Bez kreatinina renalni kriteriji se NE provjeravaju.")

crcl = egfr = None
if kreatinin > 0 and masa > 0:
    crcl = cockcroft_gault(dob, masa, kreatinin, spol)
    egfr = egfr_ckd_epi_2021(kreatinin, dob, spol)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("CrCl (Cockcroft-Gault)", f"{crcl} ml/min")
    m2.metric("eGFR (CKD-EPI 2021)", f"{egfr} ml/min/1,73m²")
    m3.metric("Stadij CKD", stadij_ckd(egfr))
    if visina > 0:
        m4.metric("BMI", f"{bmi(masa, visina)} kg/m²")
elif kreatinin == 0:
    st.warning("Kreatinin nije unesen — CrCl/eGFR se ne mogu izračunati; renalni kriteriji (Beers kat. 5) neće biti provjereni.")

if dob < 65:
    st.info("Napomena: Beers i STOPP/START kriteriji primarno ciljaju pacijente **≥65 godina**.")

# ================= 2. dijagnoze =================
st.header("2 · Aktivne dijagnoze i gerijatrijski sindromi")
odabrana_stanja: set[str] = set()
kolone = st.columns(4)
for i, (sistem, stavke) in enumerate(STANJA.items()):
    with kolone[i % 4]:
        st.markdown(f"**{sistem}**")
        for sifra, naziv in stavke:
            if st.checkbox(naziv, key=f"dg_{sifra}"):
                odabrana_stanja.add(sifra)

ogranicen_vijek = st.checkbox(
    "Ograničen očekivani životni vijek / palijativni cilj njege",
    help="Preventivne START preporuke (statin, bisfosfonat) se u tom slučaju označavaju za preispitivanje.")

# ================= 3. terapija =================
st.header("3 · Kompletna lista lijekova")
st.caption(
    "Svaki lijek je zaseban strukturisan zapis (INN, ne brend). Trajanje i indikacija su "
    "najčešće zaboravljena, a ključna polja — bez njih se trajanje-zavisni i START kriteriji ne mogu provjeriti."
)

prazna = pd.DataFrame({
    "INN (aktivna supstanca)": pd.Series(dtype="str"),
    "Dnevna doza (mg)": pd.Series(dtype="float"),
    "Režim": pd.Series(dtype="str"),
    "Put primjene": pd.Series(dtype="str"),
    "Datum početka": pd.Series(dtype="object"),
    "Trajanje (sedmice)": pd.Series(dtype="float"),
    "Indikacija": pd.Series(dtype="str"),
})

tabela = st.data_editor(
    prazna,
    num_rows="dynamic",
    width="stretch",
    key="tabela_lijekova",
    column_config={
        "INN (aktivna supstanca)": st.column_config.SelectboxColumn(
            options=SVI_INN, required=True,
            help="Odabir iz lokalnog rječnika (INN). Brend mapirati na supstancu."),
        "Dnevna doza (mg)": st.column_config.NumberColumn(min_value=0.0, format="%.3f"),
        "Režim": st.column_config.SelectboxColumn(options=["redovno", "PRN (po potrebi)"]),
        "Put primjene": st.column_config.SelectboxColumn(
            options=["per os", "topikalno", "s.c.", "i.m.", "i.v.", "inhalaciono", "transdermalno", "vaginalno"]),
        "Datum početka": st.column_config.DateColumn(
            help="Ako je unesen, trajanje se izračunava automatski (ne unosi se ručno)."),
        "Trajanje (sedmice)": st.column_config.NumberColumn(
            min_value=0, step=1, help="Koristi se samo ako datum početka nije poznat."),
        "Indikacija": st.column_config.TextColumn(
            help="Zašto pacijent prima lijek — ključno za 'lijek bez indikacije' i START."),
    },
)

# ================= 4. laboratorij i vitalni =================
st.header("4 · Ciljani laboratorijski i vitalni parametri")
st.caption("Ne treba cijeli nalaz — samo vrijednosti koje pokreću kriterije. 0 = nije dostupno.")
l1, l2, l3, l4, l5, l6 = st.columns(6)
natrij = l1.number_input("Natrij (mmol/L)", 0.0, 180.0, 0.0, step=0.5)
kalij = l2.number_input("Kalij (mmol/L)", 0.0, 9.0, 0.0, step=0.1)
hba1c = l3.number_input("HbA1c (%)", 0.0, 20.0, 0.0, step=0.1)
inr = l4.number_input("INR", 0.0, 12.0, 0.0, step=0.1)
qtc = l5.number_input("QTc (ms)", 0.0, 700.0, 0.0, step=1.0)
frekvencija = l6.number_input("Srčana frekvencija (/min)", 0.0, 220.0, 0.0, step=1.0)

alergije = st.text_input("Alergije / intolerancije na lijekove", placeholder="npr. penicilin — osip")
oznaka = st.text_input("Anonimna oznaka slučaja (za izvještaj)", placeholder="npr. SLUČAJ-2026-014",
                       help="Bez imena, JMBG-a ili broja kartona — podaci ostaju anonimni.")

koristi_claude = st.toggle(
    "Dodatna procjena jezičkim modelom (Claude API)",
    help="Šalje anonimni, već obrađeni profil Claude modelu za dodatne nalaze "
         "(interakcije, kontekstualni kriteriji). Zahtijeva ANTHROPIC_API_KEY.")

# ================= procjena =================
if st.button("🔎 Pokreni procjenu", type="primary", width="stretch"):
    # validacija obaveznih polja
    problemi = []
    if masa <= 0:
        problemi.append("Tjelesna masa je obavezna (ulaz za Cockcroft-Gault).")
    unosi = []
    for _, red in tabela.iterrows():
        inn = red.get("INN (aktivna supstanca)")
        if not isinstance(inn, str) or not inn.strip():
            continue
        traj = None
        datum = red.get("Datum početka")
        if pd.notna(datum) and datum:
            traj = trajanje_sedmica(datum if isinstance(datum, date) else datum.date())
        elif pd.notna(red.get("Trajanje (sedmice)")):
            traj = int(red["Trajanje (sedmice)"])
        unosi.append({
            "inn": inn,
            "doza_dnevno_mg": float(red["Dnevna doza (mg)"]) if pd.notna(red.get("Dnevna doza (mg)")) else None,
            "frekvencija": red.get("Režim") if isinstance(red.get("Režim"), str) else "",
            "put": red.get("Put primjene") if isinstance(red.get("Put primjene"), str) else "per os",
            "trajanje_sedmica": traj,
            "indikacija": red.get("Indikacija") if isinstance(red.get("Indikacija"), str) else "",
        })
    if not unosi:
        problemi.append("Unesite barem jedan lijek.")

    if problemi:
        for p in problemi:
            st.error(p)
        st.stop()

    lijekovi, upozorenja_rjecnik = obradi_terapiju(unosi, RJECNIK_LIJEKOVA)

    profil = Profil(
        dob=dob, spol=spol, masa_kg=masa or None,
        crcl=crcl, egfr=egfr,
        dijagnoze=odabrana_stanja, lijekovi=lijekovi,
        natrij=natrij or None, kalij=kalij or None, hba1c=hba1c or None,
        inr=inr or None, qtc=qtc or None,
        frekvencija_srca=frekvencija or None,
        ogranicen_zivotni_vijek=ogranicen_vijek,
    )

    stopp, start, nije = procijeni(profil)
    nije = upozorenja_rjecnik + nije

    if koristi_claude:
        with st.spinner("Claude analizira profil za dodatne nalaze..."):
            from claude_procjena import claude_dodatna_procjena
            dodatni, dodatno_nije, greska = claude_dodatna_procjena(profil, stopp + start)
        if greska:
            st.warning(f"Claude procjena nije izvršena: {greska}")
        else:
            for n in dodatni:
                n.izvor += " (Claude — provjeriti!)"
                (stopp if n.tip == "STOPP" else start).append(n)
            nije += dodatno_nije

    # sortiranje po pouzdanosti
    redoslijed = {"visok": 0, "srednji": 1, "nizak": 2}
    stopp.sort(key=lambda n: redoslijed.get(n.nivo_pouzdanosti, 3))
    start.sort(key=lambda n: redoslijed.get(n.nivo_pouzdanosti, 3))

    st.session_state["rezultat"] = (profil, stopp, start, nije, oznaka)

# ================= prikaz rezultata =================
if "rezultat" in st.session_state:
    profil, stopp, start, nije, oznaka = st.session_state["rezultat"]

    st.divider()
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("STOPP/Beers nalaza", len(stopp))
    r2.metric("START nalaza", len(start))
    r3.metric("Nije provjereno", len(nije))
    acb = acb_ukupno(profil.lijekovi)
    r4.metric("ACB zbir (antiholinergici)", acb, delta="⚠ visok" if acb >= 3 else None, delta_color="inverse")

    def prikazi(nalazi: list[Nalaz], naslov: str):
        st.subheader(naslov)
        if not nalazi:
            st.success("Nema detektovanih nalaza.")
            return
        for n in nalazi:
            ikona = POUZDANOST_IKONA.get(n.nivo_pouzdanosti, "⚪")
            with st.expander(f"{ikona} **{n.lijek}** — {n.kriterij}"):
                st.markdown(
                    f"**Izvor:** {n.izvor}  \n"
                    f"**Klinički rizik:** {n.klinicki_rizik}  \n"
                    f"**Preporučena akcija:** {n.preporuka}  \n"
                    f"**Nivo pouzdanosti:** {n.nivo_pouzdanosti}"
                )

    kol_s, kol_t = st.columns(2)
    with kol_s:
        prikazi(stopp, "🛑 STOPP / Beers — potencijalno neadekvatni lijekovi")
    with kol_t:
        prikazi(start, "✅ START — propušteni, a indicirani lijekovi")

    st.subheader("❔ Nije provjereno — nedostajući podaci")
    if nije:
        for stavka in nije:
            st.markdown(f"- {stavka}")
    else:
        st.markdown("Svi ključni podaci za aktivirane kriterije bili su dostupni.")

    pdf = generisi_pdf(profil, stopp, start, nije, oznaka)
    st.download_button(
        "⬇️ Preuzmi PDF izvještaj",
        data=pdf,
        file_name=f"PIP_izvjestaj_{(oznaka or date.today().isoformat()).replace(' ', '_')}.pdf",
        mime="application/pdf",
        width="stretch",
    )

    st.caption(
        "⚠️ Obavezna ljudska provjera: nijedna preporuka se ne primjenjuje bez provjere "
        "farmaceuta/ljekara. Alat sistematizuje provjeru i ništa ne propušta tiho — sve što "
        "nije moglo biti provjereno jasno je označeno."
    )
