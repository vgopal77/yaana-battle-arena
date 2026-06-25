import random
import requests
import streamlit as st
import streamlit.components.v1 as components
from gamedata import SKINS, WEAPONS

st.set_page_config(page_title="Fortnite Battle Simulator", page_icon="💥", layout="wide")

# ── Constants ─────────────────────────────────────────────────────────────────
ARENA_SIZE = 7
COVER_POS  = {2, 4}

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

for _sn in SKINS: get_skin_image(_sn)

skin_names   = list(SKINS.keys())
weapon_names = list(WEAPONS.keys())

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bangers&family=Rajdhani:wght@600;700&display=swap');
.stApp{background:linear-gradient(160deg,#122d8c 0%,#091b60 35%,#050e35 70%,#020819 100%);min-height:100vh;}
.block-container{position:relative;z-index:2;padding-top:.8rem!important;}
.stApp,.stApp p,.stApp span,.stApp div,.stApp li{color:#fff!important;}
label,.stSelectbox label,.stTextInput label{color:#FFD100!important;font-size:11px!important;font-weight:700!important;letter-spacing:2px!important;text-transform:uppercase!important;font-family:'Rajdhani',sans-serif!important;}
.stTextInput>div>div>input{background:rgba(5,10,40,.90)!important;border:2px solid rgba(255,209,0,.50)!important;border-radius:6px!important;color:#fff!important;font-family:'Bangers',sans-serif!important;font-size:18px!important;letter-spacing:3px!important;text-align:center!important;text-transform:uppercase!important;}
.stSelectbox>div>div{background:rgba(5,10,40,.90)!important;border:1.5px solid rgba(255,200,0,.35)!important;color:#fff!important;border-radius:6px!important;}
.stSelectbox>div>div>div{color:#fff!important;}.stSelectbox svg{fill:#FFD100!important;}
.stButton>button{background:rgba(5,10,40,.85)!important;color:#FFD100!important;border:1.5px solid rgba(255,209,0,.55)!important;border-radius:6px!important;font-family:'Rajdhani',sans-serif!important;font-size:14px!important;font-weight:700!important;letter-spacing:2px!important;text-transform:uppercase!important;transition:all .15s!important;}
.stButton>button:hover{background:rgba(255,209,0,.10)!important;box-shadow:0 0 26px rgba(255,209,0,.45)!important;border-color:#FFD100!important;transform:translateY(-1px)!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#FFD100 0%,#FF9500 100%)!important;color:#050a1a!important;border:2px solid #FFD100!important;font-size:16px!important;font-weight:900!important;box-shadow:0 4px 24px rgba(255,175,0,.55)!important;}
.stButton>button:disabled{opacity:.35!important;}
hr{border-color:rgba(255,200,0,.18)!important;}
.bar-wrap{background:rgba(0,0,0,.50);border-radius:3px;height:20px;overflow:hidden;margin:3px 0;border:1px solid rgba(255,255,255,.10);}
.bar-fill{height:100%;border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:900;color:#050a1a;min-width:28px;font-family:'Rajdhani',sans-serif;}
.log-row{border-left:3px solid #334;border-radius:4px;padding:6px 12px;margin:2px 0;font-size:13px;font-family:'Rajdhani',sans-serif;background:rgba(5,10,40,.80);}
</style>""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def apply_damage(hp, sh, dmg):
    if sh > 0: a = min(sh, dmg); sh -= a; dmg -= a
    return max(0, hp - dmg), sh

def hp_color(pct):
    return "#00e676" if pct > .60 else "#ff9100" if pct > .30 else "#ff1744"

def get_range_mult(wname, dist):
    if wname == "Pump Shotgun":
        return 1.8 if dist <= 1 else 1.3 if dist <= 2 else 0.8 if dist <= 3 else 0.35
    if wname == "Tactical SMG":
        return 1.2 if dist <= 2 else 1.0 if dist <= 4 else 0.65
    if wname == "Rocket Launcher": return 1.1
    return 1.0

def inject_background(s1, s2):
    i1 = get_skin_image(s1) or ""
    i2 = get_skin_image(s2) or ""
    t1 = f'<img src="{i1}" style="position:absolute;left:-30px;bottom:0;height:88vh;opacity:.10;filter:blur(1px);object-fit:contain;pointer-events:none;"/>' if i1 else ""
    t2 = f'<img src="{i2}" style="position:absolute;right:-30px;bottom:0;height:88vh;opacity:.10;filter:blur(1px);object-fit:contain;pointer-events:none;transform:scaleX(-1);"/>' if i2 else ""
    st.markdown(f"""<div style="position:fixed;inset:0;pointer-events:none;z-index:1;overflow:hidden;">{t1}{t2}</div>""", unsafe_allow_html=True)

def render_hp_row(name, skin_key, hp_key, sh_key):
    hp = st.session_state[hp_key] or 0; sh = st.session_state[sh_key] or 0
    s = SKINS[skin_key]; mhp = s["health"]; msh = s["shields"]
    hc = hp_color(hp / mhp if mhp else 0)
    img = get_skin_image(skin_key) or ""
    itag = f'<img src="{img}" style="width:32px;height:32px;object-fit:contain;border-radius:50%;border:2px solid {s["color"]};margin-right:8px;vertical-align:middle;"/>' if img else f'<span style="font-size:22px;margin-right:6px;">{s["avatar"]}</span>'
    st.markdown(f"""<div style="background:rgba(4,8,28,.85);border:1.5px solid rgba(255,200,0,.22);border-radius:10px;padding:9px 12px;margin-bottom:4px;">
<div style="display:flex;align-items:center;margin-bottom:5px;">{itag}
<div><div style="font-family:'Bangers',sans-serif;font-size:14px;letter-spacing:2px;color:{s['color']};">{name.upper()}</div>
<div style="font-size:9px;color:#aabbdd;">{skin_key}</div></div></div>
<div class="bar-wrap"><div class="bar-fill" style="width:{max(int(hp/mhp*100 if mhp else 0),2)}%;background:{hc};">{hp}/{mhp}</div></div>
<div class="bar-wrap"><div class="bar-fill" style="width:{max(int(sh/msh*100 if msh else 0),2)}%;background:#40c4ff;">{sh}/{msh}</div></div>
</div>""", unsafe_allow_html=True)

def weapon_cards(wpn1, wpn2, sel):
    RL = {"Pump Shotgun": "Best CLOSE", "Scar": "All ranges", "Rocket Launcher": "All ranges", "Tactical SMG": "Close-Med"}
    html = ""
    for i, wn in enumerate([wpn1, wpn2]):
        w = WEAPONS[wn]; is_sel = (sel == i)
        bg = "linear-gradient(135deg,#FFD100,#FF9500)" if is_sel else "rgba(5,10,40,.88)"
        bdr = "#FFD100" if is_sel else "rgba(255,255,255,.15)"
        tc = "#050a1a" if is_sel else "#fff"
        html += f"""<div style="background:{bg};border:2px solid {bdr};border-radius:10px;padding:12px 8px;text-align:center;position:relative;">
<div style="position:absolute;top:5px;right:7px;font-family:'Bangers',sans-serif;font-size:12px;color:{'#050a1a' if is_sel else '#FFD100'};">[{i+1}]</div>
<div style="font-size:30px;margin-bottom:4px;">{w['emoji']}</div>
<div style="font-family:'Bangers',sans-serif;font-size:13px;letter-spacing:2px;color:{tc};">{wn.upper()}</div>
<div style="font-size:10px;color:{tc};opacity:.75;">DMG {w['damage']} · ACC {int(w['accuracy']*100)}%</div>
<div style="font-size:9px;color:{tc};opacity:.6;margin-top:2px;">📍 {RL.get(wn,'')}</div></div>"""
    st.markdown(f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:6px;">{html}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 2-PLAYER MODE
# ══════════════════════════════════════════════════════════════════════════════
def render_arena_2p(n1, n2):
    p1c = st.session_state.p1_col; p2c = st.session_state.p2_col
    s1 = SKINS[st.session_state.p1_locked]; s2 = SKINS[st.session_state.p2_locked]
    cells = ""
    for i in range(ARENA_SIZE):
        if i == p1c:
            ic = s1["avatar"]; bg = f"rgba({int(s1['color'][1:3],16)},{int(s1['color'][3:5],16)},{int(s1['color'][5:7],16)},.30)"; bdr = s1["color"]; lb = n1[:5].upper()
        elif i == p2c:
            ic = s2["avatar"]; bg = f"rgba({int(s2['color'][1:3],16)},{int(s2['color'][3:5],16)},{int(s2['color'][5:7],16)},.30)"; bdr = s2["color"]; lb = n2[:5].upper()
        elif i in COVER_POS:
            ic = "🌲"; bg = "rgba(15,50,15,.50)"; bdr = "#3a8a3a"; lb = "COVER"
        else:
            ic = "·"; bg = "rgba(0,0,0,.15)"; bdr = "rgba(255,255,255,.07)"; lb = ""
        cells += f'<div style="flex:1;background:{bg};border:1.5px solid {bdr};border-radius:8px;padding:10px 4px;text-align:center;min-width:55px;"><div style="font-size:26px;">{ic}</div><div style="font-size:9px;color:white;font-weight:700;">{lb}</div></div>'
    dist = abs(p1c - p2c)
    rlbl = "🔴 CLOSE" if dist <= 2 else "🟡 MED" if dist <= 4 else "🟢 LONG"
    st.markdown(f"""<div style="background:rgba(0,0,10,.80);border:1px solid rgba(255,200,0,.28);border-radius:12px;padding:12px;margin:6px 0;">
<div style="display:flex;gap:5px;justify-content:center;">{cells}</div>
<div style="text-align:center;margin-top:8px;font-family:'Rajdhani',sans-serif;font-size:12px;color:#aabbdd;">
{rlbl} · Dist: <b style="color:#FFD100;">{dist}</b> · 🪖 Shotgun power: <b style="color:{'#ff4444' if dist<=2 else '#ffaa00' if dist<=4 else '#44aa44'};">{'MAX' if dist<=2 else 'MED' if dist<=4 else 'WEAK'}</b></div></div>""",
    unsafe_allow_html=True)

def do_fire_2p(atk_name, atk_skin, def_name, def_skin, weapon_name,
               def_hp_key, def_sh_key, atk_hp_key, atk_sh_key,
               atk_col_key, def_col_key, def_cover_key):
    w = WEAPONS[weapon_name]; atk = SKINS[atk_skin]; log = []
    acc = min(.98, w["accuracy"] + (atk.get("accuracy_bonus", 0) if atk_skin == "Renegade Raider" else 0))
    if random.random() >= acc:
        log.append(("miss", f"💨 <b>{atk_name}</b> {weapon_name} — MISSED!")); st.session_state.battle_log = log + st.session_state.battle_log; return
    def_s = SKINS[def_skin]
    if def_skin == "Jonesy" and random.random() < def_s.get("dodge_chance", 0):
        log.append(("ability", f"🍀 <b>{def_name}</b> — LUCKY BREAK! Dodged!")); st.session_state.battle_log = log + st.session_state.battle_log; return
    dist = abs(st.session_state[atk_col_key] - st.session_state[def_col_key])
    damage = int(w["damage"] * get_range_mult(weapon_name, dist))
    label = "Hit"; etype = "hit"
    if atk_skin == "Midas" and random.random() < atk.get("gold_chance", 0):
        damage = int(damage * 2); label = "👑 GOLDEN TOUCH 2×"; etype = "crit"
    elif random.random() < w["crit_chance"]:
        damage = int(damage * 1.75); label = "💥 CRITICAL"; etype = "crit"
    if st.session_state[def_cover_key]:
        damage = int(damage * .5); label += " | 🌲−50%"; st.session_state[def_cover_key] = False
    ph = st.session_state[def_hp_key]; ps = st.session_state[def_sh_key]
    nh, ns = apply_damage(ph, ps, damage)
    st.session_state[def_hp_key] = nh; st.session_state[def_sh_key] = ns
    log.append((etype, f"{'💥' if etype=='crit' else '🎯'} <b>{atk_name}</b>→<b>{def_name}</b> [{weapon_name}·d:{dist}]: <b>{label} {damage}dmg</b> ❤️{ph}→{nh}"))
    if atk_skin == "Cuddle Team Leader":
        heal = atk.get("heal_amount", 0); old = st.session_state[atk_hp_key]
        st.session_state[atk_hp_key] = min(SKINS[atk_skin]["health"], old + heal)
        if st.session_state[atk_hp_key] > old: log.append(("ability", f"🐻 <b>{atk_name}</b> BEAR HUG +{heal} HP!"))
    if nh <= 0:
        st.session_state.game_over = True; st.session_state.winner_name = atk_name; st.session_state.winner_skin = atk_skin
        log.append(("win", f"🏆 <b>{atk_name}</b> ELIMINATED <b>{def_name}</b>!"))
    st.session_state.battle_log = log + st.session_state.battle_log

def inject_keys_2p(phase):
    components.html(f"""<html><body><script>
(function(){{if(window.parent.__fnH)window.parent.document.removeEventListener('keydown',window.parent.__fnH);
const ph="{phase}";
window.parent.__fnH=function(e){{
if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')return;
const k=e.key.toLowerCase();
const bb=window.parent.document.querySelectorAll('.stButton button:not([disabled])');
function cl(l){{for(let b of bb){{if((b.innerText||b.textContent).includes(l)){{e.preventDefault();b.click();return;}}}}}}
if(ph.endsWith('_move')){{if(k==='a')cl('MOVE LEFT');if(k==='d')cl('MOVE RIGHT');if(k==='s')cl('STAY');}}
if(ph.endsWith('_attack')){{if(k==='1')cl('WPN1');if(k==='2')cl('WPN2');if(k===' '||k==='f')cl('FIRE');}}
}};window.parent.document.addEventListener('keydown',window.parent.__fnH);
}})();</script></body></html>""", height=1)

# ══════════════════════════════════════════════════════════════════════════════
# SINGLE-PLAYER CANVAS GAME
# ══════════════════════════════════════════════════════════════════════════════
# Template HTML — uses __TOKENS__ replaced by Python before rendering
_SP_TEMPLATE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#020a1a;overflow:hidden;font-family:'Rajdhani','Bangers',sans-serif;}
canvas{display:block;cursor:crosshair;}
</style>
</head>
<body>
<canvas id="g"></canvas>
<script>
const cvs=document.getElementById('g');
const cx=cvs.getContext('2d');
const W=cvs.width=Math.min(860,window.innerWidth-4);
const H=cvs.height=530;

// ── PYTHON CONFIG ──
const PNAME="__PNAME__";
const P_MAX_HP=__PHP__;
const P_MAX_SH=__PSH__;
const ABILITY_TYPE="__ATYPE__";
const ABILITY_VAL=__AVAL__;
const BASE_MAX=300;
const GUN=[__GUN1__,__GUN2__];

// ── GAME STATE ──
let p={x:W/2,y:H*0.72,hp:P_MAX_HP,sh:P_MAX_SH,spd:3.2,facing:1};
let enemies=[],bullets=[],particles=[],trees=[],rocks=[];
let wave=1,score=0,kills=0,frame=0,cooldown=0,selGun=0;
let gameOver=false,waveDone=false,showResult=false,baseHp=BASE_MAX;
let keys={};
let stars=Array.from({length:90},()=>({x:Math.random()*W,y:Math.random()*H*0.28,r:Math.random()*1.5+0.3,b:Math.random()}));
for(let i=0;i<20;i++) trees.push({x:30+Math.random()*(W-60),y:55+Math.random()*(H*0.53),r:20+Math.random()*18,dark:Math.random()<0.4});
for(let i=0;i<7;i++) rocks.push({x:60+Math.random()*(W-120),y:90+Math.random()*(H*0.42),w:18+Math.random()*16,h:10+Math.random()*10});

// ── SPAWN ──
function spawnWave(n){
  enemies=[];
  let z=3+n*2, s=(n>=2?Math.ceil(n/2):0), b=(n>=3?Math.floor((n-2)/2):0);
  let types=[];
  for(let i=0;i<z;i++) types.push('zombie');
  for(let i=0;i<s;i++) types.push('soldier');
  for(let i=0;i<b;i++) types.push('boss');
  types.sort(()=>Math.random()-0.5);
  types.forEach((t,i)=>{
    let mx={zombie:60,soldier:100,boss:200}[t];
    enemies.push({x:40+Math.random()*(W-80),y:-25-i*38,hp:mx,mhp:mx,
      dmg:{zombie:20,soldier:35,boss:65}[t],
      spd:{zombie:0.9,soldier:1.2,boss:0.7}[t],
      type:t,atk:0,spawn:i*7});
  });
  waveDone=false; showResult=false;
}

// ── DRAW SKY + GROUND ──
function drawWorld(){
  // Sky
  let sg=cx.createLinearGradient(0,0,0,H*0.3);
  sg.addColorStop(0,'#020b1c'); sg.addColorStop(1,'#0d2844');
  cx.fillStyle=sg; cx.fillRect(0,0,W,H*0.3);
  // Stars
  stars.forEach(s=>{
    cx.globalAlpha=0.4+0.6*Math.abs(Math.sin(frame*0.018+s.b*7));
    cx.fillStyle='#ffffff'; cx.beginPath();
    cx.arc(s.x,s.y,s.r,0,Math.PI*2); cx.fill();
  }); cx.globalAlpha=1;
  // Moon
  cx.fillStyle='#ddeeff'; cx.beginPath(); cx.arc(W-80,40,18,0,Math.PI*2); cx.fill();
  cx.fillStyle='#0d2844'; cx.beginPath(); cx.arc(W-72,36,16,0,Math.PI*2); cx.fill();
  // Horizon fog
  let fg=cx.createLinearGradient(0,H*0.2,0,H*0.32);
  fg.addColorStop(0,'rgba(0,0,0,0)'); fg.addColorStop(1,'rgba(10,40,10,0.95)');
  cx.fillStyle=fg; cx.fillRect(0,H*0.2,W,H*0.12);
  // Ground
  let gg=cx.createLinearGradient(0,H*0.3,0,H);
  gg.addColorStop(0,'#1d5e10'); gg.addColorStop(0.45,'#185210'); gg.addColorStop(1,'#0e2d07');
  cx.fillStyle=gg; cx.fillRect(0,H*0.3,W,H*0.7);
  // Grass texture
  cx.strokeStyle='rgba(25,90,15,0.22)'; cx.lineWidth=1;
  for(let x=0;x<W;x+=15){ cx.beginPath(); cx.moveTo(x,H*0.31); cx.lineTo(x+5,H); cx.stroke(); }
  // Path to base (dirt)
  let pg=cx.createLinearGradient(W/2-30,0,W/2+30,0);
  pg.addColorStop(0,'rgba(80,50,20,0)'); pg.addColorStop(0.5,'rgba(80,50,20,0.18)'); pg.addColorStop(1,'rgba(80,50,20,0)');
  cx.fillStyle=pg; cx.fillRect(W/2-30,H*0.3,60,H*0.7);
}

function drawRock(r){
  cx.fillStyle='#3a3a2a'; cx.beginPath(); cx.ellipse(r.x,r.y,r.w/2,r.h/2,0.2,0,Math.PI*2); cx.fill();
  cx.fillStyle='#4a4a38'; cx.beginPath(); cx.ellipse(r.x-r.w*0.12,r.y-r.h*0.25,r.w*0.28,r.h*0.28,0,0,Math.PI*2); cx.fill();
}

function drawTree(t){
  cx.fillStyle='#3a2000'; cx.fillRect(t.x-4,t.y,8,t.r*0.9);
  let clrs=t.dark?['#12280e','#193a12','#214a18']:['#1a4410','#245c18','#2e7420'];
  for(let i=2;i>=0;i--){
    cx.fillStyle=clrs[i]; cx.beginPath();
    cx.arc(t.x,t.y-t.r*0.25-i*t.r*0.24,t.r*(0.88-i*0.1),0,Math.PI*2); cx.fill();
  }
}

function drawBase(){
  let bx=W/2,by=H-55,bw=114,bh=78;
  // Shadow
  cx.fillStyle='rgba(0,0,0,0.4)'; cx.fillRect(bx-bw/2+10,by-bh+10,bw,bh);
  // Stone wall gradient
  let wg=cx.createLinearGradient(bx-bw/2,by-bh,bx+bw/2,by);
  wg.addColorStop(0,'#5a4228'); wg.addColorStop(0.5,'#3d2a14'); wg.addColorStop(1,'#28180a');
  cx.fillStyle=wg; cx.fillRect(bx-bw/2,by-bh,bw,bh);
  // Stone mortar lines
  cx.strokeStyle='rgba(0,0,0,0.35)'; cx.lineWidth=1;
  for(let y=by-bh+12;y<by;y+=15){ cx.beginPath(); cx.moveTo(bx-bw/2,y); cx.lineTo(bx+bw/2,y); cx.stroke(); }
  for(let y=by-bh+12;y<by;y+=30){ for(let x=bx-bw/2+10;x<bx+bw/2;x+=20){ cx.beginPath(); cx.moveTo(x,y); cx.lineTo(x,y+15); cx.stroke(); } }
  // Battlements
  cx.fillStyle='#6a5238';
  for(let bxx=bx-bw/2;bxx<bx+bw/2-14;bxx+=18){ cx.fillRect(bxx,by-bh-14,13,14); }
  // Arrow slits
  cx.fillStyle='rgba(0,0,0,0.6)';
  cx.fillRect(bx-40,by-bh+20,8,18); cx.fillRect(bx-10,by-bh+20,8,18); cx.fillRect(bx+20,by-bh+20,8,18);
  // Gate archway
  cx.fillStyle='#0d0600';
  cx.fillRect(bx-17,by-42,34,42);
  cx.beginPath(); cx.arc(bx,by-42,17,Math.PI,0); cx.fill();
  // Gate bars
  cx.strokeStyle='#3a2508'; cx.lineWidth=3;
  for(let gx=-12;gx<=12;gx+=8){ cx.beginPath(); cx.moveTo(bx+gx,by-42); cx.lineTo(bx+gx,by); cx.stroke(); }
  // Torches (flickering)
  let fl=0.7+0.3*Math.sin(frame*0.12);
  cx.fillStyle=`rgba(255,${Math.floor(100+60*Math.sin(frame*0.1))},0,${fl})`;
  cx.beginPath(); cx.arc(bx-bw/2+14,by-bh+10,5,0,Math.PI*2); cx.fill();
  cx.beginPath(); cx.arc(bx+bw/2-14,by-bh+10,5,0,Math.PI*2); cx.fill();
  // Torch glow
  [bx-bw/2+14,bx+bw/2-14].forEach(tx=>{
    let tg=cx.createRadialGradient(tx,by-bh+10,0,tx,by-bh+10,45);
    tg.addColorStop(0,'rgba(255,120,0,0.25)'); tg.addColorStop(1,'rgba(0,0,0,0)');
    cx.fillStyle=tg; cx.fillRect(tx-45,by-bh-20,90,70);
  });
  // Flag
  cx.fillStyle='#666'; cx.fillRect(bx-1,by-bh-40,2,30);
  cx.fillStyle='#FFD100';
  let fw=Math.sin(frame*0.06)*3;
  cx.beginPath(); cx.moveTo(bx+1,by-bh-38); cx.lineTo(bx+20+fw,by-bh-30+fw); cx.lineTo(bx+1,by-bh-20); cx.closePath(); cx.fill();
  // Base HP bar
  let bpct=baseHp/BASE_MAX;
  let bc=bpct>0.6?'#00e676':bpct>0.3?'#ff9100':'#ff1744';
  cx.fillStyle='rgba(0,0,0,0.75)'; cx.fillRect(bx-58,by-bh-22,116,10);
  cx.fillStyle=bc; cx.fillRect(bx-58,by-bh-22,116*bpct,10);
  cx.strokeStyle='rgba(255,215,0,0.6)'; cx.lineWidth=1; cx.strokeRect(bx-58,by-bh-22,116,10);
  cx.fillStyle='#FFD100'; cx.font='bold 8px Rajdhani,sans-serif'; cx.textAlign='center';
  cx.fillText('🏰 BASE '+baseHp+'/'+BASE_MAX,bx,by-bh-26); cx.textAlign='left';
}

function drawPlayer(){
  let x=p.x,y=p.y,f=p.facing;
  let wk=Math.sin(frame*0.22)*8;
  // Shadow
  cx.fillStyle='rgba(0,0,0,0.35)'; cx.beginPath(); cx.ellipse(x,y+21,18,5,0,0,Math.PI*2); cx.fill();
  // Boots
  cx.fillStyle='#0d0800';
  cx.fillRect(x+f*(-9),y+14,9,9); cx.fillRect(x+f*0,y+14+Math.abs(wk)*0.5,9,9);
  // Legs
  cx.fillStyle='#243c10';
  cx.fillRect(x+f*(-9),y+2,8,14+Math.abs(wk*0.4));
  cx.fillStyle='#1e3209';
  cx.fillRect(x+f*0,y+2,8,14);
  // Torso (camo)
  let tg=cx.createLinearGradient(x-11,y-18,x+11,y+2);
  tg.addColorStop(0,'#3e6018'); tg.addColorStop(1,'#2a4a10');
  cx.fillStyle=tg; cx.fillRect(x-11,y-18,22,22);
  // Camo patches
  cx.fillStyle='rgba(14,30,6,0.55)';
  cx.fillRect(x-8,y-14,6,5); cx.fillRect(x+2,y-9,5,4); cx.fillRect(x-4,y-4,4,5);
  // Belt
  cx.fillStyle='#1a1200'; cx.fillRect(x-11,y+2,22,4);
  // Arms
  cx.fillStyle='#3e6018';
  cx.fillRect(x-19,y-14,9,14); cx.fillRect(x+10,y-14,9,14);
  cx.fillStyle='#d0944a'; cx.fillRect(x-19,y,9,8); cx.fillRect(x+10,y,9,8);
  // Neck + Head
  cx.fillStyle='#d0944a'; cx.fillRect(x-5,y-22,10,6);
  let hg=cx.createRadialGradient(x,y-32,2,x,y-32,12);
  hg.addColorStop(0,'#e0a85c'); hg.addColorStop(1,'#c88840');
  cx.fillStyle=hg; cx.beginPath(); cx.arc(x,y-30,11,0,Math.PI*2); cx.fill();
  // Helmet
  cx.fillStyle='#2e4812'; cx.fillRect(x-13,y-40,26,14);
  cx.beginPath(); cx.arc(x,y-40,13,Math.PI,0); cx.fill();
  cx.fillStyle='#1e3009'; cx.fillRect(x-14,y-30,28,4);
  // Eyes
  cx.fillStyle='#1a1a1a'; cx.beginPath(); cx.arc(x-3,y-31,2,0,Math.PI*2); cx.fill();
  cx.beginPath(); cx.arc(x+3,y-31,2,0,Math.PI*2); cx.fill();
  // Gun
  cx.fillStyle='#1a1a1a'; cx.fillRect(x+10*f,y-14,24*f,6);
  cx.fillStyle='#2a2a2a'; cx.fillRect(x+30*f,y-16,5*f,10);
  cx.fillStyle='#3a3a3a'; cx.fillRect(x+14*f,y-16,8*f,3);
}

function drawEnemy(e){
  if(frame<e.spawn||e.hp<=0) return;
  let x=e.x,y=e.y,t=e.type;
  // Spawn fade-in
  if(frame<e.spawn+20) cx.globalAlpha=(frame-e.spawn)/20;
  // Shadow
  let sw=t==='boss'?24:15;
  cx.fillStyle='rgba(0,0,0,0.28)'; cx.beginPath(); cx.ellipse(x,y+20,sw,5,0,0,Math.PI*2); cx.fill();
  let wk=Math.sin(frame*0.15+x)*7;
  if(t==='zombie'){
    // Legs shambling
    cx.fillStyle='#1a360a'; cx.fillRect(x-7,y+2,7,16+Math.abs(wk*0.6));
    cx.fillStyle='#122608'; cx.fillRect(x,y+2,7,16);
    // Body
    cx.fillStyle='#2a5010'; cx.fillRect(x-10,y-16,20,20);
    cx.fillStyle='rgba(0,60,0,0.5)'; cx.fillRect(x-6,y-12,5,5); cx.fillRect(x+3,y-7,4,4);
    // Outstretched arms
    let ar=Math.sin(frame*0.1)*5;
    cx.fillStyle='#2a5010';
    cx.save(); cx.translate(x-10,y-10); cx.rotate(-0.25+ar*0.02); cx.fillRect(-18,0,18,7); cx.restore();
    cx.save(); cx.translate(x+10,y-10); cx.rotate(0.25-ar*0.02); cx.fillRect(0,0,18,7); cx.restore();
    // Head
    cx.fillStyle='#4a7a1a'; cx.beginPath(); cx.arc(x,y-24,10,0,Math.PI*2); cx.fill();
    cx.fillStyle='#3a5c10'; cx.fillRect(x-5,y-34,10,12);
    // Glowing red eyes
    cx.shadowColor='#ff0000'; cx.shadowBlur=10;
    cx.fillStyle='#ff2200'; cx.beginPath(); cx.arc(x-4,y-25,2.5,0,Math.PI*2); cx.fill();
    cx.beginPath(); cx.arc(x+4,y-25,2.5,0,Math.PI*2); cx.fill();
    cx.shadowBlur=0;
    // Wounds/mouth
    cx.strokeStyle='#1a2a0a'; cx.lineWidth=2;
    cx.beginPath(); cx.moveTo(x-4,y-19); cx.lineTo(x-1,y-16); cx.lineTo(x+4,y-19); cx.stroke();
  } else if(t==='soldier'){
    // Legs
    cx.fillStyle='#4a3010'; cx.fillRect(x-7,y+2,7,16+Math.abs(wk*0.5));
    cx.fillStyle='#3a2008'; cx.fillRect(x,y+2,7,16);
    cx.fillStyle='#0d0600'; cx.fillRect(x-8,y+16,8,8); cx.fillRect(x,y+16,8,8);
    // Body + vest
    cx.fillStyle='#5a3a10'; cx.fillRect(x-10,y-16,20,20);
    cx.fillStyle='#3a2508'; cx.fillRect(x-8,y-14,16,16);
    // Ammo belts
    cx.fillStyle='rgba(255,180,0,0.4)';
    for(let i=0;i<3;i++) cx.fillRect(x-7+i*5,y-12,3,14);
    // Arms
    cx.fillStyle='#5a3a10'; cx.fillRect(x-17,y-12,8,12); cx.fillRect(x+9,y-12,8,12);
    // Head
    cx.fillStyle='#d0844a'; cx.beginPath(); cx.arc(x,y-24,9,0,Math.PI*2); cx.fill();
    cx.fillStyle='#3a2508'; cx.fillRect(x-11,y-34,22,12);
    cx.beginPath(); cx.arc(x,y-34,11,Math.PI,0); cx.fill();
    // Eyes
    cx.shadowColor='#ff2200'; cx.shadowBlur=8;
    cx.fillStyle='#ff0000'; cx.beginPath(); cx.arc(x-3,y-25,2,0,Math.PI*2); cx.fill();
    cx.beginPath(); cx.arc(x+3,y-25,2,0,Math.PI*2); cx.fill();
    cx.shadowBlur=0;
    // Gun
    cx.fillStyle='#1a1a1a'; cx.fillRect(x+9,y-10,18,5);
  } else {
    // BOSS
    let pulse=Math.sin(frame*0.07)*4;
    cx.fillStyle='rgba(140,0,140,0.22)'; cx.shadowColor='#cc00cc'; cx.shadowBlur=25;
    cx.beginPath(); cx.arc(x,y-14,28+pulse,0,Math.PI*2); cx.fill(); cx.shadowBlur=0;
    // Body
    cx.fillStyle='#50006a'; cx.fillRect(x-16,y-22,32,32);
    // Armour plates
    cx.fillStyle='#7000a0';
    cx.fillRect(x-14,y-20,8,14); cx.fillRect(x+6,y-20,8,14);
    // Head
    cx.fillStyle='#6600aa'; cx.beginPath(); cx.arc(x,y-30,17,0,Math.PI*2); cx.fill();
    // Horns
    cx.fillStyle='#cc22cc';
    cx.beginPath(); cx.moveTo(x-14,y-42); cx.lineTo(x-8,y-28); cx.lineTo(x-4,y-42); cx.closePath(); cx.fill();
    cx.beginPath(); cx.moveTo(x+4,y-42); cx.lineTo(x+8,y-28); cx.lineTo(x+14,y-42); cx.closePath(); cx.fill();
    // Eyes
    cx.shadowColor='#ff00ff'; cx.shadowBlur=14;
    cx.fillStyle='#ff44ff'; cx.beginPath(); cx.arc(x-6,y-32,4,0,Math.PI*2); cx.fill();
    cx.beginPath(); cx.arc(x+6,y-32,4,0,Math.PI*2); cx.fill();
    cx.shadowBlur=0;
    // Claws
    cx.fillStyle='#4a006a'; cx.fillRect(x-30,y-16,15,8); cx.fillRect(x+15,y-16,15,8);
    cx.fillStyle='#cc22cc';
    for(let c=0;c<3;c++){ cx.fillRect(x-30+c*4,y-10,3,9); cx.fillRect(x+15+c*4,y-10,3,9); }
  }
  cx.globalAlpha=1;
  // HP bar
  let pct=e.hp/e.mhp, hw=t==='boss'?38:26;
  let hby=y-(t==='boss'?60:45);
  cx.fillStyle='rgba(0,0,0,0.75)'; cx.fillRect(x-hw,hby,hw*2,6);
  cx.fillStyle=pct>0.6?'#00e676':pct>0.3?'#ff9100':'#ff1744';
  cx.fillRect(x-hw,hby,hw*2*pct,6);
  cx.strokeStyle='rgba(255,255,255,0.2)'; cx.lineWidth=1; cx.strokeRect(x-hw,hby,hw*2,6);
}

function drawBullets(){
  bullets.forEach(b=>{
    cx.save();
    cx.shadowColor=b.c; cx.shadowBlur=12;
    cx.fillStyle=b.c; cx.beginPath(); cx.arc(b.x,b.y,b.r,0,Math.PI*2); cx.fill();
    cx.globalAlpha=0.3; cx.beginPath();
    cx.arc(b.x-b.vx*2,b.y-b.vy*2,b.r*0.5,0,Math.PI*2); cx.fill();
    cx.restore();
  });
}

function drawParticles(){
  particles.forEach(pt=>{
    cx.globalAlpha=pt.l/pt.ml;
    cx.fillStyle=pt.c; cx.beginPath(); cx.arc(pt.x,pt.y,pt.r,0,Math.PI*2); cx.fill();
  }); cx.globalAlpha=1;
}

function drawHUD(){
  // Top bar
  cx.fillStyle='rgba(0,0,10,0.72)'; cx.fillRect(0,0,W,54);
  // HP
  let hp=p.hp/P_MAX_HP;
  let hc=hp>0.6?'#00e676':hp>0.3?'#ff9100':'#ff1744';
  cx.fillStyle='rgba(0,0,0,0.55)'; cx.fillRect(10,7,145,12);
  cx.fillStyle=hc; cx.fillRect(10,7,145*hp,12);
  cx.strokeStyle='rgba(255,255,255,0.25)'; cx.lineWidth=1; cx.strokeRect(10,7,145,12);
  cx.fillStyle='#fff'; cx.font='bold 9px Rajdhani,sans-serif';
  cx.fillText('❤️ '+p.hp+'/'+P_MAX_HP,14,17);
  // Shield
  let sp=p.sh/P_MAX_SH;
  cx.fillStyle='rgba(0,0,0,0.55)'; cx.fillRect(10,23,145,9);
  cx.fillStyle='#40c4ff'; cx.fillRect(10,23,145*sp,9);
  cx.strokeStyle='rgba(255,255,255,0.2)'; cx.strokeRect(10,23,145,9);
  cx.fillStyle='#40c4ff'; cx.font='bold 8px Rajdhani,sans-serif';
  cx.fillText('🛡️ '+p.sh+'/'+P_MAX_SH,14,30);
  // Name + Wave
  cx.fillStyle='#FFD100'; cx.font='bold 15px Bangers,sans-serif';
  cx.textAlign='center'; cx.fillText(PNAME.toUpperCase()+' · WAVE '+wave+' / 5',W/2,18);
  let al=enemies.filter(e=>e.hp>0&&frame>=e.spawn).length;
  cx.fillStyle='#ff5252'; cx.font='bold 10px Rajdhani,sans-serif';
  cx.fillText(al+' ENEMIES REMAINING · BASE '+baseHp+'/'+BASE_MAX,W/2,31);
  // Score
  cx.textAlign='right'; cx.fillStyle='#FFD100';
  cx.font='bold 14px Bangers,sans-serif'; cx.fillText('SCORE: '+score,W-10,18);
  cx.fillStyle='#aabbdd'; cx.font='bold 10px Rajdhani,sans-serif';
  cx.fillText('KILLS: '+kills,W-10,30); cx.textAlign='left';
  // Gun hotbar
  let hbX=(W-174)/2,hbY=H-68;
  GUN.forEach((g,i)=>{
    let sel=i===selGun;
    cx.fillStyle=sel?'rgba(255,209,0,0.20)':'rgba(0,0,0,0.68)';
    cx.fillRect(hbX+i*88,hbY,82,48);
    cx.strokeStyle=sel?'#FFD100':'rgba(255,255,255,0.18)';
    cx.lineWidth=sel?2.5:1;
    cx.strokeRect(hbX+i*88,hbY,82,48);
    cx.fillStyle=sel?'#FFD100':'#aabbdd';
    cx.font='bold 12px Bangers,sans-serif'; cx.textAlign='center';
    cx.fillText(g.name,hbX+i*88+41,hbY+18);
    cx.font='9px Rajdhani,sans-serif';
    cx.fillText('DMG '+g.dmg+' · '+g.name.split(' ')[0],hbX+i*88+41,hbY+30);
    cx.fillStyle=sel?'#FFD100':'rgba(255,255,255,0.35)';
    cx.fillText('[KEY '+(i+1)+']',hbX+i*88+41,hbY+44);
    cx.textAlign='left';
  });
  // Active gun glow label
  let ag=GUN[selGun];
  cx.save(); cx.shadowColor=ag.color; cx.shadowBlur=10;
  cx.fillStyle=ag.color; cx.font='bold 10px Rajdhani,sans-serif'; cx.textAlign='center';
  cx.fillText('🎯 '+ag.name+' — F/SPACE=SHOOT · WASD=MOVE · 1/2=SWITCH',W/2,hbY-6);
  cx.restore(); cx.textAlign='left';
  // Bottom strip
  cx.fillStyle='rgba(0,0,10,0.55)'; cx.fillRect(0,H-20,W,20);
  cx.fillStyle='rgba(150,170,210,0.55)'; cx.font='9px Rajdhani,sans-serif';
  cx.fillText('WASD/ARROWS = Walk · F/SPACE = Shoot · 1/2 = Switch gun · CLICK = Shoot · R = Restart',10,H-7);
}

// ── SHOOTING ──
function shoot(){
  if(cooldown>0) return;
  let g=GUN[selGun]; cooldown=g.rate;
  let nearest=null,nd=9999;
  enemies.forEach(e=>{
    if(e.hp<=0||frame<e.spawn) return;
    let d=Math.hypot(e.x-p.x,e.y-p.y);
    if(d<nd){nearest=e;nd=d;}
  });
  if(!nearest) return;
  if(Math.random()>(g.acc)) return; // miss
  let dx=nearest.x-p.x,dy=nearest.y-p.y,d=Math.hypot(dx,dy);
  dx/=d; dy/=d;
  let sp=(Math.random()-0.5)*(g.name==='Pump Shotgun'?0.55:g.name==='Tactical SMG'?0.22:0.07);
  let cos=Math.cos(sp),sin=Math.sin(sp);
  // Muzzle flash particle
  particles.push({x:p.x+14*p.facing,y:p.y-12,vx:0,vy:-1,r:7,c:'#ffee44',l:6,ml:6});
  bullets.push({x:p.x+14*p.facing,y:p.y-12,vx:(dx*cos-dy*sin)*g.spd,vy:(dx*sin+dy*cos)*g.spd,
    dmg:g.dmg,r:g.r,c:g.color,aoe:g.aoe});
  // Pump fires 3 pellets
  if(g.name==='Pump Shotgun'){
    for(let i=0;i<2;i++){
      let sp2=(Math.random()-0.5)*0.6;
      let c2=Math.cos(sp2),s2=Math.sin(sp2);
      bullets.push({x:p.x+14*p.facing,y:p.y-12,vx:(dx*c2-dy*s2)*g.spd*0.9,vy:(dx*s2+dy*c2)*g.spd*0.9,
        dmg:Math.floor(g.dmg*0.4),r:g.r*0.7,c:g.color,aoe:0});
    }
  }
}

// ── UPDATE ──
function update(){
  if(gameOver||showResult) return;
  frame++; if(cooldown>0) cooldown--;
  let moved=false;
  let nx=p.x,ny=p.y;
  if(keys['KeyW']||keys['ArrowUp']){ny=Math.max(H*0.33+8,ny-p.spd);moved=true;}
  if(keys['KeyS']||keys['ArrowDown']){ny=Math.min(H-82,ny+p.spd);moved=true;}
  if(keys['KeyA']||keys['ArrowLeft']){nx=Math.max(16,nx-p.spd);p.facing=-1;moved=true;}
  if(keys['KeyD']||keys['ArrowRight']){nx=Math.min(W-16,nx+p.spd);p.facing=1;moved=true;}
  p.x=nx; p.y=ny;
  if(keys['Space']||keys['KeyF']) shoot();
  // Bullets
  bullets=bullets.filter(b=>{
    b.x+=b.vx; b.y+=b.vy;
    if(b.x<-10||b.x>W+10||b.y<-10||b.y>H+10) return false;
    let hit=false;
    enemies.forEach(e=>{
      if(e.hp<=0||frame<e.spawn) return;
      let er=e.type==='boss'?23:16;
      if(Math.hypot(b.x-e.x,b.y-e.y)<er+b.r){
        let dmg=b.dmg;
        if(ABILITY_TYPE==='double'&&Math.random()<ABILITY_VAL) dmg*=2;
        e.hp=Math.max(0,e.hp-dmg);
        for(let i=0;i<8;i++) particles.push({x:b.x,y:b.y,vx:(Math.random()-0.5)*6,vy:(Math.random()-0.5)*6,r:3+Math.random()*3,c:b.c,l:16,ml:16});
        if(e.hp<=0){
          kills++; score+=e.type==='boss'?300:e.type==='soldier'?150:50;
          let dc=e.type==='boss'?'#cc00cc':e.type==='soldier'?'#ff8800':'#44cc00';
          for(let i=0;i<18;i++) particles.push({x:e.x,y:e.y,vx:(Math.random()-0.5)*9,vy:(Math.random()-0.5)*9,r:4+Math.random()*6,c:dc,l:32,ml:32});
          if(ABILITY_TYPE==='heal') p.hp=Math.min(P_MAX_HP,p.hp+ABILITY_VAL);
        }
        if(b.aoe>0){
          enemies.forEach(e2=>{
            if(e2!==e&&e2.hp>0&&Math.hypot(e2.x-b.x,e2.y-b.y)<b.aoe) e2.hp=Math.max(0,e2.hp-Math.floor(b.dmg*0.6));
          });
          for(let i=0;i<14;i++) particles.push({x:b.x,y:b.y,vx:(Math.random()-0.5)*10,vy:(Math.random()-0.5)*10,r:5+Math.random()*7,c:'#ff4400',l:28,ml:28});
        }
        hit=true;
      }
    });
    return !hit;
  });
  // Enemy AI
  enemies.forEach(e=>{
    if(e.hp<=0||frame<e.spawn) return;
    let dp=Math.hypot(p.x-e.x,p.y-e.y);
    let db=Math.hypot(W/2-e.x,(H-55-78)-e.y);
    let tx=p.x,ty=p.y;
    if(db<dp&&db<200){tx=W/2;ty=H-55-38;}
    let dx=tx-e.x,dy=ty-e.y,d=Math.hypot(dx,dy);
    if(d>4){e.x+=dx/d*e.spd;e.y+=dy/d*e.spd;}
    e.atk++;
    // Attack player
    if(dp<32&&e.atk>55){
      e.atk=0;
      let dmg=e.dmg;
      if(ABILITY_TYPE==='dodge'&&Math.random()<ABILITY_VAL) dmg=0;
      if(p.sh>0){let s=Math.min(p.sh,dmg);p.sh-=s;dmg-=s;}
      p.hp=Math.max(0,p.hp-dmg);
      for(let i=0;i<6;i++) particles.push({x:p.x,y:p.y-20,vx:(Math.random()-0.5)*4,vy:-2-Math.random()*3,r:3,c:'#ff1744',l:14,ml:14});
      if(p.hp<=0) gameOver=true;
    }
    // Attack base
    if(db<55&&e.atk>55){
      e.atk=0;
      baseHp=Math.max(0,baseHp-e.dmg);
      if(baseHp<=0) gameOver=true;
    }
  });
  enemies=enemies.filter(e=>e.hp>0);
  if(enemies.length===0&&!waveDone&&!gameOver){
    waveDone=true; showResult=true;
  }
  particles.forEach(pt=>{pt.x+=pt.vx;pt.y+=pt.vy;pt.vx*=0.9;pt.vy*=0.9;pt.l--;});
  particles=particles.filter(pt=>pt.l>0);
}

// ── DRAW ──
function draw(){
  cx.clearRect(0,0,W,H);
  drawWorld();
  rocks.forEach(r=>drawRock(r));
  trees.filter(t=>t.y<p.y-5).forEach(t=>drawTree(t));
  drawBase();
  enemies.filter(e=>e.hp>0).sort((a,b)=>a.y-b.y).forEach(e=>drawEnemy(e));
  trees.filter(t=>t.y>=p.y-5).forEach(t=>drawTree(t));
  drawPlayer();
  drawBullets();
  drawParticles();
  drawHUD();
  // Overlay screens
  if(showResult){
    cx.fillStyle='rgba(0,0,10,0.78)'; cx.fillRect(0,0,W,H);
    cx.textAlign='center';
    if(wave>=5){
      cx.fillStyle='#FFD100'; cx.shadowColor='#FFD100'; cx.shadowBlur=22;
      cx.font='bold 46px Bangers,sans-serif'; cx.fillText('🏆 VICTORY! 🏆',W/2,H/2-28);
      cx.shadowBlur=0; cx.fillStyle='#fff'; cx.font='18px Rajdhani,sans-serif';
      cx.fillText('Kingdom defended! Score: '+score+' · Kills: '+kills,W/2,H/2+10);
      cx.fillStyle='#aabbdd'; cx.font='13px Rajdhani,sans-serif';
      cx.fillText('Press R to play again',W/2,H/2+34);
    } else {
      cx.fillStyle='#00e676'; cx.shadowColor='#00e676'; cx.shadowBlur=16;
      cx.font='bold 38px Bangers,sans-serif'; cx.fillText('✅ WAVE '+wave+' CLEARED!',W/2,H/2-28);
      cx.shadowBlur=0; cx.fillStyle='#fff'; cx.font='17px Rajdhani,sans-serif';
      cx.fillText('Score: '+score+' · Kills: '+kills+' · Base: '+baseHp+'/'+BASE_MAX+' HP',W/2,H/2+8);
      cx.fillStyle='#FFD100'; cx.font='14px Rajdhani,sans-serif';
      cx.fillText('Press ENTER or SPACE for Wave '+(wave+1),W/2,H/2+34);
    }
    cx.textAlign='left';
  }
  if(gameOver&&!showResult){
    cx.fillStyle='rgba(0,0,0,0.82)'; cx.fillRect(0,0,W,H);
    cx.textAlign='center';
    cx.fillStyle='#ff1744'; cx.shadowColor='#ff1744'; cx.shadowBlur=20;
    cx.font='bold 44px Bangers,sans-serif';
    cx.fillText(baseHp<=0?'💔 YOUR KINGDOM FELL!':'💀 YOU DIED!',W/2,H/2-28);
    cx.shadowBlur=0; cx.fillStyle='#fff'; cx.font='18px Rajdhani,sans-serif';
    cx.fillText('Wave '+wave+' · Score: '+score+' · Kills: '+kills,W/2,H/2+8);
    cx.fillStyle='#FFD100'; cx.font='14px Rajdhani,sans-serif';
    cx.fillText('Press R to restart',W/2,H/2+34);
    cx.textAlign='left';
  }
}

function loop(){ update(); draw(); requestAnimationFrame(loop); }

// ── CONTROLS ──
window.addEventListener('keydown',e=>{
  keys[e.code]=true;
  if(e.code==='Digit1') selGun=0;
  if(e.code==='Digit2') selGun=1;
  if((e.code==='Enter'||e.code==='Space')&&showResult&&!gameOver){
    if(wave>=5){ /* stay on victory screen */ }
    else { wave++; spawnWave(wave); }
  }
  if(e.code==='KeyR'){
    p.hp=P_MAX_HP;p.sh=P_MAX_SH;p.x=W/2;p.y=H*0.72;p.facing=1;
    baseHp=BASE_MAX;score=0;kills=0;wave=1;
    gameOver=false;waveDone=false;showResult=false;
    bullets=[];particles=[]; spawnWave(1);
  }
});
window.addEventListener('keyup',e=>{keys[e.code]=false;});
cvs.addEventListener('click',()=>{ if(!gameOver&&!showResult) shoot(); });
// Give canvas focus for keyboard
cvs.setAttribute('tabindex','0'); cvs.focus();
spawnWave(1);
loop();
</script>
</body>
</html>"""

def build_sp_canvas(pname, skin_sel, w1, w2):
    s = SKINS[skin_sel]
    rates   = {"Scar": 12, "Pump Shotgun": 48, "Tactical SMG": 5,  "Rocket Launcher": 68}
    bspeeds = {"Scar": 12, "Pump Shotgun": 10, "Tactical SMG": 14, "Rocket Launcher": 8}
    bsizes  = {"Scar": 4,  "Pump Shotgun": 7,  "Tactical SMG": 3,  "Rocket Launcher": 10}
    aoes    = {"Scar": 0,  "Pump Shotgun": 0,  "Tactical SMG": 0,  "Rocket Launcher": 65}
    bcolors = {"Scar": "#FFD100", "Pump Shotgun": "#FF5722", "Tactical SMG": "#40c4ff", "Rocket Launcher": "#ff3d00"}

    def gjs(wn):
        wd = WEAPONS[wn]
        return (f'{{name:"{wn}",dmg:{wd["damage"]},acc:{wd["accuracy"]},'
                f'rate:{rates[wn]},spd:{bspeeds[wn]},r:{bsizes[wn]},aoe:{aoes[wn]},color:"{bcolors[wn]}"}}')

    atype = ("dodge" if skin_sel == "Jonesy" else "double" if skin_sel == "Midas"
             else "heal" if skin_sel == "Cuddle Team Leader" else "accuracy")
    aval  = (s.get("dodge_chance") or s.get("gold_chance") or
             s.get("heal_amount")  or s.get("accuracy_bonus") or 0)

    html = _SP_TEMPLATE
    html = html.replace("__PNAME__", pname.replace('"', '').replace("'", ''))
    html = html.replace("__PHP__",   str(s["health"]))
    html = html.replace("__PSH__",   str(s["shields"]))
    html = html.replace("__ATYPE__", atype)
    html = html.replace("__AVAL__",  str(aval))
    html = html.replace("__GUN1__",  gjs(w1))
    html = html.replace("__GUN2__",  gjs(w2))
    return html

# ── State management ──────────────────────────────────────────────────────────
def init_state():
    defs = {
        "game_mode": None,
        "p1_locked": None, "p2_locked": None,
        "p1_name_locked": "Player 1", "p2_name_locked": "Player 2",
        "p1_wpn1": None, "p1_wpn2": None, "p2_wpn1": None, "p2_wpn2": None,
        "p1_wpn_sel": 0,  "p2_wpn_sel": 0,
        "p1_health": None, "p1_shields": None, "p2_health": None, "p2_shields": None,
        "p1_col": 1, "p2_col": 5, "p1_in_cover": False, "p2_in_cover": False,
        "turn_phase": "p1_move", "battle_log": [], "game_over": False,
        "winner_name": None, "winner_skin": None,
        "sp_skin": None, "sp_w1": None, "sp_w2": None, "sp_name": "Player",
    }
    for k, v in defs.items():
        if k not in st.session_state: st.session_state[k] = v
    log = st.session_state.battle_log
    if log and not isinstance(log[0], tuple): st.session_state.battle_log = []

def start_2p(s1, s2, w1a, w1b, w2a, w2b, n1, n2):
    st.session_state.game_mode = "2p"
    st.session_state.p1_health = SKINS[s1]["health"]; st.session_state.p1_shields = SKINS[s1]["shields"]
    st.session_state.p2_health = SKINS[s2]["health"]; st.session_state.p2_shields = SKINS[s2]["shields"]
    st.session_state.p1_col = 1; st.session_state.p2_col = 5
    st.session_state.p1_in_cover = False; st.session_state.p2_in_cover = False
    st.session_state.p1_locked = s1; st.session_state.p2_locked = s2
    st.session_state.p1_wpn1 = w1a; st.session_state.p1_wpn2 = w1b
    st.session_state.p2_wpn1 = w2a; st.session_state.p2_wpn2 = w2b
    st.session_state.p1_wpn_sel = 0; st.session_state.p2_wpn_sel = 0
    st.session_state.p1_name_locked = n1 or "Player 1"
    st.session_state.p2_name_locked = n2 or "Player 2"
    st.session_state.turn_phase = "p1_move"
    st.session_state.battle_log = []; st.session_state.game_over = False
    st.session_state.winner_name = None; st.session_state.winner_skin = None

def full_reset():
    for k in list(st.session_state.keys()): del st.session_state[k]

# ══════════════════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
init_state()
_sk1 = st.session_state.p1_locked or skin_names[0]
_sk2 = st.session_state.p2_locked or skin_names[1]
inject_background(_sk1, _sk2)

st.markdown("""<div style="text-align:center;padding:6px 0 2px;">
<div style="font-family:'Bangers',sans-serif;font-size:40px;letter-spacing:7px;color:#fff;
text-shadow:-3px -3px 0 #000,3px -3px 0 #000,-3px 3px 0 #000,3px 3px 0 #000,
0 0 26px rgba(255,209,0,.9);">💥 FORTNITE BATTLE SIMULATOR</div></div>""", unsafe_allow_html=True)
st.markdown("---")

LOG_C = {"hit": "#00e676", "crit": "#FFD100", "miss": "#6688aa", "ability": "#ff4da6", "win": "#FF5722", "lose": "#ff1744"}

# ════════════════════════════════════
# LOBBY — MODE SELECT
# ════════════════════════════════════
if st.session_state.game_mode is None:
    mc1, mc2 = st.columns(2)
    with mc1:
        st.markdown("""<div style="background:rgba(5,10,40,.85);border:2px solid rgba(255,200,0,.3);border-radius:12px;padding:18px;text-align:center;margin-bottom:10px;">
<div style="font-size:44px;">🎮</div>
<div style="font-family:'Bangers',sans-serif;font-size:24px;letter-spacing:3px;color:#FFD100;">2-PLAYER BATTLE</div>
<div style="font-size:12px;color:#aabbdd;">Same keyboard. Fight your friend!</div>
</div>""", unsafe_allow_html=True)
        if st.button("PLAY 2-PLAYER", use_container_width=True, type="primary", key="mode_2p"):
            st.session_state.game_mode = "lobby_2p"; st.rerun()
    with mc2:
        st.markdown("""<div style="background:rgba(5,10,40,.85);border:2px solid rgba(255,200,0,.3);border-radius:12px;padding:18px;text-align:center;margin-bottom:10px;">
<div style="font-size:44px;">🏰</div>
<div style="font-family:'Bangers',sans-serif;font-size:24px;letter-spacing:3px;color:#FFD100;">DEFEND THE KINGDOM</div>
<div style="font-size:12px;color:#aabbdd;">Single player · Walk, shoot, survive 5 waves!</div>
</div>""", unsafe_allow_html=True)
        if st.button("PLAY SOLO", use_container_width=True, type="primary", key="mode_1p"):
            st.session_state.game_mode = "lobby_1p"; st.rerun()
    st.markdown("---")
    with st.expander("📖 HOW TO PLAY", expanded=False):
        st.markdown("""
**Single Player (Defend the Kingdom):** A real-time canvas game — walk around the arena, shoot enemies, protect your castle!
- **WASD / Arrow keys** = Walk your soldier
- **F / Space / Click** = Shoot nearest enemy
- **1 / 2** = Switch between your 2 guns
- **Enter / Space** = Start next wave after clearing
- **R** = Restart after game over

**2-Player Battle:** Turn-based duel on the same keyboard.
- Move phase: **A** = Left · **S** = Stay · **D** = Right
- Attack phase: **1/2** = Pick gun · **F/Space** = Fire
""")

# ── 2P Lobby ──
elif st.session_state.game_mode == "lobby_2p":
    st.markdown("### 🎮 2-PLAYER SETUP")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🟦 Player 1"); p1n = st.text_input("Name", value="Ayaan", key="p1ni", max_chars=14)
        p1s = st.selectbox("Skin", skin_names, key="p1s")
        p1w1 = st.selectbox("🔫 Gun 1", weapon_names, index=0, key="p1w1")
        p1w2 = st.selectbox("💣 Gun 2", weapon_names, index=1, key="p1w2")
    with c2:
        st.markdown("#### 🟥 Player 2"); p2n = st.text_input("Name", value="Omer", key="p2ni", max_chars=14)
        p2s = st.selectbox("Skin", skin_names, index=1, key="p2s")
        p2w1 = st.selectbox("🔫 Gun 1", weapon_names, index=2, key="p2w1")
        p2w2 = st.selectbox("💣 Gun 2", weapon_names, index=3, key="p2w2")
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("◀ BACK", use_container_width=True, key="back2p"):
            st.session_state.game_mode = None; st.rerun()
    with bc2:
        if st.button("🎮 START MATCH", use_container_width=True, type="primary", key="start2p"):
            start_2p(p1s, p2s, p1w1, p1w2, p2w1, p2w2, p1n, p2n); st.rerun()

# ── SP Lobby ──
elif st.session_state.game_mode == "lobby_1p":
    st.markdown("### 🏰 DEFEND THE KINGDOM — SINGLE PLAYER")
    c1, c2 = st.columns([1, 2])
    with c1:
        spn  = st.text_input("Your Name", value="Ayaan", key="spni", max_chars=14)
        sps  = st.selectbox("Skin / Soldier", skin_names, key="sps")
        spw1 = st.selectbox("🔫 Gun 1 (Primary)",   weapon_names, index=0, key="spw1")
        spw2 = st.selectbox("💣 Gun 2 (Secondary)", weapon_names, index=1, key="spw2")
    with c2:
        st.markdown("""**You are a soldier defending your kingdom's castle from 5 waves of undead enemies!**

| Wave | Enemies |
|------|---------|
| 1 | 3 🧟 Zombies |
| 2 | 5 🧟 + 2 💂 Soldiers |
| 3 | 6 🧟 + 3 💂 + 1 👾 Boss |
| 4 | 7 🧟 + 4 💂 + 1 👾 |
| 5 | 6 🧟 + 4 💂 + 2 👾 |

**Controls:** WASD/Arrows = Walk · F/Space = Shoot · 1/2 = Switch gun

**Tip:** Bosses 👾 hit for 65 damage and take 200 HP to kill. Stay moving, switch guns, and protect your castle gate!
""")
    st.markdown("---")
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("◀ BACK", use_container_width=True, key="backsp"):
            st.session_state.game_mode = None; st.rerun()
    with bc2:
        if st.button("🏰 LAUNCH GAME!", use_container_width=True, type="primary", key="startsp"):
            st.session_state.sp_skin = sps; st.session_state.sp_w1 = spw1
            st.session_state.sp_w2  = spw2; st.session_state.sp_name = spn
            st.session_state.p1_locked = sps
            st.session_state.game_mode = "1p"; st.rerun()

# ════════════════════════════════════
# SINGLE PLAYER — CANVAS GAME
# ════════════════════════════════════
elif st.session_state.game_mode == "1p":
    if st.button("🏠 BACK TO MENU", key="spback"):
        full_reset(); st.rerun()
    html = build_sp_canvas(
        st.session_state.sp_name,
        st.session_state.sp_skin,
        st.session_state.sp_w1,
        st.session_state.sp_w2,
    )
    components.html(html, height=560)

# ════════════════════════════════════
# 2-PLAYER GAME
# ════════════════════════════════════
elif st.session_state.game_mode == "2p":
    n1 = st.session_state.p1_name_locked; n2 = st.session_state.p2_name_locked
    phase = st.session_state.turn_phase; is_p1 = phase.startswith("p1")
    cur_name = n1 if is_p1 else n2; turn_color = "#4da6ff" if is_p1 else "#ff5252"
    if st.session_state.game_over:
        st.balloons()
        wn = st.session_state.winner_name; ws = st.session_state.winner_skin or skin_names[0]
        wc = SKINS[ws]["color"]
        st.markdown(f"""<div style="text-align:center;padding:14px;">
<div style="font-family:'Bangers',sans-serif;font-size:40px;letter-spacing:6px;color:#FFD100;
text-shadow:-3px -3px 0 #000,3px -3px 0 #000,0 0 32px #FFD100;">🏆 {wn.upper()} WINS! 🏆</div></div>""",
            unsafe_allow_html=True)
        render_arena_2p(n1, n2)
        c1, c2 = st.columns(2)
        with c1: render_hp_row(n1, st.session_state.p1_locked, "p1_health", "p1_shields")
        with c2: render_hp_row(n2, st.session_state.p2_locked, "p2_health", "p2_shields")
    else:
        aw = "MOVE or STAY" if phase.endswith("_move") else "PICK GUN + FIRE"
        st.markdown(f"""<div style="text-align:center;padding:7px;background:rgba(5,10,40,.88);
border:2px solid {turn_color};border-radius:8px;box-shadow:0 0 22px {turn_color}55;margin-bottom:6px;">
<div style="font-family:'Bangers',sans-serif;font-size:20px;letter-spacing:4px;color:{turn_color};">
⚡ {cur_name.upper()} — {aw} ⚡</div></div>""", unsafe_allow_html=True)
        render_arena_2p(n1, n2)
        c1, c2 = st.columns(2)
        with c1: render_hp_row(n1, st.session_state.p1_locked, "p1_health", "p1_shields")
        with c2: render_hp_row(n2, st.session_state.p2_locked, "p2_health", "p2_shields")
        st.markdown("---")
        if phase.endswith("_move"):
            st.markdown('<div style="text-align:center;font-family:\'Rajdhani\',sans-serif;font-size:12px;color:#FFD100;letter-spacing:2px;margin-bottom:7px;">🎮 <b>A</b>=Left · <b>S</b>=Stay · <b>D</b>=Right · Step into 🌲 for −50% dmg</div>', unsafe_allow_html=True)
            cc = "p1_col" if is_p1 else "p2_col"; oc = "p2_col" if is_p1 else "p1_col"
            cov = "p1_in_cover" if is_p1 else "p2_in_cover"
            cur_c = st.session_state[cc]; opp_c = st.session_state[oc]
            nxt = "p1_attack" if is_p1 else "p2_attack"
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                if st.button("◀ MOVE LEFT [A]", use_container_width=True, disabled=(cur_c <= 0 or cur_c-1 == opp_c), key="mv_l"):
                    st.session_state[cc] -= 1; nc = st.session_state[cc]
                    st.session_state[cov] = (nc in COVER_POS); st.session_state.turn_phase = nxt; st.rerun()
            with mc2:
                if st.button("⏸️ STAY [S]", use_container_width=True, key="mv_s"):
                    st.session_state.turn_phase = nxt; st.rerun()
            with mc3:
                if st.button("MOVE RIGHT ▶ [D]", use_container_width=True, disabled=(cur_c >= ARENA_SIZE-1 or cur_c+1 == opp_c), key="mv_r"):
                    st.session_state[cc] += 1; nc = st.session_state[cc]
                    st.session_state[cov] = (nc in COVER_POS); st.session_state.turn_phase = nxt; st.rerun()
            inject_keys_2p(phase)
        else:
            st.markdown('<div style="text-align:center;font-family:\'Rajdhani\',sans-serif;font-size:12px;color:#FFD100;letter-spacing:2px;margin-bottom:7px;">🎮 <b>1</b>=Gun 1 · <b>2</b>=Gun 2 · <b>F/Space</b>=🔥 Fire!</div>', unsafe_allow_html=True)
            w1 = st.session_state.p1_wpn1 if is_p1 else st.session_state.p2_wpn1
            w2 = st.session_state.p1_wpn2 if is_p1 else st.session_state.p2_wpn2
            sk = "p1_wpn_sel" if is_p1 else "p2_wpn_sel"; sel = st.session_state[sk]
            weapon_cards(w1, w2, sel)
            swc1, swc2 = st.columns(2)
            with swc1:
                if st.button("SELECT GUN 1 [WPN1]", use_container_width=True, type="primary" if sel==0 else "secondary", key="sel1"):
                    st.session_state[sk] = 0; st.rerun()
            with swc2:
                if st.button("SELECT GUN 2 [WPN2]", use_container_width=True, type="primary" if sel==1 else "secondary", key="sel2"):
                    st.session_state[sk] = 1; st.rerun()
            chosen = w1 if sel == 0 else w2
            if st.button(f"🔥 FIRE {WEAPONS[chosen]['emoji']} {chosen.upper()}! [FIRE]", use_container_width=True, type="primary", key="fire2p"):
                s1v = st.session_state.p1_locked; s2v = st.session_state.p2_locked
                if is_p1:
                    do_fire_2p(n1, s1v, n2, s2v, chosen, "p2_health", "p2_shields", "p1_health", "p1_shields", "p1_col", "p2_col", "p2_in_cover")
                    if not st.session_state.game_over: st.session_state.turn_phase = "p2_move"
                else:
                    do_fire_2p(n2, s2v, n1, s1v, chosen, "p1_health", "p1_shields", "p2_health", "p2_shields", "p2_col", "p1_col", "p1_in_cover")
                    if not st.session_state.game_over: st.session_state.turn_phase = "p1_move"
                st.rerun()
            inject_keys_2p(phase)
    st.markdown("---")
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("🔄 PLAY AGAIN", use_container_width=True, type="primary", key="again2p"): full_reset(); st.rerun()
    with bc2:
        if st.button("🏠 MAIN MENU", use_container_width=True, key="menu2p"): full_reset(); st.rerun()
    st.markdown('<div style="font-family:\'Bangers\',sans-serif;font-size:16px;color:#FFD100;letter-spacing:4px;margin-bottom:5px;margin-top:8px;">📜 BATTLE LOG</div>', unsafe_allow_html=True)
    for et, txt in (st.session_state.battle_log or []):
        st.markdown(f'<div class="log-row" style="border-left-color:{LOG_C.get(et,"#334")};">{txt}</div>', unsafe_allow_html=True)
