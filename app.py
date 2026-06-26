import random, threading, time
import requests
import streamlit as st
import streamlit.components.v1 as components
from gamedata import SKINS, WEAPONS

st.set_page_config(page_title="Fortnite Battle Simulator", page_icon="💥", layout="wide")

# ── Shared online rooms ───────────────────────────────────────────────────────
# st.cache_resource creates a TRUE app-wide singleton shared across ALL user
# sessions — the correct Streamlit way to share mutable state between browsers.
@st.cache_resource
def _store():
    return {"rooms": {}, "lock": threading.Lock()}

def _rooms():  return _store()["rooms"]
def _lock():   return _store()["lock"]

def _cleanup():
    now = time.time()
    with _lock():
        stale = [k for k,v in _rooms().items() if now - v.get("ts",0) > 7200]
        for k in stale: del _rooms()[k]

def make_room(n1, sk1, w1a, w1b):
    _cleanup()
    rooms = _rooms()
    code = str(random.randint(1000, 9999))
    with _lock():
        while code in rooms: code = str(random.randint(1000,9999))
        rooms[code] = {
            "p1_name":n1,"p1_skin":sk1,"p1_w1":w1a,"p1_w2":w1b,
            "p1_hp":SKINS[sk1]["health"],"p1_sh":SKINS[sk1]["shields"],
            "p2_name":None,"p2_skin":None,"p2_w1":None,"p2_w2":None,
            "p2_hp":None,"p2_sh":None,
            "p1_col":1,"p2_col":5,"p1_cover":False,"p2_cover":False,
            "p1_wpn":0,"p2_wpn":0,
            "turn_num":0,"storm_min":0,"storm_max":6,
            "p1_medkit":True,"p2_medkit":True,"p1_built":False,"p2_built":False,
            "phase":"waiting","log":[],"winner":None,"winner_skin":None,"ts":time.time(),
        }
    return code

def join_room(code, n2, sk2, w2a, w2b):
    rooms = _rooms()
    with _lock():
        if code not in rooms: return "notfound"
        r = rooms[code]
        if r["p2_name"] is not None: return "full"
        r.update({"p2_name":n2,"p2_skin":sk2,"p2_w1":w2a,"p2_w2":w2b,
                   "p2_hp":SKINS[sk2]["health"],"p2_sh":SKINS[sk2]["shields"],
                   "phase":"p1_move","ts":time.time()})
        return "ok"

def get_room(code):
    with _lock(): return dict(_rooms().get(code,{}))

def patch_room(code, **kw):
    rooms = _rooms()
    with _lock():
        if code in rooms:
            rooms[code].update(kw); rooms[code]["ts"]=time.time()

# ── Skin image API ────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_skin_image(skin_name):
    try:
        r=requests.get("https://fortnite-api.com/v2/cosmetics/br/search",
            params={"name":skin_name,"language":"en"},timeout=5)
        if r.status_code==200:
            imgs=r.json().get("data",{}).get("images",{}); return imgs.get("featured") or imgs.get("icon")
    except: pass
    return None

for _s in SKINS: get_skin_image(_s)
skin_names=list(SKINS.keys()); weapon_names=list(WEAPONS.keys())

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
.stButton>button:hover{background:rgba(255,209,0,.10)!important;box-shadow:0 0 26px rgba(255,209,0,.45)!important;border-color:#FFD100!important;}
.stButton>button[kind="primary"]{background:linear-gradient(135deg,#FFD100 0%,#FF9500 100%)!important;color:#050a1a!important;border:2px solid #FFD100!important;font-size:16px!important;font-weight:900!important;box-shadow:0 4px 24px rgba(255,175,0,.55)!important;}
.stButton>button:disabled{opacity:.35!important;}
hr{border-color:rgba(255,200,0,.18)!important;}
.bar-wrap{background:rgba(0,0,0,.50);border-radius:3px;height:20px;overflow:hidden;margin:3px 0;}
.bar-fill{height:100%;border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:900;color:#050a1a;min-width:28px;font-family:'Rajdhani',sans-serif;}
.log-row{border-left:3px solid #334;border-radius:4px;padding:6px 12px;margin:2px 0;font-size:13px;font-family:'Rajdhani',sans-serif;background:rgba(5,10,40,.80);}
</style>""", unsafe_allow_html=True)

# ── Pure helpers ──────────────────────────────────────────────────────────────
def apply_damage(hp,sh,dmg):
    if sh>0: a=min(sh,dmg); sh-=a; dmg-=a
    return max(0,hp-dmg),sh
def hp_color(p): return "#00e676" if p>.6 else "#ff9100" if p>.3 else "#ff1744"
def get_rng(wn,d):
    if wn=="Pump Shotgun": return 1.8 if d<=1 else 1.3 if d<=2 else 0.8 if d<=3 else 0.35
    if wn=="Tactical SMG":  return 1.2 if d<=2 else 1.0 if d<=4 else 0.65
    if wn=="Rocket Launcher": return 1.1
    return 1.0
def hp_row(nm,sk,h,s,mh,ms,c):
    img=get_skin_image(sk) or ""; SDATA=SKINS[sk]
    it=f'<img src="{img}" style="width:30px;height:30px;object-fit:contain;border-radius:50%;border:2px solid {SDATA["color"]};margin-right:8px;vertical-align:middle;"/>' if img else f'<span style="font-size:20px;margin-right:6px;">{SDATA["avatar"]}</span>'
    hc=hp_color(h/mh if mh else 0)
    st.markdown(f"""<div style="background:rgba(4,8,28,.85);border:1.5px solid {c}55;border-radius:10px;padding:8px 12px;">
<div style="display:flex;align-items:center;margin-bottom:4px;">{it}<div style="font-family:'Bangers',sans-serif;font-size:14px;color:{c};">{nm.upper()}</div></div>
<div class="bar-wrap"><div class="bar-fill" style="width:{max(int(h/mh*100 if mh else 0),2)}%;background:{hc};">❤️ {h}/{mh}</div></div>
<div class="bar-wrap"><div class="bar-fill" style="width:{max(int(s/ms*100 if ms else 0),2)}%;background:#40c4ff;">🛡️ {s}/{ms}</div></div>
</div>""",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CANVAS GAME HTML TEMPLATES
# Uses __TOKENS__ replaced by Python — no f-string brace hell
# ══════════════════════════════════════════════════════════════════════════════
def _world_js():
    """Shared world drawing JS used by SP, 2P, and online canvas games"""
    return r"""
function drawWorld(){
  let hy=H*0.36;
  // Deep night sky
  let sg=cx.createLinearGradient(0,0,0,hy);
  sg.addColorStop(0,'#010810');sg.addColorStop(0.65,'#081830');sg.addColorStop(1,'#0f3020');
  cx.fillStyle=sg;cx.fillRect(0,0,W,hy);
  // Stars
  stars.forEach(s=>{
    cx.globalAlpha=0.3+0.7*Math.abs(Math.sin(frame*0.016+s.b*8));
    cx.fillStyle='#fff';cx.beginPath();cx.arc(s.x,s.y,s.r,0,Math.PI*2);cx.fill();
  });cx.globalAlpha=1;
  // Moon + glow
  let mr=cx.createRadialGradient(W-95,55,0,W-95,55,80);
  mr.addColorStop(0,'rgba(200,230,255,0.10)');mr.addColorStop(1,'rgba(0,0,0,0)');
  cx.fillStyle=mr;cx.fillRect(W-175,0,160,135);
  cx.fillStyle='#e8f4ff';cx.beginPath();cx.arc(W-95,55,24,0,Math.PI*2);cx.fill();
  cx.fillStyle='#081830';cx.beginPath();cx.arc(W-83,50,20,0,Math.PI*2);cx.fill();
  // Horizon atmospheric haze
  let ahg=cx.createLinearGradient(0,hy-40,0,hy+30);
  ahg.addColorStop(0,'rgba(0,0,0,0)');ahg.addColorStop(0.5,'rgba(18,55,18,0.7)');ahg.addColorStop(1,'rgba(0,0,0,0)');
  cx.fillStyle=ahg;cx.fillRect(0,hy-40,W,70);
  // 3D ground base — bright near horizon, dark near camera
  let gg=cx.createLinearGradient(0,hy,0,H);
  gg.addColorStop(0,'#3a8a1a');gg.addColorStop(0.12,'#2a6a10');
  gg.addColorStop(0.45,'#1a4a08');gg.addColorStop(1,'#091d03');
  cx.fillStyle=gg;cx.fillRect(0,hy,W,H-hy);
  // 3D perspective grid — logarithmic horizontal lines
  for(let i=1;i<=28;i++){
    let t=Math.pow(i/28,2.4);
    let y=hy+(H-hy)*(1-t);
    let alpha=0.05+0.28*t;
    cx.strokeStyle=`rgba(12,50,6,${alpha})`;cx.lineWidth=Math.max(0.4,t*2.5);
    cx.beginPath();cx.moveTo(0,y);cx.lineTo(W,y);cx.stroke();
  }
  // Vanishing perspective lines from horizon centre
  let vx=W/2;
  for(let i=0;i<=32;i++){
    let bx=(i/32)*W;
    let alpha=0.05+0.06*Math.abs(0.5-i/32)*2;
    cx.strokeStyle=`rgba(18,65,8,${alpha})`;cx.lineWidth=0.7;
    cx.beginPath();cx.moveTo(vx,hy);cx.lineTo(bx,H);cx.stroke();
  }
  // Dirt path converging to vanishing point
  let pw1=10,pw2=W*0.32;
  let pg=cx.createLinearGradient(0,hy,0,H);
  pg.addColorStop(0,'rgba(65,42,18,0.35)');pg.addColorStop(1,'rgba(42,26,8,0.60)');
  cx.fillStyle=pg;
  cx.beginPath();cx.moveTo(vx-pw1,hy);cx.lineTo(vx+pw1,hy);cx.lineTo(vx+pw2,H);cx.lineTo(vx-pw2,H);cx.closePath();cx.fill();
  // Path edge highlights
  cx.strokeStyle='rgba(80,55,20,0.25)';cx.lineWidth=1.5;
  cx.beginPath();cx.moveTo(vx-pw1,hy);cx.lineTo(vx-pw2,H);cx.stroke();
  cx.beginPath();cx.moveTo(vx+pw1,hy);cx.lineTo(vx+pw2,H);cx.stroke();
  // Grass blade texture (pre-seeded pattern, not random so no flicker)
  cx.strokeStyle='rgba(45,120,18,0.16)';cx.lineWidth=1;
  for(let x=0;x<W;x+=8){
    let seed=(x*7919)%100;
    let ys=hy+3+seed*0.04;
    let xe=x+(seed>50?3:-3);
    cx.beginPath();cx.moveTo(x,ys);cx.lineTo(xe,H-8);cx.stroke();
  }
}
function drawRock(r){
  cx.fillStyle='#3a3a2a';cx.beginPath();cx.ellipse(r.x,r.y,r.w/2,r.h/2,0.2,0,Math.PI*2);cx.fill();
  cx.fillStyle='#555548';cx.beginPath();cx.ellipse(r.x-r.w*.12,r.y-r.h*.28,r.w*.30,r.h*.30,0,0,Math.PI*2);cx.fill();
  cx.fillStyle='rgba(255,255,255,0.06)';cx.beginPath();cx.ellipse(r.x-r.w*.2,r.y-r.h*.3,r.w*.18,r.h*.18,0,0,Math.PI*2);cx.fill();
}
function drawTree(t){
  // Shadow
  cx.fillStyle='rgba(0,0,0,0.25)';cx.beginPath();cx.ellipse(t.x+6,t.y+6,t.r*.55,t.r*.18,0.3,0,Math.PI*2);cx.fill();
  // Trunk
  cx.fillStyle='#3a2000';cx.fillRect(t.x-5,t.y,10,t.r*.95);
  cx.fillStyle='#2a1500';cx.fillRect(t.x,t.y,5,t.r*.95);
  // Canopy layers (3 overlapping circles, darkest at back)
  let cl=t.dark?['#0e2008','#162e0e','#1e4014']:['#153610','#1e5018','#2a7020'];
  for(let i=2;i>=0;i--){
    cx.fillStyle=cl[i];
    cx.beginPath();cx.arc(t.x+(i-1)*2,t.y-t.r*.3-i*t.r*.26,t.r*(.90-i*.08),0,Math.PI*2);cx.fill();
  }
  // Highlight dot on top canopy
  cx.fillStyle='rgba(80,180,40,0.18)';cx.beginPath();cx.arc(t.x-t.r*.2,t.y-t.r*.7,t.r*.25,0,Math.PI*2);cx.fill();
}
function drawCastle(){
  let bx=W/2,by=H-38,bw=200,bh=100,tw=52,th=150;
  // Moat trench
  cx.fillStyle='rgba(0,0,0,0.55)';cx.fillRect(bx-bw/2-tw+6,by+4,bw+tw*2-12,14);
  cx.fillStyle='rgba(0,20,40,0.6)';cx.fillRect(bx-bw/2-tw+8,by+5,bw+tw*2-16,10);
  // Corner towers
  for(let s of[-1,1]){
    let tx=bx+s*(bw/2+tw/2);
    let tgT=cx.createLinearGradient(tx-tw/2,by-th,tx+tw/2,by);
    tgT.addColorStop(0,'#8a7248');tgT.addColorStop(1,'#3a2810');
    cx.fillStyle=tgT;cx.fillRect(tx-tw/2,by-th,tw,th);
    // Stone lines on tower
    cx.strokeStyle='rgba(0,0,0,0.28)';cx.lineWidth=1;
    for(let y=by-th+16;y<by;y+=20){cx.beginPath();cx.moveTo(tx-tw/2,y);cx.lineTo(tx+tw/2,y);cx.stroke();}
    // Tower battlements
    cx.fillStyle='#9a8258';
    for(let i=0;i<4;i++){cx.fillRect(tx-tw/2+i*14,by-th-18,10,18);}
    // Windows (2 per tower)
    cx.fillStyle='#0d0800';
    for(let wy of[by-th+30,by-th+75]){cx.fillRect(tx-6,wy,12,18);cx.beginPath();cx.arc(tx,wy,6,Math.PI,0);cx.fill();}
    // Torch with glow
    let fl=0.7+0.3*Math.sin(frame*.14+s*3);
    let trc={x:tx,y:by-th+52};
    let glw=cx.createRadialGradient(trc.x,trc.y,0,trc.x,trc.y,60);
    glw.addColorStop(0,`rgba(255,140,0,${fl*0.3})`);glw.addColorStop(1,'rgba(0,0,0,0)');
    cx.fillStyle=glw;cx.fillRect(trc.x-60,trc.y-60,120,120);
    cx.fillStyle=`rgba(255,${Math.floor(120+60*Math.sin(frame*.12+s))},0,${fl})`;
    cx.beginPath();cx.arc(trc.x,trc.y,6,0,Math.PI*2);cx.fill();
  }
  // Main wall
  let wg=cx.createLinearGradient(bx-bw/2,by-bh,bx+bw/2,by);
  wg.addColorStop(0,'#7a6238');wg.addColorStop(0.5,'#5a4828');wg.addColorStop(1,'#2a180a');
  cx.fillStyle=wg;cx.fillRect(bx-bw/2,by-bh,bw,bh);
  // Brick pattern
  cx.strokeStyle='rgba(0,0,0,0.28)';cx.lineWidth=1;
  for(let y=by-bh+16;y<by;y+=20){cx.beginPath();cx.moveTo(bx-bw/2,y);cx.lineTo(bx+bw/2,y);cx.stroke();}
  for(let row=0;row<6;row++){let off=(row%2)*18;for(let x=bx-bw/2+off;x<bx+bw/2;x+=36){cx.beginPath();cx.moveTo(x,by-bh+row*16);cx.lineTo(x,by-bh+(row+1)*16);cx.stroke();}}
  // Wall battlements (top)
  cx.fillStyle='#8a7248';
  for(let i=0;i<10;i++){cx.fillRect(bx-bw/2+i*21,by-bh-20,15,20);}
  // Inner keep (taller centre)
  cx.fillStyle='#6a5238';cx.fillRect(bx-35,by-bh-40,70,40);
  for(let i=0;i<4;i++){cx.fillStyle='#7a6248';cx.fillRect(bx-35+i*19,by-bh-58,14,18);}
  // Gate arch
  cx.fillStyle='#0d0600';cx.fillRect(bx-26,by-60,52,60);
  cx.beginPath();cx.arc(bx,by-60,26,Math.PI,0);cx.fill();
  // Portcullis
  cx.strokeStyle='#4a3010';cx.lineWidth=4;
  for(let gx=-20;gx<=20;gx+=10){cx.beginPath();cx.moveTo(bx+gx,by-60);cx.lineTo(bx+gx,by);cx.stroke();}
  cx.lineWidth=2;
  for(let gy=by-58;gy<by;gy+=14){cx.beginPath();cx.moveTo(bx-20,gy);cx.lineTo(bx+20,gy);cx.stroke();}
  // Flagpole + flag
  cx.fillStyle='#999';cx.fillRect(bx-1.5,by-bh-98,3,58);
  let fw=Math.sin(frame*.07)*6;
  cx.fillStyle='#FFD100';
  cx.beginPath();cx.moveTo(bx+1,by-bh-95);cx.lineTo(bx+32+fw,by-bh-80+fw*.4);cx.lineTo(bx+1,by-bh-63);cx.closePath();cx.fill();
  cx.fillStyle='#1a0a00';cx.font='bold 10px sans-serif';cx.textAlign='center';cx.fillText('👑',bx+14+fw*.3,by-bh-75);cx.textAlign='left';
}
function drawSoldier(x,y,facing,team,wk){
  let isRed=(team==='red');
  cx.fillStyle='rgba(0,0,0,0.3)';cx.beginPath();cx.ellipse(x,y+21,18,5,0,0,Math.PI*2);cx.fill();
  let lc=isRed?'#501808':'#243c10', lc2=isRed?'#3a1006':'#1e3209';
  cx.fillStyle=lc;cx.fillRect(x-9,y+2,8,14+Math.abs(wk*.4));
  cx.fillStyle=lc2;cx.fillRect(x,y+2,8,14);
  cx.fillStyle='#0d0800';cx.fillRect(x-10,y+14,10,9);cx.fillRect(x,y+14,10,9);
  let bc=isRed?'#6a1808':'#3e6018', bc2=isRed?'#501008':'#2a4a10';
  let tg2=cx.createLinearGradient(x-11,y-18,x+11,y+2);
  tg2.addColorStop(0,bc);tg2.addColorStop(1,bc2);
  cx.fillStyle=tg2;cx.fillRect(x-11,y-18,22,22);
  cx.fillStyle='rgba(0,0,0,0.4)';cx.fillRect(x-8,y-14,6,5);cx.fillRect(x+2,y-9,5,4);cx.fillRect(x-4,y-4,4,5);
  cx.fillStyle='#1a1200';cx.fillRect(x-11,y+2,22,4);
  cx.fillStyle=bc;cx.fillRect(x-19,y-14,9,14);cx.fillRect(x+10,y-14,9,14);
  cx.fillStyle='#d0944a';cx.fillRect(x-19,y,9,8);cx.fillRect(x+10,y,9,8);
  cx.fillStyle='#d0944a';cx.fillRect(x-5,y-22,10,6);
  let hg=cx.createRadialGradient(x,y-32,2,x,y-32,12);
  hg.addColorStop(0,'#e0a85c');hg.addColorStop(1,'#c88840');
  cx.fillStyle=hg;cx.beginPath();cx.arc(x,y-30,11,0,Math.PI*2);cx.fill();
  let hc=isRed?'#4a1000':'#2e4812';
  cx.fillStyle=hc;cx.fillRect(x-13,y-40,26,14);
  cx.beginPath();cx.arc(x,y-40,13,Math.PI,0);cx.fill();
  cx.fillStyle=isRed?'#3a0800':'#1e3009';cx.fillRect(x-14,y-30,28,4);
  cx.fillStyle='#1a1a1a';cx.fillRect(x-2,y-32,4,2);cx.fillRect(x-2,y-26,4,2);
  cx.fillStyle='#1a1a1a';cx.fillRect(x+10*facing,y-14,22*facing,6);
  cx.fillStyle='#2a2a2a';cx.fillRect(x+28*facing,y-16,5*facing,10);
}
"""

# ── Single-player canvas HTML ─────────────────────────────────────────────────
_SP_HTML = r"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>*{margin:0;padding:0;box-sizing:border-box;}body{background:#020a1a;overflow:hidden;}canvas{display:block;cursor:crosshair;}</style>
</head><body><canvas id="g"></canvas><script>
const cvs=document.getElementById('g');const cx=cvs.getContext('2d');
const W=cvs.width=Math.min(1100,window.innerWidth-4);const H=cvs.height=680;
const PNAME="__PNAME__";const P_MAX_HP=__PHP__;const P_MAX_SH=__PSH__;
const ABILITY_TYPE="__ATYPE__";const ABILITY_VAL=__AVAL__;const BASE_MAX=300;
const GUN=[__GUN1__,__GUN2__];
let p={x:W/2,y:H*.72,hp:P_MAX_HP,sh:P_MAX_SH,spd:3.4,facing:1};
let enemies=[],bullets=[],particles=[],trees=[],rocks=[];
let wave=1,score=0,kills=0,frame=0,cooldown=0,selGun=0;
let gameOver=false,waveDone=false,showResult=false,baseHp=BASE_MAX;
let keys={};
let stormR=W*0.88,stormShrink=0.03,stormDmgTimer=0;
const stormCX=W/2,stormCY=H*0.62;
let shieldPots=[],drops=[],hitMarkers=[],killFeed=[];
let stars=Array.from({length:130},()=>({x:Math.random()*W,y:Math.random()*H*.30,r:Math.random()*1.8+.3,b:Math.random()}));
for(let i=0;i<40;i++)trees.push({x:25+Math.random()*(W-50),y:60+Math.random()*(H*.55),r:22+Math.random()*24,dark:Math.random()<.45});
for(let i=0;i<14;i++)rocks.push({x:50+Math.random()*(W-100),y:100+Math.random()*(H*.44),w:20+Math.random()*22,h:12+Math.random()*14});
__WORLD_JS__
function spawnShieldPots(n){
  shieldPots=[];
  let pts=[[W*.18,H*.60],[W*.38,H*.56],[W*.62,H*.58],[W*.80,H*.62],[W*.50,H*.76],[W*.28,H*.70]];
  for(let i=0;i<Math.min(4+n,pts.length);i++)shieldPots.push({x:pts[i][0]+(Math.random()-.5)*50,y:pts[i][1]+(Math.random()-.5)*35,collected:false,ph:Math.random()*6.28});
}
function spawnWave(n){
  enemies=[];
  let z=[5,8,7,11,10,13,16][Math.min(n-1,6)];
  let s=[0,3,5,7, 9,10,12][Math.min(n-1,6)];
  let b=[0,0,2,3, 4, 6, 8][Math.min(n-1,6)];
  let sm=1+n*0.08;
  let types=[];
  for(let i=0;i<z;i++)types.push('zombie');
  for(let i=0;i<s;i++)types.push('soldier');
  for(let i=0;i<b;i++)types.push('boss');
  types.sort(()=>Math.random()-.5);
  types.forEach((t,i)=>{
    let mx={zombie:90,soldier:150,boss:340}[t];
    enemies.push({x:40+Math.random()*(W-80),y:-25-i*30,hp:mx,mhp:mx,
      dmg:{zombie:32,soldier:58,boss:100}[t],
      spd:{zombie:1.3*sm,soldier:1.65*sm,boss:1.0*sm}[t],
      type:t,atk:0,spawn:i*5,charging:false,chargeVx:0,chargeVy:0,chargeT:0});
  });
  if(n>1){p.sh=Math.min(P_MAX_SH,p.sh+35);}
  stormR=Math.min(W*0.88,W*0.84-(n-1)*24);stormShrink=0.022+n*0.006;
  spawnShieldPots(n);
  if(n>1)drops.push({x:W*.2+Math.random()*W*.6,y:-40,yf:0,landed:false,collected:false,type:n%2===0?'health':'shield'});
  waveDone=false;showResult=false;
}
function inCover(px,py){
  for(let t of trees)if(Math.hypot(px-t.x,py-t.y)<t.r+22)return true;
  for(let r of rocks)if(Math.hypot(px-r.x,py-r.y)<r.w/2+18)return true;
  return false;
}
function shoot(){
  if(cooldown>0)return;
  let g=GUN[selGun];cooldown=g.rate;
  let nearest=null,nd=9999;
  enemies.forEach(e=>{if(e.hp<=0||frame<e.spawn)return;let d=Math.hypot(e.x-p.x,e.y-p.y);if(d<nd){nearest=e;nd=d;}});
  if(!nearest||Math.random()>g.acc)return;
  particles.push({x:p.x+14*p.facing,y:p.y-12,vx:0,vy:-1,r:7,c:'#ffee44',l:5,ml:5});
  bullets.push({x:p.x+14*p.facing,y:p.y-12,vx:(nearest.x-p.x)/nd*g.spd*((Math.random()-.5)*.1+1),vy:(nearest.y-p.y)/nd*g.spd*((Math.random()-.5)*.1+1),dmg:g.dmg,r:g.r,c:g.color,aoe:g.aoe});
  if(g.name==='Pump Shotgun'){for(let i=0;i<2;i++){let sp=(Math.random()-.5)*.7;bullets.push({x:p.x+14*p.facing,y:p.y-12,vx:Math.cos(sp)*(nearest.x-p.x)/nd*g.spd*.85,vy:Math.sin(sp)*(nearest.y-p.y)/nd*g.spd*.85,dmg:Math.floor(g.dmg*.35),r:g.r*.7,c:g.color,aoe:0});}}
}
function update(){
  if(gameOver||showResult)return;
  frame++;if(cooldown>0)cooldown--;
  if(keys['KeyW']||keys['ArrowUp'])p.y=Math.max(H*.37+8,p.y-p.spd);
  if(keys['KeyS']||keys['ArrowDown'])p.y=Math.min(H-90,p.y+p.spd);
  if(keys['KeyA']||keys['ArrowLeft']){p.x=Math.max(16,p.x-p.spd);p.facing=-1;}
  if(keys['KeyD']||keys['ArrowRight']){p.x=Math.min(W-16,p.x+p.spd);p.facing=1;}
  if(keys['Space']||keys['KeyF'])shoot();
  // Storm shrink + damage
  stormR=Math.max(W*.14,stormR-stormShrink);
  if(Math.hypot(p.x-stormCX,p.y-stormCY)>stormR){
    stormDmgTimer++;if(stormDmgTimer>=56){stormDmgTimer=0;let d=6;if(p.sh>0){let s=Math.min(p.sh,d);p.sh-=s;d-=s;}p.hp=Math.max(0,p.hp-d);for(let i=0;i<5;i++)particles.push({x:p.x+(Math.random()-.5)*22,y:p.y-15,vx:(Math.random()-.5)*3,vy:-2.5,r:3,c:'#aa00ff',l:20,ml:20});if(p.hp<=0)gameOver=true;}
  }else stormDmgTimer=0;
  // Shield pots
  shieldPots.forEach(pt=>{if(pt.collected)return;if(Math.hypot(p.x-pt.x,p.y-pt.y)<24){pt.collected=true;p.sh=Math.min(P_MAX_SH,p.sh+40);score+=25;for(let i=0;i<9;i++)particles.push({x:pt.x,y:pt.y,vx:(Math.random()-.5)*5,vy:(Math.random()-.5)*5,r:4,c:'#40c4ff',l:22,ml:22});}});
  // Supply drops
  if(frame%460===230&&!gameOver)drops.push({x:W*.1+Math.random()*(W*.8),y:-40,yf:0,landed:false,collected:false,type:Math.random()<.5?'health':'shield'});
  drops.forEach(d=>{if(d.collected)return;if(!d.landed){d.yf=Math.min(1,d.yf+0.011);d.y=-40+d.yf*(H*.74+40);}if(!d.landed&&d.y>=H*.74-10){d.landed=true;for(let i=0;i<10;i++)particles.push({x:d.x,y:d.y,vx:(Math.random()-.5)*9,vy:-Math.random()*5,r:4,c:'#FFD100',l:22,ml:22});}if(d.landed&&Math.hypot(p.x-d.x,p.y-d.y)<30){d.collected=true;score+=50;if(d.type==='health'){p.hp=Math.min(P_MAX_HP,p.hp+65);for(let i=0;i<10;i++)particles.push({x:d.x,y:d.y,vx:(Math.random()-.5)*5,vy:(Math.random()-.5)*5,r:5,c:'#00e676',l:26,ml:26});}else{p.sh=Math.min(P_MAX_SH,p.sh+55);for(let i=0;i<10;i++)particles.push({x:d.x,y:d.y,vx:(Math.random()-.5)*5,vy:(Math.random()-.5)*5,r:5,c:'#40c4ff',l:26,ml:26});}}});
  hitMarkers=hitMarkers.filter(h=>(h.l--,h.l>0));killFeed=killFeed.filter(k=>(k.l--,k.l>0));
  bullets=bullets.filter(b=>{
    b.x+=b.vx;b.y+=b.vy;
    if(b.x<-10||b.x>W+10||b.y<-10||b.y>H+10)return false;
    let hit=false;
    enemies.forEach(e=>{
      if(e.hp<=0||frame<e.spawn)return;
      if(Math.hypot(b.x-e.x,b.y-e.y)<(e.type==='boss'?24:16)+b.r){
        let dmg=b.dmg;let crit=ABILITY_TYPE==='double'&&Math.random()<ABILITY_VAL;if(crit)dmg*=2;
        e.hp=Math.max(0,e.hp-dmg);
        hitMarkers.push({x:b.x+(Math.random()-.5)*10,y:b.y-6,l:20,ml:20,dmg,crit});
        for(let i=0;i<7;i++)particles.push({x:b.x,y:b.y,vx:(Math.random()-.5)*6,vy:(Math.random()-.5)*6,r:3+Math.random()*3,c:b.c,l:16,ml:16});
        if(e.hp<=0){kills++;score+=e.type==='boss'?350:e.type==='soldier'?150:50;
          let dc=e.type==='boss'?'#cc00cc':e.type==='soldier'?'#ff8800':'#44cc00';
          killFeed.unshift({txt:(e.type==='boss'?'☠️ BOSS ELIMINATED!':e.type==='soldier'?'💀 SOLDIER DOWN':'🧟 ZOMBIE DOWN'),c:dc,l:200});if(killFeed.length>4)killFeed.pop();
          for(let i=0;i<18;i++)particles.push({x:e.x,y:e.y,vx:(Math.random()-.5)*10,vy:(Math.random()-.5)*10,r:4+Math.random()*6,c:dc,l:32,ml:32});
          if(ABILITY_TYPE==='heal')p.hp=Math.min(P_MAX_HP,p.hp+ABILITY_VAL);}
        if(b.aoe>0){enemies.forEach(e2=>{if(e2!==e&&e2.hp>0&&Math.hypot(e2.x-b.x,e2.y-b.y)<b.aoe)e2.hp=Math.max(0,e2.hp-Math.floor(b.dmg*.6));});for(let i=0;i<14;i++)particles.push({x:b.x,y:b.y,vx:(Math.random()-.5)*10,vy:(Math.random()-.5)*10,r:5+Math.random()*7,c:'#ff4400',l:28,ml:28});}
        hit=true;
      }
    });
    return !hit;
  });
  enemies.forEach(e=>{
    if(e.hp<=0||frame<e.spawn)return;
    // Boss charge ability
    if(e.type==='boss'&&!e.charging&&e.hp<e.mhp*.5&&Math.random()<0.005){
      e.charging=true;let cd=Math.hypot(p.x-e.x,p.y-e.y)||1;
      e.chargeVx=(p.x-e.x)/cd*12;e.chargeVy=(p.y-e.y)/cd*12;e.chargeT=22;
      for(let i=0;i<8;i++)particles.push({x:e.x,y:e.y-14,vx:(Math.random()-.5)*5,vy:-Math.random()*3,r:5,c:'#cc00cc',l:18,ml:18});
    }
    if(e.charging){e.x+=e.chargeVx;e.y+=e.chargeVy;e.chargeT--;if(e.chargeT<=0)e.charging=false;}
    if(!e.charging){
      let dp2=Math.hypot(p.x-e.x,p.y-e.y);let db2=Math.hypot(W/2-e.x,(H-128)-e.y);
      let tx=p.x,ty=p.y;if(db2<dp2&&db2<220){tx=W/2;ty=H-128;}
      let dx=tx-e.x,dy=ty-e.y,d=Math.hypot(dx,dy);if(d>4){e.x+=dx/d*e.spd;e.y+=dy/d*e.spd;}
    }
    e.atk++;
    let dp=Math.hypot(p.x-e.x,p.y-e.y);
    if(dp<30&&e.atk>48){e.atk=0;
      let dmg=e.dmg*(e.charging?2:1);if(e.charging)e.charging=false;
      if(ABILITY_TYPE==='dodge'&&Math.random()<ABILITY_VAL)dmg=0;
      if(p.sh>0){let s=Math.min(p.sh,dmg);p.sh-=s;dmg-=s;}
      p.hp=Math.max(0,p.hp-dmg);
      for(let i=0;i<6;i++)particles.push({x:p.x,y:p.y-20,vx:(Math.random()-.5)*4,vy:-2-Math.random()*3,r:3,c:'#ff1744',l:14,ml:14});
      if(p.hp<=0)gameOver=true;
    }
    let db=Math.hypot(W/2-e.x,(H-128)-e.y);
    if(db<55&&e.atk>48){e.atk=0;baseHp=Math.max(0,baseHp-e.dmg);if(baseHp<=0)gameOver=true;}
  });
  enemies=enemies.filter(e=>e.hp>0);
  if(enemies.length===0&&!waveDone&&!gameOver){waveDone=true;showResult=true;}
  particles.forEach(pt=>{pt.x+=pt.vx;pt.y+=pt.vy;pt.vx*=.9;pt.vy*=.9;pt.l--;});
  particles=particles.filter(pt=>pt.l>0);
}
function drawEnemy(e){
  if(frame<e.spawn||e.hp<=0)return;
  let x=e.x,y=e.y,t=e.type;
  if(frame<e.spawn+20)cx.globalAlpha=(frame-e.spawn)/20;
  let sw=t==='boss'?24:15;
  cx.fillStyle='rgba(0,0,0,0.26)';cx.beginPath();cx.ellipse(x,y+20,sw,5,0,0,Math.PI*2);cx.fill();
  let wk=Math.sin(frame*.15+x)*(t==='boss'?5:7);
  if(t==='zombie'){
    cx.fillStyle='#1a360a';cx.fillRect(x-7,y+2,7,15+Math.abs(wk*.6));cx.fillStyle='#122608';cx.fillRect(x,y+2,7,15);
    cx.fillStyle='#2a5010';cx.fillRect(x-10,y-16,20,20);
    cx.fillStyle='rgba(0,60,0,0.5)';cx.fillRect(x-6,y-12,5,5);cx.fillRect(x+3,y-7,4,4);
    cx.fillStyle='#2a5010';
    cx.save();cx.translate(x-10,y-10);cx.rotate(-0.25+wk*.02);cx.fillRect(-18,0,18,7);cx.restore();
    cx.save();cx.translate(x+10,y-10);cx.rotate(0.25-wk*.02);cx.fillRect(0,0,18,7);cx.restore();
    cx.fillStyle='#4a7a1a';cx.beginPath();cx.arc(x,y-24,10,0,Math.PI*2);cx.fill();
    cx.fillStyle='#3a5c10';cx.fillRect(x-5,y-34,10,12);
    cx.shadowColor='#ff0000';cx.shadowBlur=10;cx.fillStyle='#ff2200';
    cx.beginPath();cx.arc(x-4,y-25,2.5,0,Math.PI*2);cx.fill();cx.beginPath();cx.arc(x+4,y-25,2.5,0,Math.PI*2);cx.fill();cx.shadowBlur=0;
  }else if(t==='soldier'){
    cx.fillStyle='#4a3010';cx.fillRect(x-7,y+2,7,16+Math.abs(wk*.5));cx.fillStyle='#3a2008';cx.fillRect(x,y+2,7,16);
    cx.fillStyle='#0d0600';cx.fillRect(x-8,y+16,8,8);cx.fillRect(x,y+16,8,8);
    cx.fillStyle='#5a3a10';cx.fillRect(x-10,y-16,20,20);cx.fillStyle='#3a2508';cx.fillRect(x-8,y-14,16,16);
    cx.fillStyle='#5a3a10';cx.fillRect(x-17,y-12,8,12);cx.fillRect(x+9,y-12,8,12);
    cx.fillStyle='#d0844a';cx.beginPath();cx.arc(x,y-24,9,0,Math.PI*2);cx.fill();
    cx.fillStyle='#3a2508';cx.fillRect(x-11,y-34,22,12);cx.beginPath();cx.arc(x,y-34,11,Math.PI,0);cx.fill();
    cx.shadowColor='#ff0000';cx.shadowBlur=8;cx.fillStyle='#ff0000';
    cx.beginPath();cx.arc(x-3,y-25,2,0,Math.PI*2);cx.fill();cx.beginPath();cx.arc(x+3,y-25,2,0,Math.PI*2);cx.fill();cx.shadowBlur=0;
    cx.fillStyle='#1a1a1a';cx.fillRect(x+9,y-10,18,5);
  }else{
    let pulse=Math.sin(frame*.07)*4;
    cx.fillStyle='rgba(140,0,140,0.2)';cx.shadowColor='#cc00cc';cx.shadowBlur=25;
    cx.beginPath();cx.arc(x,y-14,28+pulse,0,Math.PI*2);cx.fill();cx.shadowBlur=0;
    cx.fillStyle='#50006a';cx.fillRect(x-16,y-22,32,32);cx.fillStyle='#7000a0';cx.fillRect(x-14,y-20,8,14);cx.fillRect(x+6,y-20,8,14);
    cx.fillStyle='#6600aa';cx.beginPath();cx.arc(x,y-30,17,0,Math.PI*2);cx.fill();
    cx.fillStyle='#cc22cc';
    cx.beginPath();cx.moveTo(x-14,y-42);cx.lineTo(x-8,y-28);cx.lineTo(x-4,y-42);cx.closePath();cx.fill();
    cx.beginPath();cx.moveTo(x+4,y-42);cx.lineTo(x+8,y-28);cx.lineTo(x+14,y-42);cx.closePath();cx.fill();
    cx.shadowColor='#ff00ff';cx.shadowBlur=14;cx.fillStyle='#ff44ff';
    cx.beginPath();cx.arc(x-6,y-32,4,0,Math.PI*2);cx.fill();cx.beginPath();cx.arc(x+6,y-32,4,0,Math.PI*2);cx.fill();cx.shadowBlur=0;
    cx.fillStyle='#4a006a';cx.fillRect(x-30,y-16,15,8);cx.fillRect(x+15,y-16,15,8);
    cx.fillStyle='#cc22cc';for(let c=0;c<3;c++){cx.fillRect(x-30+c*4,y-10,3,9);cx.fillRect(x+15+c*4,y-10,3,9);}
  }
  cx.globalAlpha=1;
  let pct=e.hp/e.mhp,hw=t==='boss'?38:26;
  let hby=y-(t==='boss'?62:46);
  cx.fillStyle='rgba(0,0,0,0.75)';cx.fillRect(x-hw,hby,hw*2,6);
  cx.fillStyle=pct>.6?'#00e676':pct>.3?'#ff9100':'#ff1744';cx.fillRect(x-hw,hby,hw*2*pct,6);
}
function drawStorm(){
  cx.save();cx.beginPath();cx.rect(0,0,W,H);cx.arc(stormCX,stormCY,stormR,0,Math.PI*2,true);cx.closePath();
  cx.fillStyle='rgba(100,0,180,0.24)';cx.fill();
  cx.beginPath();cx.arc(stormCX,stormCY,stormR,0,Math.PI*2);
  cx.strokeStyle=`rgba(200,0,255,${0.75+0.2*Math.sin(frame*.08)})`;cx.lineWidth=4+2*Math.sin(frame*.07);
  cx.shadowColor='#aa00ff';cx.shadowBlur=20;cx.stroke();cx.shadowBlur=0;
  for(let i=0;i<4;i++){let a=(frame*0.035+i*1.57)%(Math.PI*2);let sx=stormCX+Math.cos(a)*stormR,sy=stormCY+Math.sin(a)*stormR;cx.fillStyle='rgba(220,100,255,0.9)';cx.shadowColor='#cc44ff';cx.shadowBlur=10;cx.beginPath();cx.arc(sx,sy,5,0,Math.PI*2);cx.fill();cx.shadowBlur=0;}
  cx.restore();
}
function drawShieldPots(){
  shieldPots.forEach(pt=>{if(pt.collected)return;let pulse=0.75+0.25*Math.sin(frame*.09+pt.ph);cx.save();cx.shadowColor='#40c4ff';cx.shadowBlur=12*pulse;cx.fillStyle=`rgba(64,196,255,${0.14*pulse})`;cx.beginPath();cx.arc(pt.x,pt.y,18*pulse,0,Math.PI*2);cx.fill();let og=cx.createRadialGradient(pt.x-2,pt.y-3,1,pt.x,pt.y,9);og.addColorStop(0,'#b0eeff');og.addColorStop(1,'#0077bb');cx.fillStyle=og;cx.beginPath();cx.arc(pt.x,pt.y,9,0,Math.PI*2);cx.fill();cx.fillStyle='#fff';cx.font='bold 9px sans-serif';cx.textAlign='center';cx.fillText('+40',pt.x,pt.y+3);cx.restore();cx.textAlign='left';});
}
function drawDrops(){
  drops.forEach(d=>{if(d.collected)return;let y=d.y;if(!d.landed){cx.strokeStyle='rgba(255,220,100,0.7)';cx.lineWidth=1.2;for(let i=-2;i<=2;i++){cx.beginPath();cx.moveTo(d.x+i*12,y-50);cx.lineTo(d.x,y-6);cx.stroke();}let cg=cx.createRadialGradient(d.x,y-55,2,d.x,y-50,26);cg.addColorStop(0,'rgba(255,209,0,0.9)');cg.addColorStop(1,'rgba(255,130,0,0.4)');cx.fillStyle=cg;cx.beginPath();cx.arc(d.x,y-50,24,Math.PI,0);cx.fill();}let glow=0.6+0.4*Math.sin(frame*.1);cx.shadowColor=d.type==='health'?'#00e676':'#40c4ff';cx.shadowBlur=14*glow;cx.fillStyle='#7a3200';cx.fillRect(d.x-16,y-20,32,22);cx.fillStyle='#FFD100';cx.fillRect(d.x-16,y-22,32,4);cx.fillRect(d.x-1,y-22,2,25);cx.shadowBlur=0;cx.fillStyle='#fff';cx.font='bold 11px sans-serif';cx.textAlign='center';cx.fillText(d.type==='health'?'❤️':'🛡️',d.x,y-4);cx.textAlign='left';});
}
function drawHitMarkers(){
  hitMarkers.forEach(h=>{let a=h.l/h.ml;cx.globalAlpha=a;cx.strokeStyle=h.crit?'#FFD100':'#ff1744';cx.lineWidth=2;cx.shadowColor=h.crit?'#FFD100':'#ff4444';cx.shadowBlur=6;let s=5;cx.beginPath();cx.moveTo(h.x-s,h.y-s);cx.lineTo(h.x+s,h.y+s);cx.stroke();cx.beginPath();cx.moveTo(h.x+s,h.y-s);cx.lineTo(h.x-s,h.y+s);cx.stroke();cx.shadowBlur=0;cx.fillStyle=h.crit?'#FFD100':'#fff';cx.font=`bold ${h.crit?14:10}px Bangers,sans-serif`;cx.textAlign='center';cx.fillText(h.dmg+(h.crit?' CRIT!':''),h.x,h.y-12);cx.globalAlpha=1;cx.textAlign='left';});
}
function drawHUD(){
  cx.fillStyle='rgba(0,0,10,0.72)';cx.fillRect(0,0,W,54);
  let hp=p.hp/P_MAX_HP,hc=hp>.6?'#00e676':hp>.3?'#ff9100':'#ff1744';
  cx.fillStyle='rgba(0,0,0,0.55)';cx.fillRect(10,7,145,12);cx.fillStyle=hc;cx.fillRect(10,7,145*hp,12);
  cx.strokeStyle='rgba(255,255,255,0.25)';cx.lineWidth=1;cx.strokeRect(10,7,145,12);
  cx.fillStyle='#fff';cx.font='bold 9px Rajdhani,sans-serif';cx.fillText('❤️ '+p.hp+'/'+P_MAX_HP,14,17);
  let sp=p.sh/P_MAX_SH;cx.fillStyle='rgba(0,0,0,0.55)';cx.fillRect(10,23,145,9);cx.fillStyle='#40c4ff';cx.fillRect(10,23,145*sp,9);
  cx.strokeStyle='rgba(255,255,255,0.2)';cx.strokeRect(10,23,145,9);cx.fillStyle='#40c4ff';cx.font='8px Rajdhani,sans-serif';cx.fillText('🛡️ '+p.sh+'/'+P_MAX_SH,14,30);
  cx.fillStyle='#FFD100';cx.font='bold 15px Bangers,sans-serif';cx.textAlign='center';
  cx.fillText(PNAME.toUpperCase()+' · WAVE '+wave+' / 7 · ⚠️ HARD MODE',W/2,18);
  let al=enemies.filter(e=>e.hp>0&&frame>=e.spawn).length;
  cx.fillStyle='#ff5252';cx.font='bold 10px Rajdhani,sans-serif';cx.fillText(al+' ENEMIES · BASE '+baseHp+'/'+BASE_MAX,W/2,31);
  // Storm indicator
  let stormDist=Math.hypot(p.x-stormCX,p.y-stormCY)-stormR;
  if(stormDist>0){cx.fillStyle='rgba(200,0,255,0.9)';cx.shadowColor='#aa00ff';cx.shadowBlur=8;cx.font='bold 10px Rajdhani,sans-serif';cx.fillText('⚡ STORM! GET IN! ('+Math.round(stormDist)+'px away)',W/2,44);cx.shadowBlur=0;}
  else{let pct=Math.round(stormR/(W*0.88)*100);cx.fillStyle='rgba(160,80,255,0.7)';cx.font='9px Rajdhani,sans-serif';cx.fillText('⚡ SAFE ZONE '+pct+'%',W/2,44);}
  cx.textAlign='right';cx.fillStyle='#FFD100';cx.font='bold 14px Bangers,sans-serif';cx.fillText('SCORE: '+score,W-10,18);
  cx.fillStyle='#aabbdd';cx.font='bold 10px Rajdhani,sans-serif';cx.fillText('KILLS: '+kills,W-10,30);
  // Kill feed
  killFeed.forEach((k,i)=>{cx.globalAlpha=k.l/200;cx.fillStyle='rgba(0,0,10,0.7)';cx.fillRect(W-210,38+i*15,200,13);cx.fillStyle=k.c;cx.font='bold 9px Rajdhani,sans-serif';cx.fillText(k.txt,W-10,49+i*15);cx.globalAlpha=1;});
  cx.textAlign='left';
  // Base HP bar
  let bpct=baseHp/BASE_MAX,bc=bpct>.6?'#00e676':bpct>.3?'#ff9100':'#ff1744';
  cx.fillStyle='rgba(0,0,0,0.75)';cx.fillRect(W/2-58,H-128-22,116,10);
  cx.fillStyle=bc;cx.fillRect(W/2-58,H-128-22,116*bpct,10);
  cx.strokeStyle='rgba(255,215,0,0.6)';cx.lineWidth=1;cx.strokeRect(W/2-58,H-128-22,116,10);
  cx.fillStyle='#FFD100';cx.font='bold 8px Rajdhani,sans-serif';cx.textAlign='center';cx.fillText('🏰 BASE '+baseHp+'/'+BASE_MAX,W/2,H-128-26);cx.textAlign='left';
  // Hotbar
  let hbX=(W-174)/2,hbY=H-68;
  GUN.forEach((g,i)=>{
    let sel=i===selGun;
    cx.fillStyle=sel?'rgba(255,209,0,0.22)':'rgba(0,0,0,0.68)';cx.fillRect(hbX+i*88,hbY,82,48);
    cx.strokeStyle=sel?'#FFD100':'rgba(255,255,255,0.18)';cx.lineWidth=sel?2.5:1;cx.strokeRect(hbX+i*88,hbY,82,48);
    cx.fillStyle=sel?'#FFD100':'#aabbdd';cx.font='bold 12px Bangers,sans-serif';cx.textAlign='center';
    cx.fillText(g.name,hbX+i*88+41,hbY+18);cx.font='9px Rajdhani,sans-serif';cx.fillText('DMG '+g.dmg,hbX+i*88+41,hbY+30);
    cx.fillStyle=sel?'#FFD100':'rgba(255,255,255,0.35)';cx.fillText('[KEY '+(i+1)+']',hbX+i*88+41,hbY+44);cx.textAlign='left';
  });
  cx.fillStyle='rgba(0,0,10,0.55)';cx.fillRect(0,H-20,W,20);
  cx.fillStyle='rgba(150,170,210,0.6)';cx.font='9px Rajdhani,sans-serif';
  cx.fillText('WASD/Arrows=Walk · F/Space/Click=Shoot · 1/2=Gun · 🛡️=Shield Pot · 📦=Supply Drop · R=Restart',10,H-7);
}
function draw(){
  cx.clearRect(0,0,W,H);drawWorld();drawStorm();
  rocks.forEach(r=>drawRock(r));drawShieldPots();drawDrops();
  trees.filter(t=>t.y<p.y-5).forEach(t=>drawTree(t));
  drawCastle();
  enemies.filter(e=>e.hp>0).sort((a,b)=>a.y-b.y).forEach(e=>drawEnemy(e));
  trees.filter(t=>t.y>=p.y-5).forEach(t=>drawTree(t));
  let wk=Math.sin(frame*.22)*8;
  drawSoldier(p.x,p.y,p.facing,'green',wk);
  bullets.forEach(b=>{cx.save();cx.shadowColor=b.c;cx.shadowBlur=12;cx.fillStyle=b.c;cx.beginPath();cx.arc(b.x,b.y,b.r,0,Math.PI*2);cx.fill();cx.restore();});
  particles.forEach(pt=>{cx.globalAlpha=pt.l/pt.ml;cx.fillStyle=pt.c;cx.beginPath();cx.arc(pt.x,pt.y,pt.r,0,Math.PI*2);cx.fill();});cx.globalAlpha=1;
  drawHitMarkers();drawHUD();
  if(showResult){
    cx.fillStyle='rgba(0,0,10,0.78)';cx.fillRect(0,0,W,H);cx.textAlign='center';
    if(wave>=7){
      cx.fillStyle='#FFD100';cx.shadowColor='#FFD100';cx.shadowBlur=22;cx.font='bold 46px Bangers,sans-serif';cx.fillText('🏆 KINGDOM SAVED! 🏆',W/2,H/2-28);
      cx.shadowBlur=0;cx.fillStyle='#fff';cx.font='18px Rajdhani,sans-serif';cx.fillText('Score: '+score+' · Kills: '+kills,W/2,H/2+10);
      cx.fillStyle='#aabbdd';cx.font='13px Rajdhani,sans-serif';cx.fillText('Press R to play again',W/2,H/2+34);
    }else{
      cx.fillStyle='#00e676';cx.shadowColor='#00e676';cx.shadowBlur=16;cx.font='bold 38px Bangers,sans-serif';cx.fillText('✅ WAVE '+wave+' CLEARED!',W/2,H/2-28);
      cx.shadowBlur=0;cx.fillStyle='#fff';cx.font='17px Rajdhani,sans-serif';cx.fillText('Score: '+score+' · Kills: '+kills+' · Base HP: '+baseHp,W/2,H/2+8);
      cx.fillStyle='#4da6ff';cx.font='13px Rajdhani,sans-serif';cx.fillText('+35 Shields restored!',W/2,H/2+26);
      cx.fillStyle='#FFD100';cx.font='14px Rajdhani,sans-serif';cx.fillText('Press ENTER or SPACE for Wave '+(wave+1)+' of 7',W/2,H/2+44);
    }cx.textAlign='left';
  }
  if(gameOver&&!showResult){
    cx.fillStyle='rgba(0,0,0,0.82)';cx.fillRect(0,0,W,H);cx.textAlign='center';
    cx.fillStyle='#ff1744';cx.shadowColor='#ff1744';cx.shadowBlur=20;cx.font='bold 44px Bangers,sans-serif';
    cx.fillText(baseHp<=0?'💔 YOUR KINGDOM FELL!':'💀 YOU DIED!',W/2,H/2-28);
    cx.shadowBlur=0;cx.fillStyle='#fff';cx.font='18px Rajdhani,sans-serif';cx.fillText('Wave '+wave+' · Score: '+score+' · Kills: '+kills,W/2,H/2+8);
    cx.fillStyle='#FFD100';cx.font='14px Rajdhani,sans-serif';cx.fillText('Press R to restart',W/2,H/2+34);cx.textAlign='left';
  }
}
function loop(){update();draw();requestAnimationFrame(loop);}
window.addEventListener('keydown',e=>{
  keys[e.code]=true;
  if(e.code==='Digit1')selGun=0;if(e.code==='Digit2')selGun=1;
  if((e.code==='Enter'||e.code==='Space')&&showResult&&!gameOver&&wave<7){wave++;spawnWave(wave);}
  if(e.code==='KeyR'){p.hp=P_MAX_HP;p.sh=P_MAX_SH;p.x=W/2;p.y=H*.72;p.facing=1;baseHp=BASE_MAX;score=0;kills=0;wave=1;gameOver=false;waveDone=false;showResult=false;bullets=[];particles=[];enemies=[];drops=[];hitMarkers=[];killFeed=[];stormR=W*0.88;stormDmgTimer=0;spawnWave(1);}
});
window.addEventListener('keyup',e=>{keys[e.code]=false;});
cvs.addEventListener('click',()=>{if(!gameOver&&!showResult)shoot();});
cvs.setAttribute('tabindex','0');cvs.focus();
spawnWave(1);loop();
</script></body></html>"""

# ── 2-Player same-screen canvas HTML ─────────────────────────────────────────
_2P_HTML = r"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>*{margin:0;padding:0;box-sizing:border-box;}body{background:#020a1a;overflow:hidden;}canvas{display:block;cursor:crosshair;}</style>
</head><body><canvas id="g"></canvas><script>
const cvs=document.getElementById('g');const cx=cvs.getContext('2d');
const W=cvs.width=Math.min(1100,window.innerWidth-4);const H=cvs.height=680;
const P1NAME="__P1NAME__";const P2NAME="__P2NAME__";
const P1_MAX_HP=__P1HP__;const P1_MAX_SH=__P1SH__;
const P2_MAX_HP=__P2HP__;const P2_MAX_SH=__P2SH__;
const P1_ATYPE="__P1ATYPE__";const P1_AVAL=__P1AVAL__;
const P2_ATYPE="__P2ATYPE__";const P2_AVAL=__P2AVAL__;
const GUN1=[__P1GUN1__,__P1GUN2__];
const GUN2=[__P2GUN1__,__P2GUN2__];
let p1={x:W*.12,y:H*.74,hp:P1_MAX_HP,sh:P1_MAX_SH,spd:3.8,facing:1,cd:0,gun:0,jv:0,joff:0};
let p2={x:W*.88,y:H*.74,hp:P2_MAX_HP,sh:P2_MAX_SH,spd:3.8,facing:-1,cd:0,gun:0,jv:0,joff:0};
let b1=[],b2=[],particles=[],trees=[],rocks=[];
let frame=0,gameOver=false,winner=null,score1=0,score2=0;
let keys={};
const JUMP_F=-17,GRAV=0.82;
let stormR=W*0.82,stormShrink=0.14,stormDmgTimer1=0,stormDmgTimer2=0;
const stormCX=W/2,stormCY=H*0.56;
let shieldPots=[],drops=[],hitMarkers=[];
function spawnPickups(){
  shieldPots=[];drops=[];
  let pts=[[W*.25,H*.60],[W*.50,H*.54],[W*.75,H*.60],[W*.38,H*.72],[W*.62,H*.70]];
  pts.forEach(p=>shieldPots.push({x:p[0]+(Math.random()-.5)*40,y:p[1]+(Math.random()-.5)*30,collected:0,ph:Math.random()*6.28}));
}
let stars=Array.from({length:130},()=>({x:Math.random()*W,y:Math.random()*H*.30,r:Math.random()*1.8+.3,b:Math.random()}));
for(let i=0;i<26;i++)trees.push({x:W*.10+Math.random()*(W*.80),y:62+Math.random()*(H*.55),r:22+Math.random()*24,dark:Math.random()<.45});
for(let i=0;i<10;i++)rocks.push({x:W*.08+Math.random()*(W*.84),y:105+Math.random()*(H*.40),w:20+Math.random()*22,h:12+Math.random()*14});
spawnPickups();
__WORLD_JS__
function inCover(px,py){
  for(let t of trees)if(Math.hypot(px-t.x,py-t.y)<t.r+22)return true;
  for(let r of rocks)if(Math.hypot(px-r.x,py-r.y)<r.w/2+18)return true;
  return false;
}
function fire(shooter,target,guns,blist,atype,aval){
  let g=guns[shooter.gun];if(shooter.cd>0)return;shooter.cd=g.rate;
  if(Math.random()>g.acc+(atype==='accuracy'?aval:0))return;
  let dx=target.x-shooter.x,dy=target.y-shooter.y,d=Math.hypot(dx,dy);
  if(d<1)return;dx/=d;dy/=d;
  particles.push({x:shooter.x+14*shooter.facing,y:shooter.y-12,vx:0,vy:-1,r:7,c:'#ffee44',l:5,ml:5});
  let makeBullet=(dmg,r)=>({x:shooter.x+14*shooter.facing,y:shooter.y-12,vx:dx*g.spd*(1+(Math.random()-.5)*.1),vy:dy*g.spd*(1+(Math.random()-.5)*.1),dmg:dmg,r:r,c:g.color,aoe:g.aoe||0});
  blist.push(makeBullet(g.dmg,g.r));
  if(g.name==='Pump Shotgun'){for(let i=0;i<2;i++){let sp=(Math.random()-.5)*.7;blist.push({x:shooter.x+14*shooter.facing,y:shooter.y-12,vx:(dx*Math.cos(sp)-dy*Math.sin(sp))*g.spd*.85,vy:(dx*Math.sin(sp)+dy*Math.cos(sp))*g.spd*.85,dmg:Math.floor(g.dmg*.35),r:g.r*.7,c:g.color,aoe:0});}}
}
function applyHit(b,attacker,defender,atkAtype,atkAval,defAtype,defAval){
  if(defender.joff<-20){particles.push({x:defender.x,y:defender.y+defender.joff-20,vx:0,vy:-2,r:8,c:'#FFD100',l:18,ml:18});return;}
  if(defAtype==='dodge'&&Math.random()<defAval){particles.push({x:defender.x,y:defender.y-30,vx:0,vy:-2,r:8,c:'#00e676',l:20,ml:20});return;}
  let dmg=b.dmg;let crit=atkAtype==='double'&&Math.random()<atkAval;if(crit)dmg*=2;
  if(inCover(defender.x,defender.y))dmg=Math.floor(dmg*.5);
  if(defender.sh>0){let s=Math.min(defender.sh,dmg);defender.sh-=s;dmg-=s;}
  defender.hp=Math.max(0,defender.hp-dmg);
  hitMarkers.push({x:b.x+(Math.random()-.5)*12,y:b.y-6,l:20,ml:20,dmg,crit});
  if(atkAtype==='heal')attacker.hp=Math.min(attacker===p1?P1_MAX_HP:P2_MAX_HP,attacker.hp+atkAval);
  for(let i=0;i<8;i++)particles.push({x:b.x,y:b.y,vx:(Math.random()-.5)*6,vy:(Math.random()-.5)*6,r:3+Math.random()*3,c:b.c,l:16,ml:16});
  if(defender.hp<=0){winner=attacker===p1?P1NAME:P2NAME;gameOver=true;score1+=(attacker===p1?1:0);score2+=(attacker===p2?1:0);for(let i=0;i<20;i++)particles.push({x:defender.x,y:defender.y,vx:(Math.random()-.5)*10,vy:(Math.random()-.5)*10,r:4+Math.random()*6,c:'#ff1744',l:35,ml:35});}
  if(b.aoe>0){[p1,p2].forEach(other=>{if(other!==defender&&Math.hypot(other.x-b.x,other.y-b.y)<b.aoe){other.hp=Math.max(0,other.hp-Math.floor(b.dmg*.5));if(other.hp<=0){winner=attacker===p1?P1NAME:P2NAME;gameOver=true;}}});}
}
function update(){
  if(gameOver)return;
  frame++;
  if(p1.cd>0)p1.cd--;if(p2.cd>0)p2.cd--;
  // Jump physics
  if(keys['KeyQ']&&p1.joff===0&&p1.jv===0){p1.jv=JUMP_F;}
  p1.jv+=GRAV;p1.joff=Math.min(0,p1.joff+p1.jv);if(p1.joff===0)p1.jv=0;
  if(keys['Slash']&&p2.joff===0&&p2.jv===0){p2.jv=JUMP_F;}
  p2.jv+=GRAV;p2.joff=Math.min(0,p2.joff+p2.jv);if(p2.joff===0)p2.jv=0;
  // P1: WASD+F
  if(keys['KeyW'])p1.y=Math.max(H*.37+8,p1.y-p1.spd);
  if(keys['KeyS'])p1.y=Math.min(H-90,p1.y+p1.spd);
  if(keys['KeyA']){p1.x=Math.max(16,p1.x-p1.spd);p1.facing=-1;}
  if(keys['KeyD']){p1.x=Math.min(W-16,p1.x+p1.spd);p1.facing=1;}
  if(keys['KeyF'])fire(p1,p2,GUN1,b1,P1_ATYPE,P1_AVAL);
  // P2: Arrows+L
  if(keys['ArrowUp'])p2.y=Math.max(H*.37+8,p2.y-p2.spd);
  if(keys['ArrowDown'])p2.y=Math.min(H-90,p2.y+p2.spd);
  if(keys['ArrowLeft']){p2.x=Math.max(16,p2.x-p2.spd);p2.facing=-1;}
  if(keys['ArrowRight']){p2.x=Math.min(W-16,p2.x+p2.spd);p2.facing=1;}
  if(keys['KeyL'])fire(p2,p1,GUN2,b2,P2_ATYPE,P2_AVAL);
  p1.facing=p2.x>p1.x?1:-1;p2.facing=p1.x>p2.x?1:-1;
  // Storm
  stormR=Math.max(W*.18,stormR-stormShrink);
  function stormHit(pl,tmr){if(Math.hypot(pl.x-stormCX,pl.y-stormCY)>stormR){tmr++;if(tmr>=52){tmr=0;let d=8;if(pl.sh>0){let s=Math.min(pl.sh,d);pl.sh-=s;d-=s;}pl.hp=Math.max(0,pl.hp-d);for(let i=0;i<4;i++)particles.push({x:pl.x+(Math.random()-.5)*18,y:pl.y-12,vx:(Math.random()-.5)*3,vy:-2.5,r:3,c:'#aa00ff',l:18,ml:18});if(pl.hp<=0){winner=(pl===p1?P2NAME:P1NAME);gameOver=true;(pl===p1?score2++:score1++);}}return tmr;}else return 0;}
  stormDmgTimer1=stormHit(p1,stormDmgTimer1);stormDmgTimer2=stormHit(p2,stormDmgTimer2);
  // Shield pots
  shieldPots.forEach(pt=>{if(pt.collected)return;if(!pt.collected&&Math.hypot(p1.x-pt.x,p1.y-pt.y)<24){pt.collected=1;p1.sh=Math.min(P1_MAX_SH,p1.sh+40);for(let i=0;i<9;i++)particles.push({x:pt.x,y:pt.y,vx:(Math.random()-.5)*5,vy:(Math.random()-.5)*5,r:4,c:'#40c4ff',l:22,ml:22});}else if(!pt.collected&&Math.hypot(p2.x-pt.x,p2.y-pt.y)<24){pt.collected=2;p2.sh=Math.min(P2_MAX_SH,p2.sh+40);for(let i=0;i<9;i++)particles.push({x:pt.x,y:pt.y,vx:(Math.random()-.5)*5,vy:(Math.random()-.5)*5,r:4,c:'#40c4ff',l:22,ml:22});}});
  // Supply drops
  if(frame%520===260&&!gameOver)drops.push({x:W*.15+Math.random()*(W*.7),y:-40,yf:0,landed:false,collected:0,type:Math.random()<.5?'health':'shield'});
  drops.forEach(d=>{if(d.collected)return;if(!d.landed){d.yf=Math.min(1,d.yf+0.012);d.y=-40+d.yf*(H*.74+40);}if(!d.landed&&d.y>=H*.74-10){d.landed=true;for(let i=0;i<10;i++)particles.push({x:d.x,y:d.y,vx:(Math.random()-.5)*8,vy:-Math.random()*4,r:4,c:'#FFD100',l:20,ml:20});}if(d.landed){if(Math.hypot(p1.x-d.x,p1.y-d.y)<28){d.collected=1;if(d.type==='health')p1.hp=Math.min(P1_MAX_HP,p1.hp+60);else p1.sh=Math.min(P1_MAX_SH,p1.sh+50);for(let i=0;i<10;i++)particles.push({x:d.x,y:d.y,vx:(Math.random()-.5)*6,vy:(Math.random()-.5)*6,r:5,c:d.type==='health'?'#00e676':'#40c4ff',l:26,ml:26});}else if(Math.hypot(p2.x-d.x,p2.y-d.y)<28){d.collected=2;if(d.type==='health')p2.hp=Math.min(P2_MAX_HP,p2.hp+60);else p2.sh=Math.min(P2_MAX_SH,p2.sh+50);for(let i=0;i<10;i++)particles.push({x:d.x,y:d.y,vx:(Math.random()-.5)*6,vy:(Math.random()-.5)*6,r:5,c:d.type==='health'?'#00e676':'#40c4ff',l:26,ml:26});}}});
  hitMarkers=hitMarkers.filter(h=>(h.l--,h.l>0));
  // P1 bullets hit P2
  b1=b1.filter(b=>{b.x+=b.vx;b.y+=b.vy;if(b.x<-10||b.x>W+10||b.y<-10||b.y>H+10)return false;
    if(Math.hypot(b.x-p2.x,b.y-(p2.y+p2.joff))<18+b.r){applyHit(b,p1,p2,P1_ATYPE,P1_AVAL,P2_ATYPE,P2_AVAL);return false;}return true;});
  // P2 bullets hit P1
  b2=b2.filter(b=>{b.x+=b.vx;b.y+=b.vy;if(b.x<-10||b.x>W+10||b.y<-10||b.y>H+10)return false;
    if(Math.hypot(b.x-p1.x,b.y-(p1.y+p1.joff))<18+b.r){applyHit(b,p2,p1,P2_ATYPE,P2_AVAL,P1_ATYPE,P1_AVAL);return false;}return true;});
  particles.forEach(pt=>{pt.x+=pt.vx;pt.y+=pt.vy;pt.vx*=.9;pt.vy*=.9;pt.l--;});
  particles=particles.filter(pt=>pt.l>0);
}
function draw2pStorm(){
  cx.save();cx.beginPath();cx.rect(0,0,W,H);cx.arc(stormCX,stormCY,stormR,0,Math.PI*2,true);cx.closePath();
  cx.fillStyle='rgba(100,0,180,0.22)';cx.fill();
  cx.beginPath();cx.arc(stormCX,stormCY,stormR,0,Math.PI*2);
  cx.strokeStyle=`rgba(200,0,255,${0.75+0.2*Math.sin(frame*.08)})`;cx.lineWidth=4+2*Math.sin(frame*.07);
  cx.shadowColor='#aa00ff';cx.shadowBlur=20;cx.stroke();cx.shadowBlur=0;
  for(let i=0;i<4;i++){let a=(frame*0.035+i*1.57)%(Math.PI*2);let sx=stormCX+Math.cos(a)*stormR,sy=stormCY+Math.sin(a)*stormR;cx.fillStyle='rgba(220,100,255,0.9)';cx.shadowColor='#cc44ff';cx.shadowBlur=8;cx.beginPath();cx.arc(sx,sy,5,0,Math.PI*2);cx.fill();cx.shadowBlur=0;}
  cx.restore();
}
function draw2pPickups(){
  shieldPots.forEach(pt=>{if(pt.collected)return;let pulse=0.75+0.25*Math.sin(frame*.09+pt.ph);cx.save();cx.shadowColor='#40c4ff';cx.shadowBlur=12*pulse;cx.fillStyle=`rgba(64,196,255,${0.15*pulse})`;cx.beginPath();cx.arc(pt.x,pt.y,17*pulse,0,Math.PI*2);cx.fill();let og=cx.createRadialGradient(pt.x-2,pt.y-2,1,pt.x,pt.y,8);og.addColorStop(0,'#b0eeff');og.addColorStop(1,'#0077bb');cx.fillStyle=og;cx.beginPath();cx.arc(pt.x,pt.y,8,0,Math.PI*2);cx.fill();cx.fillStyle='#fff';cx.font='8px sans-serif';cx.textAlign='center';cx.fillText('+40',pt.x,pt.y+3);cx.restore();cx.textAlign='left';});
  drops.forEach(d=>{if(d.collected)return;let y=d.y;if(!d.landed){cx.strokeStyle='rgba(255,220,100,0.7)';cx.lineWidth=1.2;for(let i=-2;i<=2;i++){cx.beginPath();cx.moveTo(d.x+i*12,y-48);cx.lineTo(d.x,y-6);cx.stroke();}let cg=cx.createRadialGradient(d.x,y-54,2,d.x,y-50,22);cg.addColorStop(0,'rgba(255,209,0,0.9)');cg.addColorStop(1,'rgba(255,130,0,0.35)');cx.fillStyle=cg;cx.beginPath();cx.arc(d.x,y-50,22,Math.PI,0);cx.fill();}let glow=0.6+0.4*Math.sin(frame*.1);cx.shadowColor=d.type==='health'?'#00e676':'#40c4ff';cx.shadowBlur=12*glow;cx.fillStyle='#7a3200';cx.fillRect(d.x-14,y-19,28,20);cx.fillStyle='#FFD100';cx.fillRect(d.x-14,y-21,28,4);cx.shadowBlur=0;cx.fillStyle='#fff';cx.font='10px sans-serif';cx.textAlign='center';cx.fillText(d.type==='health'?'❤️':'🛡️',d.x,y-4);cx.textAlign='left';});
}
function draw2pHitMarkers(){
  hitMarkers.forEach(h=>{let a=h.l/h.ml;cx.globalAlpha=a;cx.strokeStyle=h.crit?'#FFD100':'#ff1744';cx.lineWidth=2;cx.shadowColor=h.crit?'#FFD100':'#ff4444';cx.shadowBlur=6;let s=5;cx.beginPath();cx.moveTo(h.x-s,h.y-s);cx.lineTo(h.x+s,h.y+s);cx.stroke();cx.beginPath();cx.moveTo(h.x+s,h.y-s);cx.lineTo(h.x-s,h.y+s);cx.stroke();cx.shadowBlur=0;cx.fillStyle=h.crit?'#FFD100':'#fff';cx.font=`bold ${h.crit?14:10}px Bangers,sans-serif`;cx.textAlign='center';cx.fillText(h.dmg+(h.crit?' CRIT!':''),h.x,h.y-12);cx.globalAlpha=1;cx.textAlign='left';});
}
function drawHUD(){
  cx.fillStyle='rgba(0,0,10,0.72)';cx.fillRect(0,0,W,54);
  // P1 HP
  let h1=p1.hp/P1_MAX_HP,hc1=h1>.6?'#00e676':h1>.3?'#ff9100':'#ff1744';
  cx.fillStyle='rgba(0,0,0,0.5)';cx.fillRect(10,7,160,12);cx.fillStyle=hc1;cx.fillRect(10,7,160*h1,12);
  cx.strokeStyle='rgba(255,255,255,0.25)';cx.lineWidth=1;cx.strokeRect(10,7,160,12);
  cx.fillStyle='#fff';cx.font='bold 9px Rajdhani,sans-serif';cx.fillText('❤️ '+p1.hp+'/'+P1_MAX_HP,14,17);
  let s1=p1.sh/P1_MAX_SH;cx.fillStyle='rgba(0,0,0,0.5)';cx.fillRect(10,23,160,9);cx.fillStyle='#40c4ff';cx.fillRect(10,23,160*s1,9);cx.strokeStyle='rgba(255,255,255,0.2)';cx.strokeRect(10,23,160,9);
  cx.fillStyle='#4da6ff';cx.font='bold 10px Bangers,sans-serif';cx.fillText(P1NAME.toUpperCase()+(p1.joff<-10?' ✈️ AIRBORNE':''),12,42);
  // VS centre
  cx.fillStyle='#FFD100';cx.font='bold 18px Bangers,sans-serif';cx.textAlign='center';cx.fillText('⚔️ VS ⚔️',W/2,18);
  // Storm indicator
  let safe=Math.round(stormR/(W*0.82)*100);
  let stormClr=safe>50?'rgba(160,80,255,0.7)':'rgba(220,0,255,0.9)';
  cx.fillStyle=stormClr;cx.font='bold 10px Rajdhani,sans-serif';
  cx.fillText('⚡ SAFE ZONE '+safe+'%  ·  Q=P1 Jump  /=P2 Jump  ·  🛡️Pots  📦Drops',W/2,33);cx.textAlign='left';
  // P2 HP (right side)
  let h2=p2.hp/P2_MAX_HP,hc2=h2>.6?'#00e676':h2>.3?'#ff9100':'#ff1744';
  cx.fillStyle='rgba(0,0,0,0.5)';cx.fillRect(W-170,7,160,12);cx.fillStyle=hc2;cx.fillRect(W-170,7,160*h2,12);
  cx.strokeStyle='rgba(255,255,255,0.25)';cx.strokeRect(W-170,7,160,12);
  cx.fillStyle='#fff';cx.textAlign='right';cx.font='bold 9px Rajdhani,sans-serif';cx.fillText(p2.hp+'/'+P2_MAX_HP+' ❤️',W-14,17);
  let s2=p2.sh/P2_MAX_SH;cx.fillStyle='rgba(0,0,0,0.5)';cx.fillRect(W-170,23,160,9);cx.fillStyle='#40c4ff';cx.fillRect(W-170,23,160*s2,9);cx.strokeStyle='rgba(255,255,255,0.2)';cx.strokeRect(W-170,23,160,9);
  cx.fillStyle='#ff5252';cx.font='bold 10px Bangers,sans-serif';cx.fillText((p2.joff<-10?'✈️ AIRBORNE  ':'')+P2NAME.toUpperCase(),W-12,42);cx.textAlign='left';
  // Hotbars
  let h1Y=H-66;
  GUN1.forEach((g,i)=>{let sel=i===p1.gun;cx.fillStyle=sel?'rgba(77,166,255,0.22)':'rgba(0,0,0,0.68)';cx.fillRect(8+i*82,h1Y,78,46);cx.strokeStyle=sel?'#4da6ff':'rgba(255,255,255,0.18)';cx.lineWidth=sel?2:1;cx.strokeRect(8+i*82,h1Y,78,46);cx.fillStyle=sel?'#4da6ff':'#aabbdd';cx.font='bold 11px Bangers,sans-serif';cx.textAlign='center';cx.fillText(g.name,8+i*82+39,h1Y+16);cx.font='9px Rajdhani,sans-serif';cx.fillText('DMG '+g.dmg,8+i*82+39,h1Y+28);cx.fillStyle=sel?'#4da6ff':'rgba(255,255,255,0.35)';cx.fillText('['+('ZX'[i])+']',8+i*82+39,h1Y+42);cx.textAlign='left';});
  GUN2.forEach((g,i)=>{let sel=i===p2.gun,rx=W-8-78-i*82;cx.fillStyle=sel?'rgba(255,82,82,0.22)':'rgba(0,0,0,0.68)';cx.fillRect(rx,h1Y,78,46);cx.strokeStyle=sel?'#ff5252':'rgba(255,255,255,0.18)';cx.lineWidth=sel?2:1;cx.strokeRect(rx,h1Y,78,46);cx.fillStyle=sel?'#ff5252':'#aabbdd';cx.font='bold 11px Bangers,sans-serif';cx.textAlign='center';cx.fillText(g.name,rx+39,h1Y+16);cx.font='9px Rajdhani,sans-serif';cx.fillText('DMG '+g.dmg,rx+39,h1Y+28);cx.fillStyle=sel?'#ff5252':'rgba(255,255,255,0.35)';cx.fillText(i===0?'[,]':'[.]',rx+39,h1Y+42);cx.textAlign='left';});
  cx.fillStyle='rgba(0,0,10,0.55)';cx.fillRect(0,H-20,W,20);
  cx.fillStyle='rgba(150,170,210,0.6)';cx.font='9px Rajdhani,sans-serif';
  cx.fillText('P1: WASD=Move  F=Shoot  Q=Jump  Z/X=Gun  ·  P2: Arrows=Move  L=Shoot  /=Jump  ,/.=Gun  ·  R=Restart',10,H-7);
}
function draw(){
  cx.clearRect(0,0,W,H);drawWorld();draw2pStorm();
  rocks.forEach(r=>drawRock(r));draw2pPickups();
  let objs=[
    ...trees.map(t=>({k:'tree',y:t.y,d:t})),
    {k:'p',y:p1.y,d:p1,team:'green'},
    {k:'p',y:p2.y,d:p2,team:'red'}
  ];
  objs.sort((a,b)=>a.y-b.y);
  objs.forEach(o=>{
    if(o.k==='tree')drawTree(o.d);
    else{let wk=Math.sin(frame*.22)*8;drawSoldier(o.d.x,o.d.y+o.d.joff,o.d.facing,o.team,wk);}
  });
  [...b1,...b2].forEach(b=>{cx.save();cx.shadowColor=b.c;cx.shadowBlur=12;cx.fillStyle=b.c;cx.beginPath();cx.arc(b.x,b.y,b.r,0,Math.PI*2);cx.fill();cx.restore();});
  particles.forEach(pt=>{cx.globalAlpha=pt.l/pt.ml;cx.fillStyle=pt.c;cx.beginPath();cx.arc(pt.x,pt.y,pt.r,0,Math.PI*2);cx.fill();});cx.globalAlpha=1;
  draw2pHitMarkers();drawHUD();
  if(gameOver){
    cx.fillStyle='rgba(0,0,0,0.82)';cx.fillRect(0,0,W,H);cx.textAlign='center';
    let wc=winner===P1NAME?'#4da6ff':'#ff5252';
    cx.fillStyle=wc;cx.shadowColor=wc;cx.shadowBlur=22;cx.font='bold 48px Bangers,sans-serif';
    cx.fillText('🏆 '+winner.toUpperCase()+' WINS! 🏆',W/2,H/2-24);
    cx.shadowBlur=0;cx.fillStyle='#fff';cx.font='16px Rajdhani,sans-serif';
    cx.fillText(P1NAME+': '+score1+' wins  |  '+P2NAME+': '+score2+' wins',W/2,H/2+12);
    cx.fillStyle='#FFD100';cx.font='14px Rajdhani,sans-serif';cx.fillText('Press R for a rematch',W/2,H/2+36);cx.textAlign='left';
  }
}
function loop(){update();draw();requestAnimationFrame(loop);}
window.addEventListener('keydown',e=>{
  keys[e.code]=true;
  if(e.code==='KeyZ')p1.gun=0;if(e.code==='KeyX')p1.gun=1;
  if(e.code==='Comma')p2.gun=0;if(e.code==='Period')p2.gun=1;
  if(e.code==='KeyR'&&gameOver){
    p1.hp=P1_MAX_HP;p1.sh=P1_MAX_SH;p1.x=W*.12;p1.y=H*.74;p1.cd=0;p1.jv=0;p1.joff=0;
    p2.hp=P2_MAX_HP;p2.sh=P2_MAX_SH;p2.x=W*.88;p2.y=H*.74;p2.cd=0;p2.jv=0;p2.joff=0;
    b1=[];b2=[];particles=[];hitMarkers=[];gameOver=false;winner=null;
    stormR=W*0.82;stormDmgTimer1=0;stormDmgTimer2=0;spawnPickups();
  }
});
window.addEventListener('keyup',e=>{keys[e.code]=false;});
cvs.setAttribute('tabindex','0');cvs.focus();
loop();
</script></body></html>"""

# ── Canvas builders ───────────────────────────────────────────────────────────
_RATES   = {"Scar":12,"Pump Shotgun":48,"Tactical SMG":5,"Rocket Launcher":68}
_SPEEDS  = {"Scar":12,"Pump Shotgun":10,"Tactical SMG":14,"Rocket Launcher":8}
_SIZES   = {"Scar":4,"Pump Shotgun":7,"Tactical SMG":3,"Rocket Launcher":10}
_AOES    = {"Scar":0,"Pump Shotgun":0,"Tactical SMG":0,"Rocket Launcher":65}
_COLORS  = {"Scar":"#FFD100","Pump Shotgun":"#FF5722","Tactical SMG":"#40c4ff","Rocket Launcher":"#ff3d00"}

def _gjs(wn):
    d=WEAPONS[wn]
    return f'{{name:"{wn}",dmg:{d["damage"]},acc:{d["accuracy"]},rate:{_RATES[wn]},spd:{_SPEEDS[wn]},r:{_SIZES[wn]},aoe:{_AOES[wn]},color:"{_COLORS[wn]}"}}'

def _atype(sk):
    return "dodge" if sk=="Jonesy" else "double" if sk=="Midas" else "heal" if sk=="Cuddle Team Leader" else "accuracy"

def _aval(sk):
    s=SKINS[sk]; return s.get("dodge_chance") or s.get("gold_chance") or s.get("heal_amount") or s.get("accuracy_bonus") or 0

def build_sp_canvas(nm,sk,w1,w2):
    h=_SP_HTML.replace("__WORLD_JS__",_world_js())
    for t,v in [("__PNAME__",nm.replace('"','')),("__PHP__",str(SKINS[sk]["health"])),
                ("__PSH__",str(SKINS[sk]["shields"])),("__ATYPE__",_atype(sk)),
                ("__AVAL__",str(_aval(sk))),("__GUN1__",_gjs(w1)),("__GUN2__",_gjs(w2))]:
        h=h.replace(t,v)
    return h

def build_2p_canvas(n1,s1,w1a,w1b,n2,s2,w2a,w2b):
    h=_2P_HTML.replace("__WORLD_JS__",_world_js())
    for t,v in [("__P1NAME__",n1.replace('"','')),("__P2NAME__",n2.replace('"','')),
                ("__P1HP__",str(SKINS[s1]["health"])),("__P1SH__",str(SKINS[s1]["shields"])),
                ("__P2HP__",str(SKINS[s2]["health"])),("__P2SH__",str(SKINS[s2]["shields"])),
                ("__P1ATYPE__",_atype(s1)),("__P1AVAL__",str(_aval(s1))),
                ("__P2ATYPE__",_atype(s2)),("__P2AVAL__",str(_aval(s2))),
                ("__P1GUN1__",_gjs(w1a)),("__P1GUN2__",_gjs(w1b)),
                ("__P2GUN1__",_gjs(w2a)),("__P2GUN2__",_gjs(w2b))]:
        h=h.replace(t,v)
    return h

# ── Online arena canvas ───────────────────────────────────────────────────────
_ONLINE_CANVAS = r"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>*{margin:0;padding:0;box-sizing:border-box;}body{background:#010810;overflow:hidden;}canvas{display:block;}</style>
</head><body><canvas id="g"></canvas><script>
const cvs=document.getElementById('g');const cx=cvs.getContext('2d');
const W=cvs.width=Math.min(1100,window.innerWidth-4);const H=cvs.height=560;
const P1NAME="__ON_P1NAME__",P2NAME="__ON_P2NAME__";
const P1HP=__ON_P1HP__,P1MHP=__ON_P1MAXHP__,P1SH=__ON_P1SH__,P1MSH=__ON_P1MAXSH__;
const P2HP=__ON_P2HP__,P2MHP=__ON_P2MAXHP__,P2SH=__ON_P2SH__,P2MSH=__ON_P2MAXSH__;
const P1COL=__ON_P1COL__,P2COL=__ON_P2COL__;
const PHASE="__ON_PHASE__",WINNER="__ON_WINNER__";
const P1COVER=__ON_P1COVER__,P2COVER=__ON_P2COVER__;
const STORM_MIN=__ON_SMIN__,STORM_MAX=__ON_SMAX__;
const TURN_NUM=__ON_TURN__;
const TOTAL_COLS=7;
function colX(c){return 70+c*(W-140)/(TOTAL_COLS-1);}
// Players sit on ground level
const GY=H*0.78;
const p1x=colX(P1COL),p2x=colX(P2COL);
let frame=0;
let stars=Array.from({length:130},()=>({x:Math.random()*W,y:Math.random()*H*.30,r:Math.random()*1.8+.3,b:Math.random()}));
// Scattered trees all over arena (same layout every load — seeded positions)
const trees=[];
const SEED_POS=[[0.08,0.50],[0.14,0.65],[0.18,0.45],[0.25,0.58],[0.22,0.72],[0.32,0.48],
  [0.38,0.62],[0.35,0.78],[0.45,0.52],[0.50,0.44],[0.55,0.68],[0.58,0.54],
  [0.62,0.74],[0.68,0.46],[0.72,0.60],[0.78,0.50],[0.82,0.70],[0.88,0.56],[0.92,0.66],[0.96,0.48]];
SEED_POS.forEach((p,i)=>trees.push({x:p[0]*W,y:p[1]*H,r:20+i%3*8,dark:i%3===1}));
const rocks=[[0.28,0.72],[0.48,0.66],[0.70,0.70],[0.85,0.62]].map(p=>({x:p[0]*W,y:p[1]*H,w:22+Math.random()*14,h:13+Math.random()*9}));
__WORLD_JS__
function drawHUD(){
  cx.fillStyle='rgba(0,0,10,0.80)';cx.fillRect(0,0,W,56);
  // P1 bars (left)
  let h1=P1HP/P1MHP,hc1=h1>.6?'#00e676':h1>.3?'#ff9100':'#ff1744';
  cx.fillStyle='rgba(0,0,0,0.5)';cx.fillRect(10,8,180,13);cx.fillStyle=hc1;cx.fillRect(10,8,180*h1,13);
  cx.strokeStyle='rgba(77,166,255,0.6)';cx.lineWidth=1;cx.strokeRect(10,8,180,13);
  cx.fillStyle='#fff';cx.font='bold 9px Rajdhani,sans-serif';cx.fillText('❤️ '+P1HP+'/'+P1MHP,14,18);
  let s1=P1SH/P1MSH;cx.fillStyle='rgba(0,0,0,0.5)';cx.fillRect(10,25,180,10);cx.fillStyle='#40c4ff';cx.fillRect(10,25,180*s1,10);
  cx.strokeStyle='rgba(64,196,255,0.4)';cx.strokeRect(10,25,180,10);
  cx.fillStyle='#4da6ff';cx.font='bold 11px Bangers,sans-serif';cx.fillText(P1NAME.toUpperCase(),12,46);
  // VS centre
  let phase=PHASE,turnName=phase.startsWith('p1')?P1NAME:P2NAME;
  let turnClr=phase.startsWith('p1')?'#4da6ff':'#ff5252';
  cx.textAlign='center';
  if(WINNER){cx.fillStyle='#FFD100';cx.shadowColor='#FFD100';cx.shadowBlur=20;cx.font='bold 24px Bangers,sans-serif';cx.fillText('🏆 '+WINNER.toUpperCase()+' WINS!',W/2,32);cx.shadowBlur=0;}
  else{cx.fillStyle=turnClr;cx.shadowColor=turnClr;cx.shadowBlur=12;cx.font='bold 22px Bangers,sans-serif';
    let act=phase.endsWith('_move')?'MOVE':'ATTACK';cx.fillText('⚡ '+turnName.toUpperCase()+' — '+act,W/2,32);cx.shadowBlur=0;}
  cx.fillStyle='rgba(150,170,210,0.55)';cx.font='9px Rajdhani,sans-serif';cx.fillText('🌲 trees = 50% cover  ·  cols 2 & 4',W/2,47);cx.textAlign='left';
  // P2 bars (right)
  let h2=P2HP/P2MHP,hc2=h2>.6?'#00e676':h2>.3?'#ff9100':'#ff1744';
  cx.fillStyle='rgba(0,0,0,0.5)';cx.fillRect(W-190,8,180,13);cx.fillStyle=hc2;cx.fillRect(W-190,8,180*h2,13);
  cx.strokeStyle='rgba(255,82,82,0.6)';cx.strokeRect(W-190,8,180,13);
  cx.fillStyle='#fff';cx.textAlign='right';cx.font='bold 9px Rajdhani,sans-serif';cx.fillText(P2HP+'/'+P2MHP+' ❤️',W-14,18);
  let s2=P2SH/P2MSH;cx.fillStyle='rgba(0,0,0,0.5)';cx.fillRect(W-190,25,180,10);cx.fillStyle='#40c4ff';cx.fillRect(W-190,25,180*s2,10);
  cx.strokeStyle='rgba(64,196,255,0.4)';cx.strokeRect(W-190,25,180,10);
  cx.fillStyle='#ff5252';cx.font='bold 11px Bangers,sans-serif';cx.fillText(P2NAME.toUpperCase(),W-12,46);cx.textAlign='left';
  // Position bar at bottom
  cx.fillStyle='rgba(0,0,10,0.65)';cx.fillRect(0,H-28,W,28);
  for(let c=0;c<7;c++){
    let px=colX(c);
    let ic=c===P1COL?'#4da6ff':c===P2COL?'#ff5252':c===2||c===4?'#00e676':'rgba(255,255,255,0.18)';
    cx.fillStyle=ic;cx.beginPath();cx.arc(px,H-14,6,0,Math.PI*2);cx.fill();
    cx.fillStyle='rgba(255,255,255,0.35)';cx.font='8px Rajdhani,sans-serif';cx.textAlign='center';cx.fillText(c===P1COL?P1NAME.substring(0,4):c===P2COL?P2NAME.substring(0,4):c===2||c===4?'COVER':'',px,H-2);cx.textAlign='left';
  }
}
function draw(){
  cx.clearRect(0,0,W,H);drawWorld();
  rocks.forEach(r=>drawRock(r));
  // Cover glow behind players in cover
  if(P1COVER){let cg=cx.createRadialGradient(p1x,GY,0,p1x,GY,55);cg.addColorStop(0,'rgba(0,230,118,0.22)');cg.addColorStop(1,'rgba(0,0,0,0)');cx.fillStyle=cg;cx.fillRect(p1x-55,GY-55,110,110);}
  if(P2COVER){let cg=cx.createRadialGradient(p2x,GY,0,p2x,GY,55);cg.addColorStop(0,'rgba(0,230,118,0.22)');cg.addColorStop(1,'rgba(0,0,0,0)');cx.fillStyle=cg;cx.fillRect(p2x-55,GY-55,110,110);}
  // Depth sort
  let objs=[
    ...trees.map(t=>({k:'t',y:t.y,d:t})),
    {k:'p1',y:GY},{k:'p2',y:GY+1}
  ];
  objs.sort((a,b)=>a.y-b.y);
  objs.forEach(o=>{
    if(o.k==='t')drawTree(o.d);
    else if(o.k==='p1'){let wk=P1HP>0?Math.sin(frame*.18)*7:0;drawSoldier(p1x,GY,1,'green',wk);}
    else{let wk=P2HP>0?Math.sin(frame*.18+1.5)*7:0;drawSoldier(p2x,GY,-1,'red',wk);}
  });
  // Cover tree labels
  cx.fillStyle='rgba(0,230,118,0.8)';cx.font='bold 11px Rajdhani,sans-serif';cx.textAlign='center';
  cx.fillText('🌲 COVER',colX(2),H*0.36);cx.fillText('🌲 COVER',colX(4),H*0.36);cx.textAlign='left';
  // Storm column overlays
  if(STORM_MIN>0||STORM_MAX<6){
    let colW=(W-140)/(TOTAL_COLS-1);
    for(let c=0;c<TOTAL_COLS;c++){
      if(c<STORM_MIN||c>STORM_MAX){
        let cx2=colX(c);let pulse=0.18+0.06*Math.sin(frame*.07+c);
        cx.fillStyle=`rgba(140,0,220,${pulse})`;cx.fillRect(cx2-colW*.45,H*.32,colW*.9,H*.65);
        cx.strokeStyle=`rgba(200,0,255,${0.5+0.2*Math.sin(frame*.1+c)})`;cx.lineWidth=1.5;cx.strokeRect(cx2-colW*.45,H*.32,colW*.9,H*.65);
      }
    }
    cx.fillStyle='rgba(200,0,255,0.85)';cx.font='bold 10px Rajdhani,sans-serif';cx.textAlign='center';
    cx.fillText('⚡ STORM — safe zone cols '+STORM_MIN+'–'+STORM_MAX,W/2,H*0.30);cx.textAlign='left';
  }
  drawHUD();
  frame++;requestAnimationFrame(draw);
}
draw();
</script></body></html>"""

def build_online_canvas(r):
    n1=r.get("p1_name","P1"); n2=r.get("p2_name","P2") or "P2"
    s1=r.get("p1_skin",skin_names[0]); s2=r.get("p2_skin",skin_names[0])
    if s2 not in SKINS: s2=skin_names[0]
    h=_ONLINE_CANVAS.replace("__WORLD_JS__",_world_js())
    for t,v in [
        ("__ON_P1NAME__",n1.replace('"','')),("__ON_P2NAME__",n2.replace('"','')),
        ("__ON_P1HP__",str(r.get("p1_hp") or 0)),("__ON_P1MAXHP__",str(SKINS[s1]["health"])),
        ("__ON_P1SH__",str(r.get("p1_sh") or 0)),("__ON_P1MAXSH__",str(SKINS[s1]["shields"])),
        ("__ON_P2HP__",str(r.get("p2_hp") or 0)),("__ON_P2MAXHP__",str(SKINS[s2]["health"])),
        ("__ON_P2SH__",str(r.get("p2_sh") or 0)),("__ON_P2MAXSH__",str(SKINS[s2]["shields"])),
        ("__ON_P1COL__",str(r.get("p1_col",1))),("__ON_P2COL__",str(r.get("p2_col",5))),
        ("__ON_PHASE__",r.get("phase","waiting")),("__ON_WINNER__",r.get("winner","") or ""),
        ("__ON_P1COVER__","true" if r.get("p1_cover") else "false"),
        ("__ON_P2COVER__","true" if r.get("p2_cover") else "false"),
        ("__ON_SMIN__",str(r.get("storm_min",0))),
        ("__ON_SMAX__",str(r.get("storm_max",6))),
        ("__ON_TURN__",str(r.get("turn_num",0))),
    ]: h=h.replace(t,v)
    return h

# ── Online 2P combat helper ───────────────────────────────────────────────────
def do_fire_online(room_code, atk_role):
    r=get_room(room_code)
    if not r: return
    is_p1=(atk_role=="p1")
    atk_skin=r["p1_skin"] if is_p1 else r["p2_skin"]
    def_skin=r["p2_skin"] if is_p1 else r["p1_skin"]
    atk_n=r["p1_name"] if is_p1 else r["p2_name"]
    def_n=r["p2_name"] if is_p1 else r["p1_name"]
    wpn_idx=r["p1_wpn"] if is_p1 else r["p2_wpn"]
    wpn_key=(r["p1_w1"] if wpn_idx==0 else r["p1_w2"]) if is_p1 else (r["p2_w1"] if wpn_idx==0 else r["p2_w2"])
    atk_col_key,def_col_key="p1_col","p2_col" if is_p1 else ("p2_col","p1_col")
    def_hp_key,def_sh_key=("p2_hp","p2_sh") if is_p1 else ("p1_hp","p1_sh")
    atk_hp_key=("p1_hp") if is_p1 else ("p2_hp")
    def_cov=r["p2_cover"] if is_p1 else r["p1_cover"]
    def_cov_key="p2_cover" if is_p1 else "p1_cover"
    w=WEAPONS[wpn_key]; atk=SKINS[atk_skin]; log=list(r["log"])
    acc=min(.98,w["accuracy"]+(atk.get("accuracy_bonus",0) if atk_skin=="Renegade Raider" else 0))
    if random.random()>=acc:
        log.insert(0,("miss",f"💨 <b>{atk_n}</b> {wpn_key} — MISSED!"))
        patch_room(room_code,log=log,phase="p2_move" if is_p1 else "p1_move"); return
    def_skin_d=SKINS[def_skin]
    if def_skin=="Jonesy" and random.random()<def_skin_d.get("dodge_chance",0):
        log.insert(0,("ability",f"🍀 <b>{def_n}</b> LUCKY BREAK! Dodged!"))
        patch_room(room_code,log=log,phase="p2_move" if is_p1 else "p1_move"); return
    atk_col=r[atk_col_key]; def_col=r[def_col_key]
    dist=abs(atk_col-def_col)
    if is_p1: atk_col_key,def_col_key="p1_col","p2_col"
    else:      atk_col_key,def_col_key="p2_col","p1_col"
    damage=int(w["damage"]*get_rng(wpn_key,dist)); label="Hit"; etype="hit"
    if atk_skin=="Midas" and random.random()<atk.get("gold_chance",0):
        damage=int(damage*2); label="👑 GOLDEN TOUCH 2×"; etype="crit"
    elif random.random()<w["crit_chance"]:
        damage=int(damage*1.75); label="💥 CRITICAL"; etype="crit"
    if def_cov:
        damage=int(damage*.5); label+=" | 🌲−50%"
    ph=r[def_hp_key]; ps=r[def_sh_key]
    nh,ns=apply_damage(ph,ps,damage)
    updates={def_hp_key:nh,def_sh_key:ns,def_cov_key:False}
    log.insert(0,(etype,f"{'💥' if etype=='crit' else '🎯'} <b>{atk_n}</b>→<b>{def_n}</b> [{wpn_key}·d:{dist}]: <b>{label} {damage}dmg</b> ❤️{ph}→{nh}"))
    if atk_skin=="Cuddle Team Leader":
        heal=atk.get("heal_amount",0); old=r[atk_hp_key]
        new_ahp=min(SKINS[atk_skin]["health"],old+heal)
        updates[atk_hp_key]=new_ahp
        if new_ahp>old: log.insert(0,("ability",f"🐻 <b>{atk_n}</b> BEAR HUG +{heal} HP!"))
    if nh<=0:
        log.insert(0,("win",f"🏆 <b>{atk_n}</b> WINS! <b>{def_n}</b> ELIMINATED!"))
        updates["phase"]="done"; updates["winner"]=atk_n; updates["winner_skin"]=atk_skin
    else:
        next_phase="p2_move" if is_p1 else "p1_move"
        # Storm: advance turn and apply storm damage to both players on P2→P1 transition
        turn_num=r.get("turn_num",0)
        smin=r.get("storm_min",0); smax=r.get("storm_max",6)
        if not is_p1:  # P2 just attacked → full round done
            turn_num+=1
            if turn_num==6:  smin,smax=1,5; log.insert(0,("ability","⚡ STORM CLOSES! Columns 0 & 6 are now in the storm!"))
            elif turn_num==10: smin,smax=2,4; log.insert(0,("ability","⚡ STORM CLOSES! Columns 0,1,5,6 are now in the storm!"))
            elif turn_num==14: smin,smax=3,3; log.insert(0,("ability","⚡ STORM CLOSES! Only column 3 is safe!"))
            # Storm damage
            def apply_storm(hp, sh, col, name):
                if col<smin or col>smax:
                    dmg=20 if turn_num<10 else 35
                    nh2,ns2=apply_damage(hp,sh,dmg)
                    log.insert(0,("miss",f"⚡ <b>{name}</b> takes {dmg} STORM DAMAGE! ({col} outside safe {smin}-{smax})"))
                    return nh2,ns2
                return hp,sh
            p1h,p1s=apply_storm(r["p1_hp"],r["p1_sh"],r["p1_col"],r["p1_name"])
            p2h,p2s=apply_storm(nh if not is_p1 else r["p2_hp"],ns if not is_p1 else r["p2_sh"],r["p2_col"],r["p2_name"])
            if is_p1: p2h,p2s=nh,ns
            else: p2h=nh; p2s=ns
            # Check if storm killed anyone
            if p1h<=0 and r["phase"]!="done":
                log.insert(0,("win",f"🏆 <b>{r['p2_name']}</b> WINS by storm! <b>{r['p1_name']}</b> eliminated!"))
                updates["phase"]="done"; updates["winner"]=r["p2_name"]; updates["winner_skin"]=r["p2_skin"]
            elif p2h<=0 and r["phase"]!="done":
                log.insert(0,("win",f"🏆 <b>{r['p1_name']}</b> WINS by storm! <b>{r['p2_name']}</b> eliminated!"))
                updates["phase"]="done"; updates["winner"]=r["p1_name"]; updates["winner_skin"]=r["p1_skin"]
            else:
                updates["phase"]=next_phase
            updates.update({"p1_hp":p1h,"p1_sh":p1s,"p2_hp":p2h,"p2_sh":p2s,"turn_num":turn_num,"storm_min":smin,"storm_max":smax})
        else:
            updates["phase"]=next_phase
    updates["log"]=log
    patch_room(room_code,**updates)

def do_build_online(room_code, role):
    r=get_room(room_code)
    if not r: return
    is_p1=(role=="p1"); name=r["p1_name"] if is_p1 else r["p2_name"]
    cov_key="p1_built" if is_p1 else "p2_built"; cov_actual="p1_cover" if is_p1 else "p2_cover"
    log=list(r["log"])
    log.insert(0,("ability",f"🏗️ <b>{name}</b> builds COVER! (-50% damage next hit)"))
    next_phase="p2_move" if is_p1 else "p1_move"
    patch_room(room_code,**{cov_key:True,cov_actual:True,"phase":next_phase,"log":log})

def do_medkit_online(room_code, role):
    r=get_room(room_code)
    if not r: return
    is_p1=(role=="p1"); mk_key="p1_medkit" if is_p1 else "p2_medkit"
    hp_key="p1_hp" if is_p1 else "p2_hp"; sk_key="p1_skin" if is_p1 else "p2_skin"
    name=r["p1_name"] if is_p1 else r["p2_name"]
    old_hp=r[hp_key]; max_hp=SKINS[r[sk_key]]["health"]
    new_hp=min(max_hp, old_hp+70)
    log=list(r["log"])
    log.insert(0,("ability",f"💊 <b>{name}</b> uses MEDKIT! ❤️{old_hp}→{new_hp} (+{new_hp-old_hp} HP)"))
    next_phase="p2_move" if is_p1 else "p1_move"
    patch_room(room_code,**{mk_key:False,hp_key:new_hp,"phase":next_phase,"log":log})

# ── State init ────────────────────────────────────────────────────────────────
def init_state():
    defs={"game_mode":None,"sp_skin":None,"sp_w1":None,"sp_w2":None,"sp_name":"Ayaan",
          "lc_n1":"Ayaan","lc_n2":"Omer","lc_s1":skin_names[0],"lc_s2":skin_names[1],
          "lc_w1a":weapon_names[0],"lc_w1b":weapon_names[1],"lc_w2a":weapon_names[2],"lc_w2b":weapon_names[3],
          "room_code":None,"room_role":None}
    for k,v in defs.items():
        if k not in st.session_state: st.session_state[k]=v

def full_reset():
    for k in list(st.session_state.keys()): del st.session_state[k]

# ══════════════════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
init_state()
st.markdown("""<div style="text-align:center;padding:6px 0 2px;">
<div style="font-family:'Bangers',sans-serif;font-size:40px;letter-spacing:7px;color:#fff;
text-shadow:-3px -3px 0 #000,3px -3px 0 #000,-3px 3px 0 #000,3px 3px 0 #000,
0 0 26px rgba(255,209,0,.9);">💥 FORTNITE BATTLE SIMULATOR</div></div>""", unsafe_allow_html=True)
st.markdown("---")

LOG_C={"hit":"#00e676","crit":"#FFD100","miss":"#6688aa","ability":"#ff4da6","win":"#FF5722","lose":"#ff1744"}

# ════════════════════════════════════
# MAIN MENU
# ════════════════════════════════════
if st.session_state.game_mode is None:
    mc1,mc2,mc3=st.columns(3)
    for col,icon,title,desc,mode in [
        (mc1,"🏰","DEFEND THE KINGDOM","Solo vs AI zombies & soldiers. 5 hard waves!","lobby_sp"),
        (mc2,"🖥️","2-PLAYER SAME SCREEN","Both players on ONE computer. Face off!","lobby_2p_local"),
        (mc3,"🌐","2-PLAYER ONLINE","Two different computers. Share a room code!","lobby_2p_online"),
    ]:
        with col:
            st.markdown(f"""<div style="background:rgba(5,10,40,.85);border:2px solid rgba(255,200,0,.3);border-radius:12px;padding:16px;text-align:center;min-height:130px;">
<div style="font-size:40px;">{icon}</div>
<div style="font-family:'Bangers',sans-serif;font-size:20px;letter-spacing:3px;color:#FFD100;">{title}</div>
<div style="font-size:11px;color:#aabbdd;margin-top:4px;">{desc}</div></div>""",unsafe_allow_html=True)
            if st.button(f"PLAY",key=f"m_{mode}",use_container_width=True,type="primary"):
                st.session_state.game_mode=mode; st.rerun()
    with st.expander("📖 Controls",expanded=False):
        st.markdown("""
**Solo / Defend the Kingdom:** WASD/Arrows=Walk · F/Space/Click=Shoot · 1/2=Switch gun · R=Restart

**2-Player Same Screen:**
- 🟦 P1: **WASD**=Move · **F**=Shoot · **Z/X**=Switch gun
- 🟥 P2: **Arrow keys**=Move · **L**=Shoot · **,/.** =Switch gun
- **R**=Rematch after game over

**2-Player Online:** Turn-based. Create a room → share 4-digit code with friend → take turns attacking!
""")

# ── SP Lobby ──────────────────────────────────────────────────────────────────
elif st.session_state.game_mode=="lobby_sp":
    st.markdown("### 🏰 DEFEND THE KINGDOM — SOLO (HARD)")
    c1,c2=st.columns([1,2])
    with c1:
        spn=st.text_input("Your Name",value="Ayaan",key="spni",max_chars=14)
        sps=st.selectbox("Skin",skin_names,key="sps")
        spw1=st.selectbox("🔫 Gun 1",weapon_names,index=0,key="spw1")
        spw2=st.selectbox("💣 Gun 2",weapon_names,index=1,key="spw2")
    with c2:
        st.markdown("""**HARD MODE — 7 waves. Enemies get faster every wave!**

| Wave | 🧟 Zombies | 💂 Soldiers | 👾 Bosses |
|------|-----------|------------|---------|
| 1 | 5 | — | — |
| 2 | 8 | 3 | — |
| 3 | 7 | 5 | 2 |
| 4 | 11 | 7 | 3 |
| 5 | 10 | 9 | 4 |
| 6 | 13 | 10 | 6 |
| 7 | 16 | 12 | 8 |

👾 Boss: **340 HP · 100 dmg** · 💂 Soldier: **150 HP · 58 dmg** · Enemies gain +8% speed per wave.
🌲 Trees and 🪨 rocks give **50% cover**. Survive all 7 waves to save the kingdom!
+35 shields restored between waves.
""")
    bc1,bc2=st.columns(2)
    with bc1:
        if st.button("◀ BACK",use_container_width=True,key="bsp"): st.session_state.game_mode=None; st.rerun()
    with bc2:
        if st.button("🏰 LAUNCH!",use_container_width=True,type="primary",key="stsp"):
            st.session_state.sp_skin=sps; st.session_state.sp_w1=spw1
            st.session_state.sp_w2=spw2; st.session_state.sp_name=spn
            st.session_state.game_mode="sp"; st.rerun()

elif st.session_state.game_mode=="sp":
    if st.button("🏠 MENU",key="spmenu"): full_reset(); st.rerun()
    components.html(build_sp_canvas(st.session_state.sp_name,st.session_state.sp_skin,st.session_state.sp_w1,st.session_state.sp_w2),height=710)

# ── 2P Same-screen Lobby ──────────────────────────────────────────────────────
elif st.session_state.game_mode=="lobby_2p_local":
    st.markdown("### 🖥️ 2-PLAYER SAME SCREEN SETUP")
    c1,c2=st.columns(2)
    with c1:
        st.markdown("#### 🟦 Player 1 (WASD + F to shoot)")
        n1=st.text_input("Name",value="Ayaan",key="lc_n1_in",max_chars=14)
        s1=st.selectbox("Skin",skin_names,key="lcs1")
        w1a=st.selectbox("🔫 Gun 1 [Z]",weapon_names,index=0,key="lcw1a")
        w1b=st.selectbox("💣 Gun 2 [X]",weapon_names,index=1,key="lcw1b")
    with c2:
        st.markdown("#### 🟥 Player 2 (Arrows + L to shoot)")
        n2=st.text_input("Name",value="Omer",key="lc_n2_in",max_chars=14)
        s2=st.selectbox("Skin",skin_names,index=1,key="lcs2")
        w2a=st.selectbox("🔫 Gun 1 [,]",weapon_names,index=2,key="lcw2a")
        w2b=st.selectbox("💣 Gun 2 [.]",weapon_names,index=3,key="lcw2b")
    bc1,bc2=st.columns(2)
    with bc1:
        if st.button("◀ BACK",use_container_width=True,key="b2pl"): st.session_state.game_mode=None; st.rerun()
    with bc2:
        if st.button("⚔️ FIGHT!",use_container_width=True,type="primary",key="st2pl"):
            for k,v in [("lc_n1",n1),("lc_n2",n2),("lc_s1",s1),("lc_s2",s2),
                        ("lc_w1a",w1a),("lc_w1b",w1b),("lc_w2a",w2a),("lc_w2b",w2b)]:
                st.session_state[k]=v
            st.session_state.game_mode="2p_local"; st.rerun()

elif st.session_state.game_mode=="2p_local":
    if st.button("🏠 MENU",key="2plm"): full_reset(); st.rerun()
    ss=st.session_state
    components.html(build_2p_canvas(ss.lc_n1,ss.lc_s1,ss.lc_w1a,ss.lc_w1b,ss.lc_n2,ss.lc_s2,ss.lc_w2a,ss.lc_w2b),height=710)

# ── 2P Online Lobby ───────────────────────────────────────────────────────────
elif st.session_state.game_mode=="lobby_2p_online":
    st.markdown("### 🌐 2-PLAYER ONLINE — SETUP")
    st.info("💡 Both players open the same Streamlit URL. One creates a room and shares the 4-digit code. The other joins with that code.")
    c1,c2=st.columns(2)
    with c1:
        on_n=st.text_input("Your Name",value="Ayaan",key="on_name_in",max_chars=14)
        on_s=st.selectbox("Skin",skin_names,key="on_skin")
        on_w1=st.selectbox("🔫 Gun 1",weapon_names,index=0,key="on_w1")
        on_w2=st.selectbox("💣 Gun 2",weapon_names,index=1,key="on_w2")
    with c2:
        st.markdown("#### I want to...")
        if st.button("🏠 CREATE ROOM (I go first)",use_container_width=True,type="primary",key="create_room"):
            code=make_room(on_n,on_s,on_w1,on_w2)
            st.session_state["room_code"]=code
            st.session_state["room_role"]="p1"
            st.session_state["game_mode"]="online_wait"
            st.rerun()
        st.markdown("---")
        jc=st.text_input("Room code from friend",max_chars=4,key="join_code_in",placeholder="e.g. 4827")
        if st.button("🚪 JOIN ROOM",use_container_width=True,key="join_room"):
            jc=jc.strip()
            result=join_room(jc,on_n,on_s,on_w1,on_w2)
            if result=="ok":
                st.session_state["room_code"]=jc
                st.session_state["room_role"]="p2"
                st.session_state["game_mode"]="online_game"
                st.rerun()
            elif result=="notfound":
                st.error("❌ Room not found. Check the 4-digit code — your friend must create the room first.")
            else:
                st.error("❌ Room already full.")
    if st.button("◀ BACK",key="bon"): st.session_state.game_mode=None; st.rerun()

elif st.session_state.game_mode=="online_wait":
    code=st.session_state.room_code
    st.markdown(f"""<div style="text-align:center;padding:20px;background:rgba(5,10,40,.88);
border:2px solid #FFD100;border-radius:12px;margin:10px 0;">
<div style="font-family:'Bangers',sans-serif;font-size:28px;color:#FFD100;letter-spacing:5px;">
🏠 YOUR ROOM CODE</div>
<div style="font-family:'Bangers',sans-serif;font-size:72px;color:#fff;letter-spacing:12px;
text-shadow:0 0 30px #FFD100;">{code}</div>
<div style="font-family:'Rajdhani',sans-serif;font-size:14px;color:#aabbdd;">
Share this code with your friend. They open the same URL and click "Join Room".</div></div>""",
        unsafe_allow_html=True)
    r=get_room(code)
    if r and r.get("phase")!="waiting":
        st.success(f"✅ {r.get('p2_name','Friend')} joined! Starting game...")
        st.session_state.game_mode="online_game"; st.rerun()
    else:
        st.info("⏳ Waiting for your friend to join... (auto-checks every 3 seconds)")
        if st.button("🏠 CANCEL",key="cancel_wait"): full_reset(); st.rerun()
        time.sleep(1.5)
        st.rerun()

elif st.session_state.game_mode=="online_game":
    code=st.session_state.room_code
    role=st.session_state.room_role
    r=get_room(code)
    if not r:
        st.error("Room expired. Please start a new game.");
        if st.button("🏠 MENU"): full_reset(); st.rerun()
    else:
        n1=r["p1_name"]; n2=r["p2_name"] or "Waiting..."
        s1=r["p1_skin"]; s2=r["p2_skin"] or skin_names[0]
        phase=r["phase"]; my_turn=(phase.startswith("p1") and role=="p1") or (phase.startswith("p2") and role=="p2")
        my_name=r["p1_name"] if role=="p1" else r["p2_name"]
        opp_name=r["p2_name"] if role=="p1" else r["p1_name"]
        my_color="#4da6ff" if role=="p1" else "#ff5252"
        # Canvas arena view
        components.html(build_online_canvas(r), height=585)
        c1,c2=st.columns(2)
        with c1: hp_row(n1,s1,r["p1_hp"] or 0,r["p1_sh"] or 0,SKINS[s1]["health"],SKINS[s1]["shields"],SKINS[s1]["color"])
        with c2: hp_row(n2,s2,r["p2_hp"] or 0,r["p2_sh"] or 0,SKINS[s2]["health"],SKINS[s2]["shields"],SKINS[s2]["color"])
        st.markdown("---")
        if phase!="done":
            if not my_turn:
                st.info(f"⏳ Waiting for **{opp_name}** to {phase.split('_')[1]}... (auto-checks every 3 seconds)")
                time.sleep(3)
                st.rerun()
            else:
                st.success(f"✅ YOUR TURN, **{my_name}**! ({phase.split('_')[1].upper()})")
                COVER_POS_O={2,4}
                if phase.endswith("_move"):
                    cc="p1_col" if role=="p1" else "p2_col"; oc="p2_col" if role=="p1" else "p1_col"
                    cov="p1_cover" if role=="p1" else "p2_cover"
                    cur_c=r[cc]; opp_c=r[oc]; nxt="p1_attack" if role=="p1" else "p2_attack"
                    mc1,mc2,mc3=st.columns(3)
                    with mc1:
                        if st.button("◀ MOVE LEFT",use_container_width=True,disabled=(cur_c<=0 or cur_c-1==opp_c),key="onml"):
                            patch_room(code,**{cc:cur_c-1,cov:((cur_c-1) in COVER_POS_O),nxt.split("_")[0]+"_cover":((cur_c-1) in COVER_POS_O),"phase":nxt}); st.rerun()
                    with mc2:
                        if st.button("⏸️ STAY",use_container_width=True,key="onms"):
                            patch_room(code,**{"phase":nxt}); st.rerun()
                    with mc3:
                        if st.button("MOVE RIGHT ▶",use_container_width=True,disabled=(cur_c>=6 or cur_c+1==opp_c),key="onmr"):
                            patch_room(code,**{cc:cur_c+1,cov:((cur_c+1) in COVER_POS_O),"phase":nxt}); st.rerun()
                else:
                    my_w1=r["p1_w1"] if role=="p1" else r["p2_w1"]
                    my_w2=r["p1_w2"] if role=="p1" else r["p2_w2"]
                    my_wpn_sel=r["p1_wpn"] if role=="p1" else r["p2_wpn"]
                    wpn_key="p1_wpn" if role=="p1" else "p2_wpn"
                    chosen=my_w1 if my_wpn_sel==0 else my_w2
                    wc1,wc2=st.columns(2)
                    def _wcard(wn,i,sel):
                        w=WEAPONS[wn]; is_sel=(sel==i)
                        bg="linear-gradient(135deg,#FFD100,#FF9500)" if is_sel else "rgba(5,10,40,.88)"
                        bdr="#FFD100" if is_sel else "rgba(255,255,255,.15)"
                        tc="#050a1a" if is_sel else "#fff"
                        return f'<div style="background:{bg};border:2px solid {bdr};border-radius:10px;padding:10px;text-align:center;"><div style="font-size:28px;">{w["emoji"]}</div><div style="font-family:Bangers,sans-serif;font-size:12px;color:{tc};">{wn.upper()}</div><div style="font-size:9px;color:{tc};opacity:.8;">DMG {w["damage"]} · ACC {int(w["accuracy"]*100)}%</div></div>'
                    with wc1:
                        st.markdown(_wcard(my_w1,0,my_wpn_sel),unsafe_allow_html=True)
                        if st.button("GUN 1 [WPN1]",use_container_width=True,type="primary" if my_wpn_sel==0 else "secondary",key="ongw1"):
                            patch_room(code,**{wpn_key:0}); st.rerun()
                    with wc2:
                        st.markdown(_wcard(my_w2,1,my_wpn_sel),unsafe_allow_html=True)
                        if st.button("GUN 2 [WPN2]",use_container_width=True,type="primary" if my_wpn_sel==1 else "secondary",key="ongw2"):
                            patch_room(code,**{wpn_key:1}); st.rerun()
                    if st.button(f"🔥 FIRE {WEAPONS[chosen]['emoji']} {chosen.upper()}! [FIRE]",use_container_width=True,type="primary",key="onfire"):
                        do_fire_online(code,role); st.rerun()
                    # Special actions row
                    sa1,sa2=st.columns(2)
                    my_mk_key="p1_medkit" if role=="p1" else "p2_medkit"
                    my_blt_key="p1_built" if role=="p1" else "p2_built"
                    with sa1:
                        has_mk=r.get(my_mk_key,True)
                        if st.button(f"💊 USE MEDKIT (+70 HP)" if has_mk else "💊 MEDKIT USED",disabled=not has_mk,use_container_width=True,key="onmk"):
                            do_medkit_online(code,role); st.rerun()
                    with sa2:
                        if st.button("🏗️ BUILD COVER (skip attack)",use_container_width=True,key="onbuild"):
                            do_build_online(code,role); st.rerun()
                    # Storm info
                    smin=r.get("storm_min",0); smax=r.get("storm_max",6); tnum=r.get("turn_num",0)
                    if smin>0 or smax<6:
                        st.warning(f"⚡ STORM ACTIVE — safe columns: {smin}–{smax} | Columns outside deal 20-35 damage per round!")
                    else:
                        st.info(f"⚡ Storm closes at turn 6 · turn {tnum}/6 · Stay in cols {smin}–{smax}")
        st.markdown("---")
        if st.button("🔄 REFRESH",key="onref"): st.rerun()
        if st.button("🏠 QUIT",key="onquit"): full_reset(); st.rerun()
        st.markdown('<div style="font-family:\'Bangers\',sans-serif;font-size:15px;color:#FFD100;letter-spacing:4px;margin-bottom:5px;margin-top:6px;">📜 BATTLE LOG</div>',unsafe_allow_html=True)
        for et,txt in (r.get("log",[]) or []):
            st.markdown(f'<div class="log-row" style="border-left-color:{LOG_C.get(et,"#334")};">{txt}</div>',unsafe_allow_html=True)
