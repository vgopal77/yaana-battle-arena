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
(function(){var b=document.createElement('button');b.textContent='⛶';b.title='Fullscreen';b.style.cssText='position:fixed;top:8px;right:8px;z-index:9999;background:rgba(0,0,20,.8);color:#fff;border:1.5px solid rgba(255,255,255,.3);border-radius:7px;padding:5px 10px;font-size:16px;cursor:pointer;';var cv=document.getElementById('g');b.onclick=function(){if(!document.fullscreenElement){document.documentElement.requestFullscreen().catch(function(){});}else{document.exitFullscreen();}};document.addEventListener('fullscreenchange',function(){if(document.fullscreenElement){var cw=cv.width,ch=cv.height,s=Math.min(window.innerWidth/cw,window.innerHeight/ch);cv.style.position='fixed';cv.style.left=Math.round((window.innerWidth-cw*s)/2)+'px';cv.style.top=Math.round((window.innerHeight-ch*s)/2)+'px';cv.style.transform='scale('+s+')';cv.style.transformOrigin='0 0';document.body.style.background='#000';b.textContent='✕';}else{cv.style.position='';cv.style.left='';cv.style.top='';cv.style.transform='';cv.style.transformOrigin='';b.textContent='⛶';}});document.body.appendChild(b);})();
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
(function(){var b=document.createElement('button');b.textContent='⛶';b.title='Fullscreen';b.style.cssText='position:fixed;top:8px;right:8px;z-index:9999;background:rgba(0,0,20,.8);color:#fff;border:1.5px solid rgba(255,255,255,.3);border-radius:7px;padding:5px 10px;font-size:16px;cursor:pointer;';var cv=document.getElementById('g');b.onclick=function(){if(!document.fullscreenElement){document.documentElement.requestFullscreen().catch(function(){});}else{document.exitFullscreen();}};document.addEventListener('fullscreenchange',function(){if(document.fullscreenElement){var cw=cv.width,ch=cv.height,s=Math.min(window.innerWidth/cw,window.innerHeight/ch);cv.style.position='fixed';cv.style.left=Math.round((window.innerWidth-cw*s)/2)+'px';cv.style.top=Math.round((window.innerHeight-ch*s)/2)+'px';cv.style.transform='scale('+s+')';cv.style.transformOrigin='0 0';document.body.style.background='#000';b.textContent='✕';}else{cv.style.position='';cv.style.left='';cv.style.top='';cv.style.transform='';cv.style.transformOrigin='';b.textContent='⛶';}});document.body.appendChild(b);})();
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
(function(){var b=document.createElement('button');b.textContent='⛶';b.title='Fullscreen';b.style.cssText='position:fixed;top:8px;right:8px;z-index:9999;background:rgba(0,0,20,.8);color:#fff;border:1.5px solid rgba(255,255,255,.3);border-radius:7px;padding:5px 10px;font-size:16px;cursor:pointer;';var cv=document.getElementById('g');b.onclick=function(){if(!document.fullscreenElement){document.documentElement.requestFullscreen().catch(function(){});}else{document.exitFullscreen();}};document.addEventListener('fullscreenchange',function(){if(document.fullscreenElement){var cw=cv.width,ch=cv.height,s=Math.min(window.innerWidth/cw,window.innerHeight/ch);cv.style.position='fixed';cv.style.left=Math.round((window.innerWidth-cw*s)/2)+'px';cv.style.top=Math.round((window.innerHeight-ch*s)/2)+'px';cv.style.transform='scale('+s+')';cv.style.transformOrigin='0 0';document.body.style.background='#000';b.textContent='✕';}else{cv.style.position='';cv.style.left='';cv.style.top='';cv.style.transform='';cv.style.transformOrigin='';b.textContent='⛶';}});document.body.appendChild(b);})();
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

# ══════════════════════════════════════════════════════════════════════════════
# EXTRA GAMES
# ══════════════════════════════════════════════════════════════════════════════

# ── Game 4: Sniper Showdown (2P same screen timing game) ─────────────────────
_SNIPER_HTML = r"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>*{margin:0;padding:0;box-sizing:border-box;}body{background:#010810;overflow:hidden;}canvas{display:block;cursor:crosshair;}</style>
</head><body><canvas id="g"></canvas><script>
const cvs=document.getElementById('g');const cx=cvs.getContext('2d');
const W=cvs.width=Math.min(1100,window.innerWidth-4);const H=cvs.height=520;
const P1N="__SN_P1__",P2N="__SN_P2__";
let p1={hp:5,aim:0,spd:2.8,fired:false,lastDmg:0,col:'#4da6ff'};
let p2={hp:5,aim:0,spd:2.3,fired:false,lastDmg:0,col:'#ff5252'};
let frame=0,phase='countdown',cdTimer=120,roundTimer=0,winner=null;
let effects=[],impacts=[],muzzles=[];
let stars=Array.from({length:100},()=>({x:Math.random()*W,y:Math.random()*H*.55,r:Math.random()*1.6+.3,b:Math.random()}));
let keys={};
function getAcc(aim){return Math.max(0,1-Math.abs(aim));}
function fire(pl,opp,isP1){
  if(pl.fired||phase!=='aim')return;
  pl.fired=true;
  let acc=getAcc(pl.aim);
  let dmg=0,lbl='';
  if(acc>0.88){dmg=3;lbl='HEADSHOT!';}else if(acc>0.65){dmg=2;lbl='CLEAN HIT';}else if(acc>0.35){dmg=1;lbl='GLANCE';}else{lbl='MISS!';}
  pl.lastDmg=dmg;opp.hp=Math.max(0,opp.hp-dmg);
  let ex=isP1?W*.73:W*.27,ey=H*.47;
  effects.push({x:isP1?W*.25:W*.75,y:H*.5,txt:lbl,c:dmg>1?'#FFD100':dmg===1?'#00e676':'#ff5252',l:90,big:dmg>1});
  if(dmg>0){impacts.push({x:ex,y:ey+(Math.random()-.5)*40,l:40});}
  muzzles.push({x:isP1?W*.35:W*.65,y:H*.47,l:12,c:pl.col});
  if(p1.fired&&p2.fired)roundTimer=0;
}
function update(){
  if(winner)return;frame++;
  if(phase==='countdown'){cdTimer--;if(cdTimer<=0){phase='aim';}}
  else if(phase==='aim'){
    let t=frame*.06;
    p1.aim=Math.sin(t*p1.spd)*.98;p2.aim=Math.sin(t*p2.spd+1.8)*.98;
    if(keys['Space']&&!p1.fired)fire(p1,p2,true);
    if((keys['Enter']||keys['NumpadEnter'])&&!p2.fired)fire(p2,p1,false);
    if(p1.fired&&p2.fired){phase='result';roundTimer=0;}
    else if(roundTimer++>240){p1.fired=true;p2.fired=true;phase='result';roundTimer=0;}
  }else if(phase==='result'){
    roundTimer++;if(roundTimer>95){
      if(p1.hp<=0||p2.hp<=0){winner=p1.hp>0?P1N:p2.hp>0?P2N:'DRAW';}
      else{phase='aim';p1.fired=false;p2.fired=false;p1.spd+=0.12;p2.spd+=0.1;}
    }
  }
  effects=effects.filter(e=>(e.l--,e.l>0));
  impacts=impacts.filter(i=>(i.l--,i.l>0));
  muzzles=muzzles.filter(m=>(m.l--,m.l>0));
}
function drawScope(px,aimed,col,name,hp,label){
  let R=105,aimX=px+aimed*R*.9,aimY=H*.47;
  cx.save();
  // Background circle
  let bg=cx.createRadialGradient(px,H*.47,0,px,H*.47,R);bg.addColorStop(0,'rgba(0,20,10,0.9)');bg.addColorStop(1,'rgba(0,10,5,0.5)');
  cx.fillStyle=bg;cx.beginPath();cx.arc(px,H*.47,R,0,Math.PI*2);cx.fill();
  cx.strokeStyle='rgba(255,255,255,0.1)';cx.lineWidth=1;
  for(let i=1;i<=4;i++){cx.beginPath();cx.arc(px,H*.47,R*.25*i,0,Math.PI*2);cx.stroke();}
  // Scope ring
  cx.strokeStyle=col;cx.lineWidth=3;cx.shadowColor=col;cx.shadowBlur=12;cx.beginPath();cx.arc(px,H*.47,R,0,Math.PI*2);cx.stroke();cx.shadowBlur=0;
  // Cross lines
  cx.strokeStyle='rgba(255,255,255,0.25)';cx.lineWidth=1;
  cx.beginPath();cx.moveTo(px-R,H*.47);cx.lineTo(px+R,H*.47);cx.stroke();
  cx.beginPath();cx.moveTo(px,H*.47-R);cx.lineTo(px,H*.47+R);cx.stroke();
  // Crosshair
  cx.strokeStyle=col;cx.lineWidth=2.5;cx.shadowColor=col;cx.shadowBlur=14;
  cx.beginPath();cx.moveTo(aimX-20,aimY);cx.lineTo(aimX+20,aimY);cx.stroke();
  cx.beginPath();cx.moveTo(aimX,aimY-20);cx.lineTo(aimX,aimY+20);cx.stroke();
  cx.shadowBlur=0;
  // Accuracy bar
  let acc=getAcc(aimed),bw=210,bx=px-105,by=H*.47+R+14;
  cx.fillStyle='rgba(0,0,0,0.7)';cx.fillRect(bx,by,bw,16);
  let ac=acc>0.88?'#FFD100':acc>0.65?'#00e676':acc>0.35?'#ff9100':'#ff5252';
  cx.fillStyle=ac;cx.shadowColor=ac;cx.shadowBlur=6;cx.fillRect(bx,by,bw*acc,16);cx.shadowBlur=0;
  cx.strokeStyle='rgba(255,255,255,0.3)';cx.lineWidth=1;cx.strokeRect(bx,by,bw,16);
  cx.fillStyle='#fff';cx.font='bold 10px Rajdhani,sans-serif';cx.textAlign='center';
  let zone=acc>0.88?'💥 HEADSHOT':acc>0.65?'✅ CLEAN HIT':acc>0.35?'⚠️ GLANCE':'❌ MISS';
  cx.fillText(zone,px,by+12);
  // Name + HP dots
  cx.fillStyle=col;cx.font='bold 16px Bangers,sans-serif';cx.fillText(name,px,H*.47-R-16);
  cx.font='14px sans-serif';let hpStr='🔴'.repeat(hp)+'⚫'.repeat(Math.max(0,5-hp));cx.fillText(hpStr,px,H*.47-R-3);
  if(aimed!==null)cx.fillText(label,px,by+28);
  cx.restore();cx.textAlign='left';
}
function draw(){
  update();
  cx.clearRect(0,0,W,H);
  let sg=cx.createLinearGradient(0,0,0,H);sg.addColorStop(0,'#010810');sg.addColorStop(1,'#081420');
  cx.fillStyle=sg;cx.fillRect(0,0,W,H);
  stars.forEach(s=>{cx.globalAlpha=0.4+0.5*Math.abs(Math.sin(frame*.018+s.b*7));cx.fillStyle='#fff';cx.beginPath();cx.arc(s.x,s.y,s.r,0,Math.PI*2);cx.fill();});cx.globalAlpha=1;
  // Divider
  cx.strokeStyle='rgba(255,255,255,0.1)';cx.setLineDash([10,6]);cx.lineWidth=1;cx.beginPath();cx.moveTo(W/2,0);cx.lineTo(W/2,H);cx.stroke();cx.setLineDash([]);
  // Scopes
  drawScope(W*.25,p1.aim,p1.col,P1N,p1.hp,p1.fired?'✅ SHOT FIRED':'[SPACE] to fire');
  drawScope(W*.75,p2.aim,p2.col,P2N,p2.hp,p2.fired?'✅ SHOT FIRED':'[ENTER] to fire');
  // Muzzle flashes
  muzzles.forEach(m=>{cx.globalAlpha=m.l/12;cx.fillStyle=m.c;cx.shadowColor=m.c;cx.shadowBlur=20;cx.beginPath();cx.arc(m.x,m.y,14,0,Math.PI*2);cx.fill();cx.shadowBlur=0;cx.globalAlpha=1;});
  // Impact marks
  impacts.forEach(i=>{cx.globalAlpha=i.l/40;cx.strokeStyle='#FFD100';cx.lineWidth=3;cx.shadowColor='#FFD100';cx.shadowBlur=8;let s=10;cx.beginPath();cx.moveTo(i.x-s,i.y-s);cx.lineTo(i.x+s,i.y+s);cx.stroke();cx.beginPath();cx.moveTo(i.x+s,i.y-s);cx.lineTo(i.x-s,i.y+s);cx.stroke();cx.shadowBlur=0;cx.globalAlpha=1;});
  // Effects
  effects.forEach(e=>{let a=e.l/90;cx.globalAlpha=a;cx.fillStyle=e.c;cx.shadowColor=e.c;cx.shadowBlur=e.big?16:8;cx.font=`bold ${e.big?26:18}px Bangers,sans-serif`;cx.textAlign='center';cx.fillText(e.txt,e.x,H*.34);cx.shadowBlur=0;cx.globalAlpha=1;cx.textAlign='left';});
  // HUD bar
  cx.fillStyle='rgba(0,0,10,0.82)';cx.fillRect(0,0,W,42);
  cx.fillStyle='#FFD100';cx.font='bold 20px Bangers,sans-serif';cx.textAlign='center';
  if(phase==='countdown'){cx.fillStyle='#ff9100';cx.shadowColor='#ff9100';cx.shadowBlur=12;cx.fillText('GET READY... '+(Math.ceil(cdTimer/40)||1),W/2,26);cx.shadowBlur=0;}
  else if(phase==='aim'){cx.fillText('🎯 SNIPER SHOWDOWN — FIRE WHEN CROSSHAIR IS CENTERED!',W/2,26);}
  else{cx.fillText('⏱️ ROUND RESULT — NEXT ROUND INCOMING...',W/2,26);}
  cx.textAlign='left';
  // Winner screen
  if(winner){
    cx.fillStyle='rgba(0,0,0,0.84)';cx.fillRect(0,0,W,H);cx.textAlign='center';
    let wc=winner===P1N?'#4da6ff':winner===P2N?'#ff5252':'#FFD100';
    cx.fillStyle=wc;cx.shadowColor=wc;cx.shadowBlur=24;cx.font='bold 54px Bangers,sans-serif';
    cx.fillText('🏆 '+winner.toUpperCase()+' WINS!',W/2,H/2-14);cx.shadowBlur=0;
    cx.fillStyle='#aabbdd';cx.font='14px Rajdhani,sans-serif';cx.fillText('Reload page or press MENU to play again',W/2,H/2+22);cx.textAlign='left';
  }
  requestAnimationFrame(draw);
}
window.addEventListener('keydown',e=>{keys[e.code]=true;e.preventDefault();});
window.addEventListener('keyup',e=>{keys[e.code]=false;});
cvs.setAttribute('tabindex','0');cvs.focus();draw();
(function(){var b=document.createElement('button');b.textContent='⛶';b.title='Fullscreen';b.style.cssText='position:fixed;top:8px;right:8px;z-index:9999;background:rgba(0,0,20,.8);color:#fff;border:1.5px solid rgba(255,255,255,.3);border-radius:7px;padding:5px 10px;font-size:16px;cursor:pointer;';var cv=document.getElementById('g');b.onclick=function(){if(!document.fullscreenElement){document.documentElement.requestFullscreen().catch(function(){});}else{document.exitFullscreen();}};document.addEventListener('fullscreenchange',function(){if(document.fullscreenElement){var cw=cv.width,ch=cv.height,s=Math.min(window.innerWidth/cw,window.innerHeight/ch);cv.style.position='fixed';cv.style.left=Math.round((window.innerWidth-cw*s)/2)+'px';cv.style.top=Math.round((window.innerHeight-ch*s)/2)+'px';cv.style.transform='scale('+s+')';cv.style.transformOrigin='0 0';document.body.style.background='#000';b.textContent='✕';}else{cv.style.position='';cv.style.left='';cv.style.top='';cv.style.transform='';cv.style.transformOrigin='';b.textContent='⛶';}});document.body.appendChild(b);})();
</script></body></html>"""

# ── Game 5: Storm Sprint (endless side-scroll runner) ────────────────────────
_SPRINT_HTML = r"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>*{margin:0;padding:0;box-sizing:border-box;}body{background:#010810;overflow:hidden;}canvas{display:block;cursor:crosshair;}</style>
</head><body><canvas id="g"></canvas><script>
const cvs=document.getElementById('g');const cx=cvs.getContext('2d');
const W=cvs.width=Math.min(1100,window.innerWidth-4);const H=cvs.height=480;
const PNAME="__SP_NAME__";
const GY=H*.72; // ground y
const GRAV=0.72,JUMP=-15.5,DJUMP=-12;
let p={x:W*.18,y:GY,vy:0,hp:3,jumps:0,dead:false,djUsed:false};
let obstacles=[],loot=[],particles=[],stars=[];
let scrollSpd=4.8,stormX=-80,stormSpd=0.5,frame=0,score=0,gameOver=false,best=0;
let keys={};
let bgTrees=Array.from({length:14},(_,i)=>({x:i*(W/13),h:55+Math.random()*80,w:22+Math.random()*20,dark:Math.random()<.5}));
for(let i=0;i<120;i++)stars.push({x:Math.random()*W,y:Math.random()*GY*.7,r:Math.random()*1.6+.3,b:Math.random()});
let spawnT=0,lootT=0,logT=0;
let jumpBuffer=0; // coyote time
function jump(){if(p.jumps<2){if(p.jumps===0){p.vy=JUMP;}else{p.vy=DJUMP;}p.jumps++;}}
function spawnObs(){
  let r=Math.random();
  if(r<0.15&&score>300){obstacles.push({x:W+40,y:GY-2,w:90+Math.random()*50,h:10,type:'gap',gx:W+40,gw:90+Math.random()*50});}
  else if(r<0.45){let h=30+Math.random()*50;obstacles.push({x:W+30,y:GY-h,w:28+Math.random()*24,h,type:'rock'});}
  else{let h=55+Math.random()*55;obstacles.push({x:W+30,y:GY-h,w:18,h,type:'tree',r:Math.round(h*.45),dark:Math.random()<.5});}
}
function update(){
  if(gameOver)return;
  frame++;score++;
  scrollSpd=Math.min(11,4.8+score*0.0018);
  stormSpd=Math.min(6.0,0.5+score*0.0014);
  stormX+=stormSpd;
  // Player jump physics
  if((keys['Space']||keys['ArrowUp']||keys['KeyW'])){if(jumpBuffer<=0){jump();jumpBuffer=10;}}
  if(jumpBuffer>0)jumpBuffer--;
  p.vy=Math.min(18,p.vy+GRAV);p.y=Math.min(GY,p.y+p.vy);
  if(p.y>=GY){p.y=GY;p.vy=0;p.jumps=0;}
  // Scroll background trees
  bgTrees.forEach(t=>{t.x-=scrollSpd*.35;if(t.x+t.w<0)t.x=W+Math.random()*120;});
  // Spawn
  spawnT++;let rate=Math.max(32,80-score/220);
  if(spawnT>=rate){spawnT=0;spawnObs();}
  lootT++;if(lootT>=Math.max(60,180-score/100)){lootT=0;loot.push({x:W+20,y:GY-45-Math.random()*80,type:Math.random()<.5?'sh':'hp',collected:false,ph:Math.random()*6.28});}
  // Move obstacles
  obstacles.forEach(o=>{o.x-=scrollSpd;});
  loot.forEach(l=>{l.x-=scrollSpd;});
  // Collision with obstacles
  obstacles.forEach(o=>{
    let px=p.x,py=p.y;
    if(o.type==='gap'){
      if(px+10>o.x&&px-10<o.x+o.gw&&py>=GY-8){
        for(let i=0;i<8;i++)particles.push({x:px,y:py,vx:(Math.random()-.5)*6,vy:-Math.random()*5,r:4,c:'#ff1744',l:25,ml:25});
        p.dead=true;gameOver=true;
      }
    }else{
      if(px+14>o.x&&px-14<o.x+o.w&&py>o.y-5&&py<=o.y+o.h){
        p.hp--;for(let i=0;i<6;i++)particles.push({x:px,y:py-10,vx:(Math.random()-.5)*5,vy:-3-Math.random()*3,r:4,c:'#ff1744',l:22,ml:22});
        obstacles=obstacles.filter(oo=>oo!==o);
        if(p.hp<=0)gameOver=true;
      }
    }
  });
  // Loot collection
  loot.forEach(lt=>{if(!lt.collected&&Math.hypot(p.x-lt.x,p.y-lt.y)<22){lt.collected=true;p.hp=Math.min(5,lt.type==='hp'?p.hp+1:p.hp);for(let i=0;i<6;i++)particles.push({x:lt.x,y:lt.y,vx:(Math.random()-.5)*5,vy:(Math.random()-.5)*5,r:4,c:lt.type==='hp'?'#00e676':'#40c4ff',l:20,ml:20});}});
  // Storm hit
  if(stormX>=p.x-22){p.hp--;stormSpd=Math.max(stormSpd,scrollSpd+0.3);for(let i=0;i<5;i++)particles.push({x:p.x,y:p.y-10,vx:(Math.random()-.5)*4,vy:-2,r:3,c:'#aa00ff',l:20,ml:20});if(p.hp<=0)gameOver=true;}
  obstacles=obstacles.filter(o=>o.x+150>0);loot=loot.filter(l=>!l.collected&&l.x>-30);
  particles.forEach(pt=>{pt.x+=pt.vx;pt.y+=pt.vy;pt.vy+=0.3;pt.l--;});particles=particles.filter(pt=>pt.l>0);
  if(score>best)best=score;
}
function drawPlayer(){
  let wk=p.y<GY?0:Math.sin(frame*.22)*8;
  // Shadow
  cx.fillStyle='rgba(0,0,0,0.3)';cx.beginPath();cx.ellipse(p.x,GY+4,14,4,0,0,Math.PI*2);cx.fill();
  let hp=p.hp>0;
  cx.fillStyle='#1a4008';cx.fillRect(p.x-7,p.y-10+wk*.4,7,18);cx.fillStyle='#122806';cx.fillRect(p.x,p.y-10,7,18);
  cx.fillStyle='#1e5010';cx.fillRect(p.x-10,p.y-30,20,22);cx.fillStyle='#d0844a';cx.beginPath();cx.arc(p.x,p.y-38,9,0,Math.PI*2);cx.fill();
  cx.fillStyle='#1e5010';cx.fillRect(p.x-18,p.y-22,8,12+Math.abs(wk*.4));cx.fillRect(p.x+10,p.y-22,8,12+Math.abs(wk*.4));
  cx.fillStyle='#3e8a20';cx.fillRect(p.x-11,p.y-35,22,10);cx.beginPath();cx.arc(p.x,p.y-35,11,Math.PI,0);cx.fill();
}
function draw(){
  update();cx.clearRect(0,0,W,H);
  // Sky
  let sg=cx.createLinearGradient(0,0,0,GY);sg.addColorStop(0,'#010810');sg.addColorStop(0.7,'#0a1e1a');sg.addColorStop(1,'#0f3020');
  cx.fillStyle=sg;cx.fillRect(0,0,W,GY);
  stars.forEach(s=>{cx.globalAlpha=0.35+0.55*Math.abs(Math.sin(frame*.016+s.b*8));cx.fillStyle='#fff';cx.beginPath();cx.arc(s.x,s.y,s.r,0,Math.PI*2);cx.fill();});cx.globalAlpha=1;
  // BG trees (parallax)
  bgTrees.forEach(t=>{cx.fillStyle=t.dark?'#0a200a':'#0f2e0f';cx.fillRect(t.x,GY-t.h,t.w,t.h);let cg=cx.createRadialGradient(t.x+t.w/2,GY-t.h,2,t.x+t.w/2,GY-t.h,t.w*.8);cg.addColorStop(0,t.dark?'#14381a':'#1a5020');cg.addColorStop(1,'transparent');cx.fillStyle=cg;cx.beginPath();cx.arc(t.x+t.w/2,GY-t.h-10,t.w*.72,0,Math.PI*2);cx.fill();});
  // Ground
  let gg=cx.createLinearGradient(0,GY,0,H);gg.addColorStop(0,'#2a6a10');gg.addColorStop(0.15,'#1a4a08');gg.addColorStop(1,'#091d03');cx.fillStyle=gg;cx.fillRect(0,GY,W,H-GY);
  // Obstacles
  obstacles.forEach(o=>{
    if(o.type==='gap'){cx.fillStyle='#091d03';cx.fillRect(o.x,GY,o.gw,H-GY+10);cx.fillStyle='rgba(0,0,0,0.6)';cx.fillRect(o.x,GY,o.gw,8);}
    else if(o.type==='rock'){let rg=cx.createRadialGradient(o.x+o.w/2,o.y+o.h/2,2,o.x+o.w/2,o.y+o.h/2,o.w*.7);rg.addColorStop(0,'#5a5a44');rg.addColorStop(1,'#2a2a1c');cx.fillStyle=rg;cx.beginPath();cx.ellipse(o.x+o.w/2,o.y+o.h/2,o.w/2,o.h/2,.1,0,Math.PI*2);cx.fill();}
    else{cx.fillStyle='#3a2000';cx.fillRect(o.x-4,o.y,8,o.h);let cg=cx.createRadialGradient(o.x,o.y,2,o.x,o.y,o.r);cg.addColorStop(0,o.dark?'#193a12':'#245c18');cg.addColorStop(1,'rgba(0,0,0,0)');cx.fillStyle=cg;cx.beginPath();cx.arc(o.x,o.y,o.r,0,Math.PI*2);cx.fill();}
  });
  // Loot boxes
  loot.forEach(lt=>{if(lt.collected)return;let pulse=0.8+0.2*Math.sin(frame*.1+lt.ph);cx.shadowColor=lt.type==='hp'?'#00e676':'#40c4ff';cx.shadowBlur=10*pulse;cx.fillStyle=lt.type==='hp'?'#006632':'#004488';cx.fillRect(lt.x-12,lt.y-12,24,24);cx.fillStyle='#FFD100';cx.fillRect(lt.x-12,lt.y-13,24,4);cx.fillRect(lt.x-1,lt.y-13,2,27);cx.shadowBlur=0;cx.fillStyle='#fff';cx.font='12px sans-serif';cx.textAlign='center';cx.fillText(lt.type==='hp'?'❤️':'🛡️',lt.x,lt.y+5);cx.textAlign='left';});
  // Storm wall
  let sw=stormX;
  let storm=cx.createLinearGradient(sw-80,0,sw,0);storm.addColorStop(0,'rgba(0,0,0,0)');storm.addColorStop(0.6,'rgba(100,0,180,0.5)');storm.addColorStop(1,'rgba(160,0,255,0.85)');
  cx.fillStyle=storm;cx.fillRect(0,0,sw,H);
  cx.strokeStyle='rgba(200,0,255,0.9)';cx.lineWidth=4+2*Math.sin(frame*.08);cx.shadowColor='#aa00ff';cx.shadowBlur=20;cx.beginPath();cx.moveTo(sw,0);cx.lineTo(sw,H);cx.stroke();cx.shadowBlur=0;
  drawPlayer();
  particles.forEach(pt=>{cx.globalAlpha=pt.l/pt.ml;cx.fillStyle=pt.c;cx.beginPath();cx.arc(pt.x,pt.y,pt.r,0,Math.PI*2);cx.fill();});cx.globalAlpha=1;
  // HUD
  cx.fillStyle='rgba(0,0,10,0.75)';cx.fillRect(0,0,W,44);
  cx.fillStyle='#FFD100';cx.font='bold 14px Bangers,sans-serif';cx.fillText('🏃 STORM SPRINT',10,26);
  cx.fillStyle='#fff';cx.font='bold 12px Rajdhani,sans-serif';cx.textAlign='center';cx.fillText('SCORE: '+score+'  ·  BEST: '+best,W/2,16);
  cx.fillStyle='rgba(200,0,255,0.85)';cx.fillText('⚡ OUTRUN THE STORM!',W/2,34);cx.textAlign='left';
  cx.fillStyle='#ff5252';cx.font='bold 16px Bangers,sans-serif';cx.fillText('❤️'.repeat(p.hp),W-130,26);
  cx.fillStyle='rgba(150,170,210,0.65)';cx.font='8px Rajdhani,sans-serif';cx.fillText('SPACE/W/↑ = Jump (x2 for double jump) · Dodge obstacles · Collect loot',10,H-6);
  if(gameOver){
    cx.fillStyle='rgba(0,0,0,0.82)';cx.fillRect(0,0,W,H);cx.textAlign='center';
    cx.fillStyle='#ff1744';cx.shadowColor='#ff1744';cx.shadowBlur=20;cx.font='bold 48px Bangers,sans-serif';cx.fillText('💀 STORM GOT YOU!',W/2,H/2-28);cx.shadowBlur=0;
    cx.fillStyle='#fff';cx.font='18px Rajdhani,sans-serif';cx.fillText('Score: '+score,W/2,H/2+8);
    cx.fillStyle='#FFD100';cx.font='14px Rajdhani,sans-serif';cx.fillText('Best: '+best,W/2,H/2+30);cx.textAlign='left';
  }
  requestAnimationFrame(draw);
}
window.addEventListener('keydown',e=>{if(['Space','ArrowUp','KeyW'].includes(e.code))e.preventDefault();keys[e.code]=true;});
window.addEventListener('keyup',e=>{keys[e.code]=false;});
cvs.setAttribute('tabindex','0');cvs.focus();draw();
(function(){var b=document.createElement('button');b.textContent='⛶';b.title='Fullscreen';b.style.cssText='position:fixed;top:8px;right:8px;z-index:9999;background:rgba(0,0,20,.8);color:#fff;border:1.5px solid rgba(255,255,255,.3);border-radius:7px;padding:5px 10px;font-size:16px;cursor:pointer;';var cv=document.getElementById('g');b.onclick=function(){if(!document.fullscreenElement){document.documentElement.requestFullscreen().catch(function(){});}else{document.exitFullscreen();}};document.addEventListener('fullscreenchange',function(){if(document.fullscreenElement){var cw=cv.width,ch=cv.height,s=Math.min(window.innerWidth/cw,window.innerHeight/ch);cv.style.position='fixed';cv.style.left=Math.round((window.innerWidth-cw*s)/2)+'px';cv.style.top=Math.round((window.innerHeight-ch*s)/2)+'px';cv.style.transform='scale('+s+')';cv.style.transformOrigin='0 0';document.body.style.background='#000';b.textContent='✕';}else{cv.style.position='';cv.style.left='';cv.style.top='';cv.style.transform='';cv.style.transformOrigin='';b.textContent='⛶';}});document.body.appendChild(b);})();
</script></body></html>"""

# ── Game 6: Target Blitz (click targets arcade) ──────────────────────────────
_BLITZ_HTML = r"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>*{margin:0;padding:0;box-sizing:border-box;}body{background:#010810;overflow:hidden;}canvas{display:block;cursor:crosshair;}</style>
</head><body><canvas id="g"></canvas><script>
const cvs=document.getElementById('g');const cx=cvs.getContext('2d');
const W=cvs.width=Math.min(1100,window.innerWidth-4);const H=cvs.height=520;
const PNAME="__BL_NAME__";
const TOTAL=60; // seconds
let targets=[],effects=[],particles=[];
let score=0,combo=1,misses=0,shots=0,hits=0,frame=0,timer=TOTAL*60,gameOver=false;
let mx=W/2,my=H/2;
let spawnCooldown=0;
let stars=Array.from({length:80},()=>({x:Math.random()*W,y:Math.random()*H,r:Math.random()*1.4+.3,b:Math.random()}));
function spawnTarget(){
  let margin=55,r=Math.max(12,44-score/60);
  let x=margin+r+Math.random()*(W-2*(margin+r));
  let y=90+r+Math.random()*(H-90-2*r-40);
  let life=Math.max(38,100-score/50);
  // Ring type targets at higher scores
  let big=score<80;
  targets.push({x,y,r,life,maxLife:life,pulse:Math.random()*6.28,type:big?'circle':'ring',pts:big?10:25});
}
function update(){
  if(gameOver)return;frame++;timer--;
  if(timer<=0){gameOver=true;return;}
  spawnCooldown--;
  let maxT=Math.min(8+Math.floor(score/80),16);
  if(spawnCooldown<=0&&targets.length<maxT){spawnCooldown=Math.max(8,28-score/55);spawnTarget();}
  targets=targets.filter(t=>{t.life--;if(t.life<=0){combo=1;return false;}return true;});
  effects=effects.filter(e=>(e.l--,e.l>0));
  particles=particles.filter(p=>(p.l--,p.x+=p.vx,p.y+=p.vy,p.l>0));
}
cvs.addEventListener('click',e=>{
  let rect=cvs.getBoundingClientRect();
  let cx2=(e.clientX-rect.left)*(W/rect.width);
  let cy2=(e.clientY-rect.top)*(H/rect.height);
  shots++;let hit=false;
  targets=targets.filter(t=>{
    if(!hit&&Math.hypot(cx2-t.x,cy2-t.y)<t.r){
      hit=true;hits++;
      let pts=t.pts*combo;score+=pts;combo++;
      effects.push({x:t.x,y:t.y,txt:'+'+pts+(combo>2?' x'+combo:''),c:combo>4?'#FFD100':'#00e676',l:45,big:combo>3});
      for(let i=0;i<8;i++)particles.push({x:t.x,y:t.y,vx:(Math.random()-.5)*8,vy:(Math.random()-.5)*8,r:3+Math.random()*3,c:combo>4?'#FFD100':'#4da6ff',l:20});
      return false;
    }return true;
  });
  if(!hit){combo=1;misses++;effects.push({x:cx2,y:cy2,txt:'MISS',c:'#ff5252',l:22,big:false});}
});
cvs.addEventListener('mousemove',e=>{let rect=cvs.getBoundingClientRect();mx=(e.clientX-rect.left)*(W/rect.width);my=(e.clientY-rect.top)*(H/rect.height);});
function draw(){
  update();cx.clearRect(0,0,W,H);
  let sg=cx.createLinearGradient(0,0,0,H);sg.addColorStop(0,'#010810');sg.addColorStop(1,'#0a1428');
  cx.fillStyle=sg;cx.fillRect(0,0,W,H);
  stars.forEach(s=>{cx.globalAlpha=0.3+0.6*Math.abs(Math.sin(frame*.016+s.b*8));cx.fillStyle='#fff';cx.beginPath();cx.arc(s.x,s.y,s.r,0,Math.PI*2);cx.fill();});cx.globalAlpha=1;
  // Targets
  targets.forEach(t=>{
    let pct=t.life/t.maxLife;let pulse=0.85+0.15*Math.sin(frame*.12+t.pulse);
    let tc=pct>.6?'#00e676':pct>.3?'#ff9100':'#ff1744';
    // Life ring
    cx.strokeStyle='rgba(255,255,255,0.15)';cx.lineWidth=3;cx.beginPath();cx.arc(t.x,t.y,t.r+6,0,Math.PI*2);cx.stroke();
    cx.strokeStyle=tc;cx.lineWidth=3;cx.shadowColor=tc;cx.shadowBlur=6;cx.beginPath();cx.arc(t.x,t.y,t.r+6,-Math.PI/2,-Math.PI/2+Math.PI*2*pct);cx.stroke();cx.shadowBlur=0;
    if(t.type==='circle'){
      let tg=cx.createRadialGradient(t.x,t.y,0,t.x,t.y,t.r);tg.addColorStop(0,'rgba(255,255,255,0.8)');tg.addColorStop(0.35,'rgba(255,80,50,0.9)');tg.addColorStop(0.65,'rgba(220,20,0,0.9)');tg.addColorStop(1,'rgba(100,0,0,0.8)');
      cx.fillStyle=tg;cx.shadowColor='#ff3300';cx.shadowBlur=12;cx.beginPath();cx.arc(t.x,t.y,t.r*pulse,0,Math.PI*2);cx.fill();cx.shadowBlur=0;
      // Bullseye rings
      cx.strokeStyle='rgba(255,255,255,0.3)';cx.lineWidth=1;
      for(let r=t.r*.3;r<t.r*.9;r+=t.r*.28){cx.beginPath();cx.arc(t.x,t.y,r,0,Math.PI*2);cx.stroke();}
      cx.fillStyle='#fff';cx.beginPath();cx.arc(t.x,t.y,t.r*.12,0,Math.PI*2);cx.fill();
    }else{
      cx.strokeStyle='#ff9100';cx.lineWidth=4;cx.shadowColor='#ff9100';cx.shadowBlur=12;cx.beginPath();cx.arc(t.x,t.y,t.r*pulse,0,Math.PI*2);cx.stroke();cx.shadowBlur=0;
      cx.fillStyle='rgba(255,145,0,0.18)';cx.beginPath();cx.arc(t.x,t.y,t.r*pulse,0,Math.PI*2);cx.fill();
      cx.fillStyle='#FFD100';cx.font='bold 14px Bangers,sans-serif';cx.textAlign='center';cx.fillText(t.pts,t.x,t.y+5);cx.textAlign='left';
    }
  });
  // Particles
  particles.forEach(pt=>{cx.globalAlpha=pt.l/20;cx.fillStyle=pt.c;cx.beginPath();cx.arc(pt.x,pt.y,pt.r,0,Math.PI*2);cx.fill();});cx.globalAlpha=1;
  // Effects
  effects.forEach(e=>{let a=e.l/45;cx.globalAlpha=a;cx.fillStyle=e.c;cx.shadowColor=e.c;cx.shadowBlur=e.big?14:6;cx.font=`bold ${e.big?22:14}px Bangers,sans-serif`;cx.textAlign='center';cx.fillText(e.txt,e.x,e.y-20*(1-a));cx.shadowBlur=0;cx.globalAlpha=1;cx.textAlign='left';});
  // Crosshair
  cx.strokeStyle='rgba(255,255,255,0.7)';cx.lineWidth=1.5;
  cx.beginPath();cx.moveTo(mx-14,my);cx.lineTo(mx-4,my);cx.stroke();cx.beginPath();cx.moveTo(mx+4,my);cx.lineTo(mx+14,my);cx.stroke();
  cx.beginPath();cx.moveTo(mx,my-14);cx.lineTo(mx,my-4);cx.stroke();cx.beginPath();cx.moveTo(mx,my+4);cx.lineTo(mx,my+14);cx.stroke();
  cx.strokeStyle='rgba(255,255,255,0.4)';cx.beginPath();cx.arc(mx,my,5,0,Math.PI*2);cx.stroke();
  // HUD
  cx.fillStyle='rgba(0,0,10,0.8)';cx.fillRect(0,0,W,48);
  let secLeft=Math.ceil(timer/60);let tc=secLeft>20?'#00e676':secLeft>10?'#ff9100':'#ff1744';
  cx.fillStyle=tc;cx.shadowColor=tc;cx.shadowBlur=8;cx.font='bold 22px Bangers,sans-serif';cx.fillText('⏱️ '+secLeft,10,30);cx.shadowBlur=0;
  cx.fillStyle='#FFD100';cx.font='bold 20px Bangers,sans-serif';cx.textAlign='center';cx.fillText('🎯 TARGET BLITZ',W/2,18);
  cx.fillStyle='#fff';cx.font='bold 13px Rajdhani,sans-serif';cx.fillText('SCORE: '+score+'  ·  COMBO x'+combo+'  ·  ACC: '+(shots>0?Math.round(hits/shots*100):100)+'%',W/2,35);cx.textAlign='left';
  cx.fillStyle='#FFD100';cx.font='bold 20px Bangers,sans-serif';cx.textAlign='right';cx.fillText('x'+combo,W-12,30);cx.textAlign='left';
  // Game over
  if(gameOver){
    cx.fillStyle='rgba(0,0,0,0.84)';cx.fillRect(0,0,W,H);cx.textAlign='center';
    cx.fillStyle='#FFD100';cx.shadowColor='#FFD100';cx.shadowBlur=22;cx.font='bold 50px Bangers,sans-serif';cx.fillText('⏱️ TIME UP!',W/2,H/2-48);cx.shadowBlur=0;
    cx.fillStyle='#fff';cx.font='22px Bangers,sans-serif';cx.fillText('FINAL SCORE: '+score,W/2,H/2);
    cx.font='15px Rajdhani,sans-serif';cx.fillStyle='#aabbdd';
    cx.fillText('Accuracy: '+Math.round(hits/(shots||1)*100)+'%  ·  Targets hit: '+hits+'  ·  Misses: '+misses,W/2,H/2+30);
    let rank=score<500?'TRAINEE':score<1500?'MARKSMAN':score<3000?'SHARPSHOOTER':score<5000?'SNIPER ELITE':'LEGENDARY AIM';
    cx.fillStyle='#FFD100';cx.font='bold 20px Bangers,sans-serif';cx.fillText('🏅 '+rank,W/2,H/2+60);cx.textAlign='left';
  }
  requestAnimationFrame(draw);
}
cvs.setAttribute('tabindex','0');cvs.focus();draw();
(function(){var b=document.createElement('button');b.textContent='⛶';b.title='Fullscreen';b.style.cssText='position:fixed;top:8px;right:8px;z-index:9999;background:rgba(0,0,20,.8);color:#fff;border:1.5px solid rgba(255,255,255,.3);border-radius:7px;padding:5px 10px;font-size:16px;cursor:pointer;';var cv=document.getElementById('g');b.onclick=function(){if(!document.fullscreenElement){document.documentElement.requestFullscreen().catch(function(){});}else{document.exitFullscreen();}};document.addEventListener('fullscreenchange',function(){if(document.fullscreenElement){var cw=cv.width,ch=cv.height,s=Math.min(window.innerWidth/cw,window.innerHeight/ch);cv.style.position='fixed';cv.style.left=Math.round((window.innerWidth-cw*s)/2)+'px';cv.style.top=Math.round((window.innerHeight-ch*s)/2)+'px';cv.style.transform='scale('+s+')';cv.style.transformOrigin='0 0';document.body.style.background='#000';b.textContent='✕';}else{cv.style.position='';cv.style.left='';cv.style.top='';cv.style.transform='';cv.style.transformOrigin='';b.textContent='⛶';}});document.body.appendChild(b);})();
</script></body></html>"""

# ── Game 7: Zone Wars (top-down 2D battle royale vs AI) ──────────────────────
_ZONE_HTML = r"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>*{margin:0;padding:0;box-sizing:border-box;}body{background:#010810;overflow:hidden;}canvas{display:block;cursor:crosshair;}</style>
</head><body><canvas id="g"></canvas><script>
const cvs=document.getElementById('g');const cx=cvs.getContext('2d');
const W=cvs.width=Math.min(900,window.innerWidth-4);const H=cvs.height=520;
const PNAME="__ZW_NAME__";
let p={x:W/2,y:H/2,hp:100,sh:60,spd:3.2,r:14,col:'#4da6ff',aimX:0,aimY:-1};
let enemies=[],bullets=[],loot=[],particles=[],walls=[];
let stX=0,stY=0,stW=W,stH=H,stShrink=0.08;
let frame=0,score=0,kills=0,gameOver=false,winMsg='';
let mx=W/2,my=H/2;let keys={};let fireCd=0;
let stars=Array.from({length:60},()=>({x:Math.random()*W,y:Math.random()*H,r:Math.random()*1.2+.2,b:Math.random()}));
// Spawn 4 AI enemies
const eColors=['#ff5252','#ff9100','#cc00cc','#ff1744'];
[{x:W*.1,y:H*.1},{x:W*.9,y:H*.1},{x:W*.1,y:H*.9},{x:W*.9,y:H*.9}].forEach((pos,i)=>{
  enemies.push({x:pos.x,y:pos.y,hp:60,mhp:60,spd:1.4+i*.15,r:13,col:eColors[i],atkTimer:0,shootTimer:60+i*18,state:'wander',wx:pos.x,wy:pos.y,alertR:200});
});
// Loot boxes scattered around
for(let i=0;i<8;i++)loot.push({x:80+Math.random()*(W-160),y:80+Math.random()*(H-160),type:i<3?'hp':i<6?'sh':'ammo',collected:false,ph:Math.random()*6.28});
// Some cover walls
for(let i=0;i<6;i++){let x=W*.2+Math.random()*W*.6,y=H*.2+Math.random()*H*.6;walls.push({x,y,w:60+Math.random()*40,h:16+Math.random()*10});}
function inWall(x,y,r){return walls.some(w=>x+r>w.x&&x-r<w.x+w.w&&y+r>w.y&&y-r<w.y+w.h);}
function stormDmg(x,y){return x<stX||x>stX+stW||y<stY||y>stY+stH;}
function shoot(from,tx,ty,dmg,col,owner){
  let dx=tx-from.x,dy=ty-from.y,d=Math.hypot(dx,dy)||1;
  bullets.push({x:from.x,y:from.y,vx:dx/d*11,vy:dy/d*11,dmg,col,owner,r:5});
}
function update(){
  if(gameOver)return;frame++;
  // Storm shrink
  stX=Math.min(W*.38,stX+stShrink*.25);stY=Math.min(H*.38,stY+stShrink*.18);
  stW=Math.max(W*.24,stW-stShrink*.5);stH=Math.max(H*.24,stH-stShrink*.36);
  stShrink+=0.0006;
  // Player move
  let nx=p.x,ny=p.y;
  if(keys['KeyW']||keys['ArrowUp'])ny-=p.spd;if(keys['KeyS']||keys['ArrowDown'])ny+=p.spd;
  if(keys['KeyA']||keys['ArrowLeft'])nx-=p.spd;if(keys['KeyD']||keys['ArrowRight'])nx+=p.spd;
  if(!inWall(nx,p.y,p.r))p.x=Math.max(p.r,Math.min(W-p.r,nx));
  if(!inWall(p.x,ny,p.r))p.y=Math.max(p.r,Math.min(H-p.r,ny));
  p.aimX=mx-p.x;p.aimY=my-p.y;
  // Player shoot
  if(fireCd>0)fireCd--;
  if((keys['Space']||keys['KeyF'])&&fireCd<=0){shoot(p,mx,my,35,'#FFD100','p');fireCd=14;}
  // Storm damage to player
  if(stormDmg(p.x,p.y)&&frame%55===0){let d=8;if(p.sh>0){let s=Math.min(p.sh,d);p.sh-=s;d-=s;}p.hp=Math.max(0,p.hp-d);for(let i=0;i<4;i++)particles.push({x:p.x+(Math.random()-.5)*18,y:p.y-8,vx:(Math.random()-.5)*3,vy:-2,r:3,c:'#aa00ff',l:18,ml:18});}
  if(p.hp<=0){gameOver=true;winMsg='💀 YOU WERE ELIMINATED!';return;}
  // Enemies AI
  enemies.forEach(e=>{
    let dp=Math.hypot(p.x-e.x,p.y-e.y);
    if(dp<e.alertR){e.state='chase';}else if(Math.random()<0.005)e.state='wander';
    if(e.state==='chase'){
      let dx=p.x-e.x,dy=p.y-e.y,d=Math.hypot(dx,dy)||1;
      let nx2=e.x+dx/d*e.spd,ny2=e.y+dy/d*e.spd;
      if(!inWall(nx2,e.y,e.r))e.x=nx2;if(!inWall(e.x,ny2,e.r))e.y=ny2;
      e.shootTimer--;if(e.shootTimer<=0&&dp<300){e.shootTimer=70+Math.random()*40;shoot(e,p.x+(Math.random()-.5)*25,p.y+(Math.random()-.5)*25,15,e.col,'e');}
      e.atkTimer++;if(dp<22&&e.atkTimer>50){e.atkTimer=0;let d2=18;if(p.sh>0){let s=Math.min(p.sh,d2);p.sh-=s;d2-=s;}p.hp=Math.max(0,p.hp-d2);if(p.hp<=0){gameOver=true;winMsg='💀 YOU WERE ELIMINATED!';}}
    }else{
      e.wx+=((Math.random()-.5)*2.5);e.wy+=((Math.random()-.5)*2.5);
      e.wx=Math.max(e.r,Math.min(W-e.r,e.wx));e.wy=Math.max(e.r,Math.min(H-e.r,e.wy));
      let dx=e.wx-e.x,dy=e.wy-e.y,d=Math.hypot(dx,dy)||1;if(d>3){e.x+=dx/d*e.spd*.5;e.y+=dy/d*e.spd*.5;}
    }
    // Storm kills enemies too
    if(stormDmg(e.x,e.y)&&frame%70===0){e.hp-=8;if(e.hp<=0){kills++;score+=150;for(let i=0;i<12;i++)particles.push({x:e.x,y:e.y,vx:(Math.random()-.5)*8,vy:(Math.random()-.5)*8,r:4,c:e.col,l:28,ml:28});}}
  });
  enemies=enemies.filter(e=>e.hp>0);
  // Bullets
  bullets=bullets.filter(b=>{
    b.x+=b.vx;b.y+=b.vy;
    if(b.x<0||b.x>W||b.y<0||b.y>H)return false;
    if(walls.some(w=>b.x>w.x&&b.x<w.x+w.w&&b.y>w.y&&b.y<w.y+w.h)){for(let i=0;i<4;i++)particles.push({x:b.x,y:b.y,vx:(Math.random()-.5)*4,vy:(Math.random()-.5)*4,r:2,c:'#888',l:10,ml:10});return false;}
    if(b.owner==='p'){let hit=false;enemies=enemies.filter(e=>{if(!hit&&Math.hypot(b.x-e.x,b.y-e.y)<e.r+b.r){hit=true;e.hp-=b.dmg;score+=5;for(let i=0;i<6;i++)particles.push({x:b.x,y:b.y,vx:(Math.random()-.5)*6,vy:(Math.random()-.5)*6,r:3,c:e.col,l:16,ml:16});if(e.hp<=0){kills++;score+=150;for(let i=0;i<12;i++)particles.push({x:e.x,y:e.y,vx:(Math.random()-.5)*9,vy:(Math.random()-.5)*9,r:5,c:e.col,l:28,ml:28});}return e.hp>0;}return true;});return !hit;}
    else{if(Math.hypot(b.x-p.x,b.y-p.y)<p.r+b.r){let d=b.dmg;if(p.sh>0){let s=Math.min(p.sh,d);p.sh-=s;d-=s;}p.hp=Math.max(0,p.hp-d);if(p.hp<=0){gameOver=true;winMsg='💀 ELIMINATED!';}for(let i=0;i<5;i++)particles.push({x:b.x,y:b.y,vx:(Math.random()-.5)*5,vy:(Math.random()-.5)*5,r:3,c:'#ff1744',l:14,ml:14});return false;}return true;}
  });
  // Loot
  loot.forEach(lt=>{if(!lt.collected&&Math.hypot(p.x-lt.x,p.y-lt.y)<22){lt.collected=true;if(lt.type==='hp'){p.hp=Math.min(100,p.hp+40);score+=30;}else if(lt.type==='sh'){p.sh=Math.min(100,p.sh+45);score+=25;}else{score+=50;}}});
  if(enemies.length===0&&!gameOver){gameOver=true;winMsg='🏆 VICTORY ROYALE!';}
  particles=particles.filter(pt=>(pt.x+=pt.vx,pt.y+=pt.vy,pt.l--,pt.l>0));
}
function draw(){
  update();cx.clearRect(0,0,W,H);
  // Ground
  let gg=cx.createLinearGradient(0,0,0,H);gg.addColorStop(0,'#0a1e10');gg.addColorStop(1,'#061208');cx.fillStyle=gg;cx.fillRect(0,0,W,H);
  // Grid
  cx.strokeStyle='rgba(30,70,20,0.3)';cx.lineWidth=1;for(let x=0;x<W;x+=55){cx.beginPath();cx.moveTo(x,0);cx.lineTo(x,H);cx.stroke();}for(let y=0;y<H;y+=55){cx.beginPath();cx.moveTo(0,y);cx.lineTo(W,y);cx.stroke();}
  // Storm overlay
  cx.save();cx.beginPath();cx.rect(0,0,W,H);cx.rect(stX,stY,stW,stH);cx.fillStyle='rgba(100,0,180,0.28)';cx.fill('evenodd');
  cx.strokeStyle=`rgba(200,0,255,${0.7+0.2*Math.sin(frame*.08)})`;cx.lineWidth=3;cx.shadowColor='#aa00ff';cx.shadowBlur=16;cx.strokeRect(stX,stY,stW,stH);cx.shadowBlur=0;cx.restore();
  // Walls
  walls.forEach(w=>{cx.fillStyle='#4a3820';cx.fillRect(w.x,w.y,w.w,w.h);cx.fillStyle='#6a5030';cx.fillRect(w.x,w.y,w.w,4);});
  // Loot
  loot.forEach(lt=>{if(lt.collected)return;let pulse=0.8+0.2*Math.sin(frame*.1+lt.ph);let c=lt.type==='hp'?'#00e676':lt.type==='sh'?'#40c4ff':'#FFD100';cx.shadowColor=c;cx.shadowBlur=10*pulse;cx.fillStyle=c;cx.beginPath();cx.arc(lt.x,lt.y,10*pulse,0,Math.PI*2);cx.fill();cx.shadowBlur=0;cx.fillStyle='#fff';cx.font='10px sans-serif';cx.textAlign='center';cx.fillText(lt.type==='hp'?'❤️':lt.type==='sh'?'🛡️':'⚡',lt.x,lt.y+4);cx.textAlign='left';});
  // Enemies
  enemies.forEach(e=>{
    cx.shadowColor=e.col;cx.shadowBlur=8;
    cx.fillStyle=e.col;cx.beginPath();cx.arc(e.x,e.y,e.r,0,Math.PI*2);cx.fill();
    cx.shadowBlur=0;cx.fillStyle='rgba(0,0,0,0.5)';cx.beginPath();cx.arc(e.x,e.y,e.r,0,Math.PI*2);cx.fill();
    cx.strokeStyle=e.col;cx.lineWidth=2.5;cx.shadowColor=e.col;cx.shadowBlur=8;cx.beginPath();cx.arc(e.x,e.y,e.r,0,Math.PI*2);cx.stroke();cx.shadowBlur=0;
    cx.fillStyle='rgba(255,255,255,0.9)';cx.font='bold 10px sans-serif';cx.textAlign='center';cx.fillText('AI',e.x,e.y+4);cx.textAlign='left';
    // HP bar
    cx.fillStyle='rgba(0,0,0,0.7)';cx.fillRect(e.x-e.r,e.y-e.r-10,e.r*2,6);
    let hc=e.hp/e.mhp>.5?'#00e676':'#ff5252';cx.fillStyle=hc;cx.fillRect(e.x-e.r,e.y-e.r-10,e.r*2*(e.hp/e.mhp),6);
  });
  // Player
  cx.shadowColor=p.col;cx.shadowBlur=14;
  let pd=Math.hypot(p.aimX,p.aimY)||1;
  let pa=Math.atan2(p.aimY,p.aimX);
  cx.fillStyle=p.col;cx.beginPath();cx.arc(p.x,p.y,p.r,0,Math.PI*2);cx.fill();cx.shadowBlur=0;
  // Direction indicator
  cx.strokeStyle='#FFD100';cx.lineWidth=2.5;cx.shadowColor='#FFD100';cx.shadowBlur=8;
  cx.beginPath();cx.moveTo(p.x+Math.cos(pa)*p.r,p.y+Math.sin(pa)*p.r);cx.lineTo(p.x+Math.cos(pa)*(p.r+14),p.y+Math.sin(pa)*(p.r+14));cx.stroke();cx.shadowBlur=0;
  cx.fillStyle='#fff';cx.font='bold 8px sans-serif';cx.textAlign='center';cx.fillText('YOU',p.x,p.y+3);cx.textAlign='left';
  // Bullets
  bullets.forEach(b=>{cx.shadowColor=b.col;cx.shadowBlur=10;cx.fillStyle=b.col;cx.beginPath();cx.arc(b.x,b.y,b.r,0,Math.PI*2);cx.fill();cx.shadowBlur=0;});
  // Particles
  particles.forEach(pt=>{cx.globalAlpha=pt.l/pt.ml;cx.fillStyle=pt.c;cx.beginPath();cx.arc(pt.x,pt.y,pt.r,0,Math.PI*2);cx.fill();});cx.globalAlpha=1;
  // HUD
  cx.fillStyle='rgba(0,0,10,0.82)';cx.fillRect(0,0,W,48);
  cx.fillStyle='#FFD100';cx.font='bold 15px Bangers,sans-serif';cx.fillText('🗺️ ZONE WARS',10,28);
  let hb=p.hp/100,hc2=hb>.5?'#00e676':hb>.25?'#ff9100':'#ff1744';
  cx.fillStyle='rgba(0,0,0,0.5)';cx.fillRect(160,10,160,14);cx.fillStyle=hc2;cx.fillRect(160,10,160*hb,14);cx.strokeStyle='rgba(255,255,255,0.3)';cx.strokeRect(160,10,160,14);
  cx.fillStyle='#fff';cx.font='bold 9px Rajdhani,sans-serif';cx.fillText('❤️ '+p.hp+'/100',163,21);
  let sb=p.sh/100;cx.fillStyle='rgba(0,0,0,0.5)';cx.fillRect(160,26,160,12);cx.fillStyle='#40c4ff';cx.fillRect(160,26,160*sb,12);cx.strokeStyle='rgba(64,196,255,0.35)';cx.strokeRect(160,26,160,12);cx.fillStyle='#40c4ff';cx.font='8px Rajdhani,sans-serif';cx.fillText('🛡️ '+p.sh,163,35);
  cx.fillStyle='#FFD100';cx.font='bold 14px Bangers,sans-serif';cx.textAlign='center';cx.fillText('KILLS: '+kills+'  ·  SCORE: '+score+'  ·  ENEMIES LEFT: '+enemies.length,W/2,28);cx.textAlign='left';
  cx.fillStyle='rgba(200,0,255,0.8)';cx.font='bold 10px Rajdhani,sans-serif';cx.textAlign='center';cx.fillText('⚡ STORM CLOSING IN',W/2,42);cx.textAlign='left';
  cx.fillStyle='rgba(150,170,210,0.6)';cx.font='8px Rajdhani,sans-serif';cx.textAlign='right';cx.fillText('WASD=Move · SPACE/F=Shoot · Stay in safe zone!',W-6,42);cx.textAlign='left';
  if(gameOver){
    cx.fillStyle='rgba(0,0,0,0.84)';cx.fillRect(0,0,W,H);cx.textAlign='center';
    let wc=winMsg.includes('VICTORY')?'#FFD100':'#ff1744';
    cx.fillStyle=wc;cx.shadowColor=wc;cx.shadowBlur=22;cx.font='bold 52px Bangers,sans-serif';cx.fillText(winMsg,W/2,H/2-28);cx.shadowBlur=0;
    cx.fillStyle='#fff';cx.font='17px Rajdhani,sans-serif';cx.fillText('Score: '+score+'  ·  Kills: '+kills,W/2,H/2+10);
    cx.fillStyle='#aabbdd';cx.font='12px Rajdhani,sans-serif';cx.fillText('Return to menu to play again',W/2,H/2+34);cx.textAlign='left';
  }
  requestAnimationFrame(draw);
}
cvs.addEventListener('mousemove',e=>{let rect=cvs.getBoundingClientRect();mx=(e.clientX-rect.left)*(W/rect.width);my=(e.clientY-rect.top)*(H/rect.height);});
cvs.addEventListener('click',e=>{let rect=cvs.getBoundingClientRect();mx=(e.clientX-rect.left)*(W/rect.width);my=(e.clientY-rect.top)*(H/rect.height);if(!gameOver&&fireCd<=0){shoot(p,mx,my,35,'#FFD100','p');fireCd=14;}});
window.addEventListener('keydown',e=>{keys[e.code]=true;});window.addEventListener('keyup',e=>{keys[e.code]=false;});
cvs.setAttribute('tabindex','0');cvs.focus();draw();
(function(){var b=document.createElement('button');b.textContent='⛶';b.title='Fullscreen';b.style.cssText='position:fixed;top:8px;right:8px;z-index:9999;background:rgba(0,0,20,.8);color:#fff;border:1.5px solid rgba(255,255,255,.3);border-radius:7px;padding:5px 10px;font-size:16px;cursor:pointer;';var cv=document.getElementById('g');b.onclick=function(){if(!document.fullscreenElement){document.documentElement.requestFullscreen().catch(function(){});}else{document.exitFullscreen();}};document.addEventListener('fullscreenchange',function(){if(document.fullscreenElement){var cw=cv.width,ch=cv.height,s=Math.min(window.innerWidth/cw,window.innerHeight/ch);cv.style.position='fixed';cv.style.left=Math.round((window.innerWidth-cw*s)/2)+'px';cv.style.top=Math.round((window.innerHeight-ch*s)/2)+'px';cv.style.transform='scale('+s+')';cv.style.transformOrigin='0 0';document.body.style.background='#000';b.textContent='✕';}else{cv.style.position='';cv.style.left='';cv.style.top='';cv.style.transform='';cv.style.transformOrigin='';b.textContent='⛶';}});document.body.appendChild(b);})();
</script></body></html>"""

# ── Game 8: Striker FC (FIFA-style soccer) ───────────────────────────────────
_SOCCER_HTML = r"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Bangers&family=Rajdhani:wght@600;700&display=swap" rel="stylesheet">
<style>*{margin:0;padding:0;box-sizing:border-box;}body{background:#05090f;overflow:hidden;}canvas{display:block;}</style>
</head><body><canvas id="g"></canvas><script>
const cvs=document.getElementById('g');const cx=cvs.getContext('2d');
const W=cvs.width=Math.min(1100,window.innerWidth-4);const H=cvs.height=560;
const PX=W*.07,PY=H*.09,PW=W*.86,PH=H*.82,PR=PX+PW,PB=PY+PH,PCX=PX+PW/2,PCY=PY+PH/2;
const GW=PW*.24,GD=24;
const ball={x:PCX,y:PCY,vx:0,vy:0,r:11,spin:0};
const P1_JN='__SC_P1JN__',AI_JN='__SC_AI_JN__',AI_PNAME='__SC_AI_NAME__';
const p1={x:PCX,y:PCY+PH*.28,vx:0,vy:0,walk:0,hasBall:false,team:'blue',cd:0,name:'__SC_NAME__'};
const ai={x:PCX,y:PCY-PH*.28,vx:0,vy:0,walk:0,hasBall:false,team:'red',cd:0,ptx:PCX,ptTimer:0};
const gk={x:PCX,y:PB-30,walk:0,team:'red',cd:0,isGK:true};
let score={p:0,a:0},timer=180,tFrame=0,phase='play';
let goalTimer=0,goalTeam='',frame=0,trail=[];
let keys={},hitFX=[];
const P1SPD=__SC_P1SPD__,AISPD=__SC_AI_SPD__,GKSPD=5.5,FRIC=0.87,KICK=__SC_P1KICK__,AIKICK=__SC_AI_KICK__,POSS=30;
function dst(a,b){return Math.hypot(a.x-b.x,a.y-b.y);}
function clamp(v,lo,hi){return Math.max(lo,Math.min(hi,v));}
function drawPitch(){
  let bg=cx.createRadialGradient(PCX,PCY,0,PCX,PCY,Math.max(PW,PH)*.68);
  bg.addColorStop(0,'#2a8a2a');bg.addColorStop(.45,'#236023');bg.addColorStop(1,'#133813');
  cx.fillStyle=bg;cx.fillRect(PX,PY,PW,PH);
  for(let i=0;i<10;i++){if(i%2===0){cx.fillStyle='rgba(0,0,0,0.055)';cx.fillRect(PX,PY+i*(PH/10),PW,PH/10);}}
  cx.strokeStyle='rgba(255,255,255,.92)';cx.lineWidth=2.5;
  cx.strokeRect(PX,PY,PW,PH);
  cx.beginPath();cx.moveTo(PX,PCY);cx.lineTo(PR,PCY);cx.stroke();
  cx.beginPath();cx.arc(PCX,PCY,PH*.13,0,Math.PI*2);cx.stroke();
  cx.fillStyle='#fff';cx.beginPath();cx.arc(PCX,PCY,4,0,Math.PI*2);cx.fill();
  let paW=PW*.42,paH=PH*.17,gbW=PW*.22,gbH=PH*.08;
  cx.strokeRect(PCX-paW/2,PY,paW,paH);cx.strokeRect(PCX-paW/2,PB-paH,paW,paH);
  cx.strokeRect(PCX-gbW/2,PY,gbW,gbH);cx.strokeRect(PCX-gbW/2,PB-gbH,gbW,gbH);
  cx.fillStyle='#fff';
  cx.beginPath();cx.arc(PCX,PY+PH*.13,3,0,Math.PI*2);cx.fill();
  cx.beginPath();cx.arc(PCX,PB-PH*.13,3,0,Math.PI*2);cx.fill();
  [[PX,PY,0,Math.PI/2],[PR,PY,Math.PI/2,Math.PI],[PX,PB,-Math.PI/2,0],[PR,PB,Math.PI,Math.PI*1.5]].forEach(([ax,ay,sa,ea])=>{
    cx.beginPath();cx.arc(ax,ay,14,sa,ea);cx.stroke();
  });
  let gc1=cx.createLinearGradient(0,PY-GD,0,PY);gc1.addColorStop(0,'rgba(80,255,80,.3)');gc1.addColorStop(1,'rgba(255,255,255,.08)');
  cx.fillStyle=gc1;cx.fillRect(PCX-GW/2,PY-GD,GW,GD);cx.strokeStyle='#fff';cx.lineWidth=2;cx.strokeRect(PCX-GW/2,PY-GD,GW,GD);
  let gc2=cx.createLinearGradient(0,PB,0,PB+GD);gc2.addColorStop(0,'rgba(255,255,255,.08)');gc2.addColorStop(1,'rgba(255,80,80,.3)');
  cx.fillStyle=gc2;cx.fillRect(PCX-GW/2,PB,GW,GD);cx.strokeStyle='#fff';cx.strokeRect(PCX-GW/2,PB,GW,GD);
  cx.textAlign='center';
  cx.fillStyle='rgba(100,255,100,.75)';cx.font='bold 9px Rajdhani,sans-serif';cx.fillText('▲ ATTACK HERE',PCX,PY-GD-5);
  cx.fillStyle='rgba(255,100,100,.75)';cx.fillText('▼ DEFEND HERE',PCX,PB+GD+12);
  let vig=cx.createRadialGradient(PCX,PCY,PH*.3,PCX,PCY,Math.max(PW,PH)*.8);
  vig.addColorStop(0,'rgba(0,0,0,0)');vig.addColorStop(1,'rgba(0,0,0,.4)');
  cx.fillStyle=vig;cx.fillRect(0,0,W,H);cx.textAlign='left';
}
function drawCrowd(){
  cx.fillStyle='rgba(3,6,18,.95)';
  cx.fillRect(0,0,W,PY-1);cx.fillRect(0,PB+1,W,H-PB);
  cx.fillRect(0,0,PX-1,H);cx.fillRect(PR+1,0,W-PR,H);
  for(let i=0;i<=Math.floor(PW/19);i++){
    let bx=PX+i*19,ph=Math.random,wave=Math.sin(frame*.04+i*.6)*.8;
    let c1=`hsl(${220+i%40},${40+i%20}%,${15+i%12}%)`;
    cx.fillStyle=c1;
    cx.beginPath();cx.arc(bx,PY-11+wave,5+i%3,0,Math.PI*2);cx.fill();
    cx.fillRect(bx-4,PY-7+wave,8,9);
    cx.fillStyle=`hsl(${200+i%60},${30+i%25}%,${12+i%10}%)`;
    cx.beginPath();cx.arc(bx,PB+18+wave,5+i%4,0,Math.PI*2);cx.fill();
    cx.fillRect(bx-4,PB+22+wave,8,9);
  }
  for(let i=0;i<=Math.floor(PH/21);i++){
    let by=PY+i*21,wave=Math.sin(frame*.04+i*.7)*.8;
    cx.fillStyle=`hsl(${230+i%35},${35+i%20}%,${14+i%11}%)`;
    cx.beginPath();cx.arc(PX-14+wave,by,5+i%3,0,Math.PI*2);cx.fill();
    cx.beginPath();cx.arc(PR+14-wave,by,5+i%4,0,Math.PI*2);cx.fill();
  }
}
function drawPlayer(obj){
  let{x,y,walk,hasBall,team,isGK}=obj;
  let wk=Math.sin(walk)*13;
  let sk=team==='blue'?'#1565c0':'#b71c1c';
  let sh=team==='blue'?'#1e88e5':'#e53935';
  if(isGK){sk='#e65100';sh='#ff6d00';}
  cx.fillStyle='rgba(0,0,0,.28)';cx.beginPath();cx.ellipse(x,y+33,16,6,0,0,Math.PI*2);cx.fill();
  cx.strokeStyle=sk==='#1565c0'?'#0d47a1':'#7f0000';cx.lineWidth=5;cx.lineCap='round';
  cx.beginPath();cx.moveTo(x-5,y+10);cx.lineTo(x-5+wk,y+29);cx.stroke();
  cx.beginPath();cx.moveTo(x+5,y+10);cx.lineTo(x+5-wk,y+29);cx.stroke();
  cx.strokeStyle='#111';cx.lineWidth=6;
  cx.beginPath();cx.moveTo(x-5+wk,y+29);cx.lineTo(x-3+wk+(wk>0?4:-2),y+33);cx.stroke();
  cx.beginPath();cx.moveTo(x+5-wk,y+29);cx.lineTo(x+7-wk+(wk<0?4:-2),y+33);cx.stroke();
  cx.fillStyle=sh;cx.fillRect(x-13,y-18,26,30);
  cx.fillStyle=sk;cx.fillRect(x-5,y-18,10,8);
  cx.strokeStyle=sh;cx.lineWidth=7;cx.lineCap='round';
  cx.beginPath();cx.moveTo(x-13,y-13);cx.lineTo(x-22,y-4+Math.sin(walk)*5);cx.stroke();
  cx.beginPath();cx.moveTo(x+13,y-13);cx.lineTo(x+22,y-4-Math.sin(walk)*5);cx.stroke();
  cx.fillStyle='#f4c27a';
  cx.beginPath();cx.arc(x-22,y-4+Math.sin(walk)*5,4,0,Math.PI*2);cx.fill();
  cx.beginPath();cx.arc(x+22,y-4-Math.sin(walk)*5,4,0,Math.PI*2);cx.fill();
  cx.fillStyle='#f4c27a';cx.beginPath();cx.arc(x,y-28,13,0,Math.PI*2);cx.fill();
  cx.fillStyle=team==='blue'?'#2c1a08':'#0d0d0d';
  cx.beginPath();cx.arc(x,y-30,12,Math.PI+.3,-.3);cx.fill();
  cx.fillStyle='#fff';cx.font='bold 10px Arial';cx.textAlign='center';
  cx.fillText(isGK?'GK':team==='blue'?P1_JN:AI_JN,x,y-1);
  if(hasBall){cx.strokeStyle='#FFD100';cx.lineWidth=2.5;cx.setLineDash([4,3]);cx.beginPath();cx.arc(x,y,26,0,Math.PI*2);cx.stroke();cx.setLineDash([]);}
  cx.textAlign='left';
}
function drawBall(){
  let spd=Math.hypot(ball.vx,ball.vy);
  trail.push({x:ball.x,y:ball.y,a:Math.min(spd*.05,.45)});
  if(trail.length>14)trail.shift();
  trail.forEach((t,i)=>{let a=t.a*(i/trail.length)*.6;cx.fillStyle=`rgba(255,255,255,${a})`;cx.beginPath();cx.arc(t.x,t.y,ball.r*.55,0,Math.PI*2);cx.fill();});
  cx.fillStyle='rgba(0,0,0,.3)';cx.beginPath();cx.ellipse(ball.x+3,ball.y+14,10,4,0,0,Math.PI*2);cx.fill();
  let bg=cx.createRadialGradient(ball.x-3,ball.y-3,1,ball.x,ball.y,ball.r);
  bg.addColorStop(0,'#fff');bg.addColorStop(.7,'#e8e8e8');bg.addColorStop(1,'#bbb');
  cx.fillStyle=bg;cx.beginPath();cx.arc(ball.x,ball.y,ball.r,0,Math.PI*2);cx.fill();
  cx.fillStyle='#111';cx.beginPath();cx.arc(ball.x,ball.y,ball.r*.34,0,Math.PI*2);cx.fill();
  for(let i=0;i<5;i++){let a=i/5*Math.PI*2+ball.spin;cx.fillStyle='#1a1a1a';cx.beginPath();cx.arc(ball.x+Math.cos(a)*ball.r*.68,ball.y+Math.sin(a)*ball.r*.68,3.2,0,Math.PI*2);cx.fill();}
  cx.fillStyle='rgba(255,255,255,.55)';cx.beginPath();cx.arc(ball.x-4,ball.y-4,3.5,0,Math.PI*2);cx.fill();
}
function drawHUD(){
  cx.fillStyle='rgba(0,0,15,.9)';cx.fillRect(0,0,W,H*.085);
  cx.fillStyle='#1e88e5';cx.font='bold 20px Bangers,sans-serif';cx.textAlign='right';cx.fillText('🟦 '+p1.name.toUpperCase(),W*.41,H*.068);
  cx.fillStyle='#64b5f6';cx.font='bold 32px Bangers,sans-serif';cx.fillText(score.p,W*.47,H*.068);
  cx.fillStyle='rgba(255,255,255,.65)';cx.font='bold 22px Bangers,sans-serif';cx.textAlign='center';cx.fillText('—',W*.50,H*.068);
  cx.fillStyle='#ef5350';cx.font='bold 32px Bangers,sans-serif';cx.textAlign='left';cx.fillText(score.a,W*.53,H*.068);
  cx.fillStyle='#e53935';cx.font='bold 20px Bangers,sans-serif';cx.fillText('🟥 '+AI_PNAME.toUpperCase(),W*.565,H*.068);
  let mins=Math.floor(timer/60),secs=timer%60;
  let tc=timer<30?'#ff4444':'#FFD100';
  cx.fillStyle=tc;cx.font='bold 20px Bangers,sans-serif';cx.textAlign='center';
  cx.fillText(`⏱ ${mins}:${secs<10?'0':''}${secs}`,W*.50,H*.034);
  cx.fillStyle='rgba(140,160,200,.5)';cx.font='9px Rajdhani,sans-serif';
  cx.fillText('WASD / ARROWS : Move  ·  SPACE : Kick  ·  SHIFT : Sprint',W*.50,H*.088);
  cx.textAlign='left';
}
function update(){
  if(phase!=='play')return;
  tFrame++;if(tFrame>=60){tFrame=0;timer--;if(timer<=0){timer=0;phase='end';}}
  let dx=0,dy=0;
  if(keys['KeyW']||keys['ArrowUp'])dy=-1;
  if(keys['KeyS']||keys['ArrowDown'])dy=1;
  if(keys['KeyA']||keys['ArrowLeft'])dx=-1;
  if(keys['KeyD']||keys['ArrowRight'])dx=1;
  let sp=(keys['ShiftLeft']||keys['ShiftRight'])?1.6:1;
  if(dx||dy){let l=Math.hypot(dx,dy);p1.x=clamp(p1.x+dx/l*P1SPD*sp,PX+15,PR-15);p1.y=clamp(p1.y+dy/l*P1SPD*sp,PY+15,PB-15);p1.walk+=.22*sp;}
  else p1.walk+=.04;
  if(keys['Space']&&p1.cd<=0&&dst(p1,ball)<POSS+ball.r){
    let tx=PCX+(Math.random()-.5)*GW*.55,ty=PY-GD/2;
    let kl=Math.hypot(tx-p1.x,ty-p1.y)||1;
    ball.vx=(tx-p1.x)/kl*KICK+(Math.random()-.5)*2.5;ball.vy=(ty-p1.y)/kl*KICK+(Math.random()-.5)*2.5;
    p1.hasBall=false;p1.cd=22;
    hitFX.push({x:ball.x,y:ball.y,l:20,ml:20,txt:'KICK!'});
  }
  if(p1.cd>0)p1.cd--;
  // AI field player
  ai.ptTimer++;if(ai.ptTimer>90){ai.ptTimer=0;ai.patrolX=PCX+(Math.random()-.5)*PW*.45;}
  let tgtX=ball.x,tgtY=ball.y;
  if(ball.y<PCY)tgtY=ball.y;
  let ad=Math.hypot(tgtX-ai.x,tgtY-ai.y)||1;
  let ais=AISPD*(ball.y>PCY?1.25:1.0);
  ai.x=clamp(ai.x+(tgtX-ai.x)/ad*ais,PX+15,PR-15);
  ai.y=clamp(ai.y+(tgtY-ai.y)/ad*ais,PY+15,PB-15);
  ai.walk+=.18;
  if(ai.cd<=0&&dst(ai,ball)<POSS+ball.r){
    let tx=PCX+(Math.random()-.5)*GW*.65,ty=PB+GD/2;
    let kl=Math.hypot(tx-ai.x,ty-ai.y)||1;
    ball.vx=(tx-ai.x)/kl*AIKICK+(Math.random()-.5)*2.5;ball.vy=(ty-ai.y)/kl*AIKICK+(Math.random()-.5)*2.5;
    ai.cd=45;
  }
  if(ai.cd>0)ai.cd--;
  // GK tracks ball on x
  let gkTgt=clamp(ball.x,PCX-GW/2+12,PCX+GW/2-12);
  gk.x+=(gkTgt-gk.x)*0.07*GKSPD*.18;gk.x=clamp(gk.x,PCX-GW/2+12,PCX+GW/2-12);
  gk.y=PB-30;gk.walk+=.12;
  if(gk.cd<=0&&dst(gk,ball)<POSS+ball.r+4&&ball.y>PB-PH*.18){
    let tx=PCX+(Math.random()-.5)*PW*.4,ty=PCY+(Math.random()-.5)*PH*.2;
    let kl=Math.hypot(tx-gk.x,ty-gk.y)||1;
    ball.vx=(tx-gk.x)/kl*AIKICK*1.2;ball.vy=(ty-gk.y)/kl*AIKICK*1.2;gk.cd=30;
  }
  if(gk.cd>0)gk.cd--;
  // Ball physics
  ball.spin+=Math.hypot(ball.vx,ball.vy)*.05;
  ball.x+=ball.vx;ball.y+=ball.vy;ball.vx*=FRIC;ball.vy*=FRIC;
  if(Math.abs(ball.vx)<.05)ball.vx=0;if(Math.abs(ball.vy)<.05)ball.vy=0;
  if(ball.x<PX+ball.r){ball.x=PX+ball.r;ball.vx*=-.65;}
  if(ball.x>PR-ball.r){ball.x=PR-ball.r;ball.vx*=-.65;}
  let inTopGoal=ball.x>PCX-GW/2&&ball.x<PCX+GW/2;
  let inBotGoal=ball.x>PCX-GW/2&&ball.x<PCX+GW/2;
  if(ball.y<PY+ball.r&&!inTopGoal){ball.y=PY+ball.r;ball.vy*=-.65;}
  if(ball.y>PB-ball.r&&!inBotGoal){ball.y=PB-ball.r;ball.vy*=-.65;}
  if(ball.y<=PY-ball.r&&inTopGoal){score.p++;goalTeam='p';goalTimer=160;phase='goal';resetKickoff();}
  if(ball.y>=PB+ball.r&&inBotGoal){score.a++;goalTeam='a';goalTimer=160;phase='goal';resetKickoff();}
  p1.hasBall=dst(p1,ball)<POSS+ball.r;ai.hasBall=dst(ai,ball)<POSS+ball.r;
  hitFX=hitFX.filter(h=>{h.l--;h.y-=.8;return h.l>0;});
}
function resetKickoff(){
  ball.x=PCX;ball.y=PCY;ball.vx=0;ball.vy=0;trail=[];
  p1.x=PCX-50;p1.y=PCY+PH*.28;ai.x=PCX+40;ai.y=PCY-PH*.28;gk.x=PCX;
  setTimeout(()=>{if(timer>0)phase='play';},2600);
}
function draw(){
  cx.clearRect(0,0,W,H);cx.fillStyle='#05090f';cx.fillRect(0,0,W,H);
  drawCrowd();drawPitch();
  let objs=[{t:'p1',y:p1.y},{t:'ai',y:ai.y},{t:'gk',y:gk.y},{t:'ball',y:ball.y}];
  objs.sort((a,b)=>a.y-b.y);
  objs.forEach(o=>{
    if(o.t==='ball')drawBall();
    else if(o.t==='p1')drawPlayer(p1);
    else if(o.t==='ai')drawPlayer(ai);
    else drawPlayer(gk);
  });
  let nearBall=dst(p1,ball)<POSS+ball.r+20&&p1.cd<=0&&phase==='play';
  if(nearBall){cx.fillStyle='rgba(255,215,0,.9)';cx.font='bold 13px Rajdhani,sans-serif';cx.textAlign='center';cx.fillText('⚽ SPACE TO KICK',ball.x,ball.y-26);cx.textAlign='left';}
  hitFX.forEach(h=>{let a=h.l/h.ml;cx.save();cx.globalAlpha=a;cx.fillStyle='#FFD100';cx.font='bold 18px Bangers,sans-serif';cx.textAlign='center';cx.fillText(h.txt,h.x,h.y);cx.restore();});
  drawHUD();
  if(phase==='goal'){
    goalTimer--;
    let a=Math.min(1,goalTimer/60);
    cx.fillStyle=goalTeam==='p'?`rgba(30,100,255,${a*.4})`:`rgba(255,40,40,${a*.4})`;cx.fillRect(0,0,W,H);
    cx.textAlign='center';cx.fillStyle='#FFD100';cx.shadowColor='#FFD100';cx.shadowBlur=35;
    cx.font='bold 78px Bangers,sans-serif';cx.fillText('⚽ GOAL!',W/2,H*.42);cx.shadowBlur=0;
    cx.fillStyle='#fff';cx.font='bold 26px Rajdhani,sans-serif';
    cx.fillText(goalTeam==='p'?p1.name.toUpperCase()+' SCORES! 🎉':AI_PNAME.toUpperCase()+' SCORES! 🤖',W/2,H*.56);
    cx.textAlign='left';
    if(goalTimer<=0){phase=timer>0?'play':'end';}
  }
  if(phase==='end'){
    cx.fillStyle='rgba(0,0,20,.88)';cx.fillRect(0,0,W,H);
    let w=score.p>score.a?'🏆 '+p1.name.toUpperCase()+' WINS!':score.a>score.p?'🏆 '+AI_PNAME.toUpperCase()+' WINS!':'🤝 IT\'S A DRAW!';
    let wc=score.p>score.a?'#4da6ff':score.a>score.p?'#ff5252':'#FFD100';
    cx.fillStyle=wc;cx.shadowColor=wc;cx.shadowBlur=28;cx.font='bold 62px Bangers,sans-serif';cx.textAlign='center';
    cx.fillText(w,W/2,H*.42);cx.shadowBlur=0;
    cx.fillStyle='#fff';cx.font='bold 26px Bangers,sans-serif';cx.fillText('FINAL: '+score.p+' — '+score.a,W/2,H*.57);
    cx.fillStyle='rgba(255,255,255,.5)';cx.font='14px Rajdhani,sans-serif';cx.fillText('Press R to play again',W/2,H*.70);
    cx.textAlign='left';
  }
  update();frame++;requestAnimationFrame(draw);
}
document.addEventListener('keydown',e=>{
  keys[e.code]=true;
  if(e.code==='Space')e.preventDefault();
  if(e.code==='KeyR'&&phase==='end'){score={p:0,a:0};timer=180;tFrame=0;phase='play';resetKickoff();}
});
document.addEventListener('keyup',e=>{keys[e.code]=false;});
(function(){var b=document.createElement('button');b.textContent='⛶';b.title='Fullscreen';b.style.cssText='position:fixed;top:8px;right:8px;z-index:9999;background:rgba(0,0,20,.8);color:#fff;border:1.5px solid rgba(255,255,255,.3);border-radius:7px;padding:5px 10px;font-size:16px;cursor:pointer;';var cv=document.getElementById('g');b.onclick=function(){if(!document.fullscreenElement){document.documentElement.requestFullscreen().catch(function(){});}else{document.exitFullscreen();}};document.addEventListener('fullscreenchange',function(){if(document.fullscreenElement){var cw=cv.width,ch=cv.height,s=Math.min(window.innerWidth/cw,window.innerHeight/ch);cv.style.position='fixed';cv.style.left=Math.round((window.innerWidth-cw*s)/2)+'px';cv.style.top=Math.round((window.innerHeight-ch*s)/2)+'px';cv.style.transform='scale('+s+')';cv.style.transformOrigin='0 0';document.body.style.background='#000';b.textContent='✕';}else{cv.style.position='';cv.style.left='';cv.style.top='';cv.style.transform='';cv.style.transformOrigin='';b.textContent='⛶';}});document.body.appendChild(b);})();
draw();
</script></body></html>"""

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
    defs={"game_mode":None,"sp_skin":None,"sp_w1":None,"sp_w2":None,"sp_name":"",
          "lc_n1":"","lc_n2":"","lc_s1":skin_names[0],"lc_s2":skin_names[1],
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
st.markdown("""<style>
/* Kill the white Streamlit header bar */
header,header[data-testid="stHeader"]{display:none!important;height:0!important;min-height:0!important;}
div[data-testid="stDecoration"]{display:none!important;}
#MainMenu{display:none!important;}
footer{display:none!important;}
/* Full-page dark background */
html,body,.stApp{background:linear-gradient(160deg,#050d2a 0%,#091535 55%,#0a1a40 100%)!important;}
div[data-testid="stAppViewContainer"]{background:transparent!important;}
/* Content container */
.block-container{padding-top:0.6rem!important;padding-bottom:1rem!important;max-width:1200px!important;}
/* Gold primary buttons */
button[data-testid="baseButton-primary"]{background:linear-gradient(135deg,#e6a800,#FFD100)!important;color:#050a1a!important;font-family:'Bangers',sans-serif!important;letter-spacing:3px!important;font-size:15px!important;border:none!important;border-radius:8px!important;}
button[data-testid="baseButton-primary"]:hover{background:linear-gradient(135deg,#FFD100,#ffe55c)!important;}
/* Blue secondary buttons */
button[data-testid="baseButton-secondary"]{background:rgba(5,15,50,.8)!important;color:#40c4ff!important;font-family:'Bangers',sans-serif!important;letter-spacing:2px!important;border:1px solid rgba(64,196,255,.35)!important;border-radius:8px!important;}
button[data-testid="baseButton-secondary"]:hover{background:rgba(20,50,120,.8)!important;border-color:#40c4ff!important;}
/* Fullscreen button */
#_fsbtn{position:fixed;top:10px;right:14px;z-index:2147483647;background:rgba(3,8,28,.92);color:#40c4ff;border:1.5px solid rgba(64,196,255,.45);border-radius:8px;padding:7px 16px;font-size:13px;cursor:pointer;font-family:sans-serif;letter-spacing:1px;backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);}
#_fsbtn:hover{background:rgba(10,25,80,.95);border-color:#40c4ff;}
</style>
<button id="_fsbtn" onclick="(function(b){if(!document.fullscreenElement){document.documentElement.requestFullscreen().then(function(){b.innerHTML='&#x2715; EXIT FULL';}).catch(function(e){alert('Fullscreen not supported: '+e.message);});}else{document.exitFullscreen().then(function(){b.innerHTML='&#x26f6; FULLSCREEN';});}document.addEventListener('fullscreenchange',function(){b.innerHTML=document.fullscreenElement?'&#x2715; EXIT FULL':'&#x26f6; FULLSCREEN';},{once:false});}).call(this,this);">&#x26f6; FULLSCREEN</button>
""", unsafe_allow_html=True)
st.markdown("""<div style="text-align:center;padding:18px 0 6px;">
<div style="font-family:'Bangers',sans-serif;font-size:46px;letter-spacing:8px;color:#fff;
text-shadow:-2px -2px 0 #000,2px -2px 0 #000,-2px 2px 0 #000,2px 2px 0 #000,
0 0 40px rgba(255,209,0,.8),0 0 80px rgba(255,100,0,.3);">💥 FORTNITE BATTLE SIMULATOR</div>
<div style="font-family:'Rajdhani',sans-serif;font-size:12px;letter-spacing:5px;color:rgba(150,180,255,.55);margin-top:4px;">BATTLE · SURVIVE · WIN</div>
</div>""", unsafe_allow_html=True)
st.markdown('<div style="border:none;border-top:1px solid rgba(64,196,255,.18);margin:4px 0 18px;"></div>',unsafe_allow_html=True)

LOG_C={"hit":"#00e676","crit":"#FFD100","miss":"#6688aa","ability":"#ff4da6","win":"#FF5722","lose":"#ff1744"}

# ════════════════════════════════════
# MAIN MENU
# ════════════════════════════════════
if st.session_state.game_mode is None:
    # ── Classic Modes ─────────────────────────────────────────────────────────
    st.markdown("""<div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;">
<div style="flex:1;height:1px;background:linear-gradient(90deg,transparent,rgba(255,200,0,.4));"></div>
<div style="font-family:'Bangers',sans-serif;font-size:18px;letter-spacing:6px;color:#FFD100;">CLASSIC MODES</div>
<div style="flex:1;height:1px;background:linear-gradient(90deg,rgba(255,200,0,.4),transparent);"></div>
</div>""", unsafe_allow_html=True)
    mc1,mc2,mc3=st.columns(3,gap="medium")
    for col,icon,title,desc,mode,badge in [
        (mc1,"🏰","DEFEND THE KINGDOM","Solo vs 7 waves of AI enemies. Storm closes in, boss charges, supply drops!","lobby_sp","SOLO"),
        (mc2,"🖥️","2-PLAYER SAME SCREEN","Two players, one PC. Storm closes in. Jump to dodge bullets! Shields + medkits!","lobby_2p_local","2P LOCAL"),
        (mc3,"🌐","2-PLAYER ONLINE","Different computers. Real-time online battle. BUILD cover · MEDKIT · Storm!","lobby_2p_online","2P ONLINE"),
    ]:
        with col:
            st.markdown(f"""<div style="background:linear-gradient(160deg,rgba(8,16,55,.95),rgba(5,10,38,.98));border:2px solid rgba(255,200,0,.35);border-radius:14px;padding:20px 16px 14px;text-align:center;height:160px;display:flex;flex-direction:column;align-items:center;justify-content:center;position:relative;box-shadow:0 4px 24px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.06);">
<div style="position:absolute;top:10px;right:12px;background:rgba(255,200,0,.18);border:1px solid rgba(255,200,0,.4);border-radius:4px;padding:2px 7px;font-family:'Bangers',sans-serif;font-size:9px;letter-spacing:2px;color:#FFD100;">{badge}</div>
<div style="font-size:40px;margin-bottom:6px;">{icon}</div>
<div style="font-family:'Bangers',sans-serif;font-size:17px;letter-spacing:3px;color:#FFD100;margin-bottom:6px;">{title}</div>
<div style="font-size:9.5px;color:rgba(180,200,240,.7);line-height:1.5;">{desc}</div>
</div>""", unsafe_allow_html=True)
            if st.button("▶  PLAY",key=f"m_{mode}",use_container_width=True,type="primary"):
                st.session_state.game_mode=mode; st.rerun()
    # ── Bonus Games ───────────────────────────────────────────────────────────
    st.markdown("""<div style="display:flex;align-items:center;gap:14px;margin:22px 0 14px;">
<div style="flex:1;height:1px;background:linear-gradient(90deg,transparent,rgba(64,196,255,.35));"></div>
<div style="font-family:'Bangers',sans-serif;font-size:18px;letter-spacing:6px;color:#40c4ff;">BONUS GAMES</div>
<div style="flex:1;height:1px;background:linear-gradient(90deg,rgba(64,196,255,.35),transparent);"></div>
</div>""", unsafe_allow_html=True)
    bg1,bg2,bg3,bg4,bg5=st.columns(5,gap="small")
    for col,icon,title,desc,mode in [
        (bg1,"🎯","SNIPER\nSHOWDOWN","2P timing duel. Hit when scope centers. 5 HP each!","lobby_sniper"),
        (bg2,"🏃","STORM\nSPRINT","Endless runner! Double-jump & outrun the storm!","lobby_sprint"),
        (bg3,"🎯","TARGET\nBLITZ","Click bullseyes. Build combos. 60 sec. Go LEGENDARY!","lobby_blitz"),
        (bg4,"🗺️","ZONE\nWARS","Top-down. WASD + mouse. 4 AI enemies. Storm in!","lobby_zone"),
        (bg5,"⚽","STRIKER\nFC","FC 26-style soccer! Pick Messi or Ronaldo. Score!","lobby_soccer"),
    ]:
        with col:
            t_lines=title.split('\n')
            t_html=f'<span style="display:block;line-height:1.1;">{t_lines[0]}</span><span style="display:block;line-height:1.1;">{t_lines[1]}</span>'
            st.markdown(f"""<div style="background:linear-gradient(160deg,rgba(6,12,45,.95),rgba(4,8,35,.98));border:2px solid rgba(64,196,255,.25);border-radius:12px;padding:14px 8px 10px;text-align:center;height:148px;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;box-shadow:0 4px 18px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.04);">
<div style="font-size:28px;margin-bottom:5px;">{icon}</div>
<div style="font-family:'Bangers',sans-serif;font-size:13px;letter-spacing:2px;color:#40c4ff;margin-bottom:5px;">{t_html}</div>
<div style="font-size:8.5px;color:rgba(140,165,210,.65);line-height:1.45;overflow:hidden;">{desc}</div>
</div>""", unsafe_allow_html=True)
            if st.button("PLAY",key=f"m_{mode}",use_container_width=True):
                st.session_state.game_mode=mode; st.rerun()
    # ── Controls footer ───────────────────────────────────────────────────────
    st.markdown('<div style="border-top:1px solid rgba(64,196,255,.12);margin:20px 0 8px;"></div>',unsafe_allow_html=True)
    with st.expander("📖 Controls & Tips",expanded=False):
        st.markdown("""
**🏰 Defend the Kingdom:** `WASD` Move · `F`/`Space` Shoot · `1`/`2` Switch gun · Storm closes every wave

**🖥️ 2P Same Screen:** P1 `WASD`+`F`+`Q` jump · P2 `Arrows`+`L`+`/` jump · Aerial dodge when jumping!

**🌐 2P Online:** Click enemy to shoot · `💊 MEDKIT` heals 70 HP · `🏗️ BUILD` for cover · Storm after turn 6

**🎯 Sniper Showdown:** `Space` (P1) · `Enter` (P2) · Fire when crosshair is centred · Headshot = 3 damage

**🏃 Storm Sprint:** `Space`/`W`/`↑` Jump (double-jump!) · Outrun the purple wall · Collect crates for HP

**🎯 Target Blitz:** Click targets before they vanish · Chain hits to build combo multiplier

**🗺️ Zone Wars:** `WASD` Move · Mouse aim + click to shoot · Collect loot · Stay in safe zone

**⚽ Striker FC:** `WASD`/`Arrows` Move · `Space` Kick · `Shift` Sprint · Pick from 10 real players
""")

# ── SP Lobby ──────────────────────────────────────────────────────────────────
elif st.session_state.game_mode=="lobby_sp":
    st.markdown("### 🏰 DEFEND THE KINGDOM — SOLO (HARD)")
    c1,c2=st.columns([1,2])
    with c1:
        spn=st.text_input("Your Name",value="",placeholder="Enter your name",key="spni",max_chars=14)
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
        n1=st.text_input("Name",value="",placeholder="P1 name",key="lc_n1_in",max_chars=14)
        s1=st.selectbox("Skin",skin_names,key="lcs1")
        w1a=st.selectbox("🔫 Gun 1 [Z]",weapon_names,index=0,key="lcw1a")
        w1b=st.selectbox("💣 Gun 2 [X]",weapon_names,index=1,key="lcw1b")
    with c2:
        st.markdown("#### 🟥 Player 2 (Arrows + L to shoot)")
        n2=st.text_input("Name",value="",placeholder="P2 name",key="lc_n2_in",max_chars=14)
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
        on_n=st.text_input("Your Name",value="",placeholder="Enter your name",key="on_name_in",max_chars=14)
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

# ════════════════════════════════════
# BONUS GAME LOBBIES + GAMES
# ════════════════════════════════════

# ── Sniper Showdown ───────────────────────────────────────────────────────────
elif st.session_state.game_mode=="lobby_sniper":
    st.markdown("### 🎯 SNIPER SHOWDOWN — 2 PLAYERS (SAME SCREEN)")
    st.info("Each player has a wobbling scope. Press your key exactly when the crosshair is **most centred** on the target. Headshots do 3 damage, clean hits 2, glances 1. First to reduce opponent to 0 HP wins!")
    c1,c2=st.columns(2)
    with c1:
        st.markdown("**🟦 Player 1** — key: `SPACE`")
        n1=st.text_input("P1 Name",value="",placeholder="Enter name",key="sn_n1",max_chars=12)
    with c2:
        st.markdown("**🟥 Player 2** — key: `ENTER`")
        n2=st.text_input("P2 Name",value="",placeholder="Enter name",key="sn_n2",max_chars=12)
    col_l,col_r=st.columns([1,3])
    with col_l:
        if st.button("🎯 DUEL!",type="primary",use_container_width=True,key="sn_start"):
            st.session_state["sn_p1"]=n1; st.session_state["sn_p2"]=n2
            st.session_state.game_mode="sniper_game"; st.rerun()
    with col_r:
        if st.button("🏠 MENU",key="sn_back"): full_reset(); st.rerun()

elif st.session_state.game_mode=="sniper_game":
    n1=st.session_state.get("sn_p1","P1"); n2=st.session_state.get("sn_p2","P2")
    html=_SNIPER_HTML.replace("__SN_P1__",n1.replace('"','')).replace("__SN_P2__",n2.replace('"',''))
    components.html(html,height=555)
    if st.button("🏠 BACK TO MENU",key="sn_quit"): full_reset(); st.rerun()

# ── Storm Sprint ──────────────────────────────────────────────────────────────
elif st.session_state.game_mode=="lobby_sprint":
    st.markdown("### 🏃 STORM SPRINT — ENDLESS RUNNER")
    st.info("The storm chases you from the left and accelerates! Double-jump over obstacles (rocks, trees, gaps). Collect loot crates for extra HP/shields. How far can you run?")
    c1,c2=st.columns([1,3])
    with c1:
        nm=st.text_input("Your Name",value="",placeholder="Enter name",key="sp_nm",max_chars=12)
        if st.button("🏃 RUN!",type="primary",use_container_width=True,key="sp_start"):
            st.session_state["sprint_name"]=nm
            st.session_state.game_mode="sprint_game"; st.rerun()
    with c2:
        st.markdown("""**Controls:** `SPACE` / `W` / `↑` = Jump (press twice for double jump!)

**Tips:** 🌲 Jump over trees · 🪨 Jump over rocks · ⚠️ Don't fall in gaps · 📦 Collect crates!

**Scoring:** Distance run = score. Storm keeps speeding up!""")
    if st.button("🏠 MENU",key="sp_back"): full_reset(); st.rerun()

elif st.session_state.game_mode=="sprint_game":
    nm=st.session_state.get("sprint_name","Runner")
    html=_SPRINT_HTML.replace("__SP_NAME__",nm.replace('"',''))
    components.html(html,height=515)
    if st.button("🏠 BACK TO MENU",key="sprint_quit"): full_reset(); st.rerun()

# ── Target Blitz ──────────────────────────────────────────────────────────────
elif st.session_state.game_mode=="lobby_blitz":
    st.markdown("### 🎯 TARGET BLITZ — AIM TRAINER ARCADE")
    st.info("Targets appear and disappear fast. Click them before they vanish! Chain hits to build a COMBO multiplier. Targets shrink and multiply as your score grows. 60 seconds — aim for LEGENDARY!")
    c1,c2=st.columns([1,3])
    with c1:
        nm=st.text_input("Your Name",value="",placeholder="Enter name",key="bl_nm",max_chars=12)
        if st.button("🎯 PLAY!",type="primary",use_container_width=True,key="bl_start"):
            st.session_state["blitz_name"]=nm
            st.session_state.game_mode="blitz_game"; st.rerun()
    with c2:
        st.markdown("""**Controls:** Just `mouse click` on the targets!

| Score | Rank |
|-------|------|
| 0–499 | Trainee |
| 500–1499 | Marksman |
| 1500–2999 | Sharpshooter |
| 3000–4999 | Sniper Elite |
| 5000+ | 🏅 LEGENDARY AIM |""")
    if st.button("🏠 MENU",key="bl_back"): full_reset(); st.rerun()

elif st.session_state.game_mode=="blitz_game":
    nm=st.session_state.get("blitz_name","Sniper")
    html=_BLITZ_HTML.replace("__BL_NAME__",nm.replace('"',''))
    components.html(html,height=555)
    if st.button("🏠 BACK TO MENU",key="blitz_quit"): full_reset(); st.rerun()

# ── Zone Wars ─────────────────────────────────────────────────────────────────
elif st.session_state.game_mode=="lobby_zone":
    st.markdown("### 🗺️ ZONE WARS — TOP-DOWN BATTLE ROYALE VS AI")
    st.info("Top-down arena. 4 AI enemies hunt you. The storm rectangle shrinks — stay inside or take damage! Collect loot for HP/shields. Eliminate all enemies to win!")
    c1,c2=st.columns([1,3])
    with c1:
        nm=st.text_input("Your Name",value="",placeholder="Enter name",key="zw_nm",max_chars=12)
        if st.button("🗺️ DROP IN!",type="primary",use_container_width=True,key="zw_start"):
            st.session_state["zone_name"]=nm
            st.session_state.game_mode="zone_game"; st.rerun()
    with c2:
        st.markdown("""**Controls:**
- `WASD` or `Arrow keys` = Move
- `SPACE` or `F` or `Click` = Shoot (aims at mouse cursor)
- Walk over glowing loot boxes to collect them

**Enemies:** 4 AI enemies (red/orange circles) chase and shoot you. The storm closes in every second!

**Tip:** Use walls for cover! Enemies can't shoot through them.""")
    if st.button("🏠 MENU",key="zw_back"): full_reset(); st.rerun()

elif st.session_state.game_mode=="zone_game":
    nm=st.session_state.get("zone_name","Player")
    html=_ZONE_HTML.replace("__ZW_NAME__",nm.replace('"',''))
    components.html(html,height=555)
    if st.button("🏠 BACK TO MENU",key="zone_quit"): full_reset(); st.rerun()

# ── Striker FC ────────────────────────────────────────────────────────────────
elif st.session_state.game_mode=="lobby_soccer":
    _SC_PLAYERS = {
        "Messi":       {"jersey":"10","speed":5.3,"kick":13.5,"flag":"🇦🇷","rating":99,"trait":"Dribble King"},
        "Ronaldo":     {"jersey":"7", "speed":4.9,"kick":15.5,"flag":"🇵🇹","rating":98,"trait":"Power Shot"},
        "Neymar":      {"jersey":"10","speed":5.1,"kick":13.0,"flag":"🇧🇷","rating":95,"trait":"Tricky Feet"},
        "Mbappé":      {"jersey":"9", "speed":5.8,"kick":14.0,"flag":"🇫🇷","rating":97,"trait":"Pace Monster"},
        "Haaland":     {"jersey":"9", "speed":4.8,"kick":16.5,"flag":"🇳🇴","rating":96,"trait":"Clinical"},
        "Bellingham":  {"jersey":"5", "speed":4.7,"kick":13.5,"flag":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","rating":94,"trait":"All-Round"},
        "Vinicius Jr": {"jersey":"7", "speed":5.5,"kick":12.5,"flag":"🇧🇷","rating":95,"trait":"Speed Wing"},
        "Lewandowski": {"jersey":"9", "speed":4.5,"kick":15.5,"flag":"🇵🇱","rating":93,"trait":"Poacher"},
        "Salah":       {"jersey":"11","speed":5.2,"kick":14.0,"flag":"🇪🇬","rating":93,"trait":"Direct"},
        "De Bruyne":   {"jersey":"17","speed":4.6,"kick":14.5,"flag":"🇧🇪","rating":94,"trait":"Playmaker"},
    }
    _sc_names = list(_SC_PLAYERS.keys())
    if "sc_p1" not in st.session_state: st.session_state.sc_p1 = "Messi"
    if "sc_ai" not in st.session_state: st.session_state.sc_ai = "Ronaldo"
    st.markdown("### ⚽ STRIKER FC — PICK YOUR PLAYER")
    st.markdown('<div style="font-family:Bangers,sans-serif;font-size:13px;letter-spacing:3px;color:#40c4ff;margin-bottom:6px;">TOP 10 WORLD PLAYERS</div>',unsafe_allow_html=True)
    lc,rc=st.columns(2)
    for side_col,side_key,side_label,sel_col,bdr_sel in [
        (lc,"sc_p1","🟦 YOUR PLAYER","#1565c0","#4da6ff"),
        (rc,"sc_ai","🟥 AI OPPONENT","#b71c1c","#ff5252"),
    ]:
        with side_col:
            st.markdown(f'<div style="font-family:Bangers,sans-serif;font-size:16px;letter-spacing:2px;color:{bdr_sel};margin-bottom:8px;">{side_label}</div>',unsafe_allow_html=True)
            rows=[_sc_names[:5],_sc_names[5:]]
            for row in rows:
                rcols=st.columns(5)
                for rcol,pname in zip(rcols,row):
                    p=_SC_PLAYERS[pname]
                    sel=st.session_state[side_key]==pname
                    bg=f"linear-gradient(135deg,{sel_col},{sel_col}cc)" if sel else "rgba(5,10,40,.9)"
                    bdr=bdr_sel if sel else "rgba(255,255,255,.12)"
                    with rcol:
                        st.markdown(f"""<div style="background:{bg};border:2px solid {bdr};border-radius:9px;padding:6px 3px;text-align:center;min-height:80px;">
<div style="font-size:22px;line-height:1.1;">{p['flag']}</div>
<div style="font-family:Bangers,sans-serif;font-size:10px;color:{'#fff' if sel else bdr_sel};letter-spacing:1px;">{pname.upper()}</div>
<div style="font-size:8px;color:{'#eee' if sel else '#667799'};margin-top:2px;">#{p['jersey']} ⭐{p['rating']}</div>
<div style="font-size:7.5px;color:{'#ffe082' if sel else '#445566'};">{p['trait']}</div></div>""",unsafe_allow_html=True)
                        if st.button("✓" if sel else "Pick",key=f"{side_key}_{pname}",use_container_width=True):
                            st.session_state[side_key]=pname; st.rerun()
    st.markdown("---")
    p1d=_SC_PLAYERS[st.session_state.sc_p1]; aid=_SC_PLAYERS[st.session_state.sc_ai]
    mu1,mu2,mu3=st.columns([2,2,1])
    with mu1:
        st.markdown(f"""**{p1d['flag']} {st.session_state.sc_p1}** #{p1d['jersey']} ⭐{p1d['rating']}
| Stat | Value |
|------|-------|
| 💨 Speed | {'●'*round(p1d['speed']-.5)+('○'*(5-round(p1d['speed']-.5)))} |
| 🦵 Power | {'●'*round(p1d['kick']/3.5)+('○'*(5-round(p1d['kick']/3.5)))} |
| ✨ Trait | {p1d['trait']} |""")
    with mu2:
        st.markdown(f"""**{aid['flag']} {st.session_state.sc_ai}** #{aid['jersey']} ⭐{aid['rating']}
| Stat | Value |
|------|-------|
| 💨 Speed | {'●'*round(aid['speed']-.5)+('○'*(5-round(aid['speed']-.5)))} |
| 🦵 Power | {'●'*round(aid['kick']/3.5)+('○'*(5-round(aid['kick']/3.5)))} |
| ✨ Trait | {aid['trait']} |""")
    with mu3:
        st.markdown("**⚽ Controls**")
        st.markdown("`WASD` Move · `SPACE` Kick · `SHIFT` Sprint · `R` Replay")
        if st.button("⚽ KICK OFF!",type="primary",use_container_width=True,key="sc_start"):
            st.session_state["soccer_p1"]=st.session_state.sc_p1
            st.session_state["soccer_ai"]=st.session_state.sc_ai
            st.session_state["soccer_p1d"]=p1d
            st.session_state["soccer_aid"]=aid
            st.session_state.game_mode="soccer_game"; st.rerun()
        if st.button("🏠 MENU",key="sc_back"): full_reset(); st.rerun()

elif st.session_state.game_mode=="soccer_game":
    p1n=st.session_state.get("soccer_p1","Messi")
    ain=st.session_state.get("soccer_ai","Ronaldo")
    p1d=st.session_state.get("soccer_p1d",{"jersey":"10","speed":5.3,"kick":13.5})
    aid=st.session_state.get("soccer_aid",{"jersey":"7","speed":4.9,"kick":15.5})
    html=(_SOCCER_HTML
        .replace("__SC_NAME__",p1n.replace('"',''))
        .replace("__SC_AI_NAME__",ain.replace('"',''))
        .replace("__SC_P1JN__",str(p1d["jersey"]))
        .replace("__SC_AI_JN__",str(aid["jersey"]))
        .replace("__SC_P1SPD__",str(round(p1d["speed"],2)))
        .replace("__SC_AI_SPD__",str(round(aid["speed"],2)))
        .replace("__SC_P1KICK__",str(round(p1d["kick"],1)))
        .replace("__SC_AI_KICK__",str(round(aid["kick"],1)))
    )
    components.html(html,height=590)
    if st.button("🏠 BACK TO MENU",key="sc_quit"): full_reset(); st.rerun()
