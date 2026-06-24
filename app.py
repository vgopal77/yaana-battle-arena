import random
import requests
import streamlit as st
import streamlit.components.v1 as components
from gamedata import SKINS, WEAPONS

st.set_page_config(page_title="Fortnite Battle Simulator", page_icon="💥", layout="wide")

# ── Constants ─────────────────────────────────────────────────────────────────
ARENA_SIZE = 7          # columns 0–6
COVER_POS  = {2, 4}    # natural cover: 50% damage reduction when standing here

# ── Skin image API ────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_skin_image(skin_name):
    try:
        r = requests.get("https://fortnite-api.com/v2/cosmetics/br/search",
            params={"name": skin_name, "language": "en"}, timeout=5)
        if r.status_code == 200:
            imgs = r.json().get("data", {}).get("images", {})
            return imgs.get("featured") or imgs.get("icon")
    except Exception:
        pass
    return None

for _sn in SKINS:
    get_skin_image(_sn)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bangers&family=Rajdhani:wght@600;700&display=swap');

.stApp {
    background:
        linear-gradient(122deg, transparent 18%, rgba(255,195,0,0.14) 30%, rgba(255,195,0,0.07) 44%, transparent 55%),
        radial-gradient(ellipse 70% 55% at 50% 0%, rgba(100,30,220,0.30) 0%, transparent 60%),
        linear-gradient(160deg, #122d8c 0%, #091b60 35%, #050e35 70%, #020819 100%);
    background-attachment: fixed; min-height: 100vh;
}
.block-container { position: relative; z-index: 2; padding-top: 1rem !important; }
.stApp::before {
    content:''; position:fixed; inset:0;
    background:repeating-linear-gradient(0deg,transparent 0px,transparent 3px,rgba(0,0,0,0.04) 3px,rgba(0,0,0,0.04) 4px);
    pointer-events:none; z-index:9999;
}
.stApp,.stApp p,.stApp span,.stApp div,.stApp li,.stMarkdown p,.stMarkdown li { color:#ffffff !important; }
label,.stSelectbox label,.stTextInput label {
    color:#FFD100 !important; font-size:11px !important; font-weight:700 !important;
    letter-spacing:2px !important; text-transform:uppercase !important;
    font-family:'Rajdhani',sans-serif !important;
}
.stTextInput>div>div>input {
    background:rgba(5,10,40,0.90) !important; border:2px solid rgba(255,209,0,0.50) !important;
    border-radius:6px !important; color:#ffffff !important;
    font-family:'Bangers',sans-serif !important; font-size:18px !important;
    letter-spacing:3px !important; text-align:center !important; text-transform:uppercase !important;
}
.stTextInput>div>div>input:focus { border-color:#FFD100 !important; box-shadow:0 0 16px rgba(255,209,0,0.4) !important; }
.stSelectbox>div>div {
    background:rgba(5,10,40,0.90) !important; border:1.5px solid rgba(255,200,0,0.35) !important;
    color:#ffffff !important; border-radius:6px !important;
}
.stSelectbox>div>div>div { color:#ffffff !important; }
.stSelectbox svg { fill:#FFD100 !important; }
h1 { font-family:'Bangers',sans-serif !important; letter-spacing:4px !important; color:#fff !important; }
h2,h3 { font-family:'Rajdhani',sans-serif !important; color:#ffffff !important; letter-spacing:2px !important; }
.stButton>button {
    background:rgba(5,10,40,0.85) !important; color:#FFD100 !important;
    border:1.5px solid rgba(255,209,0,0.55) !important; border-radius:6px !important;
    font-family:'Rajdhani',sans-serif !important; font-size:15px !important;
    font-weight:700 !important; letter-spacing:2px !important; text-transform:uppercase !important;
    transition:all 0.15s ease !important;
}
.stButton>button:hover {
    background:rgba(255,209,0,0.10) !important; box-shadow:0 0 26px rgba(255,209,0,0.45) !important;
    border-color:#FFD100 !important; transform:translateY(-1px) !important;
}
.stButton>button[kind="primary"] {
    background:linear-gradient(135deg,#FFD100 0%,#FF9500 100%) !important;
    color:#050a1a !important; border:2px solid #FFD100 !important;
    font-size:17px !important; font-weight:900 !important;
    box-shadow:0 4px 24px rgba(255,175,0,0.55) !important;
}
.stButton>button[kind="primary"]:hover {
    background:linear-gradient(135deg,#ffe040 0%,#ffaa00 100%) !important;
    box-shadow:0 6px 36px rgba(255,180,0,0.80) !important; transform:translateY(-2px) !important;
}
.stButton>button:disabled { opacity:0.35 !important; transform:none !important; }
.streamlit-expanderHeader {
    background:rgba(5,10,40,0.85) !important; border:1px solid rgba(255,200,0,0.25) !important;
    border-radius:7px !important; color:#FFD100 !important; font-family:'Rajdhani',sans-serif !important;
}
hr { border-color:rgba(255,200,0,0.18) !important; }
.bar-wrap { background:rgba(0,0,0,0.50); border-radius:3px; height:20px; overflow:hidden; margin:3px 0; border:1px solid rgba(255,255,255,0.10); }
.bar-fill { height:100%; border-radius:2px; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:900; color:#050a1a; min-width:28px; font-family:'Rajdhani',sans-serif; }
.log-row { border-left:3px solid #334; border-radius:4px; padding:8px 14px; margin:3px 0; font-size:14px; font-family:'Rajdhani',sans-serif; background:rgba(5,10,40,0.80); }
</style>
""", unsafe_allow_html=True)

# ── Background ghost overlay ──────────────────────────────────────────────────
def inject_background(s1, s2):
    i1 = get_skin_image(s1) or ""; i2 = get_skin_image(s2) or ""
    t1 = f'<img src="{i1}" style="position:absolute;left:-30px;bottom:0;height:88vh;opacity:0.10;filter:blur(1px);object-fit:contain;pointer-events:none;"/>' if i1 else ""
    t2 = f'<img src="{i2}" style="position:absolute;right:-30px;bottom:0;height:88vh;opacity:0.10;filter:blur(1px);object-fit:contain;pointer-events:none;transform:scaleX(-1);"/>' if i2 else ""
    stars = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="white" opacity="{o}"/>'
        for x,y,r,o in [(45,120,1.2,0.8),(130,45,1,0.6),(310,70,1,0.5),(420,150,1.2,0.8),
            (610,200,1.8,0.5),(700,90,1,0.6),(900,40,1,0.7),(1100,75,1,0.6),(1300,55,1,0.5),
            (80,300,1,0.5),(350,370,1.2,0.7),(640,330,1,0.6),(930,290,1.8,0.6),(1220,380,1,0.7),
            (60,470,1.5,0.5),(430,440,1.8,0.6),(780,510,1.5,0.4),(1170,520,1.5,0.4)])
    st.markdown(f"""<div style="position:fixed;inset:0;pointer-events:none;z-index:1;overflow:hidden;">
  <svg width="100%" height="100%" style="position:absolute;inset:0;opacity:0.6;">{stars}</svg>
  {t1}{t2}
  <div style="position:absolute;inset:0;background:radial-gradient(ellipse 85% 85% at 50% 50%,transparent 45%,rgba(2,8,25,0.70) 100%);"></div>
</div>""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
skin_names   = list(SKINS.keys())
weapon_names = list(WEAPONS.keys())

def hp_bar_color(pct):
    if pct > 0.60: return "#00e676"
    if pct > 0.30: return "#ff9100"
    return "#ff1744"

def render_hp_bars(n1, s1, n2, s2):
    c1, c2 = st.columns(2)
    for col, name, skin_key, hp_key, sh_key in [
        (c1, n1, s1, "p1_health", "p1_shields"),
        (c2, n2, s2, "p2_health", "p2_shields"),
    ]:
        with col:
            hp  = st.session_state[hp_key]  or 0
            sh  = st.session_state[sh_key]  or 0
            s   = SKINS[skin_key]
            mhp = s["health"]; msh = s["shields"]
            hpct = hp / mhp if mhp else 0
            spct = sh / msh if msh else 0
            hc = hp_bar_color(hpct); sc = "#40c4ff"
            img = get_skin_image(skin_key) or ""
            img_tag = f'<img src="{img}" style="width:36px;height:36px;object-fit:contain;border-radius:50%;border:2px solid {s["color"]};margin-right:8px;vertical-align:middle;"/>' if img else f'<span style="font-size:24px;margin-right:8px;">{s["avatar"]}</span>'
            st.markdown(f"""
<div style="background:rgba(4,8,28,0.85);border:1.5px solid rgba(255,200,0,0.25);
  border-radius:10px;padding:10px 14px;margin-bottom:6px;">
  <div style="display:flex;align-items:center;margin-bottom:6px;">
    {img_tag}
    <div>
      <div style="font-family:'Bangers',sans-serif;font-size:16px;letter-spacing:2px;
        color:{s["color"]};text-shadow:-1px -1px 0 #000,1px 1px 0 #000;">{name.upper()}</div>
      <div style="font-size:10px;color:#aabbdd;font-family:'Rajdhani',sans-serif;">{skin_key}</div>
    </div>
    {'<span style="margin-left:auto;font-size:20px;">🛡️</span>' if st.session_state.get(f"{'p1' if hp_key=='p1_health' else 'p2'}_in_cover") else ''}
  </div>
  <div style="font-size:11px;color:#aabbdd;font-family:Rajdhani,sans-serif;text-transform:uppercase;letter-spacing:1px;">❤️ HP: {hp}/{mhp}</div>
  <div class="bar-wrap"><div class="bar-fill" style="width:{max(int(hpct*100),2)}%;background:{hc};box-shadow:0 0 8px {hc}88;">{hp}</div></div>
  <div style="font-size:11px;color:#aabbdd;font-family:Rajdhani,sans-serif;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">🛡️ SHIELDS: {sh}/{msh}</div>
  <div class="bar-wrap"><div class="bar-fill" style="width:{max(int(spct*100),2)}%;background:{sc};box-shadow:0 0 8px {sc}88;">{sh}</div></div>
</div>""", unsafe_allow_html=True)

def render_arena(n1, n2):
    p1c = st.session_state.p1_col
    p2c = st.session_state.p2_col
    cov1 = st.session_state.p1_in_cover
    cov2 = st.session_state.p2_in_cover
    s1 = SKINS[st.session_state.p1_locked]
    s2 = SKINS[st.session_state.p2_locked]

    cells = ""
    for i in range(ARENA_SIZE):
        if i == p1c:
            icon  = "🛡️" if cov1 else s1["avatar"]
            bg    = f"rgba({int(s1['color'][1:3],16)},{int(s1['color'][3:5],16)},{int(s1['color'][5:7],16)},0.30)"
            bdr   = s1["color"]
            lbl   = n1[:5].upper()
            sub   = "IN COVER" if cov1 else ""
        elif i == p2c:
            icon  = "🛡️" if cov2 else s2["avatar"]
            bg    = f"rgba({int(s2['color'][1:3],16)},{int(s2['color'][3:5],16)},{int(s2['color'][5:7],16)},0.30)"
            bdr   = s2["color"]
            lbl   = n2[:5].upper()
            sub   = "IN COVER" if cov2 else ""
        elif i in COVER_POS:
            icon = "🌲"; bg = "rgba(15,50,15,0.50)"; bdr = "#3a8a3a"
            lbl = "COVER"; sub = "−50% DMG"
        else:
            icon = "·"; bg = "rgba(0,0,0,0.15)"; bdr = "rgba(255,255,255,0.07)"
            lbl = ""; sub = ""

        cells += f"""<div style="flex:1;background:{bg};border:1.5px solid {bdr};border-radius:8px;
          padding:10px 4px;text-align:center;min-width:55px;">
          <div style="font-size:28px;line-height:1.1;">{icon}</div>
          <div style="font-size:9px;color:white;font-weight:700;letter-spacing:1px;margin-top:3px;">{lbl}</div>
          <div style="font-size:8px;color:rgba(255,255,255,0.5);margin-top:1px;">{sub}</div>
        </div>"""

    dist = abs(p1c - p2c)
    range_label = ("🔴 POINT BLANK" if dist <= 1 else
                   "🟡 CLOSE RANGE" if dist <= 3 else "🟢 LONG RANGE")

    st.markdown(f"""
<div style="background:rgba(0,0,10,0.80);border:1px solid rgba(255,200,0,0.28);
  border-radius:12px;padding:14px 12px;margin:6px 0;">
  <div style="font-family:'Bangers',sans-serif;font-size:11px;color:#FFD100;
    letter-spacing:3px;margin-bottom:8px;text-align:center;">⚔️ BATTLE ARENA — MOVE INTO 🌲 COVER FOR PROTECTION</div>
  <div style="display:flex;gap:5px;justify-content:center;align-items:stretch;">{cells}</div>
  <div style="text-align:center;margin-top:10px;font-family:'Rajdhani',sans-serif;font-size:13px;color:#aabbdd;">
    {range_label} &nbsp;|&nbsp; Distance: <b style="color:#FFD100;">{dist}</b> tile(s)
    &nbsp;|&nbsp; Shotgun 🪖 deals <b style="color:{'#ff4444' if dist<=2 else '#ffaa00' if dist<=4 else '#44aa44'};">
    {'MAX' if dist<=2 else 'MED' if dist<=4 else 'LOW'}</b> damage at this range
  </div>
</div>""", unsafe_allow_html=True)

def render_weapon_hotbar(wpn1, wpn2, sel, phase_is_attack, player_key):
    """Two weapon slots like Fortnite hotbar"""
    for i, wname in enumerate([wpn1, wpn2]):
        w = WEAPONS[wname]
        is_sel = (sel == i)
        bg     = "linear-gradient(135deg,#FFD100,#FF9500)" if is_sel else "rgba(5,10,40,0.88)"
        bdr    = "#FFD100" if is_sel else "rgba(255,255,255,0.15)"
        tc     = "#050a1a" if is_sel else "#ffffff"
        glow   = "0 0 20px rgba(255,209,0,0.60)" if is_sel else "none"
        num_c  = "#050a1a" if is_sel else "#FFD100"

        # Range hint text
        rng = {"Pump Shotgun":"Best CLOSE","Scar":"All ranges","Rocket Launcher":"All ranges","Tactical SMG":"Close-Med"}
        rng_txt = rng.get(wname, "")

        st.markdown(f"""
<div style="background:{bg};border:2px solid {bdr};border-radius:10px;padding:14px 10px;
  text-align:center;box-shadow:{glow};position:relative;cursor:pointer;">
  <div style="position:absolute;top:6px;right:8px;font-family:'Bangers',sans-serif;
    font-size:13px;color:{num_c};letter-spacing:1px;">[{i+1}]</div>
  <div style="font-size:36px;margin-bottom:4px;">{w['emoji']}</div>
  <div style="font-family:'Bangers',sans-serif;font-size:15px;letter-spacing:2px;color:{tc};">{wname.upper()}</div>
  <div style="font-size:11px;color:{tc};opacity:0.75;font-family:'Rajdhani',sans-serif;">
    DMG {w['damage']} · ACC {int(w['accuracy']*100)}%
  </div>
  <div style="font-size:10px;color:{tc};opacity:0.6;font-family:'Rajdhani',sans-serif;margin-top:2px;">
    📍 {rng_txt}
  </div>
</div>""", unsafe_allow_html=True)

# ── State management ──────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "p1_health":None,"p1_shields":None,"p2_health":None,"p2_shields":None,
        "p1_col":1,"p2_col":5,"p1_in_cover":False,"p2_in_cover":False,
        "p1_locked":None,"p2_locked":None,
        "p1_wpn1":None,"p1_wpn2":None,"p2_wpn1":None,"p2_wpn2":None,
        "p1_wpn_sel":0,"p2_wpn_sel":0,
        "p1_name_locked":"Player 1","p2_name_locked":"Player 2",
        "turn_phase":"p1_move",
        "battle_log":[],"game_over":False,"winner_name":None,"winner_skin":None,
    }
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v
    log = st.session_state.battle_log
    if log and not isinstance(log[0], tuple): st.session_state.battle_log = []

def start_match(s1,s2,w1a,w1b,w2a,w2b,n1,n2):
    st.session_state.p1_health=SKINS[s1]["health"]; st.session_state.p1_shields=SKINS[s1]["shields"]
    st.session_state.p2_health=SKINS[s2]["health"]; st.session_state.p2_shields=SKINS[s2]["shields"]
    st.session_state.p1_col=1;     st.session_state.p2_col=5
    st.session_state.p1_in_cover=False; st.session_state.p2_in_cover=False
    st.session_state.p1_locked=s1; st.session_state.p2_locked=s2
    st.session_state.p1_wpn1=w1a;  st.session_state.p1_wpn2=w1b
    st.session_state.p2_wpn1=w2a;  st.session_state.p2_wpn2=w2b
    st.session_state.p1_wpn_sel=0; st.session_state.p2_wpn_sel=0
    st.session_state.p1_name_locked=n1 or "Player 1"
    st.session_state.p2_name_locked=n2 or "Player 2"
    st.session_state.turn_phase="p1_move"
    st.session_state.battle_log=[]; st.session_state.game_over=False
    st.session_state.winner_name=None; st.session_state.winner_skin=None

def reset_match():
    for k in ["p1_health","p1_shields","p2_health","p2_shields","p1_col","p2_col",
              "p1_in_cover","p2_in_cover","p1_locked","p2_locked",
              "p1_wpn1","p1_wpn2","p2_wpn1","p2_wpn2",
              "game_over","winner_name","winner_skin"]:
        st.session_state[k] = None
    st.session_state.battle_log=[]; st.session_state.turn_phase="p1_move"
    st.session_state.p1_wpn_sel=0; st.session_state.p2_wpn_sel=0

def apply_damage(hp, sh, dmg):
    if sh > 0:
        a=min(sh,dmg); sh-=a; dmg-=a
    return max(0,hp-dmg), sh

def get_range_mult(wname, distance):
    if wname == "Pump Shotgun":
        if distance <= 1: return 1.8
        if distance <= 2: return 1.3
        if distance <= 3: return 0.8
        return 0.35
    if wname == "Tactical SMG":
        if distance <= 2: return 1.2
        if distance <= 4: return 1.0
        return 0.65
    if wname == "Rocket Launcher": return 1.1
    return 1.0  # Scar: consistent

def do_fire(atk_name, atk_skin_key, def_name, def_skin_key,
            weapon_name, def_hp_key, def_sh_key, atk_hp_key, atk_sh_key,
            atk_col_key, def_col_key, def_cover_key):
    w    = WEAPONS[weapon_name]
    atk  = SKINS[atk_skin_key]
    dfd  = SKINS[def_skin_key]
    log  = []

    accuracy = min(0.98, w["accuracy"] +
        (atk.get("accuracy_bonus",0) if atk_skin_key=="Renegade Raider" else 0))

    if random.random() >= accuracy:
        log.append(("miss", f"💨 <b>{atk_name}</b> fired {w['emoji']} {weapon_name} — <b>MISSED!</b>"))
        st.session_state.battle_log = log + st.session_state.battle_log; return

    if def_skin_key == "Jonesy" and random.random() < dfd.get("dodge_chance",0):
        log.append(("ability", f"🍀 <b>{def_name}</b> — <b>LUCKY BREAK!</b> Dodged!"))
        st.session_state.battle_log = log + st.session_state.battle_log; return

    dist   = abs(st.session_state[atk_col_key] - st.session_state[def_col_key])
    r_mult = get_range_mult(weapon_name, dist)
    damage = int(w["damage"] * r_mult)
    label  = "Hit"; etype = "hit"

    if atk_skin_key == "Midas" and random.random() < atk.get("gold_chance",0):
        damage = int(damage * 2); label = "👑 GOLDEN TOUCH — DOUBLE DMG"; etype = "crit"
    elif random.random() < w["crit_chance"]:
        damage = int(damage * 1.75); label = "💥 CRITICAL HIT"; etype = "crit"

    # Cover protection
    in_cover = st.session_state[def_cover_key]
    cover_note = ""
    if in_cover:
        damage = int(damage * 0.5)
        cover_note = " | 🌲 COVER blocked 50%!"
        st.session_state[def_cover_key] = False  # cover used up on hit

    prev_hp = st.session_state[def_hp_key]; prev_sh = st.session_state[def_sh_key]
    new_hp, new_sh = apply_damage(prev_hp, prev_sh, damage)
    st.session_state[def_hp_key]=new_hp; st.session_state[def_sh_key]=new_sh

    sh_note = f" | 🛡️ {prev_sh}→{new_sh}" if prev_sh!=new_sh else ""
    icon = "💥" if etype=="crit" else "🎯"
    log.append((etype,
        f"{icon} <b>{atk_name}</b>→<b>{def_name}</b> [{weapon_name} · dist:{dist}]: "
        f"<b>{label}</b> <b>{damage} dmg</b>{sh_note}{cover_note} | ❤️ {prev_hp}→{new_hp}"))

    if atk_skin_key == "Cuddle Team Leader":
        heal=atk.get("heal_amount",0); old=st.session_state[atk_hp_key]
        new_hp2=min(SKINS[atk_skin_key]["health"], old+heal)
        st.session_state[atk_hp_key]=new_hp2
        if new_hp2>old: log.append(("ability",f"🐻 <b>{atk_name}</b> — BEAR HUG +{heal} HP!"))

    if new_hp <= 0:
        st.session_state.game_over=True; st.session_state.winner_name=atk_name
        st.session_state.winner_skin=atk_skin_key
        log.append(("win",f"🏆 <b>{atk_name}</b> ELIMINATED <b>{def_name}</b>!"))

    st.session_state.battle_log = log + st.session_state.battle_log

# ── Keyboard JS injector ──────────────────────────────────────────────────────
def inject_keys(phase):
    components.html(f"""<!DOCTYPE html><html><body><script>
(function(){{
  if(window.parent.__fnHandler)
    window.parent.document.removeEventListener('keydown',window.parent.__fnHandler);
  const phase="{phase}";
  window.parent.__fnHandler=function(e){{
    if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA') return;
    const k=e.key.toLowerCase();
    const btns=window.parent.document.querySelectorAll('.stButton button:not([disabled])');
    function click(label){{
      for(let b of btns){{ if((b.innerText||b.textContent).includes(label)){{ e.preventDefault(); b.click(); return true; }} }}
    }}
    if(phase.endsWith('_move')){{
      if(k==='a') click('MOVE LEFT');
      if(k==='d') click('MOVE RIGHT');
      if(k==='s') click('STAY');
    }}
    if(phase.endsWith('_attack')){{
      if(k==='1') click('WPN1');
      if(k==='2') click('WPN2');
      if(k===' '||k==='f') click('FIRE');
    }}
  }};
  window.parent.document.addEventListener('keydown',window.parent.__fnHandler);
}})();
</script></body></html>""", height=1)

# ── Layout ────────────────────────────────────────────────────────────────────
init_state()
game_active = st.session_state.p1_health is not None

_s1 = st.session_state.p1_locked or skin_names[0]
_s2 = st.session_state.p2_locked or skin_names[1]
inject_background(_s1, _s2)

n1 = st.session_state.p1_name_locked
n2 = st.session_state.p2_name_locked

st.markdown(f"""<div style="text-align:center;padding:10px 0 4px;">
  <div style="font-family:'Bangers',sans-serif;font-size:46px;letter-spacing:7px;color:#fff;
    text-shadow:-3px -3px 0 #000,3px -3px 0 #000,-3px 3px 0 #000,3px 3px 0 #000,
    0 0 26px rgba(255,209,0,0.9),0 0 70px rgba(100,30,220,0.45);">
    💥 FORTNITE BATTLE SIMULATOR
  </div>
  <div style="font-family:'Rajdhani',sans-serif;font-size:14px;color:#FFD100;font-weight:700;
    letter-spacing:5px;margin-top:4px;">⚡ {n1.upper()} vs {n2.upper()} ⚡</div>
</div>""", unsafe_allow_html=True)

st.markdown("---")

# ════════════════════════════════════════════════════
# LOBBY (pre-match setup)
# ════════════════════════════════════════════════════
if not game_active:
    with st.expander("📖 HOW TO PLAY", expanded=False):
        st.markdown("""
**Arena:** 7 tiles. Move to 🌲 **Cover tiles** for 50% damage protection!

**Controls — MOVEMENT phase:**
- **A key** = Move Left &nbsp;|&nbsp; **D key** = Move Right &nbsp;|&nbsp; **S key** = Stay put

**Controls — ATTACK phase:**
- **1 key** = Select Gun 1 &nbsp;|&nbsp; **2 key** = Select Gun 2 &nbsp;|&nbsp; **F / Space** = 🔥 FIRE!

**Weapon range matters:**
- 🪖 Pump Shotgun — devastating up close, weak at range
- 🔫 Scar — reliable at all distances
- 🚀 Rocket Launcher — strong at all ranges
- ⚡ Tactical SMG — best close to medium

**Skin abilities:**
- 🧑 Jonesy — 10% dodge · 👑 Midas — 20% double dmg · 🐻 Cuddle — heals after attack · ✈️ Raider — +20% accuracy
""")
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🟦 Player 1")
        p1_name   = st.text_input("Your Name", value="Ayaan", key="p1_name_in", max_chars=14)
        p1_skin   = st.selectbox("Choose Skin",   skin_names,   key="p1_skin")
        p1_wpn1   = st.selectbox("🔫 Gun 1 (Primary)",   weapon_names, index=0, key="p1_w1")
        p1_wpn2   = st.selectbox("💣 Gun 2 (Secondary)", weapon_names, index=1, key="p1_w2")
    with c2:
        st.markdown("### 🟥 Player 2")
        p2_name   = st.text_input("Your Name", value="Omer", key="p2_name_in", max_chars=14)
        p2_skin   = st.selectbox("Choose Skin",   skin_names,   index=1, key="p2_skin")
        p2_wpn1   = st.selectbox("🔫 Gun 1 (Primary)",   weapon_names, index=2, key="p2_w1")
        p2_wpn2   = st.selectbox("💣 Gun 2 (Secondary)", weapon_names, index=3, key="p2_w2")
    st.markdown("---")
    if st.button("🎮  START MATCH", use_container_width=True, type="primary"):
        start_match(p1_skin,p2_skin,p1_wpn1,p1_wpn2,p2_wpn1,p2_wpn2,p1_name,p2_name)
        st.rerun()

# ════════════════════════════════════════════════════
# GAME ACTIVE
# ════════════════════════════════════════════════════
else:
    n1 = st.session_state.p1_name_locked
    n2 = st.session_state.p2_name_locked
    phase = st.session_state.turn_phase   # p1_move / p1_attack / p2_move / p2_attack
    is_p1_turn = phase.startswith("p1")
    cur_name = n1 if is_p1_turn else n2
    turn_color = "#4da6ff" if is_p1_turn else "#ff5252"

    if st.session_state.game_over:
        st.balloons()
        wname = st.session_state.winner_name
        wskin = st.session_state.winner_skin or skin_names[0]
        wc    = SKINS[wskin]["color"]
        st.markdown(f"""<div style="text-align:center;padding:16px 0;">
  <div style="font-family:'Bangers',sans-serif;font-size:44px;letter-spacing:6px;color:#FFD100;
    text-shadow:-3px -3px 0 #000,3px -3px 0 #000,-3px 3px 0 #000,3px 3px 0 #000,
    0 0 32px #FFD100,0 0 70px {wc};">🏆 {wname.upper()} WINS! 🏆</div>
</div>""", unsafe_allow_html=True)
        render_arena(n1, n2)
        render_hp_bars(n1, st.session_state.p1_locked, n2, st.session_state.p2_locked)
        if st.button("🔄  PLAY AGAIN", use_container_width=True, type="primary"):
            reset_match(); st.rerun()

    else:
        # ── Turn banner ──
        action_word = "MOVE or STAY" if phase.endswith("_move") else "PICK GUN + FIRE"
        st.markdown(f"""<div style="text-align:center;padding:8px 16px;
  background:rgba(5,10,40,0.88);border:2px solid {turn_color};border-radius:8px;
  box-shadow:0 0 22px {turn_color}55;margin-bottom:6px;">
  <div style="font-family:'Bangers',sans-serif;font-size:22px;letter-spacing:4px;
    color:{turn_color};text-shadow:-1px -1px 0 #000,1px 1px 0 #000;">
    ⚡ {cur_name.upper()} — {action_word} ⚡
  </div>
</div>""", unsafe_allow_html=True)

        # ── Arena ──
        render_arena(n1, n2)

        # ── HP bars ──
        render_hp_bars(n1, st.session_state.p1_locked, n2, st.session_state.p2_locked)

        st.markdown("---")

        # ── MOVE PHASE ──
        if phase.endswith("_move"):
            st.markdown(f"""<div style="text-align:center;font-family:'Rajdhani',sans-serif;
  font-size:13px;color:#FFD100;letter-spacing:2px;margin-bottom:8px;">
  🎮 KEYBOARD: &nbsp; <b>A</b> = Move Left &nbsp;|&nbsp; <b>S</b> = Stay &nbsp;|&nbsp; <b>D</b> = Move Right
</div>""", unsafe_allow_html=True)

            mc1, mc2, mc3 = st.columns([1,1,1])
            cur_col_key = "p1_col" if is_p1_turn else "p2_col"
            opp_col_key = "p2_col" if is_p1_turn else "p1_col"
            cur_cov_key = "p1_in_cover" if is_p1_turn else "p2_in_cover"
            cur_col     = st.session_state[cur_col_key]
            opp_col     = st.session_state[opp_col_key]

            can_left  = cur_col > 0 and (cur_col-1) != opp_col
            can_right = cur_col < ARENA_SIZE-1 and (cur_col+1) != opp_col

            with mc1:
                if st.button("◀ MOVE LEFT [A]", use_container_width=True,
                             disabled=not can_left, key="btn_move_left"):
                    st.session_state[cur_col_key] -= 1
                    new_col = st.session_state[cur_col_key]
                    st.session_state[cur_cov_key] = (new_col in COVER_POS)
                    st.session_state.turn_phase = ("p1_attack" if is_p1_turn else "p2_attack")
                    st.rerun()
            with mc2:
                if st.button("⏸️ STAY [S]", use_container_width=True, key="btn_stay"):
                    st.session_state.turn_phase = ("p1_attack" if is_p1_turn else "p2_attack")
                    st.rerun()
            with mc3:
                if st.button("MOVE RIGHT ▶ [D]", use_container_width=True,
                             disabled=not can_right, key="btn_move_right"):
                    st.session_state[cur_col_key] += 1
                    new_col = st.session_state[cur_col_key]
                    st.session_state[cur_cov_key] = (new_col in COVER_POS)
                    st.session_state.turn_phase = ("p1_attack" if is_p1_turn else "p2_attack")
                    st.rerun()
            inject_keys(phase)

        # ── ATTACK PHASE ──
        else:
            cur_wpn1 = st.session_state.p1_wpn1 if is_p1_turn else st.session_state.p2_wpn1
            cur_wpn2 = st.session_state.p1_wpn2 if is_p1_turn else st.session_state.p2_wpn2
            sel_key  = "p1_wpn_sel" if is_p1_turn else "p2_wpn_sel"
            sel      = st.session_state[sel_key]

            st.markdown(f"""<div style="text-align:center;font-family:'Rajdhani',sans-serif;
  font-size:13px;color:#FFD100;letter-spacing:2px;margin-bottom:8px;">
  🎮 KEYBOARD: &nbsp; <b>1</b> = Gun 1 &nbsp;|&nbsp; <b>2</b> = Gun 2 &nbsp;|&nbsp; <b>F / SPACE</b> = 🔥 FIRE!
</div>""", unsafe_allow_html=True)

            # Weapon hotbar — 2 guns
            wc1, wc2 = st.columns(2)
            with wc1:
                render_weapon_hotbar(cur_wpn1, cur_wpn2, sel, True, "cur")
                if st.button("SELECT  GUN 1  [WPN1]", use_container_width=True,
                             type="primary" if sel==0 else "secondary", key="sel_w1"):
                    st.session_state[sel_key]=0; st.rerun()
            with wc2:
                render_weapon_hotbar(cur_wpn2, cur_wpn1, 1-sel, True, "cur2")
                if st.button("SELECT  GUN 2  [WPN2]", use_container_width=True,
                             type="primary" if sel==1 else "secondary", key="sel_w2"):
                    st.session_state[sel_key]=1; st.rerun()

            chosen_wpn = cur_wpn1 if sel==0 else cur_wpn2
            w_emoji    = WEAPONS[chosen_wpn]["emoji"]

            if st.button(f"🔥  FIRE {w_emoji} {chosen_wpn.upper()}!  [FIRE]",
                         use_container_width=True, type="primary", key="btn_fire"):
                if is_p1_turn:
                    do_fire(n1,"p1_locked",n2,"p2_locked",chosen_wpn,
                            "p2_health","p2_shields","p1_health","p1_shields",
                            "p1_col","p2_col","p2_in_cover")
                    if not st.session_state.game_over:
                        st.session_state.turn_phase="p2_move"
                else:
                    do_fire(n2,"p2_locked",n1,"p1_locked",chosen_wpn,
                            "p1_health","p1_shields","p2_health","p2_shields",
                            "p2_col","p1_col","p1_in_cover")
                    if not st.session_state.game_over:
                        st.session_state.turn_phase="p1_move"
                st.rerun()
            inject_keys(phase)

# ── Battle Log ────────────────────────────────────────────────────────────────
LOG_COLORS={"hit":"#00e676","crit":"#FFD100","miss":"#6688aa","ability":"#ff4da6","win":"#FF5722"}
st.markdown("---")
st.markdown("""<div style="font-family:'Bangers',sans-serif;font-size:18px;color:#FFD100;
  letter-spacing:4px;margin-bottom:6px;text-shadow:-1px -1px 0 #000,1px 1px 0 #000;">
  📜 BATTLE LOG</div>""", unsafe_allow_html=True)
if st.session_state.battle_log:
    for et, txt in st.session_state.battle_log:
        st.markdown(f'<div class="log-row" style="border-left-color:{LOG_COLORS.get(et,"#334")};">{txt}</div>',
            unsafe_allow_html=True)
else:
    st.caption("No actions yet. Set up your loadout and start the match!")
