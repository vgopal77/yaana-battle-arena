import random
import requests
import streamlit as st
import streamlit.components.v1 as components
from gamedata import SKINS, WEAPONS

st.set_page_config(page_title="Fortnite Battle Simulator", page_icon="💥", layout="wide")

# ── 2-Player arena constants ──────────────────────────────────────────────────
ARENA_SIZE = 7
COVER_POS  = {2, 4}

# ── Single-player arena constants ─────────────────────────────────────────────
SP_ROWS = 9
SP_COLS = 11
SP_OBSTACLES = frozenset([(2,2),(2,4),(2,6),(2,8),(4,1),(4,5),(4,9),(6,3),(6,7)])
SP_BASE_ROW  = 8
SP_BASE_COL  = 5
SP_BASE_MAX  = 300

ENEMY_TYPES = {
    "zombie":  {"emoji":"🧟","max_hp":60, "damage":20,"color":"#3a7a1a"},
    "soldier": {"emoji":"💂","max_hp":100,"damage":35,"color":"#8a6a1a"},
    "boss":    {"emoji":"👾","max_hp":220,"damage":65,"color":"#aa22aa"},
}
WAVE_DEFS = {
    1:[("zombie",3)],
    2:[("zombie",4),("soldier",2)],
    3:[("zombie",3),("soldier",3),("boss",1)],
    4:[("zombie",5),("soldier",3),("boss",1)],
    5:[("zombie",4),("soldier",4),("boss",2)],
}
WPN_RANGE = {"Pump Shotgun":2,"Tactical SMG":5,"Scar":7,"Rocket Launcher":10}

# ── Skin image API ────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_skin_image(skin_name):
    try:
        r = requests.get("https://fortnite-api.com/v2/cosmetics/br/search",
            params={"name":skin_name,"language":"en"}, timeout=5)
        if r.status_code == 200:
            imgs = r.json().get("data",{}).get("images",{})
            return imgs.get("featured") or imgs.get("icon")
    except Exception:
        pass
    return None

for _sn in SKINS: get_skin_image(_sn)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bangers&family=Rajdhani:wght@600;700&display=swap');
.stApp{background:linear-gradient(122deg,transparent 18%,rgba(255,195,0,.14) 30%,rgba(255,195,0,.07) 44%,transparent 55%),radial-gradient(ellipse 70% 55% at 50% 0%,rgba(100,30,220,.30) 0%,transparent 60%),linear-gradient(160deg,#122d8c 0%,#091b60 35%,#050e35 70%,#020819 100%);background-attachment:fixed;min-height:100vh;}
.block-container{position:relative;z-index:2;padding-top:.8rem!important;}
.stApp::before{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent 0,transparent 3px,rgba(0,0,0,.04) 3px,rgba(0,0,0,.04) 4px);pointer-events:none;z-index:9999;}
.stApp,.stApp p,.stApp span,.stApp div,.stApp li,.stMarkdown p,.stMarkdown li{color:#fff!important;}
label,.stSelectbox label,.stTextInput label{color:#FFD100!important;font-size:11px!important;font-weight:700!important;letter-spacing:2px!important;text-transform:uppercase!important;font-family:'Rajdhani',sans-serif!important;}
.stTextInput>div>div>input{background:rgba(5,10,40,.90)!important;border:2px solid rgba(255,209,0,.50)!important;border-radius:6px!important;color:#fff!important;font-family:'Bangers',sans-serif!important;font-size:18px!important;letter-spacing:3px!important;text-align:center!important;text-transform:uppercase!important;}
.stTextInput>div>div>input:focus{border-color:#FFD100!important;box-shadow:0 0 16px rgba(255,209,0,.4)!important;}
.stSelectbox>div>div{background:rgba(5,10,40,.90)!important;border:1.5px solid rgba(255,200,0,.35)!important;color:#fff!important;border-radius:6px!important;}
.stSelectbox>div>div>div{color:#fff!important;} .stSelectbox svg{fill:#FFD100!important;}
h1{font-family:'Bangers',sans-serif!important;letter-spacing:4px!important;color:#fff!important;}
h2,h3{font-family:'Rajdhani',sans-serif!important;color:#fff!important;letter-spacing:2px!important;}
.stButton>button{background:rgba(5,10,40,.85)!important;color:#FFD100!important;border:1.5px solid rgba(255,209,0,.55)!important;border-radius:6px!important;font-family:'Rajdhani',sans-serif!important;font-size:14px!important;font-weight:700!important;letter-spacing:2px!important;text-transform:uppercase!important;transition:all .15s ease!important;}
.stButton>button:hover{background:rgba(255,209,0,.10)!important;box-shadow:0 0 26px rgba(255,209,0,.45)!important;border-color:#FFD100!important;transform:translateY(-1px)!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#FFD100 0%,#FF9500 100%)!important;color:#050a1a!important;border:2px solid #FFD100!important;font-size:16px!important;font-weight:900!important;box-shadow:0 4px 24px rgba(255,175,0,.55)!important;}
.stButton>button[kind="primary"]:hover{background:linear-gradient(135deg,#ffe040 0%,#ffaa00 100%)!important;box-shadow:0 6px 36px rgba(255,180,0,.80)!important;transform:translateY(-2px)!important;}
.stButton>button:disabled{opacity:.35!important;transform:none!important;}
.streamlit-expanderHeader{background:rgba(5,10,40,.85)!important;border:1px solid rgba(255,200,0,.25)!important;border-radius:7px!important;color:#FFD100!important;font-family:'Rajdhani',sans-serif!important;}
hr{border-color:rgba(255,200,0,.18)!important;}
.bar-wrap{background:rgba(0,0,0,.50);border-radius:3px;height:20px;overflow:hidden;margin:3px 0;border:1px solid rgba(255,255,255,.10);}
.bar-fill{height:100%;border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:900;color:#050a1a;min-width:28px;font-family:'Rajdhani',sans-serif;}
.log-row{border-left:3px solid #334;border-radius:4px;padding:6px 12px;margin:2px 0;font-size:13px;font-family:'Rajdhani',sans-serif;background:rgba(5,10,40,.80);}
</style>""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
skin_names   = list(SKINS.keys())
weapon_names = list(WEAPONS.keys())

def inject_background(s1, s2):
    i1=get_skin_image(s1) or ""; i2=get_skin_image(s2) or ""
    t1=f'<img src="{i1}" style="position:absolute;left:-30px;bottom:0;height:88vh;opacity:.10;filter:blur(1px);object-fit:contain;pointer-events:none;"/>' if i1 else ""
    t2=f'<img src="{i2}" style="position:absolute;right:-30px;bottom:0;height:88vh;opacity:.10;filter:blur(1px);object-fit:contain;pointer-events:none;transform:scaleX(-1);"/>' if i2 else ""
    stars="".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="white" opacity="{o}"/>'
        for x,y,r,o in [(45,120,1.2,.8),(130,45,1,.6),(310,70,1,.5),(420,150,1.2,.8),(610,200,1.8,.5),
            (700,90,1,.6),(900,40,1,.7),(1100,75,1,.6),(1300,55,1,.5),(80,300,1,.5),(350,370,1.2,.7),
            (640,330,1,.6),(930,290,1.8,.6),(1220,380,1,.7),(60,470,1.5,.5),(430,440,1.8,.6)])
    st.markdown(f"""<div style="position:fixed;inset:0;pointer-events:none;z-index:1;overflow:hidden;">
<svg width="100%" height="100%" style="position:absolute;inset:0;opacity:.6;">{stars}</svg>
{t1}{t2}
<div style="position:absolute;inset:0;background:radial-gradient(ellipse 85% 85% at 50% 50%,transparent 45%,rgba(2,8,25,.70) 100%);"></div>
</div>""", unsafe_allow_html=True)

def apply_damage(hp, sh, dmg):
    if sh > 0: a=min(sh,dmg); sh-=a; dmg-=a
    return max(0,hp-dmg), sh

def hp_color(pct):
    return "#00e676" if pct>.60 else "#ff9100" if pct>.30 else "#ff1744"

def get_range_mult(wname, dist):
    if wname=="Pump Shotgun":
        return 1.8 if dist<=1 else 1.3 if dist<=2 else 0.8 if dist<=3 else 0.35
    if wname=="Tactical SMG":
        return 1.2 if dist<=2 else 1.0 if dist<=4 else 0.65
    if wname=="Rocket Launcher": return 1.1
    return 1.0

def render_hp_row(name, skin_key, hp_key, sh_key, pkey):
    hp=st.session_state[hp_key] or 0; sh=st.session_state[sh_key] or 0
    s=SKINS[skin_key]; mhp=s["health"]; msh=s["shields"]
    hc=hp_color(hp/mhp if mhp else 0); sc="#40c4ff"
    img=get_skin_image(skin_key) or ""
    itag=f'<img src="{img}" style="width:32px;height:32px;object-fit:contain;border-radius:50%;border:2px solid {s["color"]};margin-right:8px;vertical-align:middle;"/>' if img else f'<span style="font-size:22px;margin-right:6px;">{s["avatar"]}</span>'
    cov=""
    if pkey and st.session_state.get(f"{pkey}_in_cover"):
        cov='<span style="margin-left:auto;font-size:18px;">🛡️</span>'
    st.markdown(f"""<div style="background:rgba(4,8,28,.85);border:1.5px solid rgba(255,200,0,.22);border-radius:10px;padding:9px 12px;margin-bottom:4px;">
<div style="display:flex;align-items:center;margin-bottom:5px;">{itag}<div><div style="font-family:'Bangers',sans-serif;font-size:14px;letter-spacing:2px;color:{s['color']};">{name.upper()}</div><div style="font-size:9px;color:#aabbdd;font-family:'Rajdhani',sans-serif;">{skin_key}</div></div>{cov}</div>
<div style="font-size:10px;color:#aabbdd;font-family:Rajdhani,sans-serif;">❤️ HP {hp}/{mhp}</div>
<div class="bar-wrap"><div class="bar-fill" style="width:{max(int(hp/mhp*100 if mhp else 0),2)}%;background:{hc};box-shadow:0 0 8px {hc}88;">{hp}</div></div>
<div style="font-size:10px;color:#aabbdd;font-family:Rajdhani,sans-serif;margin-top:3px;">🛡️ {sh}/{msh}</div>
<div class="bar-wrap"><div class="bar-fill" style="width:{max(int(sh/msh*100 if msh else 0),2)}%;background:{sc};box-shadow:0 0 8px {sc}88;">{sh}</div></div>
</div>""", unsafe_allow_html=True)

def weapon_cards(wpn1, wpn2, sel):
    WL={"Pump Shotgun":"Best CLOSE","Scar":"All ranges","Rocket Launcher":"All ranges","Tactical SMG":"Close-Med"}
    html=""
    for i,wn in enumerate([wpn1,wpn2]):
        w=WEAPONS[wn]; is_sel=(sel==i)
        bg="linear-gradient(135deg,#FFD100,#FF9500)" if is_sel else "rgba(5,10,40,.88)"
        bdr="#FFD100" if is_sel else "rgba(255,255,255,.15)"
        tc="#050a1a" if is_sel else "#fff"
        glow="0 0 20px rgba(255,209,0,.60)" if is_sel else "none"
        html+=f"""<div style="background:{bg};border:2px solid {bdr};border-radius:10px;padding:12px 8px;text-align:center;box-shadow:{glow};position:relative;">
<div style="position:absolute;top:5px;right:7px;font-family:'Bangers',sans-serif;font-size:12px;color:{'#050a1a' if is_sel else '#FFD100'};letter-spacing:1px;">[{i+1}]</div>
<div style="font-size:32px;margin-bottom:4px;">{w['emoji']}</div>
<div style="font-family:'Bangers',sans-serif;font-size:13px;letter-spacing:2px;color:{tc};">{wn.upper()}</div>
<div style="font-size:10px;color:{tc};opacity:.75;font-family:'Rajdhani',sans-serif;">DMG {w['damage']} · ACC {int(w['accuracy']*100)}%</div>
<div style="font-size:9px;color:{tc};opacity:.6;font-family:'Rajdhani',sans-serif;margin-top:2px;">📍 {WL.get(wn,'')}</div>
</div>"""
    st.markdown(f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:6px;">{html}</div>',
        unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 2-PLAYER MODE
# ══════════════════════════════════════════════════════════════════════════════
def render_arena_2p(n1, n2):
    p1c=st.session_state.p1_col; p2c=st.session_state.p2_col
    cov1=st.session_state.p1_in_cover; cov2=st.session_state.p2_in_cover
    s1=SKINS[st.session_state.p1_locked]; s2=SKINS[st.session_state.p2_locked]
    cells=""
    for i in range(ARENA_SIZE):
        if i==p1c:
            ic=("🛡️" if cov1 else s1["avatar"]); bg=f"rgba({int(s1['color'][1:3],16)},{int(s1['color'][3:5],16)},{int(s1['color'][5:7],16)},.30)"; bdr=s1["color"]; lb=n1[:5].upper(); sub="IN COVER" if cov1 else ""
        elif i==p2c:
            ic=("🛡️" if cov2 else s2["avatar"]); bg=f"rgba({int(s2['color'][1:3],16)},{int(s2['color'][3:5],16)},{int(s2['color'][5:7],16)},.30)"; bdr=s2["color"]; lb=n2[:5].upper(); sub="IN COVER" if cov2 else ""
        elif i in COVER_POS:
            ic="🌲"; bg="rgba(15,50,15,.50)"; bdr="#3a8a3a"; lb="COVER"; sub="−50% DMG"
        else:
            ic="·"; bg="rgba(0,0,0,.15)"; bdr="rgba(255,255,255,.07)"; lb=""; sub=""
        cells+=f"""<div style="flex:1;background:{bg};border:1.5px solid {bdr};border-radius:8px;padding:10px 4px;text-align:center;min-width:55px;">
<div style="font-size:26px;line-height:1.1;">{ic}</div>
<div style="font-size:9px;color:white;font-weight:700;letter-spacing:1px;margin-top:3px;">{lb}</div>
<div style="font-size:8px;color:rgba(255,255,255,.5);margin-top:1px;">{sub}</div></div>"""
    dist=abs(p1c-p2c)
    rlbl=("🔴 POINT BLANK" if dist<=1 else "🟡 CLOSE RANGE" if dist<=3 else "🟢 LONG RANGE")
    st.markdown(f"""<div style="background:rgba(0,0,10,.80);border:1px solid rgba(255,200,0,.28);border-radius:12px;padding:12px;margin:6px 0;">
<div style="font-family:'Bangers',sans-serif;font-size:11px;color:#FFD100;letter-spacing:3px;margin-bottom:8px;text-align:center;">⚔️ BATTLE ARENA — STEP INTO 🌲 COVER FOR PROTECTION</div>
<div style="display:flex;gap:5px;justify-content:center;align-items:stretch;">{cells}</div>
<div style="text-align:center;margin-top:8px;font-family:'Rajdhani',sans-serif;font-size:12px;color:#aabbdd;">
{rlbl} &nbsp;|&nbsp; Distance: <b style="color:#FFD100;">{dist}</b> &nbsp;|&nbsp;
🪖 Shotgun: <b style="color:{'#ff4444' if dist<=2 else '#ffaa00' if dist<=4 else '#44aa44'};">{'MAX PWR' if dist<=2 else 'MED' if dist<=4 else 'WEAK'}</b></div></div>""",
    unsafe_allow_html=True)

def do_fire_2p(atk_name, atk_skin, def_name, def_skin, weapon_name,
               def_hp_key, def_sh_key, atk_hp_key, atk_sh_key,
               atk_col_key, def_col_key, def_cover_key):
    # atk_skin / def_skin are the actual skin name strings, NOT session_state key names
    w=WEAPONS[weapon_name]; atk=SKINS[atk_skin]; log=[]
    acc=min(.98, w["accuracy"]+(atk.get("accuracy_bonus",0) if atk_skin=="Renegade Raider" else 0))
    if random.random()>=acc:
        log.append(("miss",f"💨 <b>{atk_name}</b> fired {w['emoji']} {weapon_name} — <b>MISSED!</b>"))
        st.session_state.battle_log=log+st.session_state.battle_log; return
    def_skin_data=SKINS[def_skin]
    if def_skin=="Jonesy" and random.random()<def_skin_data.get("dodge_chance",0):
        log.append(("ability",f"🍀 <b>{def_name}</b> — <b>LUCKY BREAK! Dodged!</b>"))
        st.session_state.battle_log=log+st.session_state.battle_log; return
    dist=abs(st.session_state[atk_col_key]-st.session_state[def_col_key])
    damage=int(w["damage"]*get_range_mult(weapon_name,dist))
    label="Hit"; etype="hit"
    if atk_skin=="Midas" and random.random()<atk.get("gold_chance",0):
        damage=int(damage*2); label="👑 GOLDEN TOUCH — DOUBLE DMG"; etype="crit"
    elif random.random()<w["crit_chance"]:
        damage=int(damage*1.75); label="💥 CRITICAL HIT"; etype="crit"
    if st.session_state[def_cover_key]:
        damage=int(damage*.5); label+=" | 🌲 COVER −50%!"; st.session_state[def_cover_key]=False
    ph=st.session_state[def_hp_key]; ps=st.session_state[def_sh_key]
    nh,ns=apply_damage(ph,ps,damage)
    st.session_state[def_hp_key]=nh; st.session_state[def_sh_key]=ns
    ic="💥" if etype=="crit" else "🎯"
    log.append((etype,f"{ic} <b>{atk_name}</b>→<b>{def_name}</b> [{weapon_name}·d:{dist}]: <b>{label} {damage}dmg</b> | ❤️{ph}→{nh}"))
    if atk_skin=="Cuddle Team Leader":
        heal=atk.get("heal_amount",0); old=st.session_state[atk_hp_key]
        new2=min(SKINS[atk_skin]["health"],old+heal); st.session_state[atk_hp_key]=new2
        if new2>old: log.append(("ability",f"🐻 <b>{atk_name}</b> — BEAR HUG +{heal} HP!"))
    if nh<=0:
        st.session_state.game_over=True; st.session_state.winner_name=atk_name; st.session_state.winner_skin=atk_skin
        log.append(("win",f"🏆 <b>{atk_name}</b> ELIMINATED <b>{def_name}</b>!"))
    st.session_state.battle_log=log+st.session_state.battle_log

def inject_keys_2p(phase):
    components.html(f"""<!DOCTYPE html><html><body><script>
(function(){{if(window.parent.__fnH)window.parent.document.removeEventListener('keydown',window.parent.__fnH);
const ph="{phase}";
window.parent.__fnH=function(e){{
if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')return;
const k=e.key.toLowerCase();
const btns=window.parent.document.querySelectorAll('.stButton button:not([disabled])');
function cl(lbl){{for(let b of btns){{if((b.innerText||b.textContent).includes(lbl)){{e.preventDefault();b.click();return;}}}}}}
if(ph.endsWith('_move')){{if(k==='a')cl('MOVE LEFT');if(k==='d')cl('MOVE RIGHT');if(k==='s')cl('STAY');}}
if(ph.endsWith('_attack')){{if(k==='1')cl('WPN1');if(k==='2')cl('WPN2');if(k===' '||k==='f')cl('FIRE');}}
}};window.parent.document.addEventListener('keydown',window.parent.__fnH);
}})();</script></body></html>""", height=1)

# ══════════════════════════════════════════════════════════════════════════════
# SINGLE-PLAYER MODE
# ══════════════════════════════════════════════════════════════════════════════
def render_arena_sp():
    pr=st.session_state.sp_p_row; pc=st.session_state.sp_p_col
    skin=SKINS[st.session_state.p1_locked]; sav=skin["avatar"]; sc=skin["color"]
    ents={(e["row"],e["col"]):e for e in st.session_state.sp_enemies if e["hp"]>0}
    rows=""
    for r in range(SP_ROWS):
        cells=""
        for c in range(SP_COLS):
            is_base=(r==SP_BASE_ROW and c==SP_BASE_COL)
            is_pl=(r==pr and c==pc)
            is_obs=(r,c) in SP_OBSTACLES
            ent=ents.get((r,c))
            if is_pl:
                ic=sav; bg=f"rgba({int(sc[1:3],16)},{int(sc[3:5],16)},{int(sc[5:7],16)},.35)"; bdr=sc; hpbar=""
            elif is_base:
                ic="🏰"; bg="rgba(255,215,0,.20)"; bdr="#FFD700"
                bp=max(0,int(st.session_state.sp_base_hp/SP_BASE_MAX*100)); bc=hp_color(bp/100)
                hpbar=f'<div style="position:absolute;bottom:2px;left:3px;right:3px;height:3px;background:rgba(0,0,0,.5);"><div style="width:{bp}%;height:100%;background:{bc};"></div></div>'
            elif ent:
                ic=ent["emoji"]; bg=ent["color"]+"33"; bdr=ent["color"]
                ep=max(0,int(ent["hp"]/ent["max_hp"]*100)); ec=hp_color(ep/100)
                hpbar=f'<div style="position:absolute;bottom:2px;left:3px;right:3px;height:3px;background:rgba(0,0,0,.5);"><div style="width:{ep}%;height:100%;background:{ec};"></div></div>'
            elif is_obs:
                ic=("🌲" if (r+c)%2==0 else "🪨"); bg="rgba(15,45,15,.55)"; bdr="rgba(40,90,40,.5)"; hpbar=""
            else:
                ic="·"; bg=("rgba(0,0,0,.12)" if (r+c)%2==0 else "rgba(5,10,30,.15)"); bdr="rgba(255,255,255,.04)"; hpbar=""
            cells+=f'<td style="width:48px;height:48px;text-align:center;vertical-align:middle;background:{bg};border:1px solid {bdr};border-radius:4px;position:relative;font-size:22px;">{ic}{hpbar}</td>'
        rows+=f"<tr>{cells}</tr>"
    bhp=st.session_state.sp_base_hp; bpct=max(0,int(bhp/SP_BASE_MAX*100)); bclr=hp_color(bpct/100)
    wave=st.session_state.sp_wave; alive=len([e for e in st.session_state.sp_enemies if e["hp"]>0])
    killed=st.session_state.get("sp_enemies_killed",0)
    st.markdown(f"""<div style="background:rgba(0,0,10,.82);border:1px solid rgba(255,200,0,.28);border-radius:12px;padding:12px;margin:6px 0;overflow-x:auto;">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:6px;">
  <div style="font-family:'Bangers',sans-serif;font-size:14px;color:#FFD100;letter-spacing:3px;">⚔️ WAVE {wave} &nbsp;|&nbsp; ENEMIES: <span style="color:#ff5252;">{alive}</span></div>
  <div style="font-family:'Rajdhani',sans-serif;font-size:12px;color:#aabbdd;">🏰 BASE: <b style="color:{bclr};">{bhp}</b> &nbsp;|&nbsp; 💀 Kills: <b style="color:#FFD100;">{killed}</b></div>
</div>
<table style="border-collapse:separate;border-spacing:2px;margin:0 auto;">{rows}</table>
<div style="text-align:center;margin-top:8px;font-family:'Rajdhani',sans-serif;font-size:11px;color:#667799;">
🌲🪨 = cover (−50% dmg) &nbsp;|&nbsp; 🏰 = defend this! &nbsp;|&nbsp; Enemies spawn at the top and march down</div></div>""",
    unsafe_allow_html=True)

def spawn_wave(wave_num):
    cfg=WAVE_DEFS.get(wave_num, WAVE_DEFS[5])
    enemies=[]; eid=0
    cols=list(range(SP_COLS)); random.shuffle(cols); ci=0
    for (etype,count) in cfg:
        et=ENEMY_TYPES[etype]
        for _ in range(count):
            enemies.append({"id":eid,"type":etype,"emoji":et["emoji"],
                "hp":et["max_hp"],"max_hp":et["max_hp"],"damage":et["damage"],"color":et["color"],
                "row":0,"col":cols[ci%len(cols)]})
            eid+=1; ci+=1
    st.session_state.sp_enemies=enemies
    st.session_state.sp_wave_cleared=False

def enemy_turn_sp():
    log=[]
    pr=st.session_state.sp_p_row; pc=st.session_state.sp_p_col
    skin_key=st.session_state.p1_locked
    occupied={(e["row"],e["col"]) for e in st.session_state.sp_enemies if e["hp"]>0}
    for e in st.session_state.sp_enemies:
        if e["hp"]<=0: continue
        er=e["row"]; ec=e["col"]
        p_dist=abs(er-pr)+abs(ec-pc)
        b_dist=abs(er-SP_BASE_ROW)+abs(ec-SP_BASE_COL)
        # Attack player if adjacent
        if p_dist<=1:
            ph=st.session_state.sp_p_hp; ps=st.session_state.sp_p_sh
            dmg=e["damage"]
            if (pr,pc) in SP_OBSTACLES: dmg=int(dmg*.5)  # cover protection
            nh,ns=apply_damage(ph,ps,dmg)
            st.session_state.sp_p_hp=nh; st.session_state.sp_p_sh=ns
            log.append(("hit",f"{e['emoji']} {e['type'].upper()} attacks <b>{st.session_state.p1_name_locked.upper()}</b> for <b>{dmg} dmg</b>! ❤️{ph}→{nh}"))
            if nh<=0: st.session_state.sp_game_over=True; log.append(("lose","💀 YOU WERE ELIMINATED! GAME OVER!"))
            continue
        # Attack base if adjacent and player is far
        if b_dist<=1 and p_dist>3:
            dmg=e["damage"]; prev=st.session_state.sp_base_hp
            st.session_state.sp_base_hp=max(0,prev-dmg)
            log.append(("hit",f"{e['emoji']} {e['type'].upper()} attacks the <b>BASE</b> for <b>{dmg} dmg</b>! 🏰{prev}→{st.session_state.sp_base_hp}"))
            if st.session_state.sp_base_hp<=0: st.session_state.sp_game_over=True; log.append(("lose","💔 BASE DESTROYED! GAME OVER!"))
            continue
        # Move toward nearest target
        tr=(pr if p_dist<=b_dist else SP_BASE_ROW); tc=(pc if p_dist<=b_dist else SP_BASE_COL)
        dr=tr-er; dc=tc-ec
        occupied.discard((er,ec))
        moves=[]
        if abs(dr)>=abs(dc):
            if dr!=0: moves.append((er+(1 if dr>0 else -1),ec))
            if dc!=0: moves.append((er,ec+(1 if dc>0 else -1)))
        else:
            if dc!=0: moves.append((er,ec+(1 if dc>0 else -1)))
            if dr!=0: moves.append((er+(1 if dr>0 else -1),ec))
        if moves and random.random()<.2: moves.reverse()
        moved=False
        for (nr,nc) in moves:
            if (0<=nr<SP_ROWS and 0<=nc<SP_COLS and
                (nr,nc) not in SP_OBSTACLES and (nr,nc) not in occupied and
                not(nr==pr and nc==pc)):
                e["row"]=nr; e["col"]=nc; occupied.add((nr,nc)); moved=True; break
        if not moved: occupied.add((er,ec))
    st.session_state.sp_enemies=[e for e in st.session_state.sp_enemies if e["hp"]>0]
    if not st.session_state.sp_enemies and not st.session_state.sp_game_over:
        st.session_state.sp_wave_cleared=True
        log.append(("win",f"✅ Wave {st.session_state.sp_wave} cleared!"))
    if log: st.session_state.sp_log=log+st.session_state.get("sp_log",[])

def do_fire_sp():
    pr=st.session_state.sp_p_row; pc=st.session_state.sp_p_col
    sel=st.session_state.p1_wpn_sel
    wpn=(st.session_state.p1_wpn1 if sel==0 else st.session_state.p1_wpn2)
    w=WEAPONS[wpn]; skin_key=st.session_state.p1_locked; atk=SKINS[skin_key]
    max_r=WPN_RANGE.get(wpn,5)
    best=None; best_d=9999
    for e in st.session_state.sp_enemies:
        if e["hp"]<=0: continue
        d=abs(e["row"]-pr)+abs(e["col"]-pc)
        if d<=max_r and d<best_d: best=e; best_d=d
    if best is None:
        st.session_state.sp_log=[("miss",f"⚠️ No enemies in range (max {max_r} tiles)! Move closer.")]+st.session_state.get("sp_log",[]); return False
    acc=min(.98,w["accuracy"]+(atk.get("accuracy_bonus",0) if skin_key=="Renegade Raider" else 0))
    if random.random()>=acc:
        st.session_state.sp_log=[("miss",f"💨 {wpn} MISSED {best['emoji']} (dist {best_d})!")]+st.session_state.get("sp_log",[]); return True
    damage=int(w["damage"]*get_range_mult(wpn,best_d)); label="Hit"; etype="hit"
    if skin_key=="Midas" and random.random()<atk.get("gold_chance",0):
        damage=int(damage*2); label="👑 GOLDEN TOUCH"; etype="crit"
    elif random.random()<w["crit_chance"]:
        damage=int(damage*1.75); label="💥 CRITICAL"; etype="crit"
    ph=best["hp"]; best["hp"]=max(0,ph-damage)
    ic="💥" if etype=="crit" else "🎯"
    st.session_state.sp_log=[(etype,f"{ic} Shot {best['emoji']} {best['type'].upper()} [{wpn}·d:{best_d}]: <b>{label} {damage}dmg</b>! ❤️{ph}→{best['hp']}")]+st.session_state.get("sp_log",[])
    if best["hp"]<=0:
        st.session_state.sp_log=[("win",f"💀 {best['emoji']} ELIMINATED!")]+st.session_state.sp_log
        st.session_state.sp_enemies_killed=st.session_state.get("sp_enemies_killed",0)+1
    if skin_key=="Cuddle Team Leader":
        heal=atk.get("heal_amount",0); old=st.session_state.sp_p_hp
        new2=min(SKINS[skin_key]["health"],old+heal); st.session_state.sp_p_hp=new2
        if new2>old: st.session_state.sp_log=[("ability",f"🐻 BEAR HUG +{heal} HP!")]+st.session_state.sp_log
    return True

def inject_keys_sp():
    components.html("""<!DOCTYPE html><html><body><script>
(function(){if(window.parent.__fnSP)window.parent.document.removeEventListener('keydown',window.parent.__fnSP);
window.parent.__fnSP=function(e){
if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')return;
const k=e.key.toLowerCase();
const btns=window.parent.document.querySelectorAll('.stButton button:not([disabled])');
function cl(lbl){for(let b of btns){if((b.innerText||b.textContent).includes(lbl)){e.preventDefault();b.click();return;}}}
if(k==='w'||k==='arrowup')cl('UP');
if(k==='s'||k==='arrowdown')cl('DOWN');
if(k==='a'||k==='arrowleft')cl('LEFT');
if(k==='d'||k==='arrowright')cl('RIGHT');
if(k===' '||k==='f')cl('SHOOT');
if(k==='1')cl('WPN1');if(k==='2')cl('WPN2');
};
window.parent.document.addEventListener('keydown',window.parent.__fnSP);
})();</script></body></html>""", height=1)

# ── State management ──────────────────────────────────────────────────────────
def init_state():
    defs={
        "game_mode":None,"p1_locked":None,"p2_locked":None,
        "p1_name_locked":"Player 1","p2_name_locked":"Player 2",
        "p1_wpn1":None,"p1_wpn2":None,"p2_wpn1":None,"p2_wpn2":None,
        "p1_wpn_sel":0,"p2_wpn_sel":0,
        # 2P
        "p1_health":None,"p1_shields":None,"p2_health":None,"p2_shields":None,
        "p1_col":1,"p2_col":5,"p1_in_cover":False,"p2_in_cover":False,
        "turn_phase":"p1_move","battle_log":[],"game_over":False,
        "winner_name":None,"winner_skin":None,
        # SP
        "sp_p_hp":None,"sp_p_sh":None,"sp_p_row":7,"sp_p_col":5,
        "sp_base_hp":SP_BASE_MAX,"sp_enemies":[],"sp_wave":1,
        "sp_enemies_killed":0,"sp_log":[],"sp_game_over":False,
        "sp_won":False,"sp_wave_cleared":False,
    }
    for k,v in defs.items():
        if k not in st.session_state: st.session_state[k]=v
    log=st.session_state.battle_log
    if log and not isinstance(log[0],tuple): st.session_state.battle_log=[]

def start_2p(s1,s2,w1a,w1b,w2a,w2b,n1,n2):
    st.session_state.game_mode="2p"
    st.session_state.p1_health=SKINS[s1]["health"]; st.session_state.p1_shields=SKINS[s1]["shields"]
    st.session_state.p2_health=SKINS[s2]["health"]; st.session_state.p2_shields=SKINS[s2]["shields"]
    st.session_state.p1_col=1; st.session_state.p2_col=5
    st.session_state.p1_in_cover=False; st.session_state.p2_in_cover=False
    st.session_state.p1_locked=s1; st.session_state.p2_locked=s2
    st.session_state.p1_wpn1=w1a; st.session_state.p1_wpn2=w1b
    st.session_state.p2_wpn1=w2a; st.session_state.p2_wpn2=w2b
    st.session_state.p1_wpn_sel=0; st.session_state.p2_wpn_sel=0
    st.session_state.p1_name_locked=n1 or "Player 1"; st.session_state.p2_name_locked=n2 or "Player 2"
    st.session_state.turn_phase="p1_move"
    st.session_state.battle_log=[]; st.session_state.game_over=False
    st.session_state.winner_name=None; st.session_state.winner_skin=None

def start_sp(skin,w1,w2,name):
    st.session_state.game_mode="1p"
    st.session_state.p1_locked=skin; st.session_state.p2_locked=skin
    st.session_state.p1_wpn1=w1; st.session_state.p1_wpn2=w2; st.session_state.p1_wpn_sel=0
    st.session_state.p1_name_locked=name or "Player"
    st.session_state.sp_p_hp=SKINS[skin]["health"]; st.session_state.sp_p_sh=SKINS[skin]["shields"]
    st.session_state.sp_p_row=7; st.session_state.sp_p_col=5
    st.session_state.sp_base_hp=SP_BASE_MAX
    st.session_state.sp_wave=1; st.session_state.sp_enemies_killed=0
    st.session_state.sp_log=[]; st.session_state.sp_game_over=False
    st.session_state.sp_won=False; st.session_state.sp_wave_cleared=False
    spawn_wave(1)

def full_reset():
    for k in list(st.session_state.keys()): del st.session_state[k]

# ══════════════════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
init_state()
_sk1=st.session_state.p1_locked or skin_names[0]
_sk2=st.session_state.p2_locked or skin_names[1]
inject_background(_sk1,_sk2)

st.markdown("""<div style="text-align:center;padding:8px 0 2px;">
<div style="font-family:'Bangers',sans-serif;font-size:42px;letter-spacing:7px;color:#fff;
text-shadow:-3px -3px 0 #000,3px -3px 0 #000,-3px 3px 0 #000,3px 3px 0 #000,
0 0 26px rgba(255,209,0,.9),0 0 70px rgba(100,30,220,.45);">💥 FORTNITE BATTLE SIMULATOR</div>
</div>""", unsafe_allow_html=True)
st.markdown("---")

LOG_C={"hit":"#00e676","crit":"#FFD100","miss":"#6688aa","ability":"#ff4da6","win":"#FF5722","lose":"#ff1744"}

# ════════════════════════════════════════════════════
# LOBBY — MODE SELECT
# ════════════════════════════════════════════════════
if st.session_state.game_mode is None:
    with st.expander("📖 HOW TO PLAY", expanded=False):
        st.markdown("""
**2-Player Battle** — two players on same device fight each other on a 7-tile arena.
- Move phase: **A**=Left · **S**=Stay · **D**=Right · Step into 🌲 Cover for −50% damage
- Attack phase: **1/2**=Switch gun · **F/Space**=🔥 Fire

**Single Player — Defend the Base** — fight waves of zombies & soldiers on a 9×11 arena grid.
- **WASD or Arrow keys** to walk · **F/Space**=Shoot nearest enemy · **1/2**=Switch gun
- 🏰 Base must survive 5 waves · 🌲🪨 = cover tiles (−50% damage when standing on them)

**Weapon ranges:** 🪖 Pump=2 · ⚡ SMG=5 · 🔫 Scar=7 · 🚀 Rocket=10
""")
    st.markdown("---")
    mc1,mc2=st.columns(2)
    with mc1:
        st.markdown("""<div style="background:rgba(5,10,40,.85);border:2px solid rgba(255,200,0,.3);border-radius:12px;padding:16px;text-align:center;">
<div style="font-size:36px;">🎮</div>
<div style="font-family:'Bangers',sans-serif;font-size:22px;letter-spacing:3px;color:#FFD100;">2-PLAYER BATTLE</div>
<div style="font-size:12px;color:#aabbdd;font-family:'Rajdhani',sans-serif;">Same keyboard. Fight your friend!</div>
</div>""", unsafe_allow_html=True)
        if st.button("PLAY 2-PLAYER",use_container_width=True,type="primary",key="mode_2p"):
            st.session_state.game_mode="lobby_2p"; st.rerun()
    with mc2:
        st.markdown("""<div style="background:rgba(5,10,40,.85);border:2px solid rgba(255,200,0,.3);border-radius:12px;padding:16px;text-align:center;">
<div style="font-size:36px;">🤖</div>
<div style="font-family:'Bangers',sans-serif;font-size:22px;letter-spacing:3px;color:#FFD100;">SINGLE PLAYER</div>
<div style="font-size:12px;color:#aabbdd;font-family:'Rajdhani',sans-serif;">Fight zombies & soldiers. Defend your base!</div>
</div>""", unsafe_allow_html=True)
        if st.button("PLAY SOLO",use_container_width=True,type="primary",key="mode_1p"):
            st.session_state.game_mode="lobby_1p"; st.rerun()

# ── 2P Lobby ──────────────────────────────────────────────────────────────────
elif st.session_state.game_mode=="lobby_2p":
    st.markdown("### 🎮 2-PLAYER SETUP")
    c1,c2=st.columns(2)
    with c1:
        st.markdown("#### 🟦 Player 1")
        p1n=st.text_input("Name",value="Ayaan",key="p1ni",max_chars=14)
        p1s=st.selectbox("Skin",skin_names,key="p1s")
        p1w1=st.selectbox("🔫 Gun 1",weapon_names,index=0,key="p1w1")
        p1w2=st.selectbox("💣 Gun 2",weapon_names,index=1,key="p1w2")
    with c2:
        st.markdown("#### 🟥 Player 2")
        p2n=st.text_input("Name",value="Omer",key="p2ni",max_chars=14)
        p2s=st.selectbox("Skin",skin_names,index=1,key="p2s")
        p2w1=st.selectbox("🔫 Gun 1",weapon_names,index=2,key="p2w1")
        p2w2=st.selectbox("💣 Gun 2",weapon_names,index=3,key="p2w2")
    st.markdown("---")
    bc1,bc2=st.columns(2)
    with bc1:
        if st.button("◀ BACK",use_container_width=True,key="back2p"):
            st.session_state.game_mode=None; st.rerun()
    with bc2:
        if st.button("🎮 START MATCH",use_container_width=True,type="primary",key="start2p"):
            start_2p(p1s,p2s,p1w1,p1w2,p2w1,p2w2,p1n,p2n); st.rerun()

# ── SP Lobby ──────────────────────────────────────────────────────────────────
elif st.session_state.game_mode=="lobby_1p":
    st.markdown("### 🤖 SINGLE PLAYER — DEFEND THE BASE")
    c1,c2=st.columns([1,2])
    with c1:
        spn=st.text_input("Your Name",value="Ayaan",key="spni",max_chars=14)
        sps=st.selectbox("Skin",skin_names,key="sps")
        spw1=st.selectbox("🔫 Gun 1 (Primary)",weapon_names,index=0,key="spw1")
        spw2=st.selectbox("💣 Gun 2 (Secondary)",weapon_names,index=1,key="spw2")
    with c2:
        st.markdown("""**5 waves of enemies march toward your base 🏰 — eliminate them all!**

| Wave | Enemies |
|------|---------|
| 1 | 3 🧟 Zombies |
| 2 | 4 🧟 + 2 💂 Soldiers |
| 3 | 3 🧟 + 3 💂 + 1 👾 Boss |
| 4 | 5 🧟 + 3 💂 + 1 👾 |
| 5 | 4 🧟 + 4 💂 + 2 👾 |

**Tips:** Stand on 🌲🪨 cover to halve incoming damage. Use 🔫 Scar to snipe from distance. 🪖 Pump Shotgun destroys up close. 🤖 Boss deals 65 damage — avoid getting surrounded!
""")
    st.markdown("---")
    bc1,bc2=st.columns(2)
    with bc1:
        if st.button("◀ BACK",use_container_width=True,key="backsp"):
            st.session_state.game_mode=None; st.rerun()
    with bc2:
        if st.button("🤖 DEFEND THE BASE!",use_container_width=True,type="primary",key="startsp"):
            start_sp(sps,spw1,spw2,spn); st.rerun()

# ════════════════════════════════════════════════════
# 2-PLAYER GAME
# ════════════════════════════════════════════════════
elif st.session_state.game_mode=="2p":
    n1=st.session_state.p1_name_locked; n2=st.session_state.p2_name_locked
    phase=st.session_state.turn_phase; is_p1=phase.startswith("p1")
    cur_name=n1 if is_p1 else n2; turn_color="#4da6ff" if is_p1 else "#ff5252"

    if st.session_state.game_over:
        st.balloons()
        wn=st.session_state.winner_name; ws=st.session_state.winner_skin or skin_names[0]
        wc=SKINS[ws]["color"]
        st.markdown(f"""<div style="text-align:center;padding:16px;">
<div style="font-family:'Bangers',sans-serif;font-size:42px;letter-spacing:6px;color:#FFD100;
text-shadow:-3px -3px 0 #000,3px -3px 0 #000,0 0 32px #FFD100,0 0 70px {wc};">🏆 {wn.upper()} WINS! 🏆</div></div>""",
            unsafe_allow_html=True)
        render_arena_2p(n1,n2)
        c1,c2=st.columns(2)
        with c1: render_hp_row(n1,st.session_state.p1_locked,"p1_health","p1_shields","p1")
        with c2: render_hp_row(n2,st.session_state.p2_locked,"p2_health","p2_shields","p2")
    else:
        aw="MOVE or STAY" if phase.endswith("_move") else "PICK GUN + FIRE"
        st.markdown(f"""<div style="text-align:center;padding:7px 14px;background:rgba(5,10,40,.88);
border:2px solid {turn_color};border-radius:8px;box-shadow:0 0 22px {turn_color}55;margin-bottom:6px;">
<div style="font-family:'Bangers',sans-serif;font-size:20px;letter-spacing:4px;color:{turn_color};">
⚡ {cur_name.upper()} — {aw} ⚡</div></div>""", unsafe_allow_html=True)
        render_arena_2p(n1,n2)
        c1,c2=st.columns(2)
        with c1: render_hp_row(n1,st.session_state.p1_locked,"p1_health","p1_shields","p1")
        with c2: render_hp_row(n2,st.session_state.p2_locked,"p2_health","p2_shields","p2")
        st.markdown("---")
        if phase.endswith("_move"):
            st.markdown('<div style="text-align:center;font-family:\'Rajdhani\',sans-serif;font-size:12px;color:#FFD100;letter-spacing:2px;margin-bottom:7px;">🎮 <b>A</b>=Move Left &nbsp;·&nbsp; <b>S</b>=Stay &nbsp;·&nbsp; <b>D</b>=Move Right &nbsp;—&nbsp; Step into 🌲 for cover!</div>', unsafe_allow_html=True)
            cc=("p1_col" if is_p1 else "p2_col"); oc=("p2_col" if is_p1 else "p1_col")
            cov=("p1_in_cover" if is_p1 else "p2_in_cover")
            cur_c=st.session_state[cc]; opp_c=st.session_state[oc]
            nxt=("p1_attack" if is_p1 else "p2_attack")
            mc1,mc2,mc3=st.columns(3)
            with mc1:
                if st.button("◀ MOVE LEFT [A]",use_container_width=True,
                             disabled=(cur_c<=0 or cur_c-1==opp_c),key="mv_l"):
                    st.session_state[cc]-=1; nc=st.session_state[cc]
                    st.session_state[cov]=(nc in COVER_POS); st.session_state.turn_phase=nxt; st.rerun()
            with mc2:
                if st.button("⏸️ STAY [S]",use_container_width=True,key="mv_s"):
                    st.session_state.turn_phase=nxt; st.rerun()
            with mc3:
                if st.button("MOVE RIGHT ▶ [D]",use_container_width=True,
                             disabled=(cur_c>=ARENA_SIZE-1 or cur_c+1==opp_c),key="mv_r"):
                    st.session_state[cc]+=1; nc=st.session_state[cc]
                    st.session_state[cov]=(nc in COVER_POS); st.session_state.turn_phase=nxt; st.rerun()
            inject_keys_2p(phase)
        else:
            st.markdown('<div style="text-align:center;font-family:\'Rajdhani\',sans-serif;font-size:12px;color:#FFD100;letter-spacing:2px;margin-bottom:7px;">🎮 <b>1</b>=Gun 1 &nbsp;·&nbsp; <b>2</b>=Gun 2 &nbsp;·&nbsp; <b>F / SPACE</b>=🔥 Fire!</div>', unsafe_allow_html=True)
            w1=st.session_state.p1_wpn1 if is_p1 else st.session_state.p2_wpn1
            w2=st.session_state.p1_wpn2 if is_p1 else st.session_state.p2_wpn2
            sk=("p1_wpn_sel" if is_p1 else "p2_wpn_sel"); sel=st.session_state[sk]
            weapon_cards(w1,w2,sel)
            swc1,swc2=st.columns(2)
            with swc1:
                if st.button("SELECT GUN 1 [WPN1]",use_container_width=True,
                             type="primary" if sel==0 else "secondary",key="sel1"):
                    st.session_state[sk]=0; st.rerun()
            with swc2:
                if st.button("SELECT GUN 2 [WPN2]",use_container_width=True,
                             type="primary" if sel==1 else "secondary",key="sel2"):
                    st.session_state[sk]=1; st.rerun()
            chosen=w1 if sel==0 else w2
            if st.button(f"🔥 FIRE {WEAPONS[chosen]['emoji']} {chosen.upper()}! [FIRE]",
                         use_container_width=True,type="primary",key="fire2p"):
                s1v=st.session_state.p1_locked; s2v=st.session_state.p2_locked
                if is_p1:
                    do_fire_2p(n1,s1v,n2,s2v,chosen,"p2_health","p2_shields","p1_health","p1_shields","p1_col","p2_col","p2_in_cover")
                    if not st.session_state.game_over: st.session_state.turn_phase="p2_move"
                else:
                    do_fire_2p(n2,s2v,n1,s1v,chosen,"p1_health","p1_shields","p2_health","p2_shields","p2_col","p1_col","p1_in_cover")
                    if not st.session_state.game_over: st.session_state.turn_phase="p1_move"
                st.rerun()
            inject_keys_2p(phase)
    st.markdown("---")
    bc1,bc2=st.columns(2)
    with bc1:
        if st.button("🔄 PLAY AGAIN",use_container_width=True,type="primary",key="again2p"):
            full_reset(); st.rerun()
    with bc2:
        if st.button("🏠 MAIN MENU",use_container_width=True,key="menu2p"):
            full_reset(); st.rerun()
    st.markdown('<div style="font-family:\'Bangers\',sans-serif;font-size:16px;color:#FFD100;letter-spacing:4px;margin-bottom:5px;">📜 BATTLE LOG</div>', unsafe_allow_html=True)
    for et,txt in (st.session_state.battle_log or []):
        st.markdown(f'<div class="log-row" style="border-left-color:{LOG_C.get(et,"#334")};">{txt}</div>',unsafe_allow_html=True)

# ════════════════════════════════════════════════════
# SINGLE-PLAYER GAME
# ════════════════════════════════════════════════════
elif st.session_state.game_mode=="1p":
    pname=st.session_state.p1_name_locked; skin_key=st.session_state.p1_locked

    if st.session_state.sp_game_over:
        won=st.session_state.sp_won
        if won: st.balloons()
        res="🏆 VICTORY! YOU DEFENDED THE BASE!" if won else "💀 GAME OVER"
        clr="#FFD100" if won else "#ff5252"
        st.markdown(f"""<div style="text-align:center;padding:16px;">
<div style="font-family:'Bangers',sans-serif;font-size:36px;letter-spacing:6px;color:{clr};
text-shadow:-3px -3px 0 #000,3px -3px 0 #000,0 0 32px {clr};">{res}</div>
<div style="font-family:'Rajdhani',sans-serif;font-size:15px;color:#aabbdd;margin-top:8px;">
Waves survived: <b style="color:#FFD100;">{st.session_state.sp_wave-1}</b> &nbsp;|&nbsp;
Kills: <b style="color:#FFD100;">{st.session_state.get('sp_enemies_killed',0)}</b> &nbsp;|&nbsp;
Base HP left: <b style="color:#FFD100;">{st.session_state.sp_base_hp}</b></div></div>""",
            unsafe_allow_html=True)
        render_arena_sp()
        bc1,bc2=st.columns(2)
        with bc1:
            if st.button("🔄 TRY AGAIN",use_container_width=True,type="primary",key="spagain"):
                full_reset(); st.rerun()
        with bc2:
            if st.button("🏠 MAIN MENU",use_container_width=True,key="spmenu"):
                full_reset(); st.rerun()

    elif st.session_state.sp_wave_cleared:
        next_wave=st.session_state.sp_wave+1
        if next_wave>5:
            st.session_state.sp_game_over=True; st.session_state.sp_won=True; st.rerun()
        else:
            st.markdown(f"""<div style="text-align:center;padding:10px;background:rgba(5,10,40,.88);
border:2px solid #00e676;border-radius:10px;margin-bottom:8px;">
<div style="font-family:'Bangers',sans-serif;font-size:28px;letter-spacing:4px;color:#00e676;">
✅ WAVE {st.session_state.sp_wave} CLEARED!</div>
<div style="font-family:'Rajdhani',sans-serif;font-size:14px;color:#aabbdd;margin-top:4px;">
Kills: <b>{st.session_state.get('sp_enemies_killed',0)}</b> &nbsp;|&nbsp;
Base HP: <b style="color:#FFD100;">{st.session_state.sp_base_hp}</b></div></div>""",
                unsafe_allow_html=True)
            render_arena_sp()
            c1,c2=st.columns(2)
            with c1: render_hp_row(pname,skin_key,"sp_p_hp","sp_p_sh",None)
            with c2:
                bpct=int(st.session_state.sp_base_hp/SP_BASE_MAX*100); bc=hp_color(bpct/100)
                st.markdown(f"""<div style="background:rgba(4,8,28,.85);border:1.5px solid rgba(255,200,0,.22);border-radius:10px;padding:9px 12px;">
<div style="font-family:'Bangers',sans-serif;font-size:14px;color:#FFD700;letter-spacing:2px;">🏰 BASE STATUS</div>
<div class="bar-wrap" style="margin-top:8px;"><div class="bar-fill" style="width:{bpct}%;background:{bc};">{st.session_state.sp_base_hp}/{SP_BASE_MAX}</div></div></div>""",
                    unsafe_allow_html=True)
            if st.button(f"⚡ LAUNCH WAVE {next_wave}!",use_container_width=True,type="primary",key="nextwv"):
                st.session_state.sp_wave=next_wave; spawn_wave(next_wave); st.rerun()

    else:
        wave=st.session_state.sp_wave; alive=len([e for e in st.session_state.sp_enemies if e["hp"]>0])
        st.markdown(f"""<div style="text-align:center;padding:6px 12px;background:rgba(5,10,40,.88);
border:2px solid #ff5252;border-radius:8px;box-shadow:0 0 18px rgba(255,82,82,.4);margin-bottom:6px;">
<div style="font-family:'Bangers',sans-serif;font-size:18px;letter-spacing:4px;color:#ff5252;">
🤖 WAVE {wave} OF 5 — {alive} ENEMIES — DEFEND THE BASE 🏰</div></div>""", unsafe_allow_html=True)
        render_arena_sp()
        c1,c2=st.columns(2)
        with c1: render_hp_row(pname,skin_key,"sp_p_hp","sp_p_sh",None)
        with c2:
            bpct=int(st.session_state.sp_base_hp/SP_BASE_MAX*100); bc=hp_color(bpct/100)
            st.markdown(f"""<div style="background:rgba(4,8,28,.85);border:1.5px solid rgba(255,200,0,.22);border-radius:10px;padding:9px 12px;">
<div style="font-family:'Bangers',sans-serif;font-size:14px;color:#FFD700;letter-spacing:2px;">🏰 YOUR BASE</div>
<div class="bar-wrap" style="margin-top:6px;"><div class="bar-fill" style="width:{bpct}%;background:{bc};box-shadow:0 0 8px {bc}88;">{st.session_state.sp_base_hp}/{SP_BASE_MAX}</div></div>
<div style="font-size:10px;color:#aabbdd;font-family:'Rajdhani',sans-serif;margin-top:3px;">{bpct}% integrity</div></div>""",
                unsafe_allow_html=True)
        st.markdown("---")
        # Nearest enemy info
        pr=st.session_state.sp_p_row; pc=st.session_state.sp_p_col
        sel=st.session_state.p1_wpn_sel
        wpn=(st.session_state.p1_wpn1 if sel==0 else st.session_state.p1_wpn2)
        max_r=WPN_RANGE.get(wpn,5)
        nearest=None; nd=9999
        for e in st.session_state.sp_enemies:
            if e["hp"]>0:
                d=abs(e["row"]-pr)+abs(e["col"]-pc)
                if d<nd: nearest=e; nd=d
        if nearest:
            in_range=(nd<=max_r); rclr="#00e676" if in_range else "#ff5252"
            st.markdown(f"""<div style="text-align:center;font-family:'Rajdhani',sans-serif;font-size:12px;color:#aabbdd;margin-bottom:6px;">
Target: <b>{nearest['emoji']} {nearest['type'].upper()}</b> at <b style="color:{rclr};">{nd} tiles</b>
&nbsp;|&nbsp; {wpn} range: <b style="color:#FFD100;">{max_r}</b>
{'&nbsp;|&nbsp; <b style="color:#00e676;">✅ IN RANGE!</b>' if in_range else '&nbsp;|&nbsp; <b style="color:#ff5252;">⚠️ MOVE CLOSER!</b>'}</div>""",
                unsafe_allow_html=True)
        # D-Pad
        st.markdown('<div style="text-align:center;font-family:\'Rajdhani\',sans-serif;font-size:12px;color:#FFD100;letter-spacing:2px;margin-bottom:4px;">🕹️ WASD / ARROW KEYS to walk &nbsp;·&nbsp; F/SPACE to shoot</div>', unsafe_allow_html=True)
        _,u,_=st.columns(3)
        l,_m,r=st.columns(3)
        _,d,_=st.columns(3)
        occ={(e["row"],e["col"]) for e in st.session_state.sp_enemies if e["hp"]>0}
        def can_move(dr,dc):
            nr=pr+dr; nc=pc+dc
            return (0<=nr<SP_ROWS and 0<=nc<SP_COLS and (nr,nc) not in SP_OBSTACLES and (nr,nc) not in occ)
        def do_move(dr,dc):
            if can_move(dr,dc):
                st.session_state.sp_p_row+=dr; st.session_state.sp_p_col+=dc
            enemy_turn_sp(); st.rerun()
        with u:
            if st.button("⬆️ UP [W]",use_container_width=True,disabled=not can_move(-1,0),key="spup"): do_move(-1,0)
        with l:
            if st.button("⬅️ LEFT [A]",use_container_width=True,disabled=not can_move(0,-1),key="spleft"): do_move(0,-1)
        with r:
            if st.button("➡️ RIGHT [D]",use_container_width=True,disabled=not can_move(0,1),key="spright"): do_move(0,1)
        with d:
            if st.button("⬇️ DOWN [S]",use_container_width=True,disabled=not can_move(1,0),key="spdown"): do_move(1,0)
        st.markdown("---")
        wpn1=st.session_state.p1_wpn1; wpn2=st.session_state.p1_wpn2
        weapon_cards(wpn1,wpn2,sel)
        swc1,swc2=st.columns(2)
        with swc1:
            if st.button("SELECT GUN 1 [WPN1]",use_container_width=True,
                         type="primary" if sel==0 else "secondary",key="spw1s"):
                st.session_state.p1_wpn_sel=0; st.rerun()
        with swc2:
            if st.button("SELECT GUN 2 [WPN2]",use_container_width=True,
                         type="primary" if sel==1 else "secondary",key="spw2s"):
                st.session_state.p1_wpn_sel=1; st.rerun()
        if st.button(f"🎯 SHOOT {WEAPONS[wpn]['emoji']} {wpn.upper()}! [SHOOT]",
                     use_container_width=True,type="primary",key="spfire"):
            acted=do_fire_sp()
            if acted: enemy_turn_sp()
            st.rerun()
        inject_keys_sp()
        st.markdown("---")
        if st.button("🏠 QUIT TO MENU",key="spquit"):
            full_reset(); st.rerun()
        st.markdown('<div style="font-family:\'Bangers\',sans-serif;font-size:16px;color:#FFD100;letter-spacing:4px;margin-bottom:5px;">📜 BATTLE LOG</div>', unsafe_allow_html=True)
        for et,txt in (st.session_state.get("sp_log",[]) or []):
            st.markdown(f'<div class="log-row" style="border-left-color:{LOG_C.get(et,"#334")};">{txt}</div>',unsafe_allow_html=True)
