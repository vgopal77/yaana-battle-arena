import random
import requests
import streamlit as st
from gamedata import SKINS, WEAPONS

st.set_page_config(page_title="Fortnite Battle Simulator", page_icon="💥", layout="wide")

# ── Fetch real Fortnite skin images ───────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_skin_image(skin_name):
    try:
        r = requests.get(
            "https://fortnite-api.com/v2/cosmetics/br/search",
            params={"name": skin_name, "language": "en"},
            timeout=5,
        )
        if r.status_code == 200:
            imgs = r.json().get("data", {}).get("images", {})
            return imgs.get("featured") or imgs.get("icon")
    except Exception:
        pass
    return None

for _sn in SKINS:
    get_skin_image(_sn)

# ── Styles ────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bangers&family=Rajdhani:wght@600;700&display=swap');

/* ── Background ── */
.stApp {
    background:
        linear-gradient(122deg, transparent 18%, rgba(255,195,0,0.14) 30%, rgba(255,195,0,0.07) 44%, transparent 55%),
        radial-gradient(ellipse 70% 55% at 50% 0%, rgba(100,30,220,0.30) 0%, transparent 60%),
        linear-gradient(160deg, #122d8c 0%, #091b60 35%, #050e35 70%, #020819 100%);
    background-attachment: fixed; min-height: 100vh;
}
.block-container { position: relative; z-index: 2; padding-top: 1.2rem !important; }
.stApp::before {
    content: ''; position: fixed; inset: 0;
    background: repeating-linear-gradient(0deg, transparent 0px, transparent 3px,
        rgba(0,0,0,0.04) 3px, rgba(0,0,0,0.04) 4px);
    pointer-events: none; z-index: 9999;
}

/* ── Global readable text ── */
.stApp, .stApp p, .stApp span, .stApp div, .stApp li,
.stMarkdown p, .stMarkdown li { color: #ffffff !important; }

/* ── Labels ── */
label, .stSelectbox label, .stTextInput label {
    color: #FFD100 !important;
    font-size: 11px !important; font-weight: 700 !important;
    letter-spacing: 2px !important; text-transform: uppercase !important;
    font-family: 'Rajdhani', sans-serif !important;
}

/* ── Text inputs ── */
.stTextInput > div > div > input {
    background: rgba(5, 10, 40, 0.90) !important;
    border: 2px solid rgba(255, 209, 0, 0.50) !important;
    border-radius: 6px !important;
    color: #ffffff !important;
    font-family: 'Bangers', sans-serif !important;
    font-size: 18px !important;
    letter-spacing: 3px !important;
    text-align: center !important;
    text-transform: uppercase !important;
}
.stTextInput > div > div > input:focus {
    border-color: #FFD100 !important;
    box-shadow: 0 0 16px rgba(255,209,0,0.40) !important;
}
.stTextInput > div > div > input::placeholder { color: rgba(255,255,255,0.30) !important; }

/* ── Selectboxes ── */
.stSelectbox > div > div {
    background: rgba(5, 10, 40, 0.90) !important;
    border: 1.5px solid rgba(255, 200, 0, 0.35) !important;
    color: #ffffff !important; border-radius: 6px !important;
}
.stSelectbox > div > div > div { color: #ffffff !important; }
.stSelectbox svg { fill: #FFD100 !important; }

/* ── Headings ── */
h1 { font-family: 'Bangers', sans-serif !important; letter-spacing: 4px !important; color: #fff !important; }
h2, h3 { font-family: 'Rajdhani', sans-serif !important; color: #ffffff !important; letter-spacing: 2px !important; }

/* ── Buttons ── */
.stButton > button {
    background: rgba(5,10,40,0.85) !important; color: #FFD100 !important;
    border: 1.5px solid rgba(255,209,0,0.55) !important; border-radius: 6px !important;
    font-family: 'Rajdhani', sans-serif !important; font-size: 15px !important;
    font-weight: 700 !important; letter-spacing: 2px !important; text-transform: uppercase !important;
    box-shadow: 0 0 10px rgba(255,209,0,0.12) !important; transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: rgba(255,209,0,0.10) !important;
    box-shadow: 0 0 26px rgba(255,209,0,0.45) !important;
    border-color: #FFD100 !important; transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #FFD100 0%, #FF9500 100%) !important;
    color: #050a1a !important; border: 2px solid #FFD100 !important;
    font-size: 17px !important; font-weight: 900 !important;
    box-shadow: 0 4px 24px rgba(255,175,0,0.55) !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #ffe040 0%, #ffaa00 100%) !important;
    box-shadow: 0 6px 36px rgba(255,180,0,0.80) !important; transform: translateY(-2px) !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: rgba(5,10,40,0.85) !important;
    border: 1px solid rgba(255,200,0,0.25) !important; border-radius: 7px !important;
    color: #FFD100 !important; font-family: 'Rajdhani', sans-serif !important; font-weight: 700 !important;
}
.streamlit-expanderContent {
    background: rgba(5,10,40,0.70) !important;
    border: 1px solid rgba(255,200,0,0.12) !important; border-radius: 0 0 7px 7px !important;
}
.streamlit-expanderContent p,
.streamlit-expanderContent li,
.streamlit-expanderContent td,
.streamlit-expanderContent th { color: #ffffff !important; }

/* ── Tables in expander ── */
table { color: #ffffff !important; }
th { color: #FFD100 !important; border-bottom: 1px solid rgba(255,209,0,0.3) !important; }
td { border-bottom: 1px solid rgba(255,255,255,0.08) !important; }

hr { border-color: rgba(255,200,0,0.18) !important; }

/* ── Ability pill ── */
.ability-pill {
    display: inline-block; border-radius: 4px;
    padding: 4px 16px; font-size: 12px; font-weight: 900;
    color: #050a1a; margin: 8px 0 4px; letter-spacing: 1.5px; text-transform: uppercase;
    font-family: 'Rajdhani', sans-serif;
}

/* ── HP bars ── */
.bar-wrap {
    background: rgba(0,0,0,0.50); border-radius: 3px; height: 22px;
    overflow: hidden; margin: 4px 0; border: 1px solid rgba(255,255,255,0.10);
}
.bar-fill {
    height: 100%; border-radius: 2px; display: flex; align-items: center;
    justify-content: center; font-size: 12px; font-weight: 900;
    color: #050a1a; min-width: 30px; font-family: 'Rajdhani', sans-serif;
}
.bar-label {
    font-size: 12px; font-weight: 700; color: #ffffff;
    letter-spacing: 1px; font-family: 'Rajdhani', sans-serif;
    text-transform: uppercase; margin-bottom: 2px;
}

/* ── Battle log ── */
.log-row {
    border-left: 3px solid #334; border-radius: 4px; padding: 8px 14px; margin: 4px 0;
    font-size: 14px; font-family: 'Rajdhani', sans-serif; letter-spacing: 0.5px;
    background: rgba(5,10,40,0.80); backdrop-filter: blur(6px); color: #ffffff;
}

/* ── Caption ── */
.stApp .stCaption, .stApp .stCaption p { color: #aabbdd !important; }
</style>
""", unsafe_allow_html=True)

# ── Background ghost overlay ──────────────────────────────────────────────────

def inject_background(s1_name, s2_name):
    img1 = get_skin_image(s1_name) or ""
    img2 = get_skin_image(s2_name) or ""
    i1 = (f'<img src="{img1}" style="position:absolute;left:-30px;bottom:0;height:90vh;'
          'opacity:0.11;filter:blur(1px);object-fit:contain;pointer-events:none;"/>') if img1 else ""
    i2 = (f'<img src="{img2}" style="position:absolute;right:-30px;bottom:0;height:90vh;'
          'opacity:0.11;filter:blur(1px);object-fit:contain;pointer-events:none;transform:scaleX(-1);"/>') if img2 else ""

    stars = "".join(
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="white" opacity="{o}"/>'
        for x,y,r,o in [
            (45,120,1.2,0.8),(130,45,1,0.6),(220,180,1.5,0.7),(310,70,1,0.5),
            (420,150,1.2,0.8),(520,30,1,0.6),(610,200,1.8,0.6),(700,90,1,0.7),
            (800,160,1.2,0.5),(900,40,1,0.8),(1000,130,1.5,0.6),(1100,75,1,0.7),
            (1200,190,1.2,0.6),(1300,55,1,0.5),(1400,140,1.8,0.7),(1500,20,1,0.6),
            (80,300,1,0.5),(170,350,1.5,0.7),(260,280,1,0.6),(350,370,1.2,0.8),
            (450,310,1,0.5),(550,390,1.5,0.6),(640,330,1,0.7),(730,270,1.2,0.5),
            (830,400,1,0.6),(930,290,1.8,0.7),(1020,360,1,0.5),(1120,310,1.2,0.6),
            (1220,380,1,0.7),(1320,300,1.5,0.5),(1420,350,1,0.8),(1520,280,1.2,0.6),
            (60,470,1.5,0.6),(150,520,1,0.7),(240,450,1.2,0.5),(330,500,1,0.8),
            (430,440,1.8,0.6),(530,490,1,0.5),(590,530,1.2,0.7),(680,460,1,0.6),
            (780,510,1.5,0.5),(880,445,1,0.8),(970,525,1.2,0.6),(1070,475,1,0.7),
        ]
    )

    st.markdown(f"""
<div style="position:fixed;inset:0;pointer-events:none;z-index:1;overflow:hidden;">
  <svg width="100%" height="100%" style="position:absolute;inset:0;opacity:0.6;">{stars}</svg>
  <div style="position:absolute;top:-60px;right:120px;width:550px;height:380px;
    background:linear-gradient(122deg,transparent 30%,rgba(255,200,0,0.08) 48%,
      rgba(255,200,0,0.04) 62%,transparent 78%);transform:rotate(-4deg);"></div>
  {i1}{i2}
  <div style="position:absolute;inset:0;
    background:radial-gradient(ellipse 85% 85% at 50% 50%,transparent 45%,rgba(2,8,25,0.70) 100%);"></div>
</div>
""", unsafe_allow_html=True)


# ── Render helpers ────────────────────────────────────────────────────────────

skin_names   = list(SKINS.keys())
weapon_names = list(WEAPONS.keys())


def hp_bar_color(pct):
    if pct > 0.60: return "#00e676"
    if pct > 0.30: return "#ff9100"
    return "#ff1744"


def render_bar(emoji, label, value, max_val, is_hp=True):
    pct   = value / max_val if max_val > 0 else 0
    color = hp_bar_color(pct) if is_hp else "#40c4ff"
    width = max(int(pct * 100), 2)
    st.markdown(f"""
<div style="margin:5px 0;">
  <div class="bar-label">{emoji} {label}: {value} / {max_val}</div>
  <div class="bar-wrap">
    <div class="bar-fill" style="width:{width}%;background:{color};
      box-shadow:0 0 10px {color}99;">{value}</div>
  </div>
</div>""", unsafe_allow_html=True)


def render_player_card(skin_name, weapon_name, health=None, shields=None):
    s = SKINS[skin_name]; w = WEAPONS[weapon_name]
    c = s["color"]
    r, g, b = int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)
    img_url = get_skin_image(skin_name) or ""

    bg_img = (f'<img src="{img_url}" style="position:absolute;right:-10px;bottom:0;'
              f'height:100%;max-height:240px;opacity:0.20;object-fit:contain;pointer-events:none;'
              f'filter:drop-shadow(0 0 14px rgba({r},{g},{b},0.7));"/>') if img_url else ""

    avatar = (
        f'<img src="{img_url}" style="width:120px;height:120px;object-fit:contain;'
        f'filter:drop-shadow(0 0 22px rgba({r},{g},{b},1));margin-bottom:6px;"/>'
        if img_url else
        f'<div style="font-size:88px;line-height:1.1;margin-bottom:6px;'
        f'filter:drop-shadow(0 0 22px rgba({r},{g},{b},0.95));">{s["avatar"]}</div>'
    )

    st.markdown(f"""
<div style="position:relative;overflow:hidden;border-radius:10px;margin-bottom:10px;
  background:linear-gradient(155deg,rgba({r},{g},{b},0.18) 0%,rgba(4,8,28,0.97) 60%);
  border:1.5px solid rgba({r},{g},{b},0.70);
  box-shadow:0 0 34px rgba({r},{g},{b},0.24),0 0 0 1px rgba(255,255,255,0.04) inset;
  padding:22px 16px 18px;text-align:center;min-height:260px;">
  <div style="position:absolute;top:0;left:0;right:0;height:3px;
    background:linear-gradient(90deg,transparent,#FFD100 40%,rgba({r},{g},{b},1) 75%,transparent);"></div>
  <div style="position:absolute;top:8px;left:8px;width:16px;height:16px;
    border-top:2px solid #FFD100;border-left:2px solid #FFD100;border-radius:2px 0 0 0;"></div>
  <div style="position:absolute;top:8px;right:8px;width:16px;height:16px;
    border-top:2px solid #FFD100;border-right:2px solid #FFD100;border-radius:0 2px 0 0;"></div>
  <div style="position:absolute;bottom:8px;left:8px;width:16px;height:16px;
    border-bottom:2px solid #FFD100;border-left:2px solid #FFD100;border-radius:0 0 0 2px;"></div>
  <div style="position:absolute;bottom:8px;right:8px;width:16px;height:16px;
    border-bottom:2px solid #FFD100;border-right:2px solid #FFD100;border-radius:0 0 2px 0;"></div>
  {bg_img}
  <div style="position:relative;z-index:1;">{avatar}</div>
  <div style="position:relative;z-index:1;font-family:'Bangers',sans-serif;font-size:24px;
    letter-spacing:5px;color:#fff;
    text-shadow:-2px -2px 0 #000,2px -2px 0 #000,-2px 2px 0 #000,2px 2px 0 #000,
    0 0 18px {c};margin-bottom:4px;">{skin_name.upper()}</div>
  <div style="position:relative;z-index:1;font-size:14px;color:#ffffff;font-weight:700;
    margin-bottom:10px;font-family:'Rajdhani',sans-serif;letter-spacing:1.5px;">
    {w['emoji']} &nbsp; {weapon_name.upper()}
  </div>
  <div class="ability-pill" style="background:#FFD100;position:relative;z-index:1;">
    ⚡ {s['ability'].upper()}
  </div>
  <div style="position:relative;z-index:1;font-size:12px;color:#ddeeff;font-weight:600;
    margin-top:5px;font-family:'Rajdhani',sans-serif;">{s['ability_desc']}</div>
</div>""", unsafe_allow_html=True)

    if health is not None:
        render_bar("❤️", "HP",      health,  SKINS[skin_name]["health"],  is_hp=True)
        render_bar("🛡️", "Shields", shields, SKINS[skin_name]["shields"], is_hp=False)


# ── Game state ────────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "p1_health":None,"p1_shields":None,"p2_health":None,"p2_shields":None,
        "p1_locked":None,"p2_locked":None,"p1_wpn_locked":None,"p2_wpn_locked":None,
        "p1_name_locked":"Player 1","p2_name_locked":"Player 2",
        "battle_log":[],"game_over":False,"winner_name":None,"winner_skin":None,
        "current_turn":"p1",
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v
    log = st.session_state.battle_log
    if log and not isinstance(log[0], tuple): st.session_state.battle_log = []

def start_match(s1, s2, w1, w2, n1, n2):
    st.session_state.p1_health       = SKINS[s1]["health"]
    st.session_state.p1_shields      = SKINS[s1]["shields"]
    st.session_state.p2_health       = SKINS[s2]["health"]
    st.session_state.p2_shields      = SKINS[s2]["shields"]
    st.session_state.p1_locked       = s1; st.session_state.p2_locked       = s2
    st.session_state.p1_wpn_locked   = w1; st.session_state.p2_wpn_locked   = w2
    st.session_state.p1_name_locked  = n1 or "Player 1"
    st.session_state.p2_name_locked  = n2 or "Player 2"
    st.session_state.battle_log      = []
    st.session_state.game_over       = False
    st.session_state.winner_name     = None
    st.session_state.winner_skin     = None
    st.session_state.current_turn    = "p1"

def reset_match():
    for k in ["p1_health","p1_shields","p2_health","p2_shields",
              "p1_locked","p2_locked","p1_wpn_locked","p2_wpn_locked",
              "game_over","winner_name","winner_skin"]:
        st.session_state[k] = None
    st.session_state.battle_log  = []
    st.session_state.current_turn = "p1"

def apply_damage(hp, sh, dmg):
    if sh > 0:
        a = min(sh, dmg); sh -= a; dmg -= a
    return max(0, hp - dmg), sh

def do_attack(atk_name, atk_skin, def_name, def_skin,
              weapon_name, def_hp_key, def_sh_key, atk_hp_key, atk_sh_key):
    w   = WEAPONS[weapon_name]
    atk = SKINS[atk_skin]
    dfd = SKINS[def_skin]
    log = []

    accuracy = min(0.98, w["accuracy"] + (atk.get("accuracy_bonus",0) if atk_skin=="Renegade Raider" else 0))
    if random.random() >= accuracy:
        log.append(("miss", f"💨 <b>{atk_name}</b> fired {w['emoji']} {weapon_name} — <b>MISSED!</b>"))
        st.session_state.battle_log = log + st.session_state.battle_log; return

    if def_skin == "Jonesy" and random.random() < dfd.get("dodge_chance", 0):
        log.append(("ability", f"🍀 <b>{def_name}</b> ({def_skin}) triggered <b>LUCKY BREAK</b> — dodged!"))
        st.session_state.battle_log = log + st.session_state.battle_log; return

    damage = w["damage"]; label = "Hit"; etype = "hit"
    if atk_skin == "Midas" and random.random() < atk.get("gold_chance", 0):
        damage = w["damage"] * 2; label = "👑 GOLDEN TOUCH — DOUBLE DMG"; etype = "crit"
    elif random.random() < w["crit_chance"]:
        damage = w["damage"] * 2; label = "💥 CRITICAL HIT"; etype = "crit"

    prev_hp = st.session_state[def_hp_key]; prev_sh = st.session_state[def_sh_key]
    new_hp, new_sh = apply_damage(prev_hp, prev_sh, damage)
    st.session_state[def_hp_key] = new_hp; st.session_state[def_sh_key] = new_sh

    sh_note = f" | 🛡️ {prev_sh}→{new_sh}" if prev_sh != new_sh else ""
    icon = "💥" if etype == "crit" else "🎯"
    log.append((etype,
        f"{icon} <b>{atk_name}</b> → <b>{def_name}</b> with {w['emoji']} {weapon_name}: "
        f"<b>{label}</b> for <b>{damage} dmg</b> | ❤️ {prev_hp}→{new_hp}{sh_note}"))

    if atk_skin == "Cuddle Team Leader":
        heal = atk.get("heal_amount", 0)
        old_hp = st.session_state[atk_hp_key]
        new_atk_hp = min(SKINS[atk_skin]["health"], old_hp + heal)
        st.session_state[atk_hp_key] = new_atk_hp
        if new_atk_hp > old_hp:
            log.append(("ability", f"🐻 <b>{atk_name}</b> — <b>BEAR HUG</b> healed +{heal} HP! ({old_hp}→{new_atk_hp})"))

    if new_hp <= 0:
        st.session_state.game_over    = True
        st.session_state.winner_name  = atk_name
        st.session_state.winner_skin  = atk_skin
        log.append(("win", f"🏆 <b>{atk_name}</b> has <b>ELIMINATED</b> <b>{def_name}</b>!"))

    st.session_state.battle_log = log + st.session_state.battle_log


# ── Layout ────────────────────────────────────────────────────────────────────

init_state()
game_active = st.session_state.p1_health is not None

_s1 = st.session_state.p1_locked or skin_names[0]
_s2 = st.session_state.p2_locked or skin_names[1]
inject_background(_s1, _s2)

# ── Title ──
n1_display = st.session_state.p1_name_locked if game_active else "Player 1"
n2_display = st.session_state.p2_name_locked if game_active else "Player 2"

st.markdown(f"""
<div style="text-align:center;padding:14px 0 6px;">
  <div style="font-family:'Bangers',sans-serif;font-size:50px;letter-spacing:7px;color:#fff;
    text-shadow:-3px -3px 0 #000,3px -3px 0 #000,-3px 3px 0 #000,3px 3px 0 #000,
    0 0 26px rgba(255,209,0,0.9),0 0 70px rgba(100,30,220,0.45);line-height:1.05;">
    💥 FORTNITE BATTLE SIMULATOR
  </div>
  <div style="font-family:'Rajdhani',sans-serif;font-size:15px;color:#FFD100;font-weight:700;
    letter-spacing:5px;margin-top:6px;text-transform:uppercase;">
    ⚡ &nbsp; {n1_display.upper()} &nbsp; vs &nbsp; {n2_display.upper()} &nbsp; ⚡
  </div>
</div>
""", unsafe_allow_html=True)

with st.expander("📖  HOW TO PLAY"):
    st.markdown("""
**Goal:** Reduce your opponent's HP to 0 to win the match.

**Steps:**
1. Enter your **name** so your friend knows who they're fighting.
2. Pick your **Skin** — each has a unique special ability.
3. Pick your **Weapon** — different damage, accuracy, and crit chance.
4. Hit **START MATCH** to lock in selections.
5. Take turns pressing your **ATTACK** button and watch the battle log!
6. First player to reach 0 HP loses. 🏆

**Skin Abilities:**
- 🧑 **Jonesy — Lucky Break:** 10% chance to dodge any incoming attack
- 👑 **Midas — Golden Touch:** 20% chance to deal triple damage on any hit
- 🐻 **Cuddle Team Leader — Bear Hug:** Heals +8 HP after every attack landed
- ✈️ **Renegade Raider — Aerial Precision:** +20% accuracy on all weapons

**Weapon Stats:**
| Weapon | Damage | Accuracy | Crit |
|---|---|---|---|
| 🔫 Scar | 35 | 85% | 15% |
| 🪖 Pump Shotgun | 70 | 55% | 25% |
| 🚀 Rocket Launcher | 90 | 65% | 10% |
| ⚡ Tactical SMG | 20 | 75% | 20% |
""")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    p1_name = st.text_input("🟦 Player 1 Name", value="Ayaan",
        placeholder="Enter your name...", key="p1_name_input", disabled=game_active,
        max_chars=16)
    p1_skin   = st.selectbox("Choose Skin",   skin_names,   key="p1_skin",   disabled=game_active)
    p1_weapon = st.selectbox("Choose Weapon", weapon_names, key="p1_weapon", disabled=game_active)
    locked_s1 = st.session_state.p1_locked    or p1_skin
    locked_w1 = st.session_state.p1_wpn_locked or p1_weapon
    render_player_card(locked_s1, locked_w1,
        st.session_state.p1_health  if game_active else None,
        st.session_state.p1_shields if game_active else None)

with col2:
    p2_name = st.text_input("🟥 Player 2 Name", value="Omer",
        placeholder="Enter your name...", key="p2_name_input", disabled=game_active,
        max_chars=16)
    p2_skin   = st.selectbox("Choose Skin",   skin_names,   index=1, key="p2_skin",   disabled=game_active)
    p2_weapon = st.selectbox("Choose Weapon", weapon_names, index=1, key="p2_weapon", disabled=game_active)
    locked_s2 = st.session_state.p2_locked    or p2_skin
    locked_w2 = st.session_state.p2_wpn_locked or p2_weapon
    render_player_card(locked_s2, locked_w2,
        st.session_state.p2_health  if game_active else None,
        st.session_state.p2_shields if game_active else None)

st.markdown("---")

if not game_active:
    if st.button("🎮  START MATCH", use_container_width=True, type="primary"):
        start_match(p1_skin, p2_skin, p1_weapon, p2_weapon, p1_name, p2_name)
        st.rerun()
else:
    n1 = st.session_state.p1_name_locked
    n2 = st.session_state.p2_name_locked

    if st.session_state.game_over:
        st.balloons()
        wname = st.session_state.winner_name
        wskin = st.session_state.winner_skin or skin_names[0]
        wc    = SKINS[wskin]["color"]
        st.markdown(f"""
<div style="text-align:center;padding:16px 0;">
  <div style="font-family:'Bangers',sans-serif;font-size:44px;letter-spacing:6px;color:#FFD100;
    text-shadow:-3px -3px 0 #000,3px -3px 0 #000,-3px 3px 0 #000,3px 3px 0 #000,
    0 0 32px #FFD100,0 0 70px {wc};">
    🏆 &nbsp; {wname.upper()} &nbsp; WINS! &nbsp; 🏆
  </div>
</div>""", unsafe_allow_html=True)
        if st.button("🔄  PLAY AGAIN", use_container_width=True, type="primary"):
            reset_match(); st.rerun()
    else:
        turn = st.session_state.current_turn
        cur_name  = n1 if turn == "p1" else n2
        cur_skin  = st.session_state.p1_locked if turn == "p1" else st.session_state.p2_locked
        cur_wpn   = st.session_state.p1_wpn_locked if turn == "p1" else st.session_state.p2_wpn_locked
        def_name  = n2 if turn == "p1" else n1
        def_skin  = st.session_state.p2_locked if turn == "p1" else st.session_state.p1_locked
        def_hp    = "p2_health" if turn == "p1" else "p1_health"
        def_sh    = "p2_shields" if turn == "p1" else "p1_shields"
        atk_hp    = "p1_health" if turn == "p1" else "p2_health"
        atk_sh    = "p1_shields" if turn == "p1" else "p2_shields"

        turn_color = "#4da6ff" if turn == "p1" else "#ff5252"
        st.markdown(f"""
<div style="text-align:center;padding:10px 16px;margin-bottom:10px;
  background:rgba(5,10,40,0.85);border:2px solid {turn_color};border-radius:8px;
  box-shadow:0 0 20px {turn_color}55;">
  <div style="font-family:'Bangers',sans-serif;font-size:22px;letter-spacing:4px;
    color:{turn_color};text-shadow:-1px -1px 0 #000,1px 1px 0 #000;">
    ⚡ &nbsp; IT'S {cur_name.upper()}'S TURN &nbsp; ⚡
  </div>
  <div style="font-family:'Rajdhani',sans-serif;font-size:13px;color:#aabbdd;
    margin-top:2px;letter-spacing:1px;">
    Pass the device to {cur_name} and press ATTACK
  </div>
</div>""", unsafe_allow_html=True)

        if st.button(f"💥  {cur_name.upper()} — ATTACK!", use_container_width=True, type="primary"):
            do_attack(cur_name, cur_skin, def_name, def_skin, cur_wpn,
                      def_hp, def_sh, atk_hp, atk_sh)
            if not st.session_state.game_over:
                st.session_state.current_turn = "p2" if turn == "p1" else "p1"
            st.rerun()

# ── Battle Log ────────────────────────────────────────────────────────────────

LOG_COLORS = {"hit":"#00e676","crit":"#FFD100","miss":"#6688aa","ability":"#ff4da6","win":"#FF5722"}

st.markdown("---")
st.markdown("""<div style="font-family:'Bangers',sans-serif;font-size:20px;color:#FFD100;
  letter-spacing:4px;margin-bottom:8px;
  text-shadow:-1px -1px 0 #000,1px 1px 0 #000;">📜 &nbsp; BATTLE LOG</div>""",
  unsafe_allow_html=True)

if st.session_state.battle_log:
    for entry_type, text in st.session_state.battle_log:
        border = LOG_COLORS.get(entry_type, "#334466")
        st.markdown(f'<div class="log-row" style="border-left-color:{border};">{text}</div>',
            unsafe_allow_html=True)
else:
    st.caption("No actions yet — enter names, pick your skin and weapon, then start the match!")
