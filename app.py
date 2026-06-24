import random
import streamlit as st
from gamedata import SKINS, WEAPONS

st.set_page_config(page_title="Fortnite Battle Simulator", page_icon="💥", layout="wide")
st.title("💥 Fortnite Battle Simulator")
st.markdown("---")

skin_names = list(SKINS.keys())
weapon_names = list(WEAPONS.keys())


def init_state():
    defaults = {
        "p1_health": None,
        "p1_shields": None,
        "p2_health": None,
        "p2_shields": None,
        "battle_log": [],
        "game_over": False,
        "winner": None,
        "p1_skin_locked": None,
        "p2_skin_locked": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def start_match(p1_skin, p2_skin):
    st.session_state.p1_health = SKINS[p1_skin]["health"]
    st.session_state.p1_shields = SKINS[p1_skin]["shields"]
    st.session_state.p2_health = SKINS[p2_skin]["health"]
    st.session_state.p2_shields = SKINS[p2_skin]["shields"]
    st.session_state.battle_log = []
    st.session_state.game_over = False
    st.session_state.winner = None
    st.session_state.p1_skin_locked = p1_skin
    st.session_state.p2_skin_locked = p2_skin


def reset_match():
    for key in ["p1_health", "p1_shields", "p2_health", "p2_shields",
                "battle_log", "game_over", "winner",
                "p1_skin_locked", "p2_skin_locked"]:
        st.session_state[key] = None if key != "battle_log" else []
    st.session_state.game_over = False
    st.session_state.winner = None


def apply_damage(health, shields, raw_damage):
    if shields > 0:
        shield_absorbed = min(shields, raw_damage)
        shields -= shield_absorbed
        raw_damage -= shield_absorbed
    health = max(0, health - raw_damage)
    return health, shields


def do_attack(attacker_name, defender_name, weapon_name,
              def_health_key, def_shields_key):
    weapon = WEAPONS[weapon_name]
    hit = random.random() < weapon["accuracy"]
    if not hit:
        st.session_state.battle_log.append(
            f"**{attacker_name}** fired {weapon_name} — MISSED!"
        )
        return

    crit = random.random() < weapon["crit_chance"]
    damage = weapon["damage"] * 2 if crit else weapon["damage"]
    label = "💥 CRITICAL HIT" if crit else "Hit"

    prev_health = st.session_state[def_health_key]
    prev_shields = st.session_state[def_shields_key]
    new_health, new_shields = apply_damage(prev_health, prev_shields, damage)
    st.session_state[def_health_key] = new_health
    st.session_state[def_shields_key] = new_shields

    shield_msg = f" (shields: {prev_shields}→{new_shields})" if prev_shields != new_shields else ""
    st.session_state.battle_log.append(
        f"**{attacker_name}** → {defender_name} with {weapon_name}: "
        f"{label} for **{damage} dmg**{shield_msg} | HP: {prev_health}→{new_health}"
    )

    if new_health <= 0:
        st.session_state.game_over = True
        st.session_state.winner = attacker_name


init_state()

game_active = st.session_state.p1_health is not None

col1, col2 = st.columns(2)

with col1:
    st.subheader("🟦 Player 1")
    p1_skin = st.selectbox("Choose Skin", skin_names, key="p1_skin", disabled=game_active)
    p1_weapon = st.selectbox("Choose Weapon", weapon_names, key="p1_weapon", disabled=game_active)
    if game_active:
        skin = st.session_state.p1_skin_locked
        st.markdown(f"**Skin:** {skin}")
        hp = st.session_state.p1_health
        sh = st.session_state.p1_shields
        max_hp = SKINS[skin]["health"]
        max_sh = SKINS[skin]["shields"]
        st.progress(hp / max_hp, text=f"❤️ HP: {hp} / {max_hp}")
        st.progress(sh / max_sh if max_sh > 0 else 0, text=f"🛡️ Shields: {sh} / {max_sh}")

with col2:
    st.subheader("🟥 Player 2")
    p2_skin = st.selectbox("Choose Skin", skin_names, index=1, key="p2_skin", disabled=game_active)
    p2_weapon = st.selectbox("Choose Weapon", weapon_names, index=1, key="p2_weapon", disabled=game_active)
    if game_active:
        skin = st.session_state.p2_skin_locked
        st.markdown(f"**Skin:** {skin}")
        hp = st.session_state.p2_health
        sh = st.session_state.p2_shields
        max_hp = SKINS[skin]["health"]
        max_sh = SKINS[skin]["shields"]
        st.progress(hp / max_hp, text=f"❤️ HP: {hp} / {max_hp}")
        st.progress(sh / max_sh if max_sh > 0 else 0, text=f"🛡️ Shields: {sh} / {max_sh}")

st.markdown("---")

if not game_active:
    if st.button("🎮 Start Match", use_container_width=True):
        start_match(p1_skin, p2_skin)
        st.rerun()
else:
    if st.session_state.game_over:
        st.balloons()
        st.success(f"🏆 {st.session_state.winner} wins the match!")
        if st.button("🔄 Reset Match", use_container_width=True):
            reset_match()
            st.rerun()
    else:
        atk_col1, atk_col2 = st.columns(2)
        with atk_col1:
            if st.button("💥 P1 ATTACKS!", use_container_width=True):
                do_attack(
                    st.session_state.p1_skin_locked,
                    st.session_state.p2_skin_locked,
                    st.session_state.p1_weapon,
                    "p2_health", "p2_shields",
                )
                st.rerun()
        with atk_col2:
            if st.button("💥 P2 ATTACKS!", use_container_width=True):
                do_attack(
                    st.session_state.p2_skin_locked,
                    st.session_state.p1_skin_locked,
                    st.session_state.p2_weapon,
                    "p1_health", "p1_shields",
                )
                st.rerun()

st.markdown("---")
st.subheader("📜 Battle Log")
if st.session_state.battle_log:
    for entry in reversed(st.session_state.battle_log):
        st.markdown(entry)
else:
    st.caption("No actions yet — start a match and attack!")
