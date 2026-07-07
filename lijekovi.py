"""Lokalni rječnik lijekova — INN -> ATC šifra, terapijske grupe i ACB skor.

Obuhvata supstance uobičajene na tržištu BiH. Grupe se koriste u kriterijima
(kriteriji.py) i za detekciju duplikata. ACB = Anticholinergic Cognitive
Burden skala (0-3).

Napomena: rječnik je namjerno po INN-u (aktivnoj supstanci), ne po brendu —
brendove treba mapirati na INN prije unosa.
"""

RJECNIK_LIJEKOVA: dict[str, dict] = {
    # --- NSAID ---
    "diklofenak":     {"atc": "M01AB05", "grupe": ["nsaid"], "acb": 0},
    "ibuprofen":      {"atc": "M01AE01", "grupe": ["nsaid"], "acb": 0},
    "naproksen":      {"atc": "M01AE02", "grupe": ["nsaid"], "acb": 0},
    "ketoprofen":     {"atc": "M01AE03", "grupe": ["nsaid"], "acb": 0},
    "meloksikam":     {"atc": "M01AC06", "grupe": ["nsaid"], "acb": 0},
    "piroksikam":     {"atc": "M01AC01", "grupe": ["nsaid", "beers_izbjegavati"], "acb": 0},
    "indometacin":    {"atc": "M01AB01", "grupe": ["nsaid", "beers_izbjegavati"], "acb": 0},
    "celekoksib":     {"atc": "M01AH01", "grupe": ["nsaid", "koksib"], "acb": 0},
    "etorikoksib":    {"atc": "M01AH05", "grupe": ["nsaid", "koksib"], "acb": 0},
    "acetilsalicilna kiselina": {"atc": "B01AC06", "grupe": ["antiagregans", "aspirin"], "acb": 0},
    "paracetamol":    {"atc": "N02BE01", "grupe": ["analgetik"], "acb": 0},
    "metamizol":      {"atc": "N02BB02", "grupe": ["analgetik"], "acb": 0},

    # --- Benzodiazepini i Z-lijekovi ---
    "diazepam":       {"atc": "N05BA01", "grupe": ["bzd", "bzd_dugodjelujuci", "sedativ"], "acb": 0},
    "bromazepam":     {"atc": "N05BA08", "grupe": ["bzd", "sedativ"], "acb": 0},
    "alprazolam":     {"atc": "N05BA12", "grupe": ["bzd", "sedativ"], "acb": 0},
    "lorazepam":      {"atc": "N05BA06", "grupe": ["bzd", "sedativ"], "acb": 0},
    "oksazepam":      {"atc": "N05BA04", "grupe": ["bzd", "sedativ"], "acb": 0},
    "klonazepam":     {"atc": "N03AE01", "grupe": ["bzd", "bzd_dugodjelujuci", "sedativ"], "acb": 0},
    "midazolam":      {"atc": "N05CD08", "grupe": ["bzd", "sedativ"], "acb": 0},
    "nitrazepam":     {"atc": "N05CD02", "grupe": ["bzd", "bzd_dugodjelujuci", "sedativ"], "acb": 0},
    "zolpidem":       {"atc": "N05CF02", "grupe": ["z-lijek", "sedativ"], "acb": 0},
    "zopiklon":       {"atc": "N05CF01", "grupe": ["z-lijek", "sedativ"], "acb": 0},

    # --- Antidepresivi ---
    "sertralin":      {"atc": "N06AB06", "grupe": ["ssri"], "acb": 1},
    "escitalopram":   {"atc": "N06AB10", "grupe": ["ssri"], "acb": 1},
    "citalopram":     {"atc": "N06AB04", "grupe": ["ssri", "qt_rizik"], "acb": 1},
    "paroksetin":     {"atc": "N06AB05", "grupe": ["ssri", "beers_izbjegavati"], "acb": 3},
    "fluoksetin":     {"atc": "N06AB03", "grupe": ["ssri"], "acb": 1},
    "venlafaksin":    {"atc": "N06AX16", "grupe": ["snri"], "acb": 1},
    "duloksetin":     {"atc": "N06AX21", "grupe": ["snri"], "acb": 1},
    "mirtazapin":     {"atc": "N06AX11", "grupe": ["antidepresiv_ostali"], "acb": 1},
    "trazodon":       {"atc": "N06AX05", "grupe": ["antidepresiv_ostali", "sedativ"], "acb": 1},
    "amitriptilin":   {"atc": "N06AA09", "grupe": ["tca", "beers_izbjegavati"], "acb": 3},
    "klomipramin":    {"atc": "N06AA04", "grupe": ["tca", "beers_izbjegavati"], "acb": 3},
    "maprotilin":     {"atc": "N06AA21", "grupe": ["tca"], "acb": 2},

    # --- Antipsihotici ---
    "haloperidol":    {"atc": "N05AD01", "grupe": ["antipsihotik", "qt_rizik"], "acb": 1},
    "risperidon":     {"atc": "N05AX08", "grupe": ["antipsihotik"], "acb": 1},
    "kvetiapin":      {"atc": "N05AH04", "grupe": ["antipsihotik", "sedativ"], "acb": 3},
    "olanzapin":      {"atc": "N05AH03", "grupe": ["antipsihotik", "sedativ"], "acb": 3},
    "aripiprazol":    {"atc": "N05AX12", "grupe": ["antipsihotik"], "acb": 0},
    "promazin":       {"atc": "N05AA03", "grupe": ["antipsihotik", "sedativ"], "acb": 3},
    "sulpirid":       {"atc": "N05AL01", "grupe": ["antipsihotik"], "acb": 0},

    # --- Antihistaminici 1. generacije / antiholinergici ---
    "difenhidramin":  {"atc": "R06AA02", "grupe": ["antihistaminik_1g", "beers_izbjegavati"], "acb": 3},
    "hidroksizin":    {"atc": "N05BB01", "grupe": ["antihistaminik_1g", "beers_izbjegavati"], "acb": 3},
    "kloropiramin":   {"atc": "R06AC03", "grupe": ["antihistaminik_1g", "beers_izbjegavati"], "acb": 3},
    "prometazin":     {"atc": "R06AD02", "grupe": ["antihistaminik_1g", "beers_izbjegavati"], "acb": 3},
    "loratadin":      {"atc": "R06AX13", "grupe": ["antihistaminik_2g"], "acb": 0},
    "cetirizin":      {"atc": "R06AE07", "grupe": ["antihistaminik_2g"], "acb": 1},
    "biperiden":      {"atc": "N04AA02", "grupe": ["antiholinergik", "beers_izbjegavati"], "acb": 3},

    # --- Urološki antimuskarinici / BPH ---
    "solifenacin":    {"atc": "G04BD08", "grupe": ["antiholinergik_urin"], "acb": 3},
    "tolterodin":     {"atc": "G04BD07", "grupe": ["antiholinergik_urin"], "acb": 3},
    "trospij":        {"atc": "G04BD09", "grupe": ["antiholinergik_urin"], "acb": 1},
    "tamsulozin":     {"atc": "G04CA02", "grupe": ["alfa_blokator_uro"], "acb": 0},
    "doksazosin":     {"atc": "C02CA04", "grupe": ["alfa_blokator", "beers_izbjegavati_htn"], "acb": 1},

    # --- Opioidi ---
    "tramadol":       {"atc": "N02AX02", "grupe": ["opioid", "snizava_prag_napada"], "acb": 0},
    "kodein":         {"atc": "R05DA04", "grupe": ["opioid"], "acb": 1},
    "morfin":         {"atc": "N02AA01", "grupe": ["opioid"], "acb": 0},
    "fentanil":       {"atc": "N02AB03", "grupe": ["opioid"], "acb": 0},
    "oksikodon":      {"atc": "N02AA05", "grupe": ["opioid"], "acb": 0},

    # --- Kardiovaskularni ---
    "ramipril":       {"atc": "C09AA05", "grupe": ["acei"], "acb": 0},
    "enalapril":      {"atc": "C09AA02", "grupe": ["acei"], "acb": 0},
    "lizinopril":     {"atc": "C09AA03", "grupe": ["acei"], "acb": 0},
    "perindopril":    {"atc": "C09AA04", "grupe": ["acei"], "acb": 0},
    "fosinopril":     {"atc": "C09AA09", "grupe": ["acei"], "acb": 0},
    "losartan":       {"atc": "C09CA01", "grupe": ["arb"], "acb": 0},
    "valsartan":      {"atc": "C09CA03", "grupe": ["arb"], "acb": 0},
    "telmisartan":    {"atc": "C09CA07", "grupe": ["arb"], "acb": 0},
    "kandesartan":    {"atc": "C09CA06", "grupe": ["arb"], "acb": 0},
    "bisoprolol":     {"atc": "C07AB07", "grupe": ["bb"], "acb": 0},
    "metoprolol":     {"atc": "C07AB02", "grupe": ["bb"], "acb": 0},
    "nebivolol":      {"atc": "C07AB12", "grupe": ["bb"], "acb": 0},
    "karvedilol":     {"atc": "C07AG02", "grupe": ["bb"], "acb": 0},
    "atenolol":       {"atc": "C07AB03", "grupe": ["bb"], "acb": 1},
    "amlodipin":      {"atc": "C08CA01", "grupe": ["ccb_dhp"], "acb": 0},
    "lerkanidipin":   {"atc": "C08CA13", "grupe": ["ccb_dhp"], "acb": 0},
    "nifedipin":      {"atc": "C08CA05", "grupe": ["ccb_dhp"], "acb": 0},
    "verapamil":      {"atc": "C08DA01", "grupe": ["ccb_nondhp"], "acb": 0},
    "diltiazem":      {"atc": "C08DB01", "grupe": ["ccb_nondhp"], "acb": 0},
    "furosemid":      {"atc": "C03CA01", "grupe": ["diuretik_petlje", "diuretik"], "acb": 1},
    "torasemid":      {"atc": "C03CA04", "grupe": ["diuretik_petlje", "diuretik"], "acb": 0},
    "hidrohlorotiazid": {"atc": "C03AA03", "grupe": ["tiazid", "diuretik"], "acb": 0},
    "indapamid":      {"atc": "C03BA11", "grupe": ["tiazid", "diuretik"], "acb": 0},
    "spironolakton":  {"atc": "C03DA01", "grupe": ["k_stedeci", "diuretik", "spironolakton"], "acb": 0},
    "eplerenon":      {"atc": "C03DA04", "grupe": ["k_stedeci", "diuretik"], "acb": 0},
    "digoksin":       {"atc": "C01AA05", "grupe": ["digoksin"], "acb": 1},
    "amiodaron":      {"atc": "C01BD01", "grupe": ["antiaritmik", "qt_rizik"], "acb": 0},
    "propafenon":     {"atc": "C01BC03", "grupe": ["antiaritmik"], "acb": 0},
    "moksonidin":     {"atc": "C02AC05", "grupe": ["centralni_antihipertenziv"], "acb": 0},
    "metildopa":      {"atc": "C02AB01", "grupe": ["centralni_antihipertenziv", "beers_izbjegavati"], "acb": 0},
    "nitroglicerin":  {"atc": "C01DA02", "grupe": ["nitrat"], "acb": 0},
    "izosorbid mononitrat": {"atc": "C01DA14", "grupe": ["nitrat"], "acb": 0},

    # --- Antikoagulansi / antiagregansi ---
    "varfarin":       {"atc": "B01AA03", "grupe": ["antikoagulans", "varfarin"], "acb": 1},
    "acenokumarol":   {"atc": "B01AA07", "grupe": ["antikoagulans", "varfarin"], "acb": 0},
    "rivaroksaban":   {"atc": "B01AF01", "grupe": ["antikoagulans", "noak"], "acb": 0},
    "apiksaban":      {"atc": "B01AF02", "grupe": ["antikoagulans", "noak"], "acb": 0},
    "dabigatran":     {"atc": "B01AE07", "grupe": ["antikoagulans", "noak"], "acb": 0},
    "edoksaban":      {"atc": "B01AF03", "grupe": ["antikoagulans", "noak"], "acb": 0},
    "klopidogrel":    {"atc": "B01AC04", "grupe": ["antiagregans"], "acb": 0},
    "tikagrelor":     {"atc": "B01AC24", "grupe": ["antiagregans"], "acb": 0},

    # --- GI ---
    "pantoprazol":    {"atc": "A02BC02", "grupe": ["ppi"], "acb": 0},
    "omeprazol":      {"atc": "A02BC01", "grupe": ["ppi"], "acb": 0},
    "esomeprazol":    {"atc": "A02BC05", "grupe": ["ppi"], "acb": 0},
    "lansoprazol":    {"atc": "A02BC03", "grupe": ["ppi"], "acb": 0},
    "ranitidin":      {"atc": "A02BA02", "grupe": ["h2_blokator"], "acb": 1},
    "famotidin":      {"atc": "A02BA03", "grupe": ["h2_blokator"], "acb": 0},
    "metoklopramid":  {"atc": "A03FA01", "grupe": ["prokinetik", "beers_izbjegavati"], "acb": 0},
    "laktuloza":      {"atc": "A06AD11", "grupe": ["laksativ"], "acb": 0},
    "bisakodil":      {"atc": "A06AB02", "grupe": ["laksativ"], "acb": 0},
    "makrogol":       {"atc": "A06AD15", "grupe": ["laksativ"], "acb": 0},
    "butilskopolamin": {"atc": "A03BB01", "grupe": ["antiholinergik", "spazmolitik"], "acb": 1},

    # --- Endokrini / metabolički ---
    "metformin":      {"atc": "A10BA02", "grupe": ["metformin", "antidijabetik"], "acb": 0},
    "glibenklamid":   {"atc": "A10BB01", "grupe": ["sulfonilureja", "sulfonilureja_dugodjelujuca", "antidijabetik", "beers_izbjegavati"], "acb": 0},
    "glimepirid":     {"atc": "A10BB12", "grupe": ["sulfonilureja", "sulfonilureja_dugodjelujuca", "antidijabetik"], "acb": 0},
    "gliklazid":      {"atc": "A10BB09", "grupe": ["sulfonilureja", "antidijabetik"], "acb": 0},
    "sitagliptin":    {"atc": "A10BH01", "grupe": ["dpp4", "antidijabetik"], "acb": 0},
    "empagliflozin":  {"atc": "A10BK03", "grupe": ["sglt2", "antidijabetik"], "acb": 0},
    "dapagliflozin":  {"atc": "A10BK01", "grupe": ["sglt2", "antidijabetik"], "acb": 0},
    "inzulin":        {"atc": "A10A", "grupe": ["inzulin", "antidijabetik"], "acb": 0},
    "levotiroksin":   {"atc": "H03AA01", "grupe": ["tireoidni"], "acb": 0},
    "alendronat":     {"atc": "M05BA04", "grupe": ["bisfosfonat"], "acb": 0},
    "ibandronat":     {"atc": "M05BA06", "grupe": ["bisfosfonat"], "acb": 0},
    "zoledronska kiselina": {"atc": "M05BA08", "grupe": ["bisfosfonat"], "acb": 0},
    "denosumab":      {"atc": "M05BX04", "grupe": ["antiresorptiv"], "acb": 0},
    "holekalciferol": {"atc": "A11CC05", "grupe": ["vitamin_d"], "acb": 0},
    "kalcij":         {"atc": "A12AA", "grupe": ["kalcij"], "acb": 0},
    "alopurinol":     {"atc": "M04AA01", "grupe": ["urikostatik"], "acb": 0},
    "kolhicin":       {"atc": "M04AC01", "grupe": ["antigiht"], "acb": 0},
    "prednizon":      {"atc": "H02AB07", "grupe": ["kortikosteroid_sistemski"], "acb": 1},
    "prednizolon":    {"atc": "H02AB06", "grupe": ["kortikosteroid_sistemski"], "acb": 1},
    "metilprednizolon": {"atc": "H02AB04", "grupe": ["kortikosteroid_sistemski"], "acb": 0},
    "deksametazon":   {"atc": "H02AB02", "grupe": ["kortikosteroid_sistemski"], "acb": 0},
    "estradiol":      {"atc": "G03CA03", "grupe": ["estrogen"], "acb": 0},

    # --- Statini / lipidi ---
    "atorvastatin":   {"atc": "C10AA05", "grupe": ["statin"], "acb": 0},
    "rosuvastatin":   {"atc": "C10AA07", "grupe": ["statin"], "acb": 0},
    "simvastatin":    {"atc": "C10AA01", "grupe": ["statin"], "acb": 0},
    "fenofibrat":     {"atc": "C10AB05", "grupe": ["fibrat"], "acb": 0},
    "ezetimib":       {"atc": "C10AX09", "grupe": ["hipolipemik"], "acb": 0},

    # --- Neurologija ---
    "karbamazepin":   {"atc": "N03AF01", "grupe": ["antiepileptik", "hiponatremija_rizik"], "acb": 2},
    "valproat":       {"atc": "N03AG01", "grupe": ["antiepileptik"], "acb": 0},
    "lamotrigin":     {"atc": "N03AX09", "grupe": ["antiepileptik"], "acb": 0},
    "levetiracetam":  {"atc": "N03AX14", "grupe": ["antiepileptik"], "acb": 0},
    "gabapentin":     {"atc": "N03AX12", "grupe": ["gabapentinoid"], "acb": 0},
    "pregabalin":     {"atc": "N03AX16", "grupe": ["gabapentinoid"], "acb": 0},
    "levodopa":       {"atc": "N04BA", "grupe": ["antiparkinsonik"], "acb": 0},
    "pramipeksol":    {"atc": "N04BC05", "grupe": ["antiparkinsonik"], "acb": 0},
    "donepezil":      {"atc": "N06DA02", "grupe": ["antidementiv", "inhibitor_ache"], "acb": 0},
    "rivastigmin":    {"atc": "N06DA03", "grupe": ["antidementiv", "inhibitor_ache"], "acb": 0},
    "memantin":       {"atc": "N06DX01", "grupe": ["antidementiv"], "acb": 0},
    "betahistin":     {"atc": "N07CA01", "grupe": ["vertigo"], "acb": 0},
    "cinarizin":      {"atc": "N07CA02", "grupe": ["vertigo", "beers_izbjegavati"], "acb": 1},

    # --- Respiratorni ---
    "teofilin":       {"atc": "R03DA04", "grupe": ["teofilin"], "acb": 1},
    "salbutamol":     {"atc": "R03AC02", "grupe": ["saba", "inhalacioni"], "acb": 0},
    "salmeterol":     {"atc": "R03AC12", "grupe": ["laba", "inhalacioni"], "acb": 0},
    "formoterol":     {"atc": "R03AC13", "grupe": ["laba", "inhalacioni"], "acb": 0},
    "tiotropij":      {"atc": "R03BB04", "grupe": ["lama", "inhalacioni"], "acb": 0},
    "budezonid":      {"atc": "R03BA02", "grupe": ["iks", "inhalacioni"], "acb": 0},
    "flutikazon":     {"atc": "R03BA05", "grupe": ["iks", "inhalacioni"], "acb": 0},
    "montelukast":    {"atc": "R03DC03", "grupe": ["antileukotrien"], "acb": 0},

    # --- Antibiotici (relevantni za kriterije) ---
    "nitrofurantoin": {"atc": "J01XE01", "grupe": ["nitrofurantoin"], "acb": 0},
    "ciprofloksacin": {"atc": "J01MA02", "grupe": ["hinolon", "qt_rizik"], "acb": 0},
    "azitromicin":    {"atc": "J01FA10", "grupe": ["makrolid", "qt_rizik"], "acb": 0},
    "trimetoprim-sulfametoksazol": {"atc": "J01EE01", "grupe": ["sulfonamid", "hiperkalemija_rizik"], "acb": 0},
}


def nadji_lijek(ime: str) -> dict | None:
    """Pronalazi lijek po INN-u (neosjetljivo na velika/mala slova)."""
    return RJECNIK_LIJEKOVA.get(ime.strip().lower())


SVI_INN = sorted(RJECNIK_LIJEKOVA.keys())
