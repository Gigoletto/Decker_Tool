import html
import json
import re
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent
BANANA = "#FFE135"
FARBE_PROGRAMME = "#FF2DAA"
FARBE_MODULE = "#03D8F3"
FARBE_VORTEILE = "#00FF9F"
FARBE_GERAETE = "#FF8A3D"

CSV_FILES = {
    "Cyberdecks": "Cyberdecks.CSV",
    "Cyberware / Bioware": "Cyberware_Bioware.CSV",
    "Ger\u00e4temodifikationen": "Ger\u00e4temodifikationen.CSV",
    "Matrixhandlungen": "Matrixhandlungen.CSV",
    "Module": "Module.CSV",
    "Programme": "Programme.CSV",
    "Vorteile": "Vorteile.CSV",
}

PAGE_DECK = "Deck-Konfiguration"
PAGE_MODS = "Charakter-Mods"
PAGE_DASHBOARD = "Aktions-Dashboard"
ANSICHTEN = [PAGE_DECK, PAGE_MODS, PAGE_DASHBOARD, *CSV_FILES.keys()]

CHARAKTERWERTE = {
    "attr_konstitution": ("Konstitution", 3, 1, 20),
    "attr_reaktion": ("Reaktion", 3, 1, 20),
    "attr_intuition": ("Intuition", 3, 1, 20),
    "attr_logik": ("Logik", 3, 1, 20),
    "attr_willenskraft": ("Willenskraft", 3, 1, 20),
}

MATRIX_FERTIGKEITEN = {
    "skill_computernutzung": ("Computer", 0, 0, 25),
    "skill_elektronische_kriegfuehrung": ("Elektronische Kriegsf\u00fchrung", 0, 0, 25),
    "skill_hacking": ("Hacking", 0, 0, 25),
    "skill_hardware": ("Hardware", 0, 0, 25),
    "skill_matrixkampf": ("Matrixkampf", 0, 0, 25),
    "skill_software": ("Software", 0, 0, 25),
}

# Frühere Schlüsselnamen aus gespeicherten Profilen auf die aktuellen abbilden.
LEGACY_WERT_KEYS = {
    "skill_cyberkampf": "skill_hardware",
    "skill_matrixbau": "skill_matrixkampf",
}

ASDF_ATTRIBUTE = ("Angriff", "Schleicher", "Datenverarbeitung", "Firewall")
GEISTIGE_ATTRIBUTE = ("Logik", "Intuition", "Willenskraft")
KOERPER_ATTRIBUTE = ("Konstitution", "Reaktion")
ALLE_ATTRIBUTE = GEISTIGE_ATTRIBUTE + ASDF_ATTRIBUTE + KOERPER_ATTRIBUTE
ASDF_SELECT_PREFIX = "asdf_select_"
ASDF_HAND_MOD_MIN = -10
ASDF_HAND_MOD_MAX = 10
SAVE_PREFIX = "_save_"
DECK_LISTEN_KEYS = (
    "selected_programme",
    "selected_module",
    "selected_vorteile",
    "selected_cyberware",
    "selected_geraetemods",
)
PROGRAMM_FUNKTION_PREFIX = "selected_programme_fn_"
PROGRAMM_FUNKTION_SONSTIGE = "Sonstige"
PROGRAMM_FUNKTION_REIHENFOLGE = (
    "Deck-Limits",
    "Offensiv & Kampf",
    "Defensiv & Schutz",
    "Heimlichkeit & Infiltration",
    "Hilfsprogramme & System",
)
DECK_WERT_KEYS = ("selected_deck", "uebertakter_attr", "aufmerksamkeit_bonus", "programmiergenie_handlung", "agent_stufe", "verschleiern_stufe")
SCHADEN_KEYS = ("schaden_matrix", "schaden_geistig", "schaden_koerperlich", "schaden_haerte")
HAERTE_MONITOR = 5
INIT_KEYS = ("initiative_wert_mod", "initiative_wuerfel_mod")
SIM_MODI = ("AR", "Kalter SIM", "Hei\u00dfer SIM")
SIM_DEFAULT = "AR"
BOOSTERWOLKE_STUFEN = ("0", "E", "K")
BOOSTERWOLKE_BONUS = {"0": 0, "E": 1, "K": 2}
BOOSTERWOLKE_PREFIX = "boosterwolke_"
ETAC_MODI = ("Ohne", "Team", "Leader")
ETAC_DEFAULT = "Ohne"
ETAC_BUDGET = {"Ohne": 0, "Team": 2, "Leader": 3}
AGENT_STUFE_MIN = 1
AGENT_STUFE_MAX = 6
AGENT_STUFE_DEFAULT = 1
VERSCHLEIERN_MIN = 1
VERSCHLEIERN_MAX = 5
VERSCHLEIERN_DEFAULT = 1
AUFMERKSAMKEIT_OPTIONEN = ("+1", "+2")
AUFMERKSAMKEIT_DEFAULT = "+1"
ANALYTISCHER_GEIST_HANDLUNGEN = (
    "Datei cracken",
    "Datei editieren",
    "Datenbombe legen",
    "Zielerfassung erkennen",
)
PROGRAMMIERGENIE_DEFAULT = "Eiliges Hacken"
PROGRAMMIERGENIE_HANDLUNGEN = (
    "Abschneiden",
    "Ausst\u00f6pseln",
    "Befehl vort\u00e4uschen",
    "Brute Force",
    "Datei cracken",
    "Datei editieren",
    "Datenbombe entsch\u00e4rfen",
    "Datenbombe legen",
    "Datenspike",
    "Dienstverweigerung",
    "Digitalverteidigung",
    "Eiliges Hacken",
    "Ersticken",
    "Ger\u00e4t formatieren",
    "Ger\u00e4t markieren",
    "Ger\u00e4t neu starten",
    "Ger\u00e4t steuern",
    "Icon aufsp\u00fcren / Datei aufsp\u00fcren",
    "In ein Ger\u00e4t springen",
    "Infrastruktur Unterwandern",
    "Intervention",
    "Kalibrierung",
    "Marke l\u00f6schen",
    "Maskerade",
    "Matrixsuche",
    "Matrixwahrnehmung",
    "Overwatch-Wert bestimmen",
    "Pilotprogramm verwirren",
    "Pop-up",
    "Programm abst\u00fcrzen lassen",
    "Rauschen unterdr\u00fccken",
    "Signal st\u00f6ren",
    "Stalking",
    "Taggen",
    "\u00dcbertragung abfangen",
    "Verstecken",
    "Zielerfassung absch\u00fctteln",
    "Zielerfassung erkennen",
)
LEERE_NAMEN = {"", "nan", "none", "nat", "<na>", "null"}

ATTR_LOOKUP = {
    "angriff": "Angriff",
    "schleicher": "Schleicher",
    "datenverarbeitung": "Datenverarbeitung",
    "firewall": "Firewall",
    "firewallattribut": "Firewall",
    "logik": "Logik",
    "intuition": "Intuition",
    "willenskraft": "Willenskraft",
    "konstitution": "Konstitution",
    "reaktion": "Reaktion",
}

SKILL_LOOKUP = {
    "hacking": "skill_hacking",
    "computer": "skill_computernutzung",
    "computernutzung": "skill_computernutzung",
    "hardware": "skill_hardware",
    "cyberkampf": "skill_matrixkampf",
    "matrixkampf": "skill_matrixkampf",
    "matrixbau": "skill_matrixkampf",
    "elektronischekriegsfuehrung": "skill_elektronische_kriegfuehrung",
    "elektronischekriegsfuhrung": "skill_elektronische_kriegfuehrung",
    "software": "skill_software",
}

SITUATIONAL_MARKERS = (
    "wenn",
    "bei der handlung",
    "fuer alle",
    "fur alle",
)

WURFELPOOL_MARKERS = ("wurfelpool", "wuerfelpool", "w\u00fcrfelpool")

THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&family=Share+Tech+Mono&display=swap');

html, body, [data-testid="stAppViewContainer"] {
  background: #07070A;
}

.stApp {
  background:
    radial-gradient(900px 420px at 8% -8%, rgba(255, 225, 53, 0.10), transparent 55%),
    radial-gradient(700px 380px at 100% 0%, rgba(0, 229, 255, 0.05), transparent 45%),
    linear-gradient(180deg, #0b0b10 0%, #07070A 42%, #050508 100%) !important;
  color: #EDE6C8;
}

.stApp::before {
  content: "";
  pointer-events: none;
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: repeating-linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0.018) 0px,
    rgba(255, 255, 255, 0.018) 1px,
    transparent 1px,
    transparent 4px
  );
}

.stApp::after {
  content: "";
  pointer-events: none;
  position: fixed;
  inset: 0;
  z-index: 0;
  background-image:
    linear-gradient(rgba(255, 225, 53, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 225, 53, 0.035) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse at center, black 35%, transparent 80%);
}

section.main > div {
  position: relative;
  z-index: 1;
}

h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
  font-family: "Orbitron", sans-serif !important;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #FFE135 !important;
  text-shadow: 0 0 12px rgba(255, 225, 53, 0.35);
}

p, label, span, div, .stMarkdown, .stCaption {
  font-family: "Rajdhani", sans-serif;
}

[data-testid="stSidebar"] .stButton {
  margin-bottom: 0.4rem;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
  font-size: 0.92rem !important;
  color: #FFE135 !important;
}

[data-testid="stHeader"] {
  background: transparent !important;
}

[data-testid="stMetric"] {
  background: linear-gradient(180deg, rgba(255, 225, 53, 0.08), rgba(18, 18, 26, 0.92));
  border: 1px solid #FFE135;
  border-radius: 4px;
  padding: 0.85rem 0.9rem;
  box-shadow:
    0 0 0 1px rgba(255, 225, 53, 0.15) inset,
    0 0 18px rgba(255, 225, 53, 0.18);
  position: relative;
}

[data-testid="stMetric"]::before,
[data-testid="stMetric"]::after {
  content: "";
  position: absolute;
  width: 10px;
  height: 10px;
  border: 1px solid #FFE135;
}
[data-testid="stMetric"]::before { top: -1px; left: -1px; border-right: 0; border-bottom: 0; }
[data-testid="stHtml"] {
  display: none !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}

[data-testid="stMetric"]::after { bottom: -1px; right: -1px; border-left: 0; border-top: 0; }

[data-testid="stMetricLabel"] {
  font-family: "Share Tech Mono", monospace !important;
  color: #FFE135 !important;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

[data-testid="stMetricValue"] {
  font-family: "Orbitron", sans-serif !important;
  color: #FFE135 !important;
  text-shadow: 0 0 16px rgba(255, 225, 53, 0.55);
  font-weight: 700 !important;
}

[data-testid="stMetricDelta"] {
  font-family: "Share Tech Mono", monospace !important;
}

.sr-asdf-final {
  font-family: "Rajdhani", sans-serif;
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.55rem;
  letter-spacing: 0;
  color: #FFE135;
  margin: 0;
  padding: 0 0.35rem 0 0.5rem;
  border: 0;
  background: transparent;
  display: flex;
  align-items: center;
  height: 1.55rem;
}
.sr-asdf-final-label,
.sr-asdf-final-value {
  font-family: inherit;
  font-size: inherit;
  font-weight: inherit;
  line-height: inherit;
  letter-spacing: inherit;
  color: inherit;
  text-shadow: none;
  display: inline;
}
[data-testid="stColumn"] [data-testid="stHorizontalBlock"]:has(.sr-asdf-final) {
  border: 1px solid #FFE135;
  background: linear-gradient(180deg, rgba(255, 225, 53, 0.08), rgba(18, 18, 26, 0.92));
  box-shadow: 0 0 8px rgba(255, 225, 53, 0.12);
  padding: 0.1rem 0.12rem 0.1rem 0;
  margin-top: 0.2rem;
  align-items: center !important;
}
[data-testid="stColumn"] [data-testid="stHorizontalBlock"]:has(.sr-asdf-final) [data-testid="stColumn"]:has(.sr-asdf-final),
[data-testid="stColumn"] [data-testid="stHorizontalBlock"]:has(.sr-asdf-final) [data-testid="stColumn"]:has(.sr-asdf-final) > div,
[data-testid="stColumn"] [data-testid="stHorizontalBlock"]:has(.sr-asdf-final) [data-testid="stColumn"]:has(.sr-asdf-final) [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stColumn"] [data-testid="stHorizontalBlock"]:has(.sr-asdf-final) [data-testid="stColumn"]:has(.sr-asdf-final) [data-testid="stVerticalBlock"],
[data-testid="stColumn"] [data-testid="stHorizontalBlock"]:has(.sr-asdf-final) [data-testid="stColumn"]:has(.sr-asdf-final) [data-testid="stElementContainer"],
[data-testid="stColumn"] [data-testid="stHorizontalBlock"]:has(.sr-asdf-final) [data-testid="stColumn"]:has(.sr-asdf-final) [data-testid="stMarkdown"],
[data-testid="stColumn"] [data-testid="stHorizontalBlock"]:has(.sr-asdf-final) [data-testid="stColumn"]:has(.sr-asdf-final) [data-testid="stMarkdownContainer"] {
  height: auto !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}
[data-testid="stColumn"] [data-testid="stHorizontalBlock"]:has(.sr-asdf-final) [data-testid="stColumn"]:has(.sr-asdf-final) p {
  margin: 0 !important;
  padding: 0 !important;
  line-height: 1 !important;
  width: 100%;
}
[data-testid="stColumn"] [data-testid="stHorizontalBlock"]:has(.sr-asdf-final) [data-testid="stButton"] {
  min-width: 0;
  margin: 0 !important;
  display: flex;
  align-items: center;
}
[data-testid="stColumn"] [data-testid="stHorizontalBlock"]:has(.sr-asdf-final) button {
  min-height: 1.55rem !important;
  height: 1.55rem !important;
  padding: 0 0.42rem !important;
  font-size: 0.95rem !important;
  line-height: 1 !important;
  letter-spacing: 0 !important;
}
div[data-testid="stMarkdown"]:has(.sr-asdf-final) {
  margin-top: 0 !important;
  margin-bottom: 0 !important;
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
.stTextInput > div > div,
.stNumberInput > div > div,
.stMultiSelect > div > div {
  background-color: #101018 !important;
  border: 1px solid rgba(255, 225, 53, 0.45) !important;
  border-radius: 2px !important;
}

.stButton > button, .stDownloadButton > button {
  font-family: "Orbitron", sans-serif !important;
  letter-spacing: 0.08em;
  font-weight: 700 !important;
  text-transform: uppercase;
  border-radius: 2px !important;
}
.stButton > button[data-testid="stBaseButton-secondary"] {
  background: transparent !important;
  color: #FFE135 !important;
  border: 1px solid rgba(255, 225, 53, 0.55) !important;
}
.stButton > button[data-testid="stBaseButton-primary"],
.stDownloadButton > button {
  background: #FFE135 !important;
  color: #14120a !important;
  border: 0 !important;
}

hr, [data-testid="stDecorator"] {
  border-color: rgba(255, 225, 53, 0.28) !important;
}

[data-testid="stExpander"] {
  border: 1px solid rgba(255, 225, 53, 0.35) !important;
  background: rgba(16, 16, 24, 0.8) !important;
}

.sr-header {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 1.5rem;
  margin: 0 0 1.6rem 0;
  padding: 1.1rem 1.25rem 1.2rem 1.15rem;
  background:
    linear-gradient(90deg, rgba(255, 225, 53, 0.10), rgba(7, 7, 10, 0.15) 42%, rgba(0, 229, 255, 0.05)),
    #0c0c12;
  border: 1px solid #FFE135;
  box-shadow:
    0 0 0 1px rgba(255, 225, 53, 0.12) inset,
    0 0 28px rgba(255, 225, 53, 0.16);
  position: relative;
  overflow: hidden;
}
.sr-header::before {
  content: "";
  position: absolute;
  inset: 8px auto 8px 8px;
  width: 3px;
  background: #FFE135;
  box-shadow: 0 0 12px #FFE135;
}
.sr-brand {
  display: flex;
  align-items: center;
  gap: 1.15rem;
  min-width: 0;
}
.sr-mark {
  width: 92px;
  height: 92px;
  flex: 0 0 92px;
  clip-path: polygon(25% 4%, 75% 4%, 98% 50%, 75% 96%, 25% 96%, 2% 50%);
  background: #07070A;
  border: 2px solid #FFE135;
  box-shadow: 0 0 22px rgba(255, 225, 53, 0.45), inset 0 0 18px rgba(255, 225, 53, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: "Orbitron", sans-serif;
  font-size: 3.4rem;
  font-weight: 900;
  color: #FFE135;
  text-shadow:
    2px 0 #00e5ff,
    -2px 0 #ff2a6d,
    0 0 18px rgba(255, 225, 53, 0.8);
}
.sr-wordmark {
  min-width: 0;
}
.sr-kicker {
  font-family: "Share Tech Mono", monospace;
  color: #FFE135;
  letter-spacing: 0.42em;
  font-size: 0.72rem;
  margin-bottom: 0.15rem;
  opacity: 0.9;
}
.sr-title {
  font-family: "Orbitron", sans-serif;
  font-weight: 900;
  font-size: clamp(1.8rem, 4.6vw, 3.35rem);
  line-height: 0.92;
  letter-spacing: 0.16em;
  color: #FFE135;
  text-transform: uppercase;
  text-shadow:
    0 0 18px rgba(255, 225, 53, 0.45),
    3px 0 0 rgba(0, 229, 255, 0.35),
    -3px 0 0 rgba(255, 42, 109, 0.28);
}
.sr-sub {
  margin-top: 0.35rem;
  font-family: "Share Tech Mono", monospace;
  font-size: 0.92rem;
  letter-spacing: 0.28em;
  color: #cfc7a1;
  text-transform: uppercase;
}
.sr-status {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-end;
  gap: 0.35rem;
  font-family: "Share Tech Mono", monospace;
  color: #FFE135;
  letter-spacing: 0.16em;
  font-size: 0.78rem;
  text-transform: uppercase;
  white-space: nowrap;
}
.sr-status strong {
  color: #FFE135;
  text-shadow: 0 0 10px rgba(255, 225, 53, 0.6);
}
.sr-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #FFE135;
  box-shadow: 0 0 10px #FFE135;
  display: inline-block;
  margin-right: 0.45rem;
  animation: sr-pulse 1.8s ease-in-out infinite;
}
@keyframes sr-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}
@media (max-width: 900px) {
  .sr-header { flex-direction: column; }
  .sr-status { align-items: flex-start; }
  .sr-mark { width: 72px; height: 72px; flex-basis: 72px; font-size: 2.6rem; }
}
.sr-action {
  font-family: "Rajdhani", sans-serif;
  font-size: 0.95rem;
  line-height: 1.3;
  color: #FFE135;
  padding: 0;
  margin: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
}
[data-testid="stColumn"]:has(.sr-action-card) {
  font-family: "Rajdhani", sans-serif;
  color: #FFE135;
  box-sizing: border-box !important;
  overflow: visible !important;
  height: auto !important;
  min-height: 0 !important;
  align-self: start;
  padding: 0.55rem 0.7rem 0.7rem 0.7rem !important;
  margin: 0 0 0.65rem 0;
  border: 1px solid #FFE135 !important;
  background: linear-gradient(180deg, rgba(255, 225, 53, 0.07), rgba(10, 10, 16, 0.94)) !important;
  box-shadow: 0 0 12px rgba(255, 225, 53, 0.12);
}
[data-testid="stColumn"]:has(.sr-action-card) [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stColumn"]:has(.sr-action-card) [data-testid="stVerticalBlock"],
[data-testid="stColumn"]:has(.sr-action-card) [data-testid="stElementContainer"],
[data-testid="stColumn"]:has(.sr-action-card) [data-testid="stHorizontalBlock"] {
  height: auto !important;
  min-height: 0 !important;
  overflow: visible !important;
}
[data-testid="stColumn"]:has(.sr-action-card) > div {
  height: auto !important;
  overflow: visible !important;
}
[data-testid="stColumn"]:has(.sr-action-card) > [data-testid="stVerticalBlockBorderWrapper"] {
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
}
[data-testid="stColumn"]:has(.sr-action-card) [data-testid="stSlider"] {
  margin: 0 0 0.15rem 0;
  padding: 0;
  overflow: hidden;
}
[data-testid="stColumn"]:has(.sr-action-card) [data-testid="stSlider"] > label {
  font-family: "Rajdhani", sans-serif !important;
  font-size: 0.85rem !important;
  font-weight: 600 !important;
  color: #FFE135 !important;
  margin-bottom: 0 !important;
}
[data-testid="stColumn"]:has(.sr-action-card) [data-testid="stSlider"] [data-baseweb="slider"] {
  margin-top: 0.1rem;
  margin-bottom: 0;
  padding-bottom: 0 !important;
}
[data-testid="stColumn"]:has(.sr-action-card) [data-testid="stSlider"] [role="slider"] {
  width: 12px !important;
  height: 12px !important;
}
[data-testid="stColumn"]:has(.sr-action-card) [data-testid="stSliderTickBar"] {
  display: none !important;
}
.sr-action-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.75rem;
  margin-bottom: 0.4rem;
}
.sr-action-head strong {
  font-family: "Orbitron", sans-serif;
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #FFE135;
}
.sr-action-head span,
.sr-action-value,
.sr-action-text,
.sr-action-label {
  font-size: 0.95rem;
  font-weight: 600;
  color: #FFE135;
  text-shadow: none;
  opacity: 1;
  -webkit-font-smoothing: auto;
}
.sr-action-stats,
.sr-action-attrs {
  display: grid;
  gap: 0.45rem 0.7rem;
}
.sr-action-stats {
  grid-template-columns: 1fr 1fr 1fr;
  margin-bottom: 0.4rem;
}
.sr-action-attrs {
  grid-template-columns: 1fr 1fr minmax(5.5rem, 22%);
  border-top: 1px solid rgba(255, 225, 53, 0.28);
  padding-top: 0.4rem;
  align-items: start;
}
.sr-booster-label {
  font-family: "Rajdhani", sans-serif;
  font-size: 0.85rem;
  font-weight: 600;
  color: #FFE135;
  margin: 0 0 0.1rem 0;
}
.sr-action-attrs-line {
  border-top: 1px solid rgba(255, 225, 53, 0.28);
  margin: 0.3rem 0 0.25rem 0;
}
.sr-action-label {
  font-family: "Rajdhani", sans-serif;
  letter-spacing: 0;
  display: block;
  font-weight: 600;
}
.sr-action-value,
.sr-action-text {
  font-family: "Rajdhani", sans-serif;
  display: block;
}
.sr-action-number {
  font-size: 1.2rem;
  font-weight: 700;
  line-height: 1.15;
}
.sr-action-foot {
  margin-top: 0.3rem;
  padding-bottom: 0.15rem;
}
.sr-action details,
.sr-action-foot details {
  margin-top: 0.15rem;
  border-top: 1px solid rgba(255, 225, 53, 0.18);
  padding-top: 0.3rem;
}
.sr-action summary,
.sr-action-foot summary {
  cursor: pointer;
  font-family: "Rajdhani", sans-serif;
  font-size: 0.95rem;
  font-weight: 600;
  color: #FFE135;
  text-shadow: none;
}
.sr-action details p,
.sr-action-foot details p {
  margin: 0.35rem 0 0 0;
  color: #EDE6C8;
  font-size: 0.95rem;
}
.sr-action-malus {
  margin-top: 0.4rem;
  padding: 0.2rem 0.45rem;
  display: inline-block;
  font-family: "Share Tech Mono", monospace;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #FF4D4D;
  border: 1px solid rgba(255, 77, 77, 0.7);
  background: rgba(255, 77, 77, 0.12);
}
div[data-testid="stVerticalBlock"]:has(> div .sr-schaden-anchor) {
  position: sticky;
  top: 0;
  z-index: 80;
  background: #07070A;
  padding: 0.15rem 0 0.55rem 0;
  margin-bottom: 0.4rem;
  box-shadow: 0 12px 18px rgba(7, 7, 10, 0.92);
}
.sr-schaden-panel {
  font-family: "Rajdhani", sans-serif;
  border: 1px solid #FFE135;
  background: linear-gradient(180deg, rgba(255, 225, 53, 0.10), rgba(10, 10, 16, 0.96));
  box-shadow: 0 0 18px rgba(255, 225, 53, 0.16);
  padding: 0.7rem 0.9rem 0.55rem 0.9rem;
}
.sr-schaden-panel strong {
  font-family: "Orbitron", sans-serif;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #FFE135;
}
.sr-kampf-box {
  font-family: "Rajdhani", sans-serif;
  border: 1px solid #FFE135;
  background: linear-gradient(180deg, rgba(255, 225, 53, 0.10), rgba(10, 10, 16, 0.96));
  box-shadow: 0 0 18px rgba(255, 225, 53, 0.16);
  padding: 0.7rem 0.9rem 0.85rem 0.9rem;
  margin: 0 0 0.85rem 0;
}
.sr-kampf-box strong {
  font-family: "Orbitron", sans-serif;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #FFE135;
}
.sr-kampf-value {
  font-family: "Orbitron", sans-serif;
  font-size: 1.45rem;
  font-weight: 700;
  color: #FFE135;
  text-shadow: 0 0 14px rgba(255, 225, 53, 0.45);
  margin: 0.2rem 0 0.15rem 0;
}
.sr-kampf-line {
  font-family: "Rajdhani", sans-serif;
  font-size: 1.05rem;
  font-weight: 600;
  color: #FFE135;
  margin: 0.15rem 0;
}
.sr-kampf-formel {
  font-family: "Share Tech Mono", monospace;
  font-size: 0.78rem;
  letter-spacing: 0.04em;
  color: #EDE6C8;
  margin: 0.15rem 0 0 0;
  opacity: 0.9;
}
.sr-kampf-sub {
  margin-top: 0.75rem;
  padding-top: 0.55rem;
  border-top: 1px solid rgba(255, 225, 53, 0.28);
}
div[data-testid="stMarkdown"]:has(.sr-action),
div[data-testid="stMarkdown"]:has(.sr-action-card) {
  margin-bottom: 0 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
  border: 1px solid #FFE135 !important;
  background: linear-gradient(180deg, rgba(255, 225, 53, 0.07), rgba(10, 10, 16, 0.94)) !important;
  box-shadow: 0 0 16px rgba(255, 225, 53, 0.14);
}
.sr-pick-label {
  font-family: "Orbitron", sans-serif;
  font-size: 0.92rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  display: block;
  margin: 0 0 0.35rem 0;
}
[class*="st-key-selected_programme"] [data-baseweb="select"] > div,
[class*="st-key-selected_programme"] [data-baseweb="input"] > div {
  border-color: #FF2DAA !important;
  box-shadow: 0 0 10px rgba(255, 45, 170, 0.25);
}
.st-key-selected_module [data-baseweb="select"] > div,
.st-key-selected_module [data-baseweb="input"] > div {
  border-color: #03D8F3 !important;
  box-shadow: 0 0 10px rgba(3, 216, 243, 0.25);
}
.st-key-selected_vorteile [data-baseweb="select"] > div,
.st-key-selected_vorteile [data-baseweb="input"] > div {
  border-color: #00FF9F !important;
  box-shadow: 0 0 10px rgba(0, 255, 159, 0.25);
}
.st-key-selected_geraetemods [data-baseweb="select"] > div,
.st-key-selected_geraetemods [data-baseweb="input"] > div {
  border-color: #FF8A3D !important;
  box-shadow: 0 0 10px rgba(255, 138, 61, 0.25);
}
.st-key-selected_geraetemods [data-tag],
.st-key-selected_geraetemods [data-testid="stMultiSelectTagsContainer"] [data-tag] {
  background: #FF8A3D !important;
  background-color: #FF8A3D !important;
  color: #0a0a10 !important;
}
.st-key-selected_geraetemods [data-tag] span,
.st-key-selected_geraetemods [data-tag] button {
  color: #0a0a10 !important;
}
.st-key-selected_geraetemods [data-tag] svg {
  fill: #0a0a10 !important;
  color: #0a0a10 !important;
}
[class*="st-key-selected_programme"] [data-tag],
[class*="st-key-selected_programme"] [data-testid="stMultiSelectTagsContainer"] [data-tag] {
  background: #FF2DAA !important;
  background-color: #FF2DAA !important;
  color: #14120a !important;
}
.st-key-selected_module [data-tag],
.st-key-selected_module [data-testid="stMultiSelectTagsContainer"] [data-tag] {
  background: #03D8F3 !important;
  background-color: #03D8F3 !important;
  color: #0a0a10 !important;
}
.st-key-selected_vorteile [data-tag],
.st-key-selected_vorteile [data-testid="stMultiSelectTagsContainer"] [data-tag] {
  background: #00FF9F !important;
  background-color: #00FF9F !important;
  color: #0a0a10 !important;
}
[class*="st-key-selected_programme"] [data-tag] span,
[class*="st-key-selected_programme"] [data-tag] button,
.st-key-selected_module [data-tag] span,
.st-key-selected_module [data-tag] button,
.st-key-selected_vorteile [data-tag] span,
.st-key-selected_vorteile [data-tag] button {
  color: #0a0a10 !important;
}
[class*="st-key-selected_programme"] [data-tag] svg,
.st-key-selected_module [data-tag] svg,
.st-key-selected_vorteile [data-tag] svg {
  fill: #0a0a10 !important;
  color: #0a0a10 !important;
}
.sr-hint {
  font-family: "Rajdhani", sans-serif;
  font-size: 0.98rem;
  line-height: 1.45;
  padding: 0.8rem 1rem;
  margin: 0.6rem 0 1rem 0;
  border: 1px solid;
  background: rgba(0, 0, 0, 0.35);
}
.sr-hint p { margin: 0 0 0.65rem 0; }
.sr-hint p:last-child { margin-bottom: 0; }
.sr-hint-programme { color: #FF2DAA; border-color: #FF2DAA; background: rgba(255, 45, 170, 0.08); }
.sr-hint-module { color: #03D8F3; border-color: #03D8F3; background: rgba(3, 216, 243, 0.08); }
.sr-hint-vorteile { color: #00FF9F; border-color: #00FF9F; background: rgba(0, 255, 159, 0.08); }
.sr-hint-geraete { color: #FF8A3D; border-color: #FF8A3D; background: rgba(255, 138, 61, 0.08); }
.sr-cap-programme { color: #FF2DAA !important; }
.sr-cap-module { color: #03D8F3 !important; }
.sr-cap-vorteile { color: #00FF9F !important; }
.sr-cap-geraete { color: #FF8A3D !important; }
.sr-agent-box {
  font-family: "Rajdhani", sans-serif;
  font-size: 0.92rem;
  font-weight: 600;
  color: #FFE135;
  line-height: 1.35;
}
.sr-agent-box p {
  margin: 0.15rem 0;
}
.sr-agent-box strong {
  font-family: "Rajdhani", sans-serif;
  font-weight: 700;
  color: #FF2DAA;
}
"""

HEADER_HTML = (
    '<div class="sr-header">'
    '<div class="sr-brand">'
    '<div class="sr-mark">5</div>'
    '<div class="sr-wordmark">'
    '<div class="sr-kicker">// SIXTH WORLD ACCESS NODE</div>'
    '<div class="sr-title">SHADOWRUN</div>'
    '<div class="sr-sub">Decker-Konsole // JACK IN // ASDF ONLINE</div>'
    "</div></div>"
    '<div class="sr-status">'
    '<div><span class="sr-dot"></span>MATRIX LINK STABLE</div>'
    f"<div>SIGNAL <strong>BANANA</strong> // {BANANA}</div>"
    "<div>USER // DECKER</div>"
    "</div></div>"
)


@st.cache_data
def load_csv(filename: str, mtime: float = 0.0) -> pd.DataFrame | None:
    path = DATA_DIR / filename
    _cache_bust = mtime
    # cp1252 zuerst: die Tabellen enthalten typografische Zeichen (\u201e \u201c \u2013 \u2026),
    # die latin-1 in unsichtbare Steuerzeichen verwandeln w\u00fcrde.
    for encoding in ("cp1252", "utf-8", "latin-1"):
        try:
            return pd.read_csv(path, sep=";", encoding=encoding)
        except FileNotFoundError:
            return None
        except UnicodeDecodeError:
            continue
    return None


def csv_mtime(filename: str) -> float:
    path = DATA_DIR / filename
    return path.stat().st_mtime if path.exists() else 0.0


def load_all_tables() -> dict[str, pd.DataFrame | None]:
    tables: dict[str, pd.DataFrame | None] = {}
    for name, filename in CSV_FILES.items():
        dataframe = load_csv(filename, csv_mtime(filename))
        if dataframe is None:
            st.error(f"Datei nicht gefunden: {filename}")
        tables[name] = dataframe
    return tables


def save_key(key: str) -> str:
    return f"{SAVE_PREFIX}{key}"


def state_kopie(value: object) -> object:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def snapshot_key(key: str) -> None:
    if key in st.session_state:
        st.session_state[save_key(key)] = state_kopie(st.session_state[key])


def restore_key(key: str) -> None:
    gespeichert = save_key(key)
    if gespeichert in st.session_state:
        st.session_state[key] = state_kopie(st.session_state[gespeichert])


def snapshot_deck_auswahl() -> None:
    for key in (*DECK_LISTEN_KEYS, *DECK_WERT_KEYS, *SCHADEN_KEYS, *INIT_KEYS):
        snapshot_key(key)
    snapshot_key("asdf")
    snapshot_key("deck_array")
    for attr in ASDF_ATTRIBUTE:
        snapshot_key(f"{ASDF_SELECT_PREFIX}{attr}")


def restore_deck_auswahl() -> None:
    for key in (*DECK_LISTEN_KEYS, *DECK_WERT_KEYS, *SCHADEN_KEYS, *INIT_KEYS):
        restore_key(key)
    restore_key("asdf")
    restore_key("deck_array")
    gespeichertes_asdf = st.session_state.get(save_key("asdf"))
    if isinstance(gespeichertes_asdf, dict):
        st.session_state.asdf = {
            attr: gespeichertes_asdf.get(attr) for attr in ASDF_ATTRIBUTE
        }
    for attr in ASDF_ATTRIBUTE:
        widget_key = f"{ASDF_SELECT_PREFIX}{attr}"
        wert = (st.session_state.get("asdf") or {}).get(attr)
        if wert is not None:
            st.session_state[widget_key] = wert
            st.session_state[save_key(widget_key)] = wert
        else:
            restore_key(widget_key)


def on_liste_change(key: str) -> None:
    snapshot_key(key)
    snapshot_deck_auswahl()


def reset_programm_gruppen_widgets() -> None:
    for key in list(st.session_state.keys()):
        if isinstance(key, str) and (
            key.startswith(PROGRAMM_FUNKTION_PREFIX)
            or key.startswith(SAVE_PREFIX + PROGRAMM_FUNKTION_PREFIX)
        ):
            del st.session_state[key]


def reset_boosterwolke_widgets() -> None:
    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith(BOOSTERWOLKE_PREFIX):
            del st.session_state[key]


def programm_funktion_key(funktion: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", normalize(funktion)).strip("_")
    return f"{PROGRAMM_FUNKTION_PREFIX}{slug or 'sonstige'}"


def on_programme_gruppen_change() -> None:
    merged: list[str] = []
    gesehen: set[str] = set()
    for key in st.session_state.get("_programm_gruppen_keys", []):
        for name in namen_liste(st.session_state.get(key, [])):
            if name not in gesehen:
                gesehen.add(name)
                merged.append(name)
    st.session_state["selected_programme"] = merged
    snapshot_key("selected_programme")
    snapshot_deck_auswahl()


def liste_aus_state(key: str) -> list[str]:
    wert = st.session_state.get(key)
    if wert is None:
        wert = st.session_state.get(save_key(key), [])
    return namen_liste(wert)


def init_session_state() -> None:
    for key, (_label, default, _min_value, _max_value) in {
        **CHARAKTERWERTE,
        **MATRIX_FERTIGKEITEN,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default
    if "asdf" not in st.session_state:
        st.session_state.asdf = {attr: None for attr in ASDF_ATTRIBUTE}
    if "deck_array" not in st.session_state:
        st.session_state.deck_array = []
    for key in DECK_LISTEN_KEYS:
        if save_key(key) not in st.session_state:
            st.session_state[save_key(key)] = []
        if key not in st.session_state:
            st.session_state[key] = list(st.session_state[save_key(key)])
    if save_key("selected_deck") not in st.session_state:
        st.session_state[save_key("selected_deck")] = None
    if "uebertakter_attr" not in st.session_state:
        st.session_state.uebertakter_attr = "Angriff"
    if save_key("uebertakter_attr") not in st.session_state:
        st.session_state[save_key("uebertakter_attr")] = st.session_state.uebertakter_attr
    if "agent_stufe" not in st.session_state:
        st.session_state.agent_stufe = AGENT_STUFE_DEFAULT
    if save_key("agent_stufe") not in st.session_state:
        st.session_state[save_key("agent_stufe")] = st.session_state.agent_stufe
    if "verschleiern_stufe" not in st.session_state:
        st.session_state.verschleiern_stufe = VERSCHLEIERN_DEFAULT
    if save_key("verschleiern_stufe") not in st.session_state:
        st.session_state[save_key("verschleiern_stufe")] = st.session_state.verschleiern_stufe
    if "programmiergenie_handlung" not in st.session_state:
        st.session_state.programmiergenie_handlung = PROGRAMMIERGENIE_DEFAULT
    if save_key("programmiergenie_handlung") not in st.session_state:
        st.session_state[save_key("programmiergenie_handlung")] = st.session_state.programmiergenie_handlung
    if save_key("asdf") not in st.session_state:
        st.session_state[save_key("asdf")] = dict(st.session_state.asdf)
    if save_key("deck_array") not in st.session_state:
        st.session_state[save_key("deck_array")] = list(st.session_state.deck_array)
    for attr in ASDF_ATTRIBUTE:
        widget_key = f"{ASDF_SELECT_PREFIX}{attr}"
        if save_key(widget_key) not in st.session_state:
            st.session_state[save_key(widget_key)] = st.session_state.asdf.get(attr)
    if "ansicht" not in st.session_state:
        st.session_state.ansicht = PAGE_DECK
    if "decker_name" not in st.session_state:
        st.session_state.decker_name = ""
    if "aktuelles_rauschen" not in st.session_state:
        st.session_state.aktuelles_rauschen = 0
    if "modus_schleichfahrt" not in st.session_state:
        st.session_state.modus_schleichfahrt = False
    if "aufmerksamkeit_bonus" not in st.session_state:
        st.session_state.aufmerksamkeit_bonus = AUFMERKSAMKEIT_DEFAULT
    if save_key("aufmerksamkeit_bonus") not in st.session_state:
        st.session_state[save_key("aufmerksamkeit_bonus")] = st.session_state.aufmerksamkeit_bonus
    if "overwatch_wert" not in st.session_state:
        st.session_state.overwatch_wert = 0
    if "sim_modus" not in st.session_state:
        st.session_state.sim_modus = SIM_DEFAULT
    if "etac_modus" not in st.session_state:
        st.session_state.etac_modus = ETAC_DEFAULT
    for key in ("etac_dv", "etac_fw"):
        if save_key(key) not in st.session_state:
            st.session_state[save_key(key)] = 0
        if key not in st.session_state:
            st.session_state[key] = int(st.session_state[save_key(key)] or 0)
    if "datenbuchse_plus" not in st.session_state:
        st.session_state.datenbuchse_plus = 0
    for key in SCHADEN_KEYS:
        if save_key(key) not in st.session_state:
            st.session_state[save_key(key)] = 0
        if key not in st.session_state:
            st.session_state[key] = int(st.session_state[save_key(key)] or 0)
    for key in INIT_KEYS:
        if save_key(key) not in st.session_state:
            st.session_state[save_key(key)] = 0
        if key not in st.session_state:
            st.session_state[key] = int(st.session_state[save_key(key)] or 0)
    if "boosterwolke" not in st.session_state:
        st.session_state.boosterwolke = {}
    if "asdf_hand_mod" not in st.session_state:
        st.session_state.asdf_hand_mod = {attr: 0 for attr in ASDF_ATTRIBUTE}
    restore_deck_auswahl()


def json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value)
    if hasattr(value, "item"):
        try:
            return json_safe(value.item())
        except Exception:
            pass
    return value if isinstance(value, str) else str(value)


def collect_profil() -> dict:
    felder = {**CHARAKTERWERTE, **MATRIX_FERTIGKEITEN}
    werte = {
        key: json_safe(st.session_state.get(key, default))
        for key, (_label, default, _min_value, _max_value) in felder.items()
    }
    cyber_stufen = {
        key: json_safe(value)
        for key, value in st.session_state.items()
        if isinstance(key, str) and key.startswith("cyber_stufe_")
    }
    return {
        "format": "shadowrun5-decker-konsole",
        "version": 1,
        "ansicht": st.session_state.get("ansicht", PAGE_DECK),
        "werte": werte,
        "selected_deck": st.session_state.get("selected_deck") or st.session_state.get(save_key("selected_deck")),
        "deck_array": json_safe(list(st.session_state.get("deck_array") or st.session_state.get(save_key("deck_array")) or [])),
        "asdf": json_safe(dict(st.session_state.get("asdf") or st.session_state.get(save_key("asdf")) or {})),
        "selected_programme": json_safe(liste_aus_state("selected_programme")),
        "selected_module": json_safe(liste_aus_state("selected_module")),
        "selected_cyberware": json_safe(liste_aus_state("selected_cyberware")),
        "selected_geraetemods": json_safe(liste_aus_state("selected_geraetemods")),
        "selected_vorteile": json_safe(liste_aus_state("selected_vorteile")),
        "uebertakter_attr": st.session_state.get("uebertakter_attr") or st.session_state.get(save_key("uebertakter_attr"), "Angriff"),
        "programmiergenie_handlung": programmiergenie_handlung(),
        "agent_stufe": agent_stufe_wert(),
        "verschleiern_stufe": verschleiern_stufe_wert(),
        "modus_schleichfahrt": bool(st.session_state.get("modus_schleichfahrt", False)),
        "aufmerksamkeit_bonus": aufmerksamkeit_bonus_wahl(),
        "decker_name": str(st.session_state.get("decker_name") or "").strip(),
        "aktuelles_rauschen": int(st.session_state.get("aktuelles_rauschen", 0) or 0),
        "overwatch_wert": int(st.session_state.get("overwatch_wert", 0) or 0),
        "sim_modus": sim_modus(),
        "etac_modus": etac_modus(),
        "etac_dv": int(st.session_state.get("etac_dv", 0) or 0),
        "etac_fw": int(st.session_state.get("etac_fw", 0) or 0),
        "datenbuchse_plus": int(st.session_state.get("datenbuchse_plus", 0) or 0),
        "schaden_matrix": int(st.session_state.get("schaden_matrix", 0) or 0),
        "schaden_geistig": int(st.session_state.get("schaden_geistig", 0) or 0),
        "schaden_koerperlich": int(st.session_state.get("schaden_koerperlich", 0) or 0),
        "schaden_haerte": int(st.session_state.get("schaden_haerte", 0) or 0),
        "initiative_wert_mod": int(st.session_state.get("initiative_wert_mod", 0) or 0),
        "initiative_wuerfel_mod": int(st.session_state.get("initiative_wuerfel_mod", 0) or 0),
        "boosterwolke": json_safe(dict(st.session_state.get("boosterwolke") or {})),
        "asdf_hand_mod": json_safe(dict(st.session_state.get("asdf_hand_mod") or {})),
        "cyber_stufen": cyber_stufen,
    }


def namen_liste(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if ist_gueltiger_name(value) else []
    if isinstance(value, (list, tuple, set)):
        return [str(name).strip() for name in value if ist_gueltiger_name(name)]
    return []


def apply_profil(data: object) -> None:
    if not isinstance(data, dict):
        raise ValueError("JSON muss ein Objekt sein.")

    werte = data.get("werte")
    if not isinstance(werte, dict):
        werte = data

    def profil_wert(key: str, default: object) -> object:
        alt_keys = [alt for alt, neu in LEGACY_WERT_KEYS.items() if neu == key]
        for kandidat in (key, *alt_keys):
            if kandidat in werte:
                return werte[kandidat]
            if kandidat in data:
                return data[kandidat]
        return default

    for key, (_label, default, min_value, max_value) in {**CHARAKTERWERTE, **MATRIX_FERTIGKEITEN}.items():
        roh = profil_wert(key, default)
        try:
            zahl = int(roh)
        except (TypeError, ValueError):
            zahl = default
        st.session_state[key] = max(min_value, min(max_value, zahl))

    deck = data.get("selected_deck")
    if ist_gueltiger_name(deck):
        st.session_state.selected_deck = str(deck).strip()

    array = data.get("deck_array")
    if isinstance(array, list) and array:
        st.session_state.deck_array = [int(wert) for wert in array]

    asdf = data.get("asdf")
    if isinstance(asdf, dict):
        neu = {attr: None for attr in ASDF_ATTRIBUTE}
        for attr in ASDF_ATTRIBUTE:
            if asdf.get(attr) is None:
                continue
            neu[attr] = int(asdf[attr])
        st.session_state.asdf = neu
        for attr, value in neu.items():
            if value is not None:
                st.session_state[f"{ASDF_SELECT_PREFIX}{attr}"] = value

    for key in (
        "selected_programme",
        "selected_module",
        "selected_cyberware",
        "selected_vorteile",
        "selected_geraetemods",
    ):
        if key in data:
            st.session_state[key] = namen_liste(data.get(key))
            if key == "selected_programme":
                reset_programm_gruppen_widgets()

    ueber = data.get("uebertakter_attr")
    if ueber in ASDF_ATTRIBUTE:
        st.session_state.uebertakter_attr = ueber

    genie = data.get("programmiergenie_handlung", werte.get("programmiergenie_handlung") if isinstance(werte, dict) else None)
    if isinstance(genie, str):
        st.session_state.programmiergenie_handlung = programmiergenie_wahl_aus(genie)
        st.session_state[save_key("programmiergenie_handlung")] = st.session_state.programmiergenie_handlung

    agent = data.get("agent_stufe", werte.get("agent_stufe") if isinstance(werte, dict) else None)
    if agent is not None:
        try:
            st.session_state.agent_stufe = max(AGENT_STUFE_MIN, min(AGENT_STUFE_MAX, int(agent)))
            st.session_state[save_key("agent_stufe")] = st.session_state.agent_stufe
        except (TypeError, ValueError):
            pass

    versch = data.get("verschleiern_stufe", werte.get("verschleiern_stufe") if isinstance(werte, dict) else None)
    if versch is not None:
        try:
            st.session_state.verschleiern_stufe = max(
                VERSCHLEIERN_MIN, min(VERSCHLEIERN_MAX, int(versch))
            )
            st.session_state[save_key("verschleiern_stufe")] = st.session_state.verschleiern_stufe
        except (TypeError, ValueError):
            pass

    name = data.get("decker_name", data.get("name"))
    if isinstance(name, str):
        st.session_state.decker_name = name.strip()

    rauschen = data.get("aktuelles_rauschen", werte.get("aktuelles_rauschen") if isinstance(werte, dict) else None)
    if rauschen is not None:
        try:
            st.session_state.aktuelles_rauschen = max(0, min(24, int(rauschen)))
        except (TypeError, ValueError):
            pass

    schleich = data.get("modus_schleichfahrt", werte.get("modus_schleichfahrt") if isinstance(werte, dict) else None)
    if schleich is not None:
        st.session_state.modus_schleichfahrt = bool(schleich)

    aufm = data.get("aufmerksamkeit_bonus", werte.get("aufmerksamkeit_bonus") if isinstance(werte, dict) else None)
    if aufm is not None:
        st.session_state.aufmerksamkeit_bonus = aufmerksamkeit_wahl_aus(aufm)
        st.session_state[save_key("aufmerksamkeit_bonus")] = st.session_state.aufmerksamkeit_bonus

    overwatch = data.get("overwatch_wert", werte.get("overwatch_wert") if isinstance(werte, dict) else None)
    if overwatch is not None:
        try:
            st.session_state.overwatch_wert = max(0, min(50, int(overwatch)))
        except (TypeError, ValueError):
            pass

    sim = data.get("sim_modus", werte.get("sim_modus") if isinstance(werte, dict) else None)
    if isinstance(sim, str) and sim.strip() in SIM_MODI:
        st.session_state.sim_modus = sim.strip()

    etac = data.get("etac_modus", werte.get("etac_modus") if isinstance(werte, dict) else None)
    if isinstance(etac, str) and etac.strip() in ETAC_MODI:
        st.session_state.etac_modus = etac.strip()
    for key, maximum in (("etac_dv", 3), ("etac_fw", 3)):
        roh = data.get(key, werte.get(key) if isinstance(werte, dict) else None)
        if roh is None:
            continue
        try:
            st.session_state[key] = max(0, min(maximum, int(roh)))
        except (TypeError, ValueError):
            pass

    datenbuchse = data.get("datenbuchse_plus", werte.get("datenbuchse_plus") if isinstance(werte, dict) else None)
    if datenbuchse is not None:
        try:
            st.session_state.datenbuchse_plus = max(0, min(3, int(datenbuchse)))
        except (TypeError, ValueError):
            pass

    for schaden_key in SCHADEN_KEYS:
        roh = data.get(schaden_key, werte.get(schaden_key) if isinstance(werte, dict) else None)
        if roh is None:
            continue
        try:
            maximum = HAERTE_MONITOR if schaden_key == "schaden_haerte" else 40
            st.session_state[schaden_key] = max(0, min(maximum, int(roh)))
            st.session_state[save_key(schaden_key)] = st.session_state[schaden_key]
        except (TypeError, ValueError):
            pass

    wert_mod = data.get("initiative_wert_mod", werte.get("initiative_wert_mod") if isinstance(werte, dict) else None)
    if wert_mod is not None:
        try:
            st.session_state.initiative_wert_mod = max(-20, min(20, int(wert_mod)))
            st.session_state[save_key("initiative_wert_mod")] = st.session_state.initiative_wert_mod
        except (TypeError, ValueError):
            pass
    wuerfel_mod = data.get("initiative_wuerfel_mod", werte.get("initiative_wuerfel_mod") if isinstance(werte, dict) else None)
    if wuerfel_mod is not None:
        try:
            st.session_state.initiative_wuerfel_mod = max(-5, min(5, int(wuerfel_mod)))
            st.session_state[save_key("initiative_wuerfel_mod")] = st.session_state.initiative_wuerfel_mod
        except (TypeError, ValueError):
            pass

    booster = data.get("boosterwolke")
    if isinstance(booster, dict):
        st.session_state.boosterwolke = {
            str(name): stufe
            for name, stufe in booster.items()
            if str(stufe) in BOOSTERWOLKE_STUFEN
        }
    reset_boosterwolke_widgets()

    hand = data.get("asdf_hand_mod")
    if isinstance(hand, dict):
        neu = {attr: 0 for attr in ASDF_ATTRIBUTE}
        for attr in ASDF_ATTRIBUTE:
            try:
                neu[attr] = max(
                    ASDF_HAND_MOD_MIN,
                    min(ASDF_HAND_MOD_MAX, int(hand.get(attr, 0) or 0)),
                )
            except (TypeError, ValueError):
                neu[attr] = 0
        st.session_state.asdf_hand_mod = neu

    stufen = data.get("cyber_stufen")
    if isinstance(stufen, dict):
        for key, value in stufen.items():
            if isinstance(key, str) and key.startswith("cyber_stufe_"):
                st.session_state[key] = int(value)

    ansicht = data.get("ansicht")
    if ansicht in ANSICHTEN:
        st.session_state.ansicht = ansicht
    snapshot_deck_auswahl()


def on_profil_import() -> None:
    uploaded = st.session_state.get("profil_datei")
    # Nach dem Entfernen im Uploader bleibt ein Platzhalter ohne getvalue() zurueck.
    if uploaded is None or not hasattr(uploaded, "getvalue"):
        st.session_state.profil_meldung = ("error", "Keine JSON-Datei gew\u00e4hlt.")
        return
    try:
        data = json.loads(uploaded.getvalue().decode("utf-8-sig"))
        apply_profil(data)
        st.session_state.profil_meldung = ("ok", "Profil geladen.")
    except json.JSONDecodeError:
        st.session_state.profil_meldung = ("error", "Die Datei ist kein g\u00fcltiges JSON.")
    except (TypeError, ValueError) as exc:
        st.session_state.profil_meldung = ("error", f"Import fehlgeschlagen: {exc}")


def gehe_zu(seite: str) -> None:
    st.session_state.ansicht = seite


def profil_dateiname() -> str:
    stempel = datetime.now().strftime("%Y-%m-%d")
    name = str(st.session_state.get("decker_name") or "").strip()
    if not name:
        return f"decker-konsole-{stempel}.json"
    sicher = re.sub(r"[^A-Za-z0-9_\-]+", "-", name).strip("-")
    return f"{sicher or 'decker'}-{stempel}.json"


def render_sidebar_sicherung() -> None:
    with st.sidebar.expander("Sicherung", expanded=False):
        st.caption("Aktuelle Werte als JSON exportieren oder ein gespeichertes Profil laden.")
        payload = json.dumps(collect_profil(), indent=2, ensure_ascii=False)
        st.download_button(
            "Exportieren",
            data=payload.encode("utf-8"),
            file_name=profil_dateiname(),
            mime="application/json",
            width="stretch",
            key="profil_export",
        )
        st.file_uploader(
            "JSON-Datei",
            type=["json"],
            key="profil_datei",
            accept_multiple_files=False,
        )
        st.button(
            "Importieren",
            width="stretch",
            key="profil_import",
            type="primary",
            on_click=on_profil_import,
        )
        meldung = st.session_state.pop("profil_meldung", None)
        if meldung:
            art, text = meldung
            if art == "ok":
                st.success(text)
            else:
                st.error(text)


def render_sidebar_decker_name() -> None:
    st.sidebar.text_input(
        "Name des Deckers",
        key="decker_name",
        placeholder="Decker-Name",
    )


def render_sidebar_navigation() -> None:
    aktuelle = st.session_state.get("ansicht", PAGE_DECK)
    st.sidebar.button(
        PAGE_DECK,
        type="primary" if aktuelle == PAGE_DECK else "secondary",
        width="stretch",
        key="nav_deck",
        on_click=gehe_zu,
        args=(PAGE_DECK,),
    )
    st.sidebar.button(
        PAGE_DASHBOARD,
        type="primary" if aktuelle == PAGE_DASHBOARD else "secondary",
        width="stretch",
        key="nav_dashboard",
        on_click=gehe_zu,
        args=(PAGE_DASHBOARD,),
    )


def render_sidebar_rauschen() -> None:
    st.sidebar.number_input(
        "Aktuelles Rauschen",
        min_value=0,
        max_value=24,
        step=1,
        key="aktuelles_rauschen",
    )
    umgebung = max(0, int(st.session_state.get("aktuelles_rauschen", 0) or 0))
    _roh, effektiv, quellen = effektives_rauschen()
    stufe = verschleiern_bonus()
    if quellen:
        st.sidebar.caption(f"{', '.join(quellen)}: Rauschunterdr\u00fcckung aktiv")
    if stufe:
        st.sidebar.caption(
            f"{programm_anzeigename('Verschleiern')}: Schleicher +{stufe}, "
            f"Rauschen +{stufe} (nicht unterdr\u00fcckbar)"
        )
    if effektiv != umgebung:
        st.sidebar.caption(f"Rauschen effektiv {effektiv}")
    st.sidebar.toggle("Modus Schleichfahrt", key="modus_schleichfahrt")
    if modus_schleichfahrt():
        st.sidebar.caption("Schleichfahrt: -2 auf Matrixhandlungen")


def render_sidebar_etac() -> None:
    st.sidebar.markdown("**E-Tac**")
    st.sidebar.segmented_control(
        "E-Tac",
        options=list(ETAC_MODI),
        key="etac_modus",
        required=True,
        width="stretch",
        label_visibility="collapsed",
    )
    budget, dv, fw = etac_punkte()
    if budget <= 0:
        snapshot_key("etac_dv")
        snapshot_key("etac_fw")
        st.sidebar.caption("Kein E-Tac-Bonus")
        return
    st.session_state.etac_dv = dv
    st.session_state.etac_fw = fw
    st.sidebar.number_input(
        "Datenverarbeitung +",
        min_value=0,
        max_value=budget,
        step=1,
        key="etac_dv",
        on_change=on_liste_change,
        args=("etac_dv",),
    )
    rest = max(0, budget - int(st.session_state.get("etac_dv", 0) or 0))
    fw = min(fw, rest)
    st.session_state.etac_fw = fw
    st.sidebar.number_input(
        "Firewall +",
        min_value=0,
        max_value=rest,
        step=1,
        key="etac_fw",
        on_change=on_liste_change,
        args=("etac_fw",),
    )
    verteilt = int(st.session_state.get("etac_dv", 0) or 0) + int(st.session_state.get("etac_fw", 0) or 0)
    st.sidebar.caption(f"{verteilt} / {budget} Punkte auf Datenverarbeitung und Firewall")
    snapshot_key("etac_dv")
    snapshot_key("etac_fw")


def render_sidebar_datenbuchse() -> None:
    stufe = datenbuchse_cyber_stufe()
    if stufe is not None:
        st.sidebar.markdown(f"**{DATENBUCHSE_NAME}**")
        st.sidebar.caption(
            f"Stufe {stufe} aus der Cyberware: +{stufe} Programmpl\u00e4tze"
        )
        return
    st.sidebar.slider(
        DATENBUCHSE_NAME,
        min_value=0,
        max_value=3,
        step=1,
        key="datenbuchse_plus",
    )


def inject_theme() -> None:
    st.html(
        "<style>" + THEME_CSS + "</style>"
        "<script>"
        "(function(){"
        "var rules={"
        '"st-key-selected_programme":["#FF2DAA","#14120a"],'
        '"st-key-selected_module":["#03D8F3","#0a0a10"],'
        '"st-key-selected_vorteile":["#00FF9F","#0a0a10"],'
        '"st-key-selected_geraetemods":["#FF8A3D","#0a0a10"]'
        "};"
        "function paint(){"
        "Object.keys(rules).forEach(function(cls){"
        "var bg=rules[cls][0], fg=rules[cls][1];"
        "document.querySelectorAll('[class*=\"'+cls+'\"] [data-tag]').forEach(function(el){"
        "el.style.setProperty('background-color',bg,'important');"
        "el.style.setProperty('background',bg,'important');"
        "el.style.setProperty('color',fg,'important');"
        "el.querySelectorAll('span,button,svg').forEach(function(inner){"
        "inner.style.setProperty('color',fg,'important');"
        "inner.style.setProperty('fill',fg,'important');"
        "});"
        "});"
        "});"
        "}"
        "paint();"
        "if(!window.__srChipPaint){"
        "window.__srChipPaint=true;"
        "new MutationObserver(paint).observe(document.body,{childList:true,subtree:true});"
        "}"
        "})();"
        "</script>",
        unsafe_allow_javascript=True,
    )


def render_header() -> None:
    name = str(st.session_state.get("decker_name") or "").strip() or "DECKER"
    st.markdown(
        HEADER_HTML.replace("USER // DECKER", f"USER // {html.escape(name).upper()}"),
        unsafe_allow_html=True,
    )


def render_number_inputs(felder: dict[str, tuple[str, int, int, int]]) -> None:
    for key, (label, _default, min_value, max_value) in felder.items():
        st.sidebar.number_input(
            label,
            min_value=min_value,
            max_value=max_value,
            step=1,
            key=key,
        )


def find_column(dataframe: pd.DataFrame, prefix: str) -> str | None:
    for column in dataframe.columns:
        if str(column).startswith(prefix):
            return column
    return None


def normalize(text: str) -> str:
    replacements = {
        "\u00e4": "ae",
        "\u00f6": "oe",
        "\u00fc": "ue",
        "\u00df": "ss",
        "\u00c4": "ae",
        "\u00d6": "oe",
        "\u00dc": "ue",
    }
    result = str(text)
    for src, dst in replacements.items():
        result = result.replace(src, dst)
    return result.lower()


def col_matching(dataframe: pd.DataFrame | None, *needles: str) -> str | None:
    """Findet eine Spalte, unabhängig von Groß-/Kleinschreibung und Umlauten."""
    if dataframe is None or dataframe.empty or not needles:
        return None
    if len(needles) == 1:
        ziel = str(needles[0]).lower().strip()
        for column in dataframe.columns:
            if str(column).lower().strip() == ziel:
                return column
    for column in dataframe.columns:
        name = normalize(str(column))
        if all(normalize(needle) in name for needle in needles):
            return column
    return None


def ist_gueltiger_name(wert: object) -> bool:
    if wert is None or (isinstance(wert, float) and pd.isna(wert)):
        return False
    text = str(wert).strip()
    return bool(text) and text.lower() not in LEERE_NAMEN


def item_names(dataframe: pd.DataFrame | None) -> list[str]:
    if dataframe is None or dataframe.empty or "Name" not in dataframe.columns:
        return []
    serie = dataframe["Name"].dropna()
    namen = [str(wert).strip() for wert in serie if ist_gueltiger_name(wert)]
    return sorted(dict.fromkeys(namen))


def row_by_name(dataframe: pd.DataFrame, name: str) -> pd.Series | None:
    if not ist_gueltiger_name(name):
        return None
    treffer = dataframe.loc[dataframe["Name"].astype(str).str.strip() == name.strip()]
    if treffer.empty:
        return None
    return treffer.iloc[0]


def item_text(dataframe: pd.DataFrame, name: str) -> str:
    row = row_by_name(dataframe, name)
    if row is None:
        return ""
    column = find_column(dataframe, "Erl")
    if column is None:
        return ""
    return str(row[column])


def stufen_bereich(dataframe: pd.DataFrame, name: str) -> tuple[int, int]:
    row = row_by_name(dataframe, name)
    if row is None or "Stufe" not in row.index:
        return 1, 1
    zahlen = [int(wert) for wert in re.findall(r"\d+", str(row["Stufe"]))]
    if len(zahlen) >= 2:
        return zahlen[0], zahlen[1]
    if zahlen:
        return zahlen[0], zahlen[0]
    return 1, 1


def cyber_stufe_key(name: str) -> str:
    return f"cyber_stufe_{name.strip()}"


def resolve_attr(token: str) -> str | None:
    cleaned = normalize(re.sub("[^a-zA-Z\u00e4\u00f6\u00fc\u00c4\u00d6\u00dc\u00df]", "", token))
    for key in sorted(ATTR_LOOKUP, key=len, reverse=True):
        if cleaned == key or cleaned.startswith(key):
            return ATTR_LOOKUP[key]
    return None


def parse_attribute_bonuses(text: str, stufe: int = 1) -> dict[str, int]:
    bonuses: dict[str, int] = defaultdict(int)
    if not text or text.lower() == "nan":
        return {}

    saetze = re.split(r"(?<=[.!?])\s+", str(text))
    for satz in saetze:
        low = satz.lower()
        norm = normalize(satz)
        if any(marker in low or marker in norm for marker in WURFELPOOL_MARKERS):
            continue
        if any(marker in low or marker in norm for marker in SITUATIONAL_MARKERS):
            continue
        if re.search(r"um\s+\d+\s+bis\s+\d+", low):
            continue

        plus_treffer = list(
            re.finditer(
                r"\+(\d+)\s+auf\s+(?:das\s+attribut\s+|sein\s+)?"
                "([a-z\u00e4\u00f6\u00fc]+)",
                low,
            )
        )
        if plus_treffer:
            for treffer in plus_treffer:
                attr = resolve_attr(treffer.group(2))
                if attr:
                    bonuses[attr] += int(treffer.group(1))
            continue

        for treffer in re.finditer(
            r"attribut\s+" "([a-z\u00e4\u00f6\u00fc]+)" r"[^\d]{0,50}um\s+(\d+)",
            low,
        ):
            attr = resolve_attr(treffer.group(1))
            if attr:
                bonuses[attr] += int(treffer.group(2))

        if "stufe" in low:
            for token, attr in (
                ("logik", "Logik"),
                ("intuition", "Intuition"),
                ("willenskraft", "Willenskraft"),
            ):
                if token in norm and any(
                    phrase in low
                    for phrase in ("um seine stufe", "um die stufe", "direkt um")
                ):
                    bonuses[attr] += stufe

    return dict(bonuses)


def ist_uebertakter(name: str) -> bool:
    return normalize(name).replace(" ", "") == "uebertakter"


ASDF_BONI = {
    "entschluesselung": {"Angriff": 1},
    "tarnkappe": {"Schleicher": 1},
    "toolbox": {"Datenverarbeitung": 1},
    "verschluesselung": {"Firewall": 1},
}


def programm_asdf_bonus(name: str) -> dict[str, int]:
    schluessel = normalize(str(name).strip()).replace(" ", "")
    return dict(ASDF_BONI.get(schluessel, {}))


def csv_int(value: object) -> int:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0
    text = str(value).strip()
    if not text or text.lower() in LEERE_NAMEN:
        return 0
    try:
        return int(float(text.replace(",", ".")))
    except ValueError:
        treffer = re.search(r"-?\d+", text)
        return int(treffer.group()) if treffer else 0


def geraetemod_effekte(dataframe: pd.DataFrame, name: str) -> tuple[dict[str, int], int]:
    row = row_by_name(dataframe, name)
    if row is None:
        return {}, 0
    boni: dict[str, int] = {}
    mapping = (
        ("Angriff", ("angriff", "angrif")),
        ("Schleicher", ("schleich",)),
        ("Datenverarbeitung", ("datenverarbeitung",)),
        ("Firewall", ("firewall",)),
    )
    for attr, needles in mapping:
        spalte = None
        for column in dataframe.columns:
            titel = normalize(str(column))
            if "zustand" in titel or "monitor" in titel:
                continue
            if any(needle in titel for needle in needles):
                spalte = column
                break
        if spalte is None:
            continue
        bonus = csv_int(row[spalte])
        if bonus:
            boni[attr] = bonus
    monitor = 0
    for column in dataframe.columns:
        titel = normalize(str(column))
        if "zustand" in titel or "monitor" in titel:
            monitor = csv_int(row[column])
            break
    return boni, monitor


def geraetemod_text(dataframe: pd.DataFrame, name: str) -> str:
    boni, monitor = geraetemod_effekte(dataframe, name)
    teile = [f"{attr} {bonus:+d}" for attr, bonus in boni.items()]
    if monitor:
        teile.append(f"Zustandsmonitor {monitor:+d}")
    if "modulhinzufuegen" in programm_schluessel(name):
        teile.append("zus\u00e4tzlicher Modulplatz")
    return ", ".join(teile) if teile else "ohne Zahlenwerte"


def geraetemod_monitor_bonus(tables: dict[str, pd.DataFrame | None]) -> int:
    mods = tables.get("Ger\u00e4temodifikationen")
    if mods is None:
        return 0
    return sum(
        geraetemod_effekte(mods, name)[1]
        for name in liste_aus_state("selected_geraetemods")
    )


def matrix_monitor_hinweis(tables: dict[str, pd.DataFrame | None]) -> str:
    mods = tables.get("Ger\u00e4temodifikationen")
    if mods is None:
        return ""
    hinweise = []
    for name in liste_aus_state("selected_geraetemods"):
        _boni, monitor = geraetemod_effekte(mods, name)
        if monitor:
            hinweise.append(f"{name}: Zustandsmonitor {monitor:+d}")
    return " | ".join(hinweise)


def modul_limit() -> int:
    limit = 1
    if programm_in_liste(liste_aus_state("selected_geraetemods"), "Modul Hinzuf\u00fcgen", "Modul hinzuf\u00fcgen"):
        limit += 1
    if programm_in_liste(liste_aus_state("selected_vorteile"), "Deckbastler"):
        limit += 1
    return min(3, limit)


def sammeln_boni(tables: dict[str, pd.DataFrame | None]) -> tuple[dict[str, int], list[tuple[str, str, str, int]]]:
    totals: dict[str, int] = defaultdict(int, {attr: 0 for attr in ALLE_ATTRIBUTE})
    details: list[tuple[str, str, str, int]] = []

    quellen = (
        ("Programm", "selected_programme", "Programme"),
        ("Modul", "selected_module", "Module"),
        ("Cyberware", "selected_cyberware", "Cyberware / Bioware"),
        ("Vorteil", "selected_vorteile", "Vorteile"),
    )

    for quelle, state_key, table_key in quellen:
        dataframe = tables.get(table_key)
        if dataframe is None:
            continue
        for name in liste_aus_state(state_key):
            if not ist_gueltiger_name(name):
                continue
            if quelle == "Vorteil" and ist_uebertakter(name):
                attr = (
                    st.session_state.get("uebertakter_attr")
                    or st.session_state.get(save_key("uebertakter_attr"), "Angriff")
                )
                totals[attr] += 1
                details.append((quelle, name, attr, 1))
                continue

            if quelle == "Programm":
                for attr, bonus in programm_asdf_bonus(name).items():
                    if not bonus:
                        continue
                    totals[attr] += bonus
                    details.append((quelle, name, attr, bonus))
                continue

            stufe = 1
            if quelle == "Cyberware":
                min_s, max_s = stufen_bereich(dataframe, name)
                stufe = int(st.session_state.get(cyber_stufe_key(name), min_s))
                stufe = min(max(stufe, min_s), max_s)

            for attr, bonus in parse_attribute_bonuses(item_text(dataframe, name), stufe).items():
                totals[attr] += bonus
                details.append((quelle, name, attr, bonus))

    mods = tables.get("Ger\u00e4temodifikationen")
    if mods is not None:
        for name in liste_aus_state("selected_geraetemods"):
            boni, monitor = geraetemod_effekte(mods, name)
            for attr, bonus in boni.items():
                totals[attr] += bonus
                details.append(("Ger\u00e4temod", name, attr, bonus))
            if monitor:
                details.append(("Ger\u00e4temod", name, "Zustandsmonitor", monitor))

    _budget, etac_dv, etac_fw = etac_punkte()
    modus = etac_modus()
    if etac_dv:
        totals["Datenverarbeitung"] += etac_dv
        details.append(("E-Tac", modus, "Datenverarbeitung", etac_dv))
    if etac_fw:
        totals["Firewall"] += etac_fw
        details.append(("E-Tac", modus, "Firewall", etac_fw))

    versch = verschleiern_bonus()
    if versch:
        totals["Schleicher"] += versch
        details.append(
            ("Programm", programm_anzeigename("Verschleiern"), "Schleicher", versch)
        )

    return dict(totals), details


def basiswert(attr: str) -> int:
    if attr in ASDF_ATTRIBUTE:
        wert = st.session_state.asdf.get(attr)
        return int(wert) if wert is not None else 0
    mapping = {
        "Logik": "attr_logik",
        "Intuition": "attr_intuition",
        "Willenskraft": "attr_willenskraft",
        "Konstitution": "attr_konstitution",
        "Reaktion": "attr_reaktion",
    }
    return int(st.session_state.get(mapping[attr], 0))


def asdf_hand_mod(attr: str) -> int:
    if attr not in ASDF_ATTRIBUTE:
        return 0
    mods = st.session_state.get("asdf_hand_mod") or {}
    try:
        return max(
            ASDF_HAND_MOD_MIN,
            min(ASDF_HAND_MOD_MAX, int(mods.get(attr, 0) or 0)),
        )
    except (TypeError, ValueError):
        return 0


def on_asdf_hand_mod(attr: str, delta: int) -> None:
    aktuelle = dict(st.session_state.get("asdf_hand_mod") or {})
    aktuelle[attr] = max(
        ASDF_HAND_MOD_MIN,
        min(ASDF_HAND_MOD_MAX, asdf_hand_mod(attr) + int(delta)),
    )
    st.session_state.asdf_hand_mod = aktuelle


def attribut_final(attr: str, boni: dict[str, int] | None = None) -> int:
    quelle = boni if boni is not None else (st.session_state.get("boni") or {})
    bonus = int(quelle.get(attr, 0) or 0)
    return basiswert(attr) + bonus + asdf_hand_mod(attr)


def finalwert(attr: str) -> int:
    werte = st.session_state.get("final_werte") or {}
    if attr in werte:
        return int(werte[attr])
    return attribut_final(attr)


def setze_finalwerte(boni: dict[str, int]) -> dict[str, int]:
    st.session_state.boni = boni
    st.session_state.final_werte = {
        attr: attribut_final(attr, boni) for attr in ALLE_ATTRIBUTE
    }
    return st.session_state.final_werte


def aktualisiere_finalwerte(tables: dict[str, pd.DataFrame | None]) -> dict[str, int]:
    boni, _details = sammeln_boni(tables)
    return setze_finalwerte(boni)


def render_asdf_final_chip(attr: str) -> None:
    slug = programm_schluessel(attr)
    wert_col, minus_col, plus_col = st.columns(
        [3.4, 0.7, 0.7], gap="small", vertical_alignment="center"
    )
    with wert_col:
        st.markdown(
            f'<div class="sr-asdf-final">Final {attribut_final(attr)}</div>',
            unsafe_allow_html=True,
        )
    with minus_col:
        st.button(
            "\u2212",
            key=f"asdf_hand_minus_{slug}",
            on_click=on_asdf_hand_mod,
            args=(attr, -1),
            width="stretch",
        )
    with plus_col:
        st.button(
            "+",
            key=f"asdf_hand_plus_{slug}",
            on_click=on_asdf_hand_mod,
            args=(attr, 1),
            width="stretch",
        )


def render_final_metrics(boni: dict[str, int]) -> None:
    setze_finalwerte(boni)
    st.markdown("**Finale Werte** (Basis + Boni)")
    geist_spalten = st.columns(3)
    for spalte, attr in zip(geist_spalten, GEISTIGE_ATTRIBUTE):
        with spalte:
            bonus = boni.get(attr, 0)
            st.metric(
                attr,
                attribut_final(attr, boni),
                delta=f"+{bonus}" if bonus > 0 else (str(bonus) if bonus else None),
            )
    asdf_spalten = st.columns(4)
    for spalte, attr in zip(asdf_spalten, ASDF_ATTRIBUTE):
        with spalte:
            bonus = boni.get(attr, 0) + asdf_hand_mod(attr)
            st.metric(
                attr,
                attribut_final(attr, boni),
                delta=f"+{bonus}" if bonus > 0 else (str(bonus) if bonus else None),
            )


def render_bonus_details(details: list[tuple[str, str, str, int]]) -> None:
    aktive = [eintrag for eintrag in details if eintrag[3]]
    if not aktive:
        return
    with st.expander("Aktive Attribut-Boni"):
        for quelle, name, attr, bonus in aktive:
            vorzeichen = f"+{bonus}" if bonus > 0 else str(bonus)
            st.write(f"{quelle} **{name}**: {vorzeichen} {attr}")


def render_berechnungs_uebersicht(
    tables: dict[str, pd.DataFrame | None],
    details: list[tuple[str, str, str, int]],
    deck_row: pd.Series,
) -> None:
    with st.expander("Berechnung ASDF, Programme, Module"):
        st.markdown("**ASDF-Werte**")
        for attr in ASDF_ATTRIBUTE:
            teile = [f"Basis {basiswert(attr)}"]
            for quelle, name, ziel, bonus in details:
                if ziel != attr or not bonus:
                    continue
                vorzeichen = f"+{bonus}" if bonus > 0 else str(bonus)
                teile.append(f"{name} {vorzeichen}")
            hand = asdf_hand_mod(attr)
            if hand:
                teile.append(f"Hand {hand:+d}")
            st.write(f"{attr}: {' | '.join(teile)} = **{attribut_final(attr)}**")

        st.markdown("**Programmpl\u00e4tze**")
        programm_teile = []
        basis = int(deck_row["Programme"]) if "Programme" in deck_row.index else 0
        programm_teile.append(f"Deck {basis}")
        if programm_aktiv("Virtuelle Maschine"):
            programm_teile.append(f"{programm_anzeigename('Virtuelle Maschine')} +2")
        if modul_aktiv("Programmtr\u00e4ger"):
            programm_teile.append("Programmtr\u00e4ger +1")
        plus = datenbuchse_plus()
        if plus:
            programm_teile.append(f"Datenbuchse plus +{plus}")
        aktiv = liste_aus_state("selected_programme")
        st.write(
            f"{' | '.join(programm_teile)} = **{programm_limit(deck_row, aktiv)}**"
        )

        st.markdown("**Module**")
        modul_teile = ["Grund 1"]
        if programm_in_liste(
            liste_aus_state("selected_geraetemods"),
            "Modul Hinzuf\u00fcgen",
            "Modul hinzuf\u00fcgen",
        ):
            modul_teile.append("Modul Hinzuf\u00fcgen +1")
        if vorteil_aktiv("Deckbastler"):
            modul_teile.append(f"{vorteil_anzeigename('Deckbastler')} +1")
        st.write(f"{' | '.join(modul_teile)} = **{modul_limit()}** (Maximum 3)")


def deck_array_from_row(row: pd.Series) -> list[int]:
    return [int(row[attr]) for attr in ASDF_ATTRIBUTE]


def apply_deck_defaults(row: pd.Series) -> None:
    array = deck_array_from_row(row)
    st.session_state.deck_array = array
    st.session_state.asdf = {
        attr: value for attr, value in zip(ASDF_ATTRIBUTE, array)
    }
    for attr, value in zip(ASDF_ATTRIBUTE, array):
        st.session_state[f"{ASDF_SELECT_PREFIX}{attr}"] = value
    snapshot_deck_auswahl()


def on_deck_selected() -> None:
    snapshot_key("selected_deck")
    dateiname = CSV_FILES["Cyberdecks"]
    cyberdecks = load_csv(dateiname, csv_mtime(dateiname))
    if cyberdecks is None or cyberdecks.empty:
        return
    name = st.session_state.selected_deck
    if not ist_gueltiger_name(name):
        return
    treffer = cyberdecks.loc[cyberdecks["Name"].astype(str).str.strip() == str(name).strip()]
    if treffer.empty:
        return
    apply_deck_defaults(treffer.iloc[0])


def on_asdf_change(attr: str) -> None:
    new_val = st.session_state[f"{ASDF_SELECT_PREFIX}{attr}"]
    old_val = st.session_state.asdf[attr]
    if new_val == old_val:
        snapshot_deck_auswahl()
        return
    for other in ASDF_ATTRIBUTE:
        if other != attr and st.session_state.asdf[other] == new_val:
            st.session_state.asdf[other] = old_val
            st.session_state[f"{ASDF_SELECT_PREFIX}{other}"] = old_val
            break
    st.session_state.asdf[attr] = new_val
    snapshot_deck_auswahl()


def ensure_deck_state(cyberdecks: pd.DataFrame) -> None:
    restore_deck_auswahl()
    namen = item_names(cyberdecks)
    if not namen:
        return
    aktuelle = st.session_state.get("selected_deck")
    if aktuelle not in namen:
        gespeichert = st.session_state.get(save_key("selected_deck"))
        if gespeichert in namen:
            st.session_state.selected_deck = gespeichert
            aktuelle = gespeichert
        else:
            st.session_state.selected_deck = namen[0]
            row = row_by_name(cyberdecks, namen[0])
            if row is not None:
                apply_deck_defaults(row)
            snapshot_deck_auswahl()
            return
    asdf = st.session_state.get("asdf") or {}
    if not st.session_state.get("deck_array") or any(asdf.get(attr) is None for attr in ASDF_ATTRIBUTE):
        row = row_by_name(cyberdecks, aktuelle)
        if row is not None:
            apply_deck_defaults(row)
    snapshot_deck_auswahl()


def render_multiselect(
    label: str,
    dataframe: pd.DataFrame | None,
    key: str,
    *,
    farbe: str | None = None,
    css_klasse: str | None = None,
    max_selections: int | None = None,
    options: list[str] | None = None,
    on_change_fn=None,
) -> None:
    options = list(options) if options is not None else item_names(dataframe)
    if not options:
        st.warning(f"{label} konnten nicht geladen werden.")
        st.session_state[key] = []
        return

    aktuelle = liste_aus_state(key)
    if isinstance(aktuelle, str):
        aktuelle = [aktuelle]

    bereinigt = [name for name in aktuelle if ist_gueltiger_name(name) and name in options]
    if max_selections is not None and len(bereinigt) > int(max_selections):
        bereinigt = bereinigt[: int(max_selections)]
    st.session_state[key] = bereinigt
    snapshot_key(key)

    sichtbares_label = label
    versteckt = "visible"
    if farbe and css_klasse:
        st.markdown(
            f'<div class="{html.escape(css_klasse)}">'
            f'<span class="sr-pick-label" style="color:{html.escape(farbe)}">'
            f"{html.escape(label)}</span></div>",
            unsafe_allow_html=True,
        )
        versteckt = "collapsed"

    extra = {}
    if max_selections is not None:
        extra["max_selections"] = max(0, int(max_selections))
    callback = on_change_fn if on_change_fn is not None else on_liste_change
    if on_change_fn is None:
        extra["args"] = (key,)
    st.multiselect(
        sichtbares_label,
        options=options,
        key=key,
        placeholder="Auswahl...",
        accept_new_options=False,
        label_visibility=versteckt,
        on_change=callback,
        **extra,
    )


def render_farb_caption(text: str, css_klasse: str) -> None:
    st.markdown(
        f'<div class="{html.escape(css_klasse)}">{html.escape(text)}</div>',
        unsafe_allow_html=True,
    )


def programme_gruppen(dataframe: pd.DataFrame | None) -> list[tuple[str, list[str]]]:
    if dataframe is None or dataframe.empty:
        return []
    name_col = "Name" if "Name" in dataframe.columns else dataframe.columns[0]
    funktion_col = col_matching(dataframe, "funktion")
    buckets: dict[str, list[str]] = {}
    for _idx, row in dataframe.iterrows():
        name = str(row[name_col]).strip()
        if not ist_gueltiger_name(name):
            continue
        funktion = PROGRAMM_FUNKTION_SONSTIGE
        if funktion_col is not None:
            roh = str(row[funktion_col]).strip()
            if roh and roh.lower() not in LEERE_NAMEN:
                funktion = roh
        buckets.setdefault(funktion, [])
        if name not in buckets[funktion]:
            buckets[funktion].append(name)
    for funktion in buckets:
        buckets[funktion].sort(key=str.casefold)

    geordnet: list[tuple[str, list[str]]] = []
    gesehen: set[str] = set()
    for funktion in PROGRAMM_FUNKTION_REIHENFOLGE:
        if funktion in buckets:
            geordnet.append((funktion, buckets[funktion]))
            gesehen.add(funktion)
    for funktion in sorted(buckets, key=str.casefold):
        if funktion not in gesehen:
            geordnet.append((funktion, buckets[funktion]))
    return geordnet


def agent_stufe_wert() -> int:
    roh = st.session_state.get("agent_stufe", AGENT_STUFE_DEFAULT)
    try:
        return max(AGENT_STUFE_MIN, min(AGENT_STUFE_MAX, int(roh)))
    except (TypeError, ValueError):
        return AGENT_STUFE_DEFAULT


def render_agenten_panel() -> None:
    if "agent_stufe" not in st.session_state:
        gespeichert = st.session_state.get(save_key("agent_stufe"), AGENT_STUFE_DEFAULT)
        try:
            st.session_state.agent_stufe = max(
                AGENT_STUFE_MIN, min(AGENT_STUFE_MAX, int(gespeichert))
            )
        except (TypeError, ValueError):
            st.session_state.agent_stufe = AGENT_STUFE_DEFAULT
    st.markdown(
        f'<div class="sr-pick-programme">'
        f'<span class="sr-pick-label" style="color:{html.escape(FARBE_PROGRAMME)}">'
        "Agent</span></div>",
        unsafe_allow_html=True,
    )
    with st.expander("Werte", expanded=True):
        st.selectbox(
            "Stufe",
            options=list(range(AGENT_STUFE_MIN, AGENT_STUFE_MAX + 1)),
            key="agent_stufe",
            on_change=on_liste_change,
            args=("agent_stufe",),
        )
        snapshot_key("agent_stufe")
        stufe = agent_stufe_wert()
        angriff = finalwert("Angriff")
        schleicher = finalwert("Schleicher")
        daten = finalwert("Datenverarbeitung")
        firewall = finalwert("Firewall")
        initiative = daten + stufe
        st.markdown(
            f'<div class="sr-agent-box">'
            f"<p><strong>Matrixattribute</strong> (Ger\u00e4t): "
            f"Angriff {angriff} | Schleicher {schleicher} | "
            f"Datenverarbeitung {daten} | Firewall {firewall}</p>"
            f"<p><strong>Attribute</strong> (Stufe): "
            f"Logik {stufe} | Intuition {stufe} | Willenskraft {stufe}</p>"
            f"<p><strong>Fertigkeiten</strong> (Stufe): "
            f"Computer {stufe} | Hacking {stufe} | Matrixkampf {stufe}</p>"
            f"<p><strong>Initiative:</strong> Datenverarbeitung {daten} + Stufe {stufe} + 4W6"
            f" = {initiative} + 4W6</p>"
            "</div>",
            unsafe_allow_html=True,
        )


def render_programme_auswahl(dataframe: pd.DataFrame | None, deck_row: pd.Series) -> list[str]:
    gruppen = programme_gruppen(dataframe)
    alle_namen = [name for _funktion, namen in gruppen for name in namen]
    if not alle_namen:
        st.warning("Aktive Programme konnten nicht geladen werden.")
        st.session_state["selected_programme"] = []
        snapshot_key("selected_programme")
        return []

    gruppen_keys = [programm_funktion_key(funktion) for funktion, _namen in gruppen]
    st.session_state["_programm_gruppen_keys"] = gruppen_keys

    aktiv = [name for name in liste_aus_state("selected_programme") if name in alle_namen]
    st.session_state["selected_programme"] = aktiv
    snapshot_key("selected_programme")

    st.markdown(
        f'<div class="sr-pick-programme">'
        f'<span class="sr-pick-label" style="color:{html.escape(FARBE_PROGRAMME)}">'
        "Aktive Programme</span></div>",
        unsafe_allow_html=True,
    )
    limit = programm_limit(deck_row, aktiv)
    if len(aktiv) > limit:
        st.markdown(
            f'<div class="sr-hint sr-hint-programme">'
            f"{len(aktiv)} Programme aktiv, das Deck erlaubt {limit} Pl\u00e4tze."
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        render_farb_caption(f"{len(aktiv)} / {limit} Programmpl\u00e4tze", "sr-cap-programme")

    max_total = programm_max_auswahl(deck_row)
    panels = []
    if programm_in_liste(aktiv, "Agent"):
        panels.append(render_agenten_panel)
    if programm_in_liste(aktiv, "Verschleiern"):
        panels.append(render_verschleiern_panel)
    spalten_anzahl = 3
    for start in range(0, len(gruppen), spalten_anzahl):
        zeile = gruppen[start : start + spalten_anzahl]
        letzte_zeile = start + spalten_anzahl >= len(gruppen)
        spalten = st.columns(spalten_anzahl)
        for spalte, (funktion, namen) in zip(spalten, zeile):
            key = programm_funktion_key(funktion)
            in_gruppe = [name for name in aktiv if name in set(namen)]
            st.session_state[key] = in_gruppe
            andere = len(aktiv) - len(in_gruppe)
            max_sel = max(len(in_gruppe), max_total - andere)
            with spalte:
                render_multiselect(
                    funktion,
                    dataframe,
                    key,
                    farbe=FARBE_PROGRAMME,
                    css_klasse="sr-pick-programme",
                    max_selections=max_sel,
                    options=namen,
                    on_change_fn=on_programme_gruppen_change,
                )
        if letzte_zeile and panels:
            frei = spalten_anzahl - len(zeile)
            for spalte, panel in zip(spalten[len(zeile) :], panels[:frei]):
                with spalte:
                    panel()
            rest = panels[frei:]
            while rest:
                extra = st.columns(spalten_anzahl)
                for spalte, panel in zip(extra, rest[:spalten_anzahl]):
                    with spalte:
                        panel()
                rest = rest[spalten_anzahl:]
    return liste_aus_state("selected_programme")


DATENBUCHSE_NAME = "Datenbuchse plus"


def datenbuchse_cyber_stufe() -> int | None:
    """Stufe der eingebauten Cyberware, falls sie gew\u00e4hlt ist."""
    ziel = programm_schluessel(DATENBUCHSE_NAME)
    for name in liste_aus_state("selected_cyberware"):
        if programm_schluessel(name) != ziel:
            continue
        try:
            return max(0, min(3, int(st.session_state.get(cyber_stufe_key(name), 1))))
        except (TypeError, ValueError):
            return 1
    return None


def datenbuchse_plus() -> int:
    stufe = datenbuchse_cyber_stufe()
    if stufe is not None:
        return stufe
    return max(0, min(3, int(st.session_state.get("datenbuchse_plus", 0) or 0)))


def aktive_module() -> list[str]:
    return liste_aus_state("selected_module")


def modul_aktiv(*namen: str) -> bool:
    return programm_in_liste(aktive_module(), *namen)


def programm_limit(deck_row: pd.Series, selected_programme: list[str]) -> int:
    limit = int(deck_row["Programme"]) if "Programme" in deck_row.index else 0
    if programm_in_liste(selected_programme, "Virtuelle Maschine"):
        limit += 2
    if modul_aktiv("Programmtr\u00e4ger"):
        limit += 1
    return limit + datenbuchse_plus()


def programm_max_auswahl(deck_row: pd.Series) -> int:
    basis = int(deck_row["Programme"]) if "Programme" in deck_row.index else 0
    extra = 2 + datenbuchse_plus()
    if modul_aktiv("Programmtr\u00e4ger"):
        extra += 1
    return max(basis + extra, 1)


def aktive_programme() -> list[str]:
    return liste_aus_state("selected_programme")


def programm_schluessel(name: str) -> str:
    return normalize(name).replace(" ", "")


def programm_in_liste(namen: list[str], *ziele: str) -> bool:
    keys = {programm_schluessel(name) for name in namen if ist_gueltiger_name(name)}
    return any(programm_schluessel(ziel) in keys for ziel in ziele)


def programm_aktiv(*namen: str) -> bool:
    return programm_in_liste(aktive_programme(), *namen)


def vorteil_aktiv(*namen: str) -> bool:
    return programm_in_liste(liste_aus_state("selected_vorteile"), *namen)


def vorteil_anzeigename(*ziele: str) -> str:
    ziele_keys = {programm_schluessel(ziel) for ziel in ziele}
    for name in liste_aus_state("selected_vorteile"):
        if programm_schluessel(name) in ziele_keys:
            return name
    return ziele[0]


def programm_anzeigename(*ziele: str) -> str:
    ziele_keys = {programm_schluessel(ziel) for ziel in ziele}
    for name in aktive_programme():
        if programm_schluessel(name) in ziele_keys:
            return name
    return ziele[0]


def handlung_heisst(name: str, *ziele: str) -> bool:
    schluessel = programm_schluessel(name)
    return any(programm_schluessel(ziel) == schluessel for ziel in ziele)


def modus_schleichfahrt() -> bool:
    return bool(st.session_state.get("modus_schleichfahrt", False))


def aufmerksamkeit_wahl_aus(wert: object) -> str:
    text = str(wert).strip()
    if text in AUFMERKSAMKEIT_OPTIONEN:
        return text
    if text in {"1", "2"}:
        return f"+{text}"
    try:
        zahl = int(wert)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return AUFMERKSAMKEIT_DEFAULT
    return "+2" if zahl >= 2 else "+1"


def aufmerksamkeit_bonus_wahl() -> str:
    widget = st.session_state.get("aufmerksamkeit_bonus")
    if widget in AUFMERKSAMKEIT_OPTIONEN:
        return str(widget)
    gespeichert = st.session_state.get(save_key("aufmerksamkeit_bonus"), AUFMERKSAMKEIT_DEFAULT)
    return gespeichert if gespeichert in AUFMERKSAMKEIT_OPTIONEN else AUFMERKSAMKEIT_DEFAULT


def aufmerksamkeit_bonus() -> int:
    if not vorteil_aktiv("Aufmerksamkeit"):
        return 0
    return 2 if aufmerksamkeit_bonus_wahl() == "+2" else 1


def analytischer_geist_bonus(handlung: str) -> int:
    if not vorteil_aktiv("Analytischer Geist"):
        return 0
    return 2 if handlung_heisst(handlung, *ANALYTISCHER_GEIST_HANDLUNGEN) else 0


def programmiergenie_wahl_aus(wert: object) -> str:
    text = str(wert).strip()
    for name in PROGRAMMIERGENIE_HANDLUNGEN:
        if programm_schluessel(name) == programm_schluessel(text):
            return name
    return PROGRAMMIERGENIE_DEFAULT


def programmiergenie_handlung() -> str:
    widget = st.session_state.get("programmiergenie_handlung")
    if isinstance(widget, str) and widget.strip():
        return programmiergenie_wahl_aus(widget)
    gespeichert = st.session_state.get(save_key("programmiergenie_handlung"), PROGRAMMIERGENIE_DEFAULT)
    return programmiergenie_wahl_aus(gespeichert)


def programmiergenie_bonus(handlung: str) -> int:
    if not vorteil_aktiv("Programmiergenie"):
        return 0
    return 2 if handlung_heisst(handlung, programmiergenie_handlung()) else 0


def icu_bonus(handlung: str) -> int:
    if not vorteil_aktiv("I C U"):
        return 0
    return 2 if handlung_heisst(handlung, "Matrixwahrnehmung") else 0


def datenanomalie_bonus() -> int:
    return 2 if vorteil_aktiv("Datenanomalie") else 0


def render_programmiergenie_option() -> None:
    if not vorteil_aktiv("Programmiergenie"):
        return
    if "programmiergenie_handlung" not in st.session_state:
        st.session_state.programmiergenie_handlung = programmiergenie_handlung()
    st.selectbox(
        "Programmiergenie: +2 auf",
        options=list(PROGRAMMIERGENIE_HANDLUNGEN),
        key="programmiergenie_handlung",
        on_change=on_liste_change,
        args=("programmiergenie_handlung",),
    )
    snapshot_key("programmiergenie_handlung")


def render_aufmerksamkeit_option(*, kompakt: bool = False) -> None:
    if not vorteil_aktiv("Aufmerksamkeit"):
        return
    if "aufmerksamkeit_bonus" not in st.session_state:
        st.session_state.aufmerksamkeit_bonus = aufmerksamkeit_bonus_wahl()
    st.segmented_control(
        "Aufmerksamkeit" if kompakt else "Aufmerksamkeit auf Matrixwahrnehmung",
        options=list(AUFMERKSAMKEIT_OPTIONEN),
        key="aufmerksamkeit_bonus",
        required=True,
        width="stretch",
        on_change=on_liste_change,
        args=("aufmerksamkeit_bonus",),
    )
    snapshot_key("aufmerksamkeit_bonus")
    if not kompakt:
        st.caption("W\u00fcrfelpool-Bonus auf die Handlung Matrixwahrnehmung")


def verschleiern_stufe_wert() -> int:
    roh = st.session_state.get("verschleiern_stufe", VERSCHLEIERN_DEFAULT)
    try:
        return max(VERSCHLEIERN_MIN, min(VERSCHLEIERN_MAX, int(roh)))
    except (TypeError, ValueError):
        return VERSCHLEIERN_DEFAULT


def verschleiern_bonus() -> int:
    if not programm_aktiv("Verschleiern"):
        return 0
    return verschleiern_stufe_wert()


def render_verschleiern_panel() -> None:
    if not programm_aktiv("Verschleiern"):
        return
    if "verschleiern_stufe" not in st.session_state:
        gespeichert = st.session_state.get(save_key("verschleiern_stufe"), VERSCHLEIERN_DEFAULT)
        try:
            st.session_state.verschleiern_stufe = max(
                VERSCHLEIERN_MIN, min(VERSCHLEIERN_MAX, int(gespeichert))
            )
        except (TypeError, ValueError):
            st.session_state.verschleiern_stufe = VERSCHLEIERN_DEFAULT
    st.markdown(
        f'<div class="sr-pick-programme">'
        f'<span class="sr-pick-label" style="color:{html.escape(FARBE_PROGRAMME)}">'
        "Verschleiern</span></div>",
        unsafe_allow_html=True,
    )
    with st.expander("Werte", expanded=True):
        st.selectbox(
            "Schleicher +",
            options=list(range(VERSCHLEIERN_MIN, VERSCHLEIERN_MAX + 1)),
            key="verschleiern_stufe",
            on_change=on_liste_change,
            args=("verschleiern_stufe",),
        )
        snapshot_key("verschleiern_stufe")
        stufe = verschleiern_bonus()
        st.caption(
            f"Schleicher +{stufe}, daf\u00fcr Rauschen +{stufe} auf alle Matrixhandlungen "
            "mit dem Deck (durch Rauschunterdr\u00fcckung nicht senkbar)"
        )


def effektives_rauschen() -> tuple[int, int, list[str]]:
    umgebung = max(0, int(st.session_state.get("aktuelles_rauschen", 0) or 0))
    quellen: list[str] = []
    unter = 0
    if programm_aktiv("Signalreiniger"):
        unter += 2
        quellen.append(programm_anzeigename("Signalreiniger"))
    if modul_aktiv("Gerichteter Signalfilter"):
        unter += 2
        quellen.append("Gerichteter Signalfilter")
    # Rauschunterdr\u00fcckung wirkt nur auf Umgebungsrauschen, nicht auf das Rauschen,
    # das Verschleiern selbst erzeugt.
    eigen = verschleiern_bonus()
    roh = umgebung + eigen
    effektiv = max(0, umgebung - unter) + eigen
    if effektiv >= roh:
        return roh, effektiv, []
    return roh, effektiv, quellen


def sim_modus() -> str:
    wert = st.session_state.get("sim_modus") or SIM_DEFAULT
    return wert if wert in SIM_MODI else SIM_DEFAULT


def ist_heisser_sim() -> bool:
    return "heiss" in normalize(sim_modus())


def etac_modus() -> str:
    wert = st.session_state.get("etac_modus") or ETAC_DEFAULT
    return wert if wert in ETAC_MODI else ETAC_DEFAULT


def etac_budget() -> int:
    return int(ETAC_BUDGET.get(etac_modus(), 0))


def etac_punkte() -> tuple[int, int, int]:
    budget = etac_budget()
    if budget <= 0:
        return 0, 0, 0
    dv = max(0, int(st.session_state.get("etac_dv", 0) or 0))
    fw = max(0, int(st.session_state.get("etac_fw", 0) or 0))
    dv = min(budget, dv)
    fw = min(budget - dv, fw)
    return budget, dv, fw


def limit_plus(limit_zahl: str, bonus: int) -> str:
    if bonus <= 0 or not limit_zahl or limit_zahl == "-":
        return limit_zahl
    teile = []
    for teil in str(limit_zahl).split(" / "):
        try:
            teile.append(str(int(teil.strip()) + bonus))
        except (TypeError, ValueError):
            teile.append(teil)
    return " / ".join(teile)


def limit_plus_attr(limit_zahl: str, limit_label: str, attr: str, bonus: int) -> str:
    """Erhöht nur den Teil eines Limits, der zum genannten Matrixattribut gehört."""
    if bonus <= 0 or not limit_zahl or limit_zahl == "-":
        return limit_zahl
    werte = str(limit_zahl).split(" / ")
    labels = str(limit_label).split(" / ")
    if len(labels) != len(werte):
        return limit_plus(limit_zahl, bonus)
    ziel = normalize(attr)
    teile = []
    for wert, label in zip(werte, labels):
        if normalize(label).strip() == ziel:
            try:
                teile.append(str(int(wert.strip()) + bonus))
                continue
            except (TypeError, ValueError):
                pass
        teile.append(wert)
    return " / ".join(teile)


def boosterwolke_key(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", programm_schluessel(name)).strip("_")
    return f"{BOOSTERWOLKE_PREFIX}{slug or 'handlung'}"


def boosterwolke_stufe(name: str) -> str:
    widget_key = boosterwolke_key(name)
    widget = st.session_state.get(widget_key)
    if widget in BOOSTERWOLKE_STUFEN:
        return str(widget)
    gespeichert = (st.session_state.get("boosterwolke") or {}).get(name, "0")
    return gespeichert if gespeichert in BOOSTERWOLKE_STUFEN else "0"


def boosterwolke_bonus(name: str) -> int:
    return int(BOOSTERWOLKE_BONUS.get(boosterwolke_stufe(name), 0))


def on_boosterwolke_change(name: str, key: str) -> None:
    stufe = st.session_state.get(key, "0")
    if stufe not in BOOSTERWOLKE_STUFEN:
        stufe = "0"
    aktuelle = dict(st.session_state.get("boosterwolke") or {})
    aktuelle[name] = stufe
    st.session_state.boosterwolke = aktuelle


def anwenden_boosterwolke(
    name: str,
    pool: int | None,
    pool_detail: str,
    limit_zahl: str,
) -> tuple[int | None, str, str, int]:
    bonus = boosterwolke_bonus(name)
    if bonus <= 0:
        return pool, pool_detail, limit_zahl, 0
    if pool is not None:
        pool += bonus
        extra = f"Boosterwolke +{bonus}"
        pool_detail = f"{pool_detail} | {extra}" if pool_detail else extra
    limit_zahl = limit_plus(limit_zahl, bonus)
    return pool, pool_detail, limit_zahl, bonus


def anwenden_programm_regeln(
    handlung: str,
    pool: int | None,
    pool_detail: str,
    limit_zahl: str,
    limit_label: str = "",
) -> tuple[int | None, str, str, list[str]]:
    hinweise: list[str] = []
    extras: list[str] = []
    _roh, effektiv, rausch_quellen = effektives_rauschen()

    if pool is not None:
        if ist_heisser_sim():
            pool += 2
            extras.append("Hei\u00dfer SIM +2")
        if modus_schleichfahrt():
            pool -= 2
            extras.append("Schleichfahrt -2")
        geist_bonus = analytischer_geist_bonus(handlung)
        if geist_bonus:
            pool += geist_bonus
            extras.append(f"{vorteil_anzeigename('Analytischer Geist')} +{geist_bonus}")
        aufm_bonus = (
            aufmerksamkeit_bonus() if handlung_heisst(handlung, "Matrixwahrnehmung") else 0
        )
        if aufm_bonus:
            pool += aufm_bonus
            extras.append(f"{vorteil_anzeigename('Aufmerksamkeit')} +{aufm_bonus}")
        icu = icu_bonus(handlung)
        if icu:
            pool += icu
            extras.append(f"{vorteil_anzeigename('I C U')} +{icu}")
        genie_bonus = programmiergenie_bonus(handlung)
        if genie_bonus:
            pool += genie_bonus
            extras.append(f"{vorteil_anzeigename('Programmiergenie')} +{genie_bonus}")
        if programm_aktiv("Teerball") and handlung_heisst(handlung, "Programm abst\u00fcrzen lassen"):
            pool += 1
            extras.append(f"{programm_anzeigename('Teerball')} +1")
        if effektiv:
            pool -= effektiv
            extras.append(f"Rauschen -{effektiv}")
        hinweise.extend(rausch_quellen)
        if extras:
            pool_detail = f"{pool_detail} | " + " | ".join(extras)

    limit_regeln = (
        ("Eiliges Hacken", "Schleicher", ("Ausnutzen", "Ausbeuten")),
        ("Datei editieren", "Datenverarbeitung", ("Editieren",)),
        ("Icon aufsp\u00fcren / Datei aufsp\u00fcren", "Datenverarbeitung", ("Aufsp\u00fcren",)),
        ("Programm abst\u00fcrzen lassen", "Angriff", ("Teerball",)),
        ("Marke l\u00f6schen", "Angriff", ("Umlackieren",)),
    )
    for ziel_handlung, attr, programme in limit_regeln:
        if not programm_aktiv(*programme) or not handlung_heisst(handlung, ziel_handlung):
            continue
        limit_zahl = limit_plus_attr(limit_zahl, limit_label, attr, 2)
        hinweise.append(programm_anzeigename(*programme))

    return pool, pool_detail, limit_zahl, hinweise


def render_erlaeuterungen(
    dataframe: pd.DataFrame | None,
    selected: list[str],
    *,
    skip_asdf_programme: bool = False,
    css_klasse: str = "sr-hint-programme",
) -> None:
    if dataframe is None or not selected:
        return
    bloecke: list[str] = []
    for name in selected:
        if skip_asdf_programme and programm_asdf_bonus(name):
            continue
        text = item_text(dataframe, name).strip()
        if not text or text.lower() == "nan":
            continue
        bloecke.append(
            f"<p><strong>{html.escape(name)}:</strong> {html.escape(text)}</p>"
        )
    if not bloecke:
        return
    st.markdown(
        f'<div class="sr-hint {html.escape(css_klasse)}">{"".join(bloecke)}</div>',
        unsafe_allow_html=True,
    )


def render_deck_konfiguration(tables: dict[str, pd.DataFrame | None]) -> None:
    st.subheader("Deck-Konfiguration")
    cyberdecks = tables.get("Cyberdecks")
    if cyberdecks is None or cyberdecks.empty:
        st.warning("Cyberdecks konnten nicht geladen werden.")
        return

    ensure_deck_state(cyberdecks)
    deck_namen = item_names(cyberdecks)
    if not deck_namen:
        st.warning("Keine g\u00fcltigen Cyberdeck-Namen gefunden.")
        return

    aktuell = st.session_state.get("selected_deck")
    if aktuell not in deck_namen:
        aktuell = deck_namen[0]
        st.session_state.selected_deck = aktuell
    snapshot_key("selected_deck")
    st.selectbox(
        "Cyberdeck",
        options=deck_namen,
        key="selected_deck",
        on_change=on_deck_selected,
    )

    row = row_by_name(cyberdecks, st.session_state.selected_deck)
    if row is None:
        st.warning("Ausgew\u00e4hltes Deck wurde nicht gefunden.")
        return
    stufe_col = find_column(cyberdecks, "Ger")
    stufe = int(row[stufe_col]) if stufe_col else "-"
    programme_max = int(row["Programme"]) if "Programme" in row.index else "-"
    array_text = " / ".join(str(wert) for wert in st.session_state.deck_array)
    st.caption(
        f"Ger\u00e4testufe {stufe} | Programme {programme_max} | "
        f"Attribut-Array: {array_text}"
    )

    st.markdown("**ASDF-Verteilung** (jede Zahl aus dem Array genau einmal)")
    optionen = sorted({wert for wert in st.session_state.deck_array if wert is not None}, reverse=True)
    if not optionen:
        st.warning("Attribut-Array konnte nicht gelesen werden.")
        return
    wahl_spalten = st.columns(4)
    for spalte, attr in zip(wahl_spalten, ASDF_ATTRIBUTE):
        with spalte:
            widget_key = f"{ASDF_SELECT_PREFIX}{attr}"
            wert = (st.session_state.get("asdf") or {}).get(attr)
            if wert in optionen:
                st.session_state[widget_key] = wert
            elif st.session_state.get(widget_key) not in optionen:
                # z. B. nach einem Profilimport mit Werten aus einem anderen Deck-Array
                st.session_state[widget_key] = optionen[0]
                st.session_state.asdf[attr] = optionen[0]
            st.selectbox(
                attr,
                options=optionen,
                key=widget_key,
                on_change=on_asdf_change,
                args=(attr,),
            )
            render_asdf_final_chip(attr)

    with st.container():
        geraete = tables.get("Ger\u00e4temodifikationen")
        render_multiselect(
            "Ger\u00e4temodifikationen",
            geraete,
            "selected_geraetemods",
            farbe=FARBE_GERAETE,
            css_klasse="sr-pick-geraete",
            max_selections=1,
        )
    geraete_aktiv = liste_aus_state("selected_geraetemods")
    monitor_summe = geraetemod_monitor_bonus(tables)
    extra = f" | Zustandsmonitor {monitor_summe:+d}" if monitor_summe else ""
    render_farb_caption(
        f"{len(geraete_aktiv)} / 1 Modifikationen aktiv{extra}",
        "sr-cap-geraete",
    )
    if geraete is not None and geraete_aktiv:
        bloecke = []
        for name in geraete_aktiv:
            bloecke.append(
                f"<p><strong>{html.escape(name)}:</strong> "
                f"{html.escape(geraetemod_text(geraete, name))}</p>"
            )
        st.markdown(
            f'<div class="sr-hint sr-hint-geraete">{"".join(bloecke)}</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    render_programme_auswahl(tables.get("Programme"), row)
    aktiv = liste_aus_state("selected_programme")
    modul_col, vorteil_col = st.columns(2)
    with modul_col:
        render_multiselect(
            "Aktive Module",
            tables.get("Module"),
            "selected_module",
            farbe=FARBE_MODULE,
            css_klasse="sr-pick-module",
            max_selections=modul_limit(),
        )
        module_aktiv = liste_aus_state("selected_module")
        render_farb_caption(
            f"{len(module_aktiv)} / {modul_limit()} Module eingebaut",
            "sr-cap-module",
        )
    with vorteil_col:
        render_multiselect(
            "Vorteile",
            tables.get("Vorteile"),
            "selected_vorteile",
            farbe=FARBE_VORTEILE,
            css_klasse="sr-pick-vorteile",
        )
        vorteile_aktiv = liste_aus_state("selected_vorteile")
        render_farb_caption(f"{len(vorteile_aktiv)} Vorteile aktiv", "sr-cap-vorteile")
        if any(ist_uebertakter(name) for name in vorteile_aktiv):
            st.selectbox(
                "\u00dcbertakter: +1 auf",
                options=list(ASDF_ATTRIBUTE),
                key="uebertakter_attr",
                on_change=on_liste_change,
                args=("uebertakter_attr",),
            )
        render_aufmerksamkeit_option()
        render_programmiergenie_option()

    render_erlaeuterungen(
        tables.get("Programme"),
        aktiv,
        skip_asdf_programme=True,
        css_klasse="sr-hint-programme",
    )
    render_erlaeuterungen(
        tables.get("Module"),
        module_aktiv,
        css_klasse="sr-hint-module",
    )
    render_erlaeuterungen(
        tables.get("Vorteile"),
        vorteile_aktiv,
        css_klasse="sr-hint-vorteile",
    )

    st.divider()
    boni, details = sammeln_boni(tables)
    setze_finalwerte(boni)
    render_bonus_details(details)
    render_berechnungs_uebersicht(tables, details, row)
    snapshot_deck_auswahl()


def render_charakter_mods(tables: dict[str, pd.DataFrame | None]) -> None:
    st.subheader("Charakter-Mods")
    cyberware = tables.get("Cyberware / Bioware")
    vorteile = tables.get("Vorteile")

    render_multiselect("Cyberware / Bioware", cyberware, "selected_cyberware")
    ausgewaehlt = liste_aus_state("selected_cyberware")
    if cyberware is not None and ausgewaehlt:
        stufen_spalten = st.columns(min(3, len(ausgewaehlt)))
        for index, name in enumerate(ausgewaehlt):
            min_s, max_s = stufen_bereich(cyberware, name)
            key = cyber_stufe_key(name)
            with stufen_spalten[index % len(stufen_spalten)]:
                if min_s == max_s:
                    st.session_state[key] = min_s
                    st.caption(f"{name}: Stufe {min_s}")
                else:
                    if key not in st.session_state:
                        st.session_state[key] = min_s
                    st.number_input(
                        f"{name} (Stufe)",
                        min_value=min_s,
                        max_value=max_s,
                        step=1,
                        key=key,
                    )

    vorteil_spalte, = st.columns(1)
    with vorteil_spalte:
        render_multiselect(
            "Vorteile",
            vorteile,
            "selected_vorteile",
            farbe=FARBE_VORTEILE,
            css_klasse="sr-pick-vorteile",
        )
        vorteile_aktiv = liste_aus_state("selected_vorteile")
        if any(ist_uebertakter(name) for name in vorteile_aktiv):
            st.selectbox(
                "\u00dcbertakter: +1 auf",
                options=list(ASDF_ATTRIBUTE),
                key="uebertakter_attr",
                on_change=on_liste_change,
                args=("uebertakter_attr",),
            )
        render_aufmerksamkeit_option()
        render_programmiergenie_option()
        render_erlaeuterungen(vorteile, vorteile_aktiv, css_klasse="sr-hint-vorteile")

    st.divider()
    boni, details = sammeln_boni(tables)
    render_final_metrics(boni)
    render_bonus_details(details)
    snapshot_deck_auswahl()


LIMIT_FILTER_OPTIONEN = (
    "Alle",
    "Angriff",
    "Schleicher",
    "Datenverarbeitung",
    "Firewall",
    "Sonstige",
)
LIMIT_FILTER_ASDF = {
    "Angriff": "angriff",
    "Schleicher": "schleicher",
    "Datenverarbeitung": "datenverarbeitung",
    "Firewall": "firewall",
}


def art_kurz(art: str) -> str:
    name = normalize(art)
    if "frei" in name:
        return "Frei"
    if "einfach" in name:
        return "Einfach"
    if "komplex" in name:
        return "Komplex"
    if "unterbrechung" in name:
        return "Unterbrechung"
    if "variabel" in name:
        return "Variabel"
    return str(art).strip() or "-"


def limit_filter_passt(limit_text: str, auswahl: str) -> bool:
    if auswahl == "Alle":
        return True
    name = normalize(limit_text)
    asdf_treffer = any(schluessel in name for schluessel in LIMIT_FILTER_ASDF.values())
    if auswahl == "Sonstige":
        return not asdf_treffer
    ziel = LIMIT_FILTER_ASDF.get(auswahl)
    return bool(ziel and ziel in name)


def split_alternativen(text: str) -> list[str]:
    roh = str(text).strip()
    if not roh or normalize(roh) in {"ohne", "kein", "keine", "nan"}:
        return []
    teile = re.split(r"\s+oder\s+|/", roh, flags=re.IGNORECASE)
    return [teil.strip() for teil in teile if teil.strip()]


def token_wert(token: str) -> int | None:
    schluessel = normalize(token).replace(" ", "")
    if not schluessel:
        return None
    if "kriegsf" in schluessel:
        return int(st.session_state.get("skill_elektronische_kriegfuehrung", 0))
    for key, state_key in sorted(SKILL_LOOKUP.items(), key=lambda item: len(item[0]), reverse=True):
        if schluessel == key or key in schluessel:
            return int(st.session_state.get(state_key, 0))
    for attr in ALLE_ATTRIBUTE:
        attr_key = normalize(attr).replace(" ", "")
        if schluessel == attr_key:
            return finalwert(attr)
    return None


def wuerfelpool_aus_formel(formel: str) -> tuple[int | None, str]:
    optionen = []
    for alternativ in split_alternativen(formel) or ([str(formel).strip()] if str(formel).strip() else []):
        if normalize(alternativ) in {"ohne", "kein", "keine", "nan", "variablefertigkeit"}:
            continue
        teile = [teil.strip() for teil in alternativ.split("+") if teil.strip()]
        if not teile:
            continue
        summe = 0
        bekannt = False
        for teil in teile:
            wert = token_wert(teil)
            if wert is None:
                continue
            summe += wert
            bekannt = True
        if bekannt:
            optionen.append((summe, alternativ))
    if not optionen:
        return None, str(formel).strip()
    maximum = max(optionen, key=lambda item: item[0])[0]
    details = " | ".join(f"{label} = {wert}" for wert, label in optionen)
    return maximum, details


def limit_aus_asdf(limit_text: str) -> tuple[str, str]:
    werte = []
    labels = []
    rest = []
    for alternativ in split_alternativen(limit_text) or [str(limit_text).strip()]:
        clean = re.sub(r"\(.*?\)", "", alternativ).strip()
        if not clean or normalize(clean) in {"ohne", "kein", "keine", "nan"}:
            continue
        treffer = None
        for attr in ASDF_ATTRIBUTE:
            if normalize(attr) in normalize(clean):
                treffer = attr
                break
        if treffer:
            werte.append(str(finalwert(treffer)))
            labels.append(treffer)
        else:
            rest.append(clean)
    if werte:
        return " / ".join(werte), " / ".join(labels + rest)
    return "-", str(limit_text).strip() or "ohne"


def csv_anzeige(value: object, leer: str = "ohne") -> str:
    text = str(value).strip() if value is not None else ""
    if not text or text.lower() in {"nan", "none", "nat"}:
        return leer
    return text


def kaufmaennisch_runden(wert: float | int) -> int:
    return int(Decimal(str(wert)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def monitor_maximum(attribut_wert: int) -> int:
    return 8 + kaufmaennisch_runden(max(0, int(attribut_wert)) / 2)


def aktuelle_geraetestufe(tables: dict[str, pd.DataFrame | None]) -> int:
    cyberdecks = tables.get("Cyberdecks")
    if cyberdecks is None or cyberdecks.empty:
        return 0
    name = st.session_state.get("selected_deck") or st.session_state.get(save_key("selected_deck"))
    row = row_by_name(cyberdecks, str(name) if name else "")
    if row is None:
        return 0
    stufe_col = find_column(cyberdecks, "Ger")
    if not stufe_col:
        return 0
    return max(0, csv_int(row[stufe_col]))


def schadensmonitore(tables: dict[str, pd.DataFrame | None]) -> tuple[int, int, int]:
    matrix = monitor_maximum(aktuelle_geraetestufe(tables)) + geraetemod_monitor_bonus(tables)
    geistig = monitor_maximum(finalwert("Willenskraft"))
    koerperlich = monitor_maximum(finalwert("Konstitution"))
    return max(1, matrix), geistig, koerperlich


def schadensmalus() -> int:
    geistig_dmg = max(0, int(st.session_state.get("schaden_geistig", 0) or 0))
    koerperlich_dmg = max(0, int(st.session_state.get("schaden_koerperlich", 0) or 0))
    return (geistig_dmg // 3) + (koerperlich_dmg // 3)


def anwenden_schadensmalus(
    pool: int | None,
    pool_detail: str,
) -> tuple[int | None, str, int]:
    malus = schadensmalus()
    if pool is None or malus <= 0:
        return pool, pool_detail, malus
    pool -= malus
    extra = f"Schadensmalus -{malus}"
    pool_detail = f"{pool_detail} | {extra}" if pool_detail else extra
    return pool, pool_detail, malus


def render_schadens_panel(tables: dict[str, pd.DataFrame | None]) -> None:
    matrix_max, geistig_max, koerper_max = schadensmonitore(tables)
    matrix_hinweis = matrix_monitor_hinweis(tables)
    felder = (
        ("schaden_matrix", "Matrixschaden", matrix_max, matrix_hinweis),
        ("schaden_geistig", "Geistiger Schaden", geistig_max, ""),
        ("schaden_koerperlich", "K\u00f6rperlicher Schaden", koerper_max, ""),
    )
    with st.container():
        st.markdown('<div class="sr-schaden-anchor"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sr-schaden-panel"><strong>Schadensmonitore</strong></div>',
            unsafe_allow_html=True,
        )
        spalten = st.columns(3)
        for spalte, (key, label, maximum, hinweis) in zip(spalten, felder):
            with spalte:
                aktuell = max(0, int(st.session_state.get(key, 0) or 0))
                aktuell = min(aktuell, maximum)
                st.session_state[key] = aktuell
                st.number_input(
                    label,
                    min_value=0,
                    max_value=max(0, maximum),
                    step=1,
                    key=key,
                    on_change=on_liste_change,
                    args=(key,),
                )
                st.caption(f"Maximum {maximum}")
                if hinweis:
                    st.caption(hinweis)
                if key == "schaden_matrix" and modul_aktiv("H\u00e4rte"):
                    haerte = max(0, int(st.session_state.get("schaden_haerte", 0) or 0))
                    haerte = min(haerte, HAERTE_MONITOR)
                    st.session_state["schaden_haerte"] = haerte
                    st.number_input(
                        "H\u00e4rte",
                        min_value=0,
                        max_value=HAERTE_MONITOR,
                        step=1,
                        key="schaden_haerte",
                        on_change=on_liste_change,
                        args=("schaden_haerte",),
                    )
                    st.caption(f"Maximum {HAERTE_MONITOR}")
                    st.caption("Modul H\u00e4rte: eigener Matrix-Monitor")
        malus = schadensmalus()
        if malus:
            st.markdown(
                f'<p class="sr-schaden-malus">Schadensmalus -{malus}</p>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("Kein Schadensmalus")
        snapshot_key("schaden_matrix")
        snapshot_key("schaden_geistig")
        snapshot_key("schaden_koerperlich")
        snapshot_key("schaden_haerte")


def initiative_grundwerte() -> tuple[int, int, str, str]:
    intuition = finalwert("Intuition")
    if sim_modus() == "AR":
        reaktion = finalwert("Reaktion")
        wert = reaktion + intuition
        wuerfel = 1
        formel = "(Reaktion + Intuition) + 1W6"
        detail = f"Reaktion {reaktion} + Intuition {intuition}"
    else:
        daten = finalwert("Datenverarbeitung")
        wert = daten + intuition
        if ist_heisser_sim():
            wuerfel = 4
            formel = "(Datenverarbeitung + Intuition) + 4W6"
        else:
            wuerfel = 3
            formel = "(Datenverarbeitung + Intuition) + 3W6"
        detail = f"Datenverarbeitung {daten} + Intuition {intuition}"
        if modul_aktiv("Multidimensionaler Koprozessor", "Multidimensionaler Kopressor"):
            wuerfel = min(5, wuerfel + 1)
            formel = f"(Datenverarbeitung + Intuition) + {wuerfel}W6"
            detail = f"{detail} | Koprozessor +1W6"
    return wert, wuerfel, formel, detail


def widerstands_programmboni() -> tuple[int, list[str], int, list[str]]:
    schaden = 0
    schaden_extras: list[str] = []
    bio = 0
    bio_extras: list[str] = []
    if programm_aktiv("Panzer"):
        schaden += 2
        schaden_extras.append(f"{programm_anzeigename('Panzer')} +2")
    if programm_aktiv("Schutzschirm"):
        name = programm_anzeigename("Schutzschirm")
        schaden += 1
        bio += 1
        schaden_extras.append(f"{name} +1")
        bio_extras.append(f"{name} +1")
    if programm_aktiv("Biofeedback-Filter"):
        bio += 2
        bio_extras.append(f"{programm_anzeigename('Biofeedback-Filter')} +2")
    return schaden, schaden_extras, bio, bio_extras


def render_kampfwerte_box(tables: dict[str, pd.DataFrame | None]) -> None:
    basis_wert, basis_wuerfel, formel, detail = initiative_grundwerte()
    wert_mod = int(st.session_state.get("initiative_wert_mod", 0) or 0)
    wuerfel_mod = int(st.session_state.get("initiative_wuerfel_mod", 0) or 0)
    initiative_wert = max(0, basis_wert + wert_mod)
    initiative_wuerfel = max(1, basis_wuerfel + wuerfel_mod)
    if sim_modus() != "AR":
        initiative_wuerfel = min(5, initiative_wuerfel)

    intuition = finalwert("Intuition")
    willenskraft = finalwert("Willenskraft")
    logik = finalwert("Logik")
    firewall = finalwert("Firewall")
    schleicher = finalwert("Schleicher")
    stufe = aktuelle_geraetestufe(tables)
    vert_int = intuition + firewall
    vert_wil = willenskraft + firewall
    entdeckung = logik + schleicher
    entdeckung_extras: list[str] = []
    anomalie = datenanomalie_bonus()
    if anomalie:
        entdeckung += anomalie
        entdeckung_extras.append(f"{vorteil_anzeigename('Datenanomalie')} +{anomalie}")
    entdeckung_formel = f"Logik {logik} + Schleicher {schleicher}"
    if entdeckung_extras:
        entdeckung_formel += " | " + " | ".join(entdeckung_extras)
    schaden_bonus, schaden_extras, bio_bonus, bio_extras = widerstands_programmboni()
    widerstand = stufe + firewall + schaden_bonus
    biofeedback = willenskraft + firewall + bio_bonus
    schaden_formel = f"Ger\u00e4testufe {stufe} + Firewall {firewall}"
    if schaden_extras:
        schaden_formel += " | " + " | ".join(schaden_extras)
    bio_formel = f"Willenskraft {willenskraft} + Firewall {firewall}"
    if bio_extras:
        bio_formel += " | " + " | ".join(bio_extras)

    with st.container(border=True):
        st.markdown(
            '<div class="sr-kampf-line">Kampfwerte</div>',
            unsafe_allow_html=True,
        )
        init_col, vert_col, wider_col = st.columns(3)
        with init_col:
            st.markdown(
                f'<div class="sr-kampf-line">Initiative</div>'
                f'<div class="sr-kampf-value">{initiative_wert} + {initiative_wuerfel}W6</div>'
                f'<p class="sr-kampf-formel">{html.escape(formel)}</p>'
                f'<p class="sr-kampf-formel">{html.escape(detail)}</p>',
                unsafe_allow_html=True,
            )
            anpassung = st.columns(2)
            with anpassung[0]:
                st.number_input(
                    "Initiativwert \u00b1",
                    min_value=-20,
                    max_value=20,
                    step=1,
                    key="initiative_wert_mod",
                    on_change=on_liste_change,
                    args=("initiative_wert_mod",),
                )
            with anpassung[1]:
                st.number_input(
                    "Initiativw\u00fcrfel \u00b1",
                    min_value=-5,
                    max_value=5,
                    step=1,
                    key="initiative_wuerfel_mod",
                    on_change=on_liste_change,
                    args=("initiative_wuerfel_mod",),
                )
            if wert_mod or wuerfel_mod:
                st.caption(f"Basis {basis_wert} + {basis_wuerfel}W6")
            snapshot_key("initiative_wert_mod")
            snapshot_key("initiative_wuerfel_mod")
        with vert_col:
            vert_html = (
                '<div class="sr-kampf-line">Verteidigungsprobe</div>'
                f'<div class="sr-kampf-value">{vert_int} / {vert_wil}</div>'
                f'<p class="sr-kampf-line">Intuition + Firewall: {vert_int}</p>'
                f'<p class="sr-kampf-formel">Intuition {intuition} + Firewall {firewall}</p>'
                f'<p class="sr-kampf-line">Willenskraft + Firewall: {vert_wil}</p>'
                f'<p class="sr-kampf-formel">Willenskraft {willenskraft} + Firewall {firewall}</p>'
            )
            if modus_schleichfahrt():
                vert_html += (
                    '<div class="sr-kampf-sub">'
                    '<div class="sr-kampf-line">Entdeckung bei Schleichfahrt</div>'
                    f'<div class="sr-kampf-value">{entdeckung}</div>'
                    f'<p class="sr-kampf-formel">Logik + Schleicher</p>'
                    f'<p class="sr-kampf-formel">{html.escape(entdeckung_formel)}</p>'
                    "</div>"
                )
            st.markdown(vert_html, unsafe_allow_html=True)
        with wider_col:
            st.markdown(
                '<div class="sr-kampf-line">Schadenswiderstandsprobe</div>'
                f'<div class="sr-kampf-value">{widerstand}</div>'
                f'<p class="sr-kampf-formel">Ger\u00e4testufe + Firewall des Decks</p>'
                f'<p class="sr-kampf-formel">{html.escape(schaden_formel)}</p>'
                '<div class="sr-kampf-sub">'
                '<div class="sr-kampf-line">Widerstand Biofeedback</div>'
                f'<div class="sr-kampf-value">{biofeedback}</div>'
                f'<p class="sr-kampf-formel">Willenskraft + Firewall</p>'
                f'<p class="sr-kampf-formel">{html.escape(bio_formel)}</p>'
                "</div>",
                unsafe_allow_html=True,
            )


def render_aktions_dashboard(tables: dict[str, pd.DataFrame | None]) -> None:
    render_schadens_panel(tables)
    render_kampfwerte_box(tables)
    st.subheader("Aktions-Dashboard")
    handlungen = tables.get("Matrixhandlungen")
    if handlungen is None or handlungen.empty:
        st.warning("Matrixhandlungen konnten nicht geladen werden.")
        return

    name_col = "Name" if "Name" in handlungen.columns else handlungen.columns[0]
    art_col = col_matching(handlungen, "art") or (
        "Art" if "Art" in handlungen.columns else handlungen.columns[min(2, len(handlungen.columns) - 1)]
    )
    pool_col = col_matching(handlungen, "attribute", "handlung") or (
        handlungen.columns[3] if len(handlungen.columns) > 3 else None
    )
    limit_col = col_matching(handlungen, "limit") or (
        "Limit" if "Limit" in handlungen.columns else None
    )
    marken_col = (
        col_matching(handlungen, "marken")
        or col_matching(handlungen, "benoetigte")
        or (handlungen.columns[5] if len(handlungen.columns) > 5 else None)
    )
    defense_col = col_matching(handlungen, "verteidigung") or col_matching(
        handlungen, "attribute", "verteidigung"
    )
    text_col = find_column(handlungen, "Erl")
    if pool_col is None or limit_col is None or marken_col is None:
        st.warning("Die Matrixhandlungen-CSV hat nicht die erwarteten Spalten.")
        return

    suche_col, art_filter_col, limit_filter_col = st.columns([2, 1, 1])
    suche = suche_col.text_input("Suche", placeholder="Handlung suchen ...")
    arten = ["Alle"] + sorted(
        {art_kurz(str(wert)) for wert in handlungen[art_col].dropna().astype(str)}
    )
    art_filter = art_filter_col.selectbox("Aktionsart", arten)
    limit_filter = limit_filter_col.selectbox("Limit", LIMIT_FILTER_OPTIONEN)

    gefiltert = handlungen.copy()
    if suche.strip():
        needle = suche.strip().lower()
        maske = gefiltert[name_col].astype(str).str.lower().str.contains(needle, na=False, regex=False)
        if text_col:
            maske = maske | gefiltert[text_col].astype(str).str.lower().str.contains(needle, na=False, regex=False)
        gefiltert = gefiltert.loc[maske]
    if art_filter != "Alle":
        gefiltert = gefiltert.loc[
            gefiltert[art_col].astype(str).map(art_kurz) == art_filter
        ]
    if limit_filter != "Alle":
        gefiltert = gefiltert.loc[
            gefiltert[limit_col].astype(str).map(lambda wert: limit_filter_passt(wert, limit_filter))
        ]

    malus = schadensmalus()
    st.caption(
        f"{len(gefiltert)} Handlungen | W\u00fcrfelpool = Skill + Attribut"
        f"{' + Hei\u00dfer SIM' if ist_heisser_sim() else ''}"
        f"{' \u2212 Schleichfahrt' if modus_schleichfahrt() else ''}"
        f"{' \u2212 Rauschen' if effektives_rauschen()[1] else ''}"
        f"{f' \u2212 Schadensmalus {malus}' if malus else ''} | "
        "Verteidigung ohne Berechnung"
    )
    if gefiltert.empty:
        st.info("Keine Matrixhandlung entspricht dem Filter.")
        return

    for start in range(0, len(gefiltert), 2):
        karten = st.columns(2)
        chunk = gefiltert.iloc[start : start + 2]
        for spalte, (_idx, row) in zip(karten, chunk.iterrows()):
            with spalte:
                name = csv_anzeige(row[name_col], "-")
                art = art_kurz(str(row[art_col]))
                formel = csv_anzeige(row[pool_col])
                pool, pool_detail = wuerfelpool_aus_formel(formel)
                limit_zahl, limit_label = limit_aus_asdf(str(row[limit_col]))
                pool, pool_detail, limit_zahl, programm_hinweise = anwenden_programm_regeln(
                    name, pool, pool_detail, limit_zahl, limit_label
                )
                pool, pool_detail, malus = anwenden_schadensmalus(pool, pool_detail)
                pool, pool_detail, limit_zahl, booster_bonus = anwenden_boosterwolke(
                    name, pool, pool_detail, limit_zahl
                )
                if pool is not None:
                    pool = max(0, pool)
                marken = csv_anzeige(row[marken_col], "-")
                pool_text = "-" if pool is None else str(pool)
                handlung_text = pool_detail if pool is not None else formel
                verteidigung = csv_anzeige(row[defense_col]) if defense_col else "ohne"
                erl = csv_anzeige(row[text_col], "") if text_col else ""

                erl_html = ""
                if erl:
                    erl_html = (
                        "<details><summary>Erl\u00e4uterung</summary>"
                        f"<p>{html.escape(erl)}</p></details>"
                    )
                malus_html = ""
                if malus:
                    malus_html = (
                        f'<div class="sr-action-malus">Schadensmalus -{malus}</div>'
                    )
                limit_caption = limit_label if limit_label else "Limit"
                st.markdown(
                    '<div class="sr-action-card"></div>'
                    '<div class="sr-action">'
                    '<div class="sr-action-head">'
                    f"<strong>{html.escape(name)}</strong>"
                    f"<span>{html.escape(art)}</span>"
                    "</div>"
                    '<div class="sr-action-stats">'
                    "<div>"
                    f'<span class="sr-action-label">W\u00fcrfelpool</span>'
                    f'<span class="sr-action-value sr-action-number">{html.escape(pool_text)}</span>'
                    "</div>"
                    "<div>"
                    f'<span class="sr-action-label">Limit ({html.escape(limit_caption)})</span>'
                    f'<span class="sr-action-value sr-action-number">{html.escape(limit_zahl)}</span>'
                    "</div>"
                    "<div>"
                    '<span class="sr-action-label">Marken</span>'
                    f'<span class="sr-action-value">{html.escape(marken)}</span>'
                    "</div>"
                    "</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )
                st.markdown('<div class="sr-action-attrs-line"></div>', unsafe_allow_html=True)
                handlung_col, vert_col, booster_col = st.columns([2.1, 2.1, 1.05], gap="small")
                with handlung_col:
                    st.markdown(
                        '<span class="sr-action-label">Attribute f\u00fcr die Handlung</span>'
                        f'<span class="sr-action-text">{html.escape(handlung_text)}</span>',
                        unsafe_allow_html=True,
                    )
                with vert_col:
                    st.markdown(
                        '<span class="sr-action-label">Attribute f\u00fcr die Verteidigung</span>'
                        f'<span class="sr-action-text">{html.escape(verteidigung)}</span>',
                        unsafe_allow_html=True,
                    )
                with booster_col:
                    widget_key = boosterwolke_key(name)
                    if widget_key not in st.session_state:
                        st.session_state[widget_key] = boosterwolke_stufe(name)
                    st.select_slider(
                        "Boosterwolke",
                        options=list(BOOSTERWOLKE_STUFEN),
                        key=widget_key,
                        on_change=on_boosterwolke_change,
                        args=(name, widget_key),
                    )
                    aktuelle = dict(st.session_state.get("boosterwolke") or {})
                    aktuelle[name] = boosterwolke_stufe(name)
                    st.session_state.boosterwolke = aktuelle
                if vorteil_aktiv("Aufmerksamkeit") and handlung_heisst(name, "Matrixwahrnehmung"):
                    render_aufmerksamkeit_option(kompakt=True)
                if malus_html or erl_html:
                    st.markdown(
                        f'<div class="sr-action-foot">{malus_html}{erl_html}</div>',
                        unsafe_allow_html=True,
                    )
                if programm_hinweise:
                    st.caption("Programmunterst\u00fctzung: " + ", ".join(programm_hinweise))


def render_rohdaten(name: str, dataframe: pd.DataFrame | None) -> None:
    if dataframe is None:
        st.warning("Diese Tabelle konnte nicht geladen werden.")
        return
    st.subheader(name)
    st.caption(f"Quelle: {CSV_FILES[name]} | {len(dataframe)} Zeilen")
    st.dataframe(dataframe, width="stretch")


st.set_page_config(
    page_title="Shadowrun 5 Decker-Konsole",
    page_icon="5",
    layout="wide",
)
inject_theme()
init_session_state()
render_header()

tables = load_all_tables()
if tables.get("Cyberdecks") is not None and not tables["Cyberdecks"].empty:
    ensure_deck_state(tables["Cyberdecks"])
aktualisiere_finalwerte(tables)

render_sidebar_sicherung()
render_sidebar_decker_name()
render_sidebar_navigation()
render_sidebar_rauschen()

st.sidebar.segmented_control(
    "Sim",
    options=list(SIM_MODI),
    key="sim_modus",
    required=True,
    width="stretch",
)
if ist_heisser_sim():
    st.sidebar.caption("Hei\u00dfer SIM: +2 auf Matrixhandlungen")
st.sidebar.slider(
    "Overwatch-Wert",
    min_value=0,
    max_value=50,
    step=1,
    key="overwatch_wert",
)
render_sidebar_etac()
render_sidebar_datenbuchse()
st.sidebar.header("Charakterwerte")
render_number_inputs(CHARAKTERWERTE)

st.sidebar.header("Matrix-Fertigkeiten")
render_number_inputs(MATRIX_FERTIGKEITEN)

with st.sidebar.expander("Weitere Ansichten"):
    aktuelle = st.session_state.get("ansicht", PAGE_DECK)
    for name in (PAGE_MODS, *CSV_FILES.keys()):
        st.button(
            name,
            type="primary" if aktuelle == name else "secondary",
            width="stretch",
            key=f"nav_extra_{name}",
            on_click=gehe_zu,
            args=(name,),
        )

ansicht = st.session_state.get("ansicht", PAGE_DECK)
if ansicht == PAGE_DECK:
    render_deck_konfiguration(tables)
elif ansicht == PAGE_MODS:
    render_charakter_mods(tables)
elif ansicht == PAGE_DASHBOARD:
    render_aktions_dashboard(tables)
else:
    render_rohdaten(ansicht, tables.get(ansicht))
