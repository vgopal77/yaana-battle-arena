import random
import streamlit as st
from gamedata import SKINS, WEAPONS

st.set_page_config(page_title="Fortnite Battle Simulator", page_icon="💥", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@600;700&display=swap');

/* ── Fortnite Storm Sky Background ── */
.stApp {
    background:
        radial-gradient(ellipse 90% 55% at 78% 4%,  rgba(130, 35, 250, 0.60) 0%, transparent 52%),
        radial-gradient(ellipse 65% 50% at 12% 96%, rgba(15,  70, 220, 0.50) 0%, transparent 52%),
        radial-gradient(ellipse 55% 45% at 50% 50%, rgba(70,  10, 140, 0.30) 0%, transparent 68%),
        radial-gradient(ellipse 40% 30% at 90% 80%, rgba(200, 80,  10, 0.18) 0%, transparent 50%),
        linear-gradient(170deg, #02010c 0%, #07041a 45%, #03020e 100%);
    background-attachment: fixed;
    min-height: 100vh;
}

/* VR scanline overlay */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent 0px, transparent 3px,
        rgba(0, 200, 255, 0.010) 3px, rgba(0, 200, 255, 0.010) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

/* ── Global text ── */
.stApp p, .stApp span, .stApp div, .stApp li { color: #b8ccff; }
label, .stSelectbox label, .stMarkdown label { color: #5566aa !important; font-size: 11px !important; letter-spacing: 1.5px !important; text-transform: uppercase !important; }

/* ── Headings ── */
h1 { font-family: 'Orbitron', sans-serif !important; color: #fff !important;
     text-shadow: 0 0 18px rgba(0,210,255,0.95), 0 0 55px rgba(140,40,255,0.65) !important;
     letter-spacing: 4px !important; }
h2, h3 { font-family: 'Rajdhani', sans-serif !important; color: #ccdaff !important; letter-spacing: 2px !important; }

/* ── Selectboxes ── */
.stSelectbox > div > div {
    background: rgba(4, 6, 28, 0.88) !important;
    border: 1px solid rgba(0, 160, 255, 0.22) !important;
    color: #b8ccff !important; border-radius: 7px !important;
}
.stSelectbox svg { fill: #4477ff !important; }

/* ── Buttons base ── */
.stButton > button {
    background: rgba(4, 6, 28, 0.82) !important;
    color: #00e5ff !important;
    border: 1px solid rgba(0, 229, 255, 0.45) !important;
    border-radius: 8px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 15px !important; font-weight: 700 !important;
    letter-spacing: 2px !important; text-transform: uppercase !important;
    box-shadow: 0 0 14px rgba(0, 229, 255, 0.18) !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    box-shadow: 0 0 28px rgba(0, 229, 255, 0.55), 0 0 10px rgba(0,229,255,0.25) inset !important;
    border-color: rgba(0, 229, 255, 0.88) !important;
    transform: translateY(-1px) !important;
}
/* Primary (attack / start) buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, rgba(210, 55, 0, 0.75), rgba(140, 15, 0, 0.92)) !important;
    color: #fff !important;
    border: 1px solid rgba(255, 120, 20, 0.80) !important;
    box-shadow: 0 0 20px rgba(255, 100, 0, 0.42) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 38px rgba(255, 130, 0, 0.78) !important;
    transform: translateY(-2px) !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: rgba(4, 6, 28, 0.75) !important;
    border: 1px solid rgba(0, 160, 255, 0.18) !important;
    border-radius: 8px !important; color: #5566aa !important;
}
.streamlit-expanderContent {
    background: rgba(4, 6, 28, 0.55) !important;
    border: 1px solid rgba(0, 160, 255, 0.10) !important;
    border-radius: 0 0 8px 8px !important;
}

/* ── Divider ── */
hr { border-color: rgba(0, 160, 255, 0.14) !important; }

/* ── Ability pill ── */
.ability-pill {
    display: inline-block; border-radius: 999px;
    padding: 3px 14px; font-size: 11px; font-weight: 700;
    color: white; margin: 7px 0 3px; letter-spacing: 1px;
}

/* ── HP bars ── */
.bar-wrap {
    background: rgba(255,255,255,0.07);
    border-radius: 8px; height: 22px;
    overflow: hidden; margin: 3px 0;
    border: 1px solid rgba(255,255,255,0.05);
}
.bar-fill {
    height: 100%; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700; color: white; min-width: 28px;
}

/* ── Battle log rows ── */
.log-row {
    border-left: 3px solid #555;
    border-radius: 5px; padding: 7px 13px; margin: 4px 0;
    font-size: 13px; font-family: 'Rajdhani', sans-serif;
    background: rgba(4, 6, 28, 0.65);
    backdrop-filter: blur(6px);
}

/* ── Caption ── */
.stApp .stCaption p { color: #2d3a6a !important; }

@keyframes glowPulse {
    0%,100% { opacity: 0.75; }
    50%      { opacity: 1.00; }
}
</style>
""", unsafe_allow_html=True)

skin_names   = list(SKINS.keys())
weapon_names = list(WEAPONS.keys())


def hp_bar_color(pct):
    if pct > 0.6: return "#00e676"
    if pct > 0.3: return "#ff9100"
    return "#ff1744"


def render_bar(emoji, label, value, max_val, color):
    pct = value / max_val if max_val > 0 else 0
    bar_color = hp_bar_color(pct) if emoji == "❤️" else "#2979ff"
    width = max(int(pct * 100), 2)
    st.markdown(f"""
<div style="margin:5px 0;">
  <span style="font-size:12px; font-weight:600; color:#7788bb; letter-spacing:1px; font-family:'Rajdhani',sans-serif;">
    {emoji} {label}: {value} / {max_val}
  </span>
  <div class="bar-wrap">
    <div class="bar-fill" style="width:{width}%; background:{bar_color};
      box-shadow:0 0 10px {bar_color}88;">{value}</div>
  </div>
</div>""", unsafe_allow_html=True)


def render_player_card(skin_name, weapon_name, health=None, shields=None):
    s = SKINS[skin_name]
    w = WEAPONS[weapon_name]
    c = s["color"]
    r, g, b = int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)
    st.markdown(f"""
<div style="
  background: linear-gradient(145deg, rgba({r},{g},{b},0.12) 0%, rgba(3,2,18,0.90) 100%);
  border: 1px solid rgba({r},{g},{b},0.60);
  border-radius: 18px; padding: 26px 18px 20px; text-align: center; margin-bottom: 10px;
  box-shadow: 0 0 28px rgba({r},{g},{b},0.22), inset 0 0 50px rgba({r},{g},{b},0.04);
  backdrop-filter: blur(14px); position: relative; overflow: hidden;">
  <!-- top shimmer line -->
  <div style="position:absolute;top:0;left:8%;right:8%;height:2px;
    background:linear-gradient(90deg,transparent,rgba({r},{g},{b},1),transparent);border-radius:2px;"></div>
  <!-- corner accents -->
  <div style="position:absolute;top:10px;left:10px;width:16px;height:16px;
    border-top:2px solid rgba({r},{g},{b},0.7);border-left:2px solid rgba({r},{g},{b},0.7);border-radius:2px 0 0 0;"></div>
  <div style="position:absolute;top:10px;right:10px;width:16px;height:16px;
    border-top:2px solid rgba({r},{g},{b},0.7);border-right:2px solid rgba({r},{g},{b},0.7);border-radius:0 2px 0 0;"></div>
  <div style="position:absolute;bottom:10px;left:10px;width:16px;height:16px;
    border-bottom:2px solid rgba({r},{g},{b},0.7);border-left:2px solid rgba({r},{g},{b},0.7);border-radius:0 0 0 2px;"></div>
  <div style="position:absolute;bottom:10px;right:10px;width:16px;height:16px;
    border-bottom:2px solid rgba({r},{g},{b},0.7);border-right:2px solid rgba({r},{g},{b},0.7);border-radius:0 0 2px 0;"></div>
  <!-- avatar -->
  <div style="font-size:84px;line-height:1.1;margin-bottom:8px;
    filter:drop-shadow(0 0 22px rgba({r},{g},{b},0.95)) drop-shadow(0 0 8px rgba({r},{g},{b},0.6));">{s['avatar']}</div>
  <!-- name -->
  <div style="font-family:'Orbitron',sans-serif;font-size:17px;font-weight:900;color:{c};
    letter-spacing:4px;text-shadow:0 0 16px {c},0 0 32px {c}44;margin-bottom:5px;">{skin_name.upper()}</div>
  <!-- weapon -->
  <div style="font-size:13px;color:rgba(160,185,255,0.60);margin-bottom:8px;letter-spacing:1px;">{w['emoji']} {weapon_name}</div>
  <!-- ability -->
  <div class="ability-pill" style="
    background:linear-gradient(135deg,rgba({r},{g},{b},0.28),rgba({r},{g},{b},0.58));
    border:1px solid rgba({r},{g},{b},0.80);">⚡ {s['ability']}</div>
  <div style="font-size:11px;color:rgba(160,185,255,0.42);margin-top:4px;">{s['ability_desc']}</div>
</div>""", unsafe_allow_html=True)

    if health is not None:
        render_bar("❤️", "HP",      health,  SKINS[skin_name]["health"],  c)
        render_bar("🛡️", "Shields", shields, SKINS[skin_name]["shields"], "#2979ff")


# ── State ─────────────────────────────────────────────────────────────────────

def init_state():
    defaults = {
        "p1_health": None, "p1_shields": None,
        "p2_health": None, "p2_shields": None,
        "p1_locked": None, "p2_locked": None,
        "p1_wpn_locked": None, "p2_wpn_locked": None,
        "battle_log": [], "game_over": False, "winner": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    log = st.session_state.battle_log
    if log and not isinstance(log[0], tuple):
        st.session_state.battle_log = []


def start_match(s1, s2, w1, w2):
    st.session_state.p1_health    = SKINS[s1]["health"]
    st.session_state.p1_shields   = SKINS[s1]["shields"]
    st.session_state.p2_health    = SKINS[s2]["health"]
    st.session_state.p2_shields   = SKINS[s2]["shields"]
    st.session_state.p1_locked    = s1
    st.session_state.p2_locked    = s2
    st.session_state.p1_wpn_locked = w1
    st.session_state.p2_wpn_locked = w2
    st.session_state.battle_log   = []
    st.session_state.game_over    = False
    st.session_state.winner       = None


def reset_match():
    for k in ["p1_health","p1_shields","p2_health","p2_shields",
              "p1_locked","p2_locked","p1_wpn_locked","p2_wpn_locked","game_over","winner"]:
        st.session_state[k] = None
    st.session_state.battle_log = []


def apply_damage(hp, sh, dmg):
    if sh > 0:
        absorbed = min(sh, dmg); sh -= absorbed; dmg -= absorbed
    return max(0, hp - dmg), sh


def do_attack(atk_skin, def_skin, weapon_name,
              def_hp_key, def_sh_key, atk_hp_key, atk_sh_key):
    w   = WEAPONS[weapon_name]
    atk = SKINS[atk_skin]
    dfd = SKINS[def_skin]
    log = []

    accuracy = w["accuracy"]
    if atk_skin == "Renegade Raider":
        accuracy = min(0.98, accuracy + atk.get("accuracy_bonus", 0))

    if random.random() >= accuracy:
        log.append(("miss", f"💨 <b>{atk_skin}</b> fired {w['emoji']} {weapon_name} — <b>MISSED!</b>"))
        st.session_state.battle_log = log + st.session_state.battle_log
        return

    if def_skin == "Jonesy" and random.random() < dfd.get("dodge_chance", 0):
        log.append(("ability", f"🍀 <b>{def_skin}</b> triggered <b>Lucky Break</b> — dodged the attack!"))
        st.session_state.battle_log = log + st.session_state.battle_log
        return

    damage = w["damage"]; label = "Hit"; entry_type = "hit"
    if atk_skin == "Midas" and random.random() < atk.get("gold_chance", 0):
        damage = w["damage"] * 3; label = "👑 GOLDEN TOUCH — TRIPLE DMG"; entry_type = "crit"
    elif random.random() < w["crit_chance"]:
        damage = w["damage"] * 2; label = "💥 CRITICAL HIT"; entry_type = "crit"

    prev_hp = st.session_state[def_hp_key]
    prev_sh = st.session_state[def_sh_key]
    new_hp, new_sh = apply_damage(prev_hp, prev_sh, damage)
    st.session_state[def_hp_key] = new_hp
    st.session_state[def_sh_key] = new_sh

    sh_note = f" | 🛡️ {prev_sh}→{new_sh}" if prev_sh != new_sh else ""
    icon = "💥" if entry_type == "crit" else "🎯"
    log.append((entry_type,
        f"{icon} <b>{atk_skin}</b> → <b>{def_skin}</b> with {w['emoji']} {weapon_name}: "
        f"<b>{label}</b> for <b>{damage} dmg</b> | ❤️ {prev_hp}→{new_hp}{sh_note}"
    ))

    if atk_skin == "Cuddle Team Leader":
        heal = atk.get("heal_amount", 0)
        old_hp = st.session_state[atk_hp_key]
        new_atk_hp = min(SKINS[atk_skin]["health"], old_hp + heal)
        st.session_state[atk_hp_key] = new_atk_hp
        if new_atk_hp > old_hp:
            log.append(("ability", f"🐻 <b>{atk_skin}</b> — <b>Bear Hug</b> healed +{heal} HP! ({old_hp}→{new_atk_hp})"))

    if new_hp <= 0:
        st.session_state.game_over = True
        st.session_state.winner    = atk_skin
        log.append(("win", f"🏆 <b>{atk_skin}</b> has <b>ELIMINATED</b> <b>{def_skin}</b>!"))

    st.session_state.battle_log = log + st.session_state.battle_log


# ── Layout ────────────────────────────────────────────────────────────────────

init_state()
game_active = st.session_state.p1_health is not None

st.markdown("""
<div style="text-align:center; padding: 10px 0 4px;">
  <div style="font-family:'Orbitron',sans-serif; font-size:36px; font-weight:900; color:#fff;
    text-shadow:0 0 20px rgba(0,210,255,0.95), 0 0 60px rgba(140,40,255,0.65); letter-spacing:5px;">
    💥 FORTNITE BATTLE SIMULATOR
  </div>
  <div style="font-family:'Rajdhani',sans-serif; font-size:14px; color:#334488;
    letter-spacing:5px; margin-top:6px; text-transform:uppercase;">
    ⚡ &nbsp; Ayaan &nbsp;vs&nbsp; Omer &nbsp; ⚡ &nbsp; — &nbsp; May the best player win
  </div>
</div>
""", unsafe_allow_html=True)

with st.expander("📖  HOW TO PLAY"):
    st.markdown("""
**Goal:** Reduce your opponent's HP to 0 to win the match.

**Steps:**
1. **Choose your skin** — each has a unique special ability that can swing the battle.
2. **Choose your weapon** — differs in damage, accuracy, and crit chance.
3. Hit **Start Match** to lock in your choices.
4. Take turns pressing your **ATTACK** button and watch the battle log.
5. First to reach 0 HP loses. 🏆

**Skin Abilities:**
- 🧑 **Jonesy — Lucky Break:** 10% chance to fully dodge any incoming attack
- 👑 **Midas — Golden Touch:** 20% chance to deal **triple** damage
- 🐻 **Cuddle Team Leader — Bear Hug:** Heals +8 HP after every attack landed
- ✈️ **Renegade Raider — Aerial Precision:** +20% accuracy on all weapons

**Weapons:**
- 🔫 **Scar** — High accuracy, reliable all-rounder
- 🪖 **Pump Shotgun** — Massive damage, low accuracy. High risk, high reward
- 🚀 **Rocket Launcher** — Highest damage in the game, moderate accuracy
- ⚡ **Tactical SMG** — Lower per-shot damage but fires fast with solid accuracy

**Battle Log:** 🟡 Crit/Golden · 🟢 Hit · ⚫ Miss · 🔴 Elimination · 🩷 Ability
""")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🟦 Ayaan")
    p1_skin   = st.selectbox("Choose Skin",   skin_names,   key="p1_skin",   disabled=game_active)
    p1_weapon = st.selectbox("Choose Weapon", weapon_names, key="p1_weapon", disabled=game_active)
    locked_s1 = st.session_state.p1_locked    or p1_skin
    locked_w1 = st.session_state.p1_wpn_locked or p1_weapon
    render_player_card(locked_s1, locked_w1,
        st.session_state.p1_health  if game_active else None,
        st.session_state.p1_shields if game_active else None)

with col2:
    st.markdown("### 🟥 Omer")
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
        start_match(p1_skin, p2_skin, p1_weapon, p2_weapon)
        st.rerun()
else:
    if st.session_state.game_over:
        st.balloons()
        winner = st.session_state.winner
        c = SKINS[winner]["color"]
        st.markdown(
            f"<div style='text-align:center; font-family:Orbitron,sans-serif; font-size:28px; "
            f"font-weight:900; color:{c}; text-shadow:0 0 24px {c}; letter-spacing:4px; "
            f"padding:12px 0;'>🏆 &nbsp; {winner.upper()} &nbsp; WINS THE MATCH! &nbsp; 🏆</div>",
            unsafe_allow_html=True)
        if st.button("🔄  PLAY AGAIN", use_container_width=True, type="primary"):
            reset_match(); st.rerun()
    else:
        a1, a2 = st.columns(2)
        with a1:
            if st.button("💥  AYAAN ATTACKS!", use_container_width=True, type="primary"):
                do_attack(st.session_state.p1_locked, st.session_state.p2_locked,
                          st.session_state.p1_wpn_locked,
                          "p2_health","p2_shields","p1_health","p1_shields")
                st.rerun()
        with a2:
            if st.button("💥  OMER ATTACKS!", use_container_width=True, type="primary"):
                do_attack(st.session_state.p2_locked, st.session_state.p1_locked,
                          st.session_state.p2_wpn_locked,
                          "p1_health","p1_shields","p2_health","p2_shields")
                st.rerun()

# ── Battle Log ────────────────────────────────────────────────────────────────

LOG_COLORS = {"hit":"#00e676","crit":"#FFD700","miss":"#445566","ability":"#E91E63","win":"#FF5722"}

st.markdown("---")
st.markdown("""<div style="font-family:'Orbitron',sans-serif; font-size:14px;
  color:#334488; letter-spacing:3px; margin-bottom:8px;">📜 &nbsp; BATTLE LOG</div>""",
  unsafe_allow_html=True)

if st.session_state.battle_log:
    for entry_type, text in st.session_state.battle_log:
        border = LOG_COLORS.get(entry_type, "#334488")
        st.markdown(
            f'<div class="log-row" style="border-left-color:{border};">{text}</div>',
            unsafe_allow_html=True)
else:
    st.caption("No actions yet — start a match and attack!")
