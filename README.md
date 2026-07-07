# PIP Procjena — Beers 2023 · STOPP/START v3

Aplikacija za provjeru **potencijalno neadekvatnog propisivanja lijekova** kod starijih
pacijenata, razvijena prema internom vodiču *„Razvoj aplikacije za provjeru neadekvatnog
propisivanja lijekova“* (Edu Pharma Community).

Unosom karakteristika pacijenta, dijagnoza i lijekova aplikacija upozorava da li pacijent
potpada pod kriterije **Beers 2023**, **STOPP v3** ili **START v3** (propušteni indicirani lijekovi).

## Pokretanje

```
pip install -r requirements.txt
streamlit run app.py
```

## Arhitektura (dva sloja koja se ne miješaju)

| Modul | Uloga |
|---|---|
| `izracuni.py` | Deterministički sloj: Cockcroft-Gault CrCl, eGFR (CKD-EPI 2021), BMI, trajanje terapije, ACB zbir, duplikati grupa. Sva matematika u kodu, nikad u modelu. |
| `lijekovi.py` | Lokalni rječnik: INN → ATC šifra, terapijske grupe, ACB skor (~140 supstanci s tržišta BiH). |
| `kriteriji.py` | Mehanizam pravila: parafrazirani, uslovni Beers/STOPP/START kriteriji koji se deterministički provjeravaju (radi i **bez interneta i bez API ključa**). |
| `claude_procjena.py` | Opcioni sloj jezičkog modela: već obrađeni anonimni profil + postojeći nalazi šalju se Claude modelu za **dodatne** nalaze (interakcije, kontekstualni kriteriji). Traži `ANTHROPIC_API_KEY`. |
| `izvjestaj.py` | Brendirani PDF izvještaj (ReportLab): STOPP i START tabele, „nije provjereno“, odricanje odgovornosti. |
| `app.py` | Streamlit forma sa strukturisanim unosom (šifrarnik dijagnoza — potvrdne kućice; lijekovi kao zasebni zapisi; ciljani lab). |

## Ključni principi (iz vodiča)

- **Podaci prije koda** — kriteriji su gotovo svi uslovni; bez trajanja terapije, indikacije
  i CrCl-a procjena nije validna.
- **CrCl se nikad ne unosi ručno** — izračunava se iz dobi, spola, mase i kreatinina.
- **Transparentnost** — sve što nije moglo biti provjereno navodi se u listi „nije provjereno“.
- **Bez identifikatora** — prema API-ju ide isključivo anonimni profil.
- **Čovjek u petlji** — alat je podrška odlučivanju, ne zamjena za farmaceuta.

## Testovi

```
python test_procjena.py
```

## Ograničenja

- Skup pravila je parafrazirani podskup (najčešći i klinički najvažniji kriteriji);
  ne pokriva svih 190 STOPP/START v3 kriterija.
- Beers je primarno američki standard — dio preporuka zahtijeva lokalizaciju.
- Rječnik lijekova se dopunjava u `lijekovi.py` (INN, ATC, grupe, ACB).

**Alat je podrška kliničkom odlučivanju i edukaciji — nije medicinsko sredstvo niti
zamjena za prosudbu zdravstvenog radnika.**
