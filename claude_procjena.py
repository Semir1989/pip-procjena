"""Sloj jezičkog modela (Dio 4 vodiča) — opcionalna dodatna procjena preko Claude API-ja.

Modelu se šalje VEĆ OBRAĐEN profil (CrCl, trajanja, ATC grupe izračunati u Pythonu)
te nalazi determinističkog sloja, a zadatak mu je da pronađe DODATNE Beers/STOPP/START
nalaze koje strukturisana pravila nisu pokrila (interakcije, kontekstualni kriteriji).

Zahtijeva ANTHROPIC_API_KEY u okruženju. Statički dio prompta se kešira
(prompt caching) radi niže cijene ponovljenih poziva.
"""

from __future__ import annotations

import json

from kriteriji import Nalaz, Profil

MODEL = "claude-opus-4-8"

SISTEMSKI_PROMPT = """<uloga>
Ti si klinički farmaceut-evaluator specijalizovan za gerijatrijsku farmakoterapiju.
Procjenjuješ terapiju isključivo prema kriterijima AGS Beers 2023 i STOPP/START
verzija 3. Ne izmišljaš kriterije. Ako podatak nedostaje, to eksplicitno navodiš,
a procjenu za taj kriterij označavaš kao "nije provjereno".
</uloga>

<pravila>
- Radi i STOPP/Beers stranu (neadekvatni lijekovi) i START stranu (propušteni indicirani lijekovi).
- Dobit ćeš nalaze koje je deterministički sloj VEĆ detektovao — NEMOJ ih ponavljati.
  Tvoj zadatak su isključivo DODATNI nalazi: klinički značajne interakcije lijek-lijek,
  kontekstualni kriteriji ("izbjegavaj osim ako..."), doza-zavisni kriteriji i
  kriteriji koje strukturisana pravila nisu obuhvatila.
- Za svaki nalaz navedi tačan izvor (kriterij i dokument: "Beers 2023", "STOPP v3" ili "START v3").
- Budi konzervativan: ako nisi siguran, snizi nivo pouzdanosti ("nizak").
- Ne daješ konačnu odluku — daješ prijedlog za provjeru farmaceuta.
- Sve matematičke vrijednosti (CrCl, eGFR, trajanja) su već izračunate u profilu — ne preračunavaj ih.
- Piši na bosanskom jeziku.
- Izlaz je ISKLJUČIVO JSON po zadatoj shemi.
</pravila>"""

JSON_SHEMA = {
    "type": "object",
    "properties": {
        "dodatni_nalazi": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tip": {"type": "string", "enum": ["STOPP", "START"]},
                    "lijek": {"type": "string"},
                    "kriterij": {"type": "string"},
                    "izvor": {"type": "string"},
                    "klinicki_rizik": {"type": "string"},
                    "preporuka": {"type": "string"},
                    "nivo_pouzdanosti": {"type": "string", "enum": ["visok", "srednji", "nizak"]},
                },
                "required": ["tip", "lijek", "kriterij", "izvor",
                             "klinicki_rizik", "preporuka", "nivo_pouzdanosti"],
                "additionalProperties": False,
            },
        },
        "nije_provjereno": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["dodatni_nalazi", "nije_provjereno"],
    "additionalProperties": False,
}


def _profil_xml(profil: Profil, postojeci: list[Nalaz]) -> str:
    """Dinamički dio poziva — obrađeni profil u XML strukturi (Dio 4.2 vodiča)."""
    dg = "\n".join(f"  <dg>{d}</dg>" for d in sorted(profil.dijagnoze)) or "  (nema unesenih)"
    lij = "\n".join(
        f'  <lijek inn="{l.inn}" atc="{l.atc}" doza_dnevno_mg="{l.doza_dnevno_mg or "?"}"'
        f' put="{l.put}" trajanje_sedmica="{l.trajanje_sedmica if l.trajanje_sedmica is not None else "?"}"'
        f' indikacija="{l.indikacija or "?"}"/>'
        for l in profil.lijekovi
    ) or "  (nema unesenih)"
    vec = "\n".join(
        f"  - [{n.tip}] {n.lijek}: {n.kriterij}" for n in postojeci
    ) or "  (nijedan)"

    def v(x):
        return x if x is not None else "?"

    return f"""<pacijent>
  <dob>{profil.dob}</dob><spol>{profil.spol}</spol><masa_kg>{v(profil.masa_kg)}</masa_kg>
  <crcl_ml_min>{v(profil.crcl)}</crcl_ml_min>
  <egfr>{v(profil.egfr)}</egfr>
  <natrij>{v(profil.natrij)}</natrij><kalij>{v(profil.kalij)}</kalij>
  <hba1c>{v(profil.hba1c)}</hba1c><inr>{v(profil.inr)}</inr><qtc>{v(profil.qtc)}</qtc>
  <frekvencija_srca>{v(profil.frekvencija_srca)}</frekvencija_srca>
  <ogranicen_zivotni_vijek>{profil.ogranicen_zivotni_vijek}</ogranicen_zivotni_vijek>
</pacijent>
<dijagnoze>
{dg}
</dijagnoze>
<terapija>
{lij}
</terapija>
<vec_detektovano>
{vec}
</vec_detektovano>

Pronađi DODATNE Beers 2023 / STOPP v3 / START v3 nalaze i klinički značajne
interakcije koje gore navedeni deterministički nalazi ne pokrivaju."""


def claude_dodatna_procjena(profil: Profil, postojeci: list[Nalaz]) -> tuple[list[Nalaz], list[str], str | None]:
    """Poziva Claude za dodatne nalaze. Vraća (nalazi, nije_provjereno, greska)."""
    try:
        import anthropic
    except ImportError:
        return [], [], "Paket 'anthropic' nije instaliran (pip install anthropic)."

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=[{
                "type": "text",
                "text": SISTEMSKI_PROMPT,
                "cache_control": {"type": "ephemeral"},  # statički dio se kešira
            }],
            output_config={"format": {"type": "json_schema", "schema": JSON_SHEMA}},
            messages=[{"role": "user", "content": _profil_xml(profil, postojeci)}],
        )
        if response.stop_reason == "refusal":
            return [], [], "Model je odbio zahtjev (refusal) — provjeriti sadržaj unosa."
        tekst = next(b.text for b in response.content if b.type == "text")
        podaci = json.loads(tekst)
    except anthropic.AuthenticationError:
        return [], [], "ANTHROPIC_API_KEY nije postavljen ili nije validan."
    except anthropic.APIConnectionError:
        return [], [], "Nema konekcije prema Claude API-ju."
    except Exception as e:  # noqa: BLE001 — UI prikazuje grešku, ne ruši aplikaciju
        return [], [], f"Greška pri pozivu modela: {e}"

    nalazi = [
        Nalaz(
            tip=n["tip"], lijek=n["lijek"], kriterij=n["kriterij"], izvor=n["izvor"],
            klinicki_rizik=n["klinicki_rizik"], preporuka=n["preporuka"],
            nivo_pouzdanosti=n["nivo_pouzdanosti"],
        )
        for n in podaci.get("dodatni_nalazi", [])
    ]
    return nalazi, podaci.get("nije_provjereno", []), None
