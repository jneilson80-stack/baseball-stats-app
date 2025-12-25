# fastgame.py

import streamlit as st
import random
from datetime import datetime
import csv
import io

# ----------------------------------------
# Default selectable players (always shown)
# ----------------------------------------
DEFAULT_PLAYERS = ["Jnana", "Nevan", "Theo"]

# ----------------------------------------
# Helper functions
# ----------------------------------------

def calculate_batting_average(s, d, t, hr, ab):
    hits = s + d + t + hr
    return hits / ab if ab > 0 else 0.0

def format_batting_average(avg):
    return f".{int(round(avg * 1000)):03d}"

def calculate_ip(outs):
    return outs / 3.0

def format_ip(ip):
    # One decimal place, e.g., 3.0, 4.2
    return f"{ip:.1f}"

def calculate_era(er, outs):
    ip = calculate_ip(outs)
    return (9.0 * er / ip) if ip > 0 else 0.0

def calculate_whip(bb, h, outs):
    ip = calculate_ip(outs)
    return ((bb + h) / ip) if ip > 0 else 0.0

def calculate_obp(s, d, t, hr, bb, ab):
    hits = s + d + t + hr
    denom = ab + bb
    return hits / denom if denom > 0 else 0.0

def calculate_slg(s, d, t, hr, ab):
    total_bases = s + 2 * d + 3 * t + 4 * hr
    return total_bases / ab if ab > 0 else 0.0

def format_three_decimal_rate(val):
    # Format like .375, .900, etc.
    return f".{int(round(val * 1000)):03d}"

def format_rate(val):
    return f"{val:.2f}"

def format_summary_table(stats):
    headers = [
        "Player",
        # Hitting (MLB-style abbreviations)
        "AB", "1B", "2B", "3B", "HR",
        "SB", "RBI", "BB", "K", "AVG", "OBP", "SLG", "OPS",
        # Pitching
        "IP", "ER", "K (P)", "BB (P)", "H (P)", "ERA", "WHIP"
    ]

    augmented_rows = []
    for p in stats:
        s = p.get("Singles", 0)
        d = p.get("Doubles", 0)
        t = p.get("Triples", 0)
        hr = p.get("Home Runs", 0)
        ab = p.get("At Bats", 0)
        bb_h = p.get("Walks", 0)

        avg = calculate_batting_average(s, d, t, hr, ab)
        obp = calculate_obp(s, d, t, hr, bb_h, ab)
        slg = calculate_slg(s, d, t, hr, ab)
        ops = obp + slg

        avg_str = format_batting_average(avg)
        obp_str = format_three_decimal_rate(obp)
        slg_str = format_three_decimal_rate(slg)
        ops_str = format_three_decimal_rate(ops)

        pitch_outs = p.get("Pitch_Outs", 0)
        er = p.get("Pitch_ER", 0)
        k_p = p.get("Pitch_K", 0)
        bb_p = p.get("Pitch_BB", 0)
        h_p = p.get("Pitch_H", 0)

        ip = calculate_ip(pitch_outs)
        era = calculate_era(er, pitch_outs)
        whip = calculate_whip(bb_p, h_p, pitch_outs)

        row = {
            "Player": p.get("Player", ""),
            "AB": ab,
            "1B": s,
            "2B": d,
            "3B": t,
            "HR": hr,
            "SB": p.get("Stolen Bases", 0),
            "RBI": p.get("RBIs", 0),
            "BB": bb_h,
            "K": p.get("Strikeouts", 0),
            "AVG": avg_str,
            "OBP": obp_str,
            "SLG": slg_str,
            "OPS": ops_str,
            "IP": format_ip(ip),
            "ER": er,
            "K (P)": k_p,
            "BB (P)": bb_p,
            "H (P)": h_p,
            "ERA": format_rate(era),
            "WHIP": format_rate(whip),
        }
        augmented_rows.append(row)

    header_row = dict(zip(headers, headers))
    col_widths = [
        max(len(str(row.get(h, h))) for row in augmented_rows + [header_row])
        for h in headers
    ]

    def row_fmt(row_dict):
        return " | ".join(
            f"{str(row_dict.get(h, '')).ljust(w)}"
            for h, w in zip(headers, col_widths)
        )

    table = [row_fmt(header_row)]
    table.append("-+-".join("-" * w for w in col_widths))
    for row in augmented_rows:
        table.append(row_fmt(row))

    return "\n".join(table)

def merge_or_add_player(stats, new_entry):
    new_name = new_entry["Player"].strip().lower()
    for player in stats:
        if player["Player"].strip().lower() == new_name:
            for key in [
                # Hitting
                "At Bats", "Singles", "Doubles", "Triples",
                "Home Runs", "Stolen Bases", "RBIs", "Walks", "Strikeouts",
                # Pitching
                "Pitch_Outs", "Pitch_ER", "Pitch_K", "Pitch_BB", "Pitch_H"
            ]:
                player[key] += new_entry.get(key, 0)
            return "merged"
    stats.append(new_entry)
    return "added"

def generate_export_filename(stats):
    names = [p["Player"].replace(" ", "_") for p in stats]
    name_part = "_".join(names) if names else "no_players"
    rand = random.randint(1, 1_000_000)
    date = datetime.now().strftime("%m-%d-%y")
    return f"{name_part}_stats_{rand}_{date}.txt"

def build_export_text(stats):
    lines = []
    lines.append("Baseball Stats Log\n")

    for p in stats:
        lines.append(f"Player: {p['Player']}")
        # Hitting (MLB labels)
        ab = p.get("At Bats", 0)
        s = p.get("Singles", 0)
        d = p.get("Doubles", 0)
        t = p.get("Triples", 0)
        hr = p.get("Home Runs", 0)
        sb = p.get("Stolen Bases", 0)
        rbi = p.get("RBIs", 0)
        bb_h = p.get("Walks", 0)
        k_h = p.get("Strikeouts", 0)

        avg = calculate_batting_average(s, d, t, hr, ab)
        obp = calculate_obp(s, d, t, hr, bb_h, ab)
        slg = calculate_slg(s, d, t, hr, ab)
        ops = obp + slg

        lines.append(f"AB: {ab}")
        lines.append(f"1B: {s}")
        lines.append(f"2B: {d}")
        lines.append(f"3B: {t}")
        lines.append(f"HR: {hr}")
        lines.append(f"SB: {sb}")
        lines.append(f"RBI: {rbi}")
        lines.append(f"BB: {bb_h}")
        lines.append(f"K: {k_h}")
        lines.append(f"AVG: {format_batting_average(avg)}")
        lines.append(f"OBP: {format_three_decimal_rate(obp)}")
        lines.append(f"SLG: {format_three_decimal_rate(slg)}")
        lines.append(f"OPS: {format_three_decimal_rate(ops)}")

        # Pitching
        pitch_outs = p.get("Pitch_Outs", 0)
        er = p.get("Pitch_ER", 0)
        k_p = p.get("Pitch_K", 0)
        bb_p = p.get("Pitch_BB", 0)
        h_p = p.get("Pitch_H", 0)

        ip = calculate_ip(pitch_outs)
        era = calculate_era(er, pitch_outs)
        whip = calculate_whip(bb_p, h_p, pitch_outs)

        lines.append(f"IP: {format_ip(ip)}")
        lines.append(f"ER (P): {er}")
        lines.append(f"K (P): {k_p}")
        lines.append(f"BB (P): {bb_p}")
        lines.append(f"H (P): {h_p}")
        lines.append(f"ERA: {format_rate(era)}")
        lines.append(f"WHIP: {format_rate(whip)}\n")

    lines.append("Summary Table:\n")
    lines.append(format_summary_table(stats))

    return "\n".join(lines)

# ----------------------------------------
# Fast Tap helpers
# ----------------------------------------

def get_player_by_name(name):
    for p in st.session_state.stats:
        if p["Player"].strip().lower() == name.strip().lower():
            return p
    return None

def ensure_player_fields(player):
    for key in [
        # Hitting
        "At Bats", "Singles", "Doubles", "Triples", "Home Runs",
        "Stolen Bases", "RBIs", "Walks", "Strikeouts",
        # Pitching
        "Pitch_Outs", "Pitch_ER", "Pitch_K", "Pitch_BB", "Pitch_H"
    ]:
        player.setdefault(key, 0)

def record_fast_tap_play(player_name, play_type, mode="hitting"):
    player = get_player_by_name(player_name)

    if player is None:
        player = {
            "Player": player_name,
            # Hitting
            "At Bats": 0,
            "Singles": 0,
            "Doubles": 0,
            "Triples": 0,
            "Home Runs": 0,
            "Stolen Bases": 0,
            "RBIs": 0,
            "Walks": 0,
            "Strikeouts": 0,
            # Pitching
            "Pitch_Outs": 0,
            "Pitch_ER": 0,
            "Pitch_K": 0,
            "Pitch_BB": 0,
            "Pitch_H": 0,
        }
        st.session_state.stats.append(player)

    ensure_player_fields(player)

    ab_delta = 0
    pitch_outs_delta = 0
    stat_deltas = {}

    if mode == "hitting":
        if play_type == "Single":
            ab_delta = 1
            stat_deltas["Singles"] = 1
        elif play_type == "Double":
            ab_delta = 1
            stat_deltas["Doubles"] = 1
        elif play_type == "Triple":
            ab_delta = 1
            stat_deltas["Triples"] = 1
        elif play_type == "Home Run":
            ab_delta = 1
            stat_deltas["Home Runs"] = 1
        elif play_type == "Walk":
            stat_deltas["Walks"] = 1
        elif play_type == "Strikeout":
            ab_delta = 1
            stat_deltas["Strikeouts"] = 1
        elif play_type == "RBI":
            stat_deltas["RBIs"] = 1
        elif play_type == "Stolen Base":
            stat_deltas["Stolen Bases"] = 1
        elif play_type == "Out":
            ab_delta = 1

        player["At Bats"] += ab_delta

    elif mode == "pitching":
        if play_type == "Pitch Strikeout":
            pitch_outs_delta = 1
            stat_deltas["Pitch_K"] = 1
        elif play_type == "Pitch Walk":
            stat_deltas["Pitch_BB"] = 1
        elif play_type == "Pitch Hit Allowed":
            stat_deltas["Pitch_H"] = 1
        elif play_type == "Pitch Earned Run":
            stat_deltas["Pitch_ER"] = 1
        elif play_type == "Pitch Out":
            pitch_outs_delta = 1
        elif play_type == "Pitch Inning Complete":
            pitch_outs_delta = 3

        player["Pitch_Outs"] += pitch_outs_delta

    for k, v in stat_deltas.items():
        player[k] += v

    st.session_state.last_play = {
        "player_name": player_name,
        "mode": mode,
        "ab_delta": ab_delta,
        "pitch_outs_delta": pitch_outs_delta,
        "stat_deltas": stat_deltas,
        "batter_index_before": st.session_state.current_batter_index,
    }

    # Auto-advance still tied to hitting / lineup
    if mode == "hitting" and st.session_state.auto_advance and st.session_state.lineup:
        st.session_state.current_batter_index = (
            st.session_state.current_batter_index + 1
        ) % len(st.session_state.lineup)

def undo_last_play():
    lp = st.session_state.last_play
    if not lp:
        st.warning("No play to undo.")
        return

    player = get_player_by_name(lp["player_name"])
    if player is None:
        st.session_state.last_play = None
        return

    player["At Bats"] -= lp.get("ab_delta", 0)
    player["Pitch_Outs"] -= lp.get("pitch_outs_delta", 0)
    for k, v in lp["stat_deltas"].items():
        player[k] -= v

    # Restore batter index only for hitting plays
    if lp.get("mode") == "hitting":
        st.session_state.current_batter_index = lp["batter_index_before"]

    st.session_state.last_play = None
    st.success(f"Undid last play for {lp['player_name']}.")

# ----------------------------------------
# Streamlit App
# ----------------------------------------

st.title("⚾ Unified Baseball Stats & Game Mode")

if "stats" not in st.session_state:
    st.session_state.stats = []

if "lineup" not in st.session_state:
    st.session_state.lineup = []

if "lineup_select" not in st.session_state:
    st.session_state.lineup_select = []

if "current_batter_index" not in st.session_state:
    st.session_state.current_batter_index = 0

if "last_play" not in st.session_state:
    st.session_state.last_play = None

if "auto_advance" not in st.session_state:
    st.session_state.auto_advance = True

if "fast_mode" not in st.session_state:
    st.session_state.fast_mode = "Hitting"

# For Add/Merge tab
if "add_merge_selector" not in st.session_state:
    st.session_state.add_merge_selector = "Reset selection (use new name field)"
if "add_new_name_input" not in st.session_state:
    st.session_state.add_new_name_input = ""

# Tabs
tab_lineup, tab_add_merge, tab_game, tab_export, tab_faq = st.tabs([
    "📝 Set Lineup",
    "➕ Add / Merge Players",
    "⚡ Game Mode (Fast Tap)",
    "📤 Export Summary File",
    "❓ FAQ / Formulas"
])

# ----------------------------------------
# TAB 1 — Set Lineup
# ----------------------------------------
with tab_lineup:
    st.header("Set Lineup")

    added_players = [p["Player"] for p in st.session_state.stats]
    all_players = sorted(set(DEFAULT_PLAYERS + added_players))

    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("💾 Save Lineup"):
            st.session_state.lineup = st.session_state.lineup_select
            st.session_state.current_batter_index = 0
            st.success("Lineup saved.")

    with col2:
        st.session_state.lineup_select = st.multiselect(
            "Select players for the lineup (alphabetical):",
            options=all_players,
            default=st.session_state.lineup
        )

# ----------------------------------------
# TAB 2 — Add / Merge Players
# ----------------------------------------
with tab_add_merge:
    st.header("Add or Update Player Stats")

    lineup_names = st.session_state.lineup
    existing_names = [p["Player"] for p in st.session_state.stats]
    combined_names = sorted(set(lineup_names + existing_names))

    name_options = [
        "Reset selection (use new name field)"
    ] + combined_names

    last_selected = st.session_state.add_merge_selector

    if last_selected != "Reset selection (use new name field)":
        st.session_state.add_new_name_input = ""

    new_name_input = st.text_input(
        "New player name (if adding someone new):",
        key="add_new_name_input"
    )

    selected_option = st.selectbox(
        "Choose an existing player or reset:",
        options=name_options,
        key="add_merge_selector"
    )

    if selected_option == "Reset selection (use new name field)":
        name = st.session_state.add_new_name_input.strip()
    else:
        name = selected_option.strip()

    # Hitting inputs (labels kept descriptive for data entry)
    ab = st.number_input("At Bats", min_value=0, step=1)
    s = st.number_input("Singles", min_value=0, step=1)
    d = st.number_input("Doubles", min_value=0, step=1)
    t = st.number_input("Triples", min_value=0, step=1)
    hr = st.number_input("Home Runs", min_value=0, step=1)
    sb = st.number_input("Stolen Bases", min_value=0, step=1)
    rbis = st.number_input("RBIs", min_value=0, step=1)
    walks = st.number_input("Walks", min_value=0, step=1)
    strikeouts = st.number_input("Strikeouts", min_value=0, step=1)

    st.subheader("Pitching Stats (optional)")

    pitch_outs = st.number_input("Pitching Outs", min_value=0, step=1)
    pitch_er = st.number_input("Earned Runs (Pitching)", min_value=0, step=1)
    pitch_k = st.number_input("Strikeouts (Pitching)", min_value=0, step=1)
    pitch_bb = st.number_input("Walks (Pitching)", min_value=0, step=1)
    pitch_h = st.number_input("Hits Allowed (Pitching)", min_value=0, step=1)

    if st.button("Add / Merge Player Stats"):
        if not name:
            st.error("Please select a player or enter a new player name.")
        else:
            is_new = get_player_by_name(name) is None

            total_offense = ab + s + d + t + hr + sb + rbis + walks + strikeouts
            if is_new and total_offense == 0 and pitch_outs == 0 and pitch_er == 0 and pitch_k == 0 and pitch_bb == 0 and pitch_h == 0:
                st.error("Please enter stats for a new player.")
            elif s + d + t + hr > ab:
                st.error("Too many hits for At Bats.")
            else:
                entry = {
                    "Player": name,
                    # Hitting
                    "At Bats": ab,
                    "Singles": s,
                    "Doubles": d,
                    "Triples": t,
                    "Home Runs": hr,
                    "Stolen Bases": sb,
                    "RBIs": rbis,
                    "Walks": walks,
                    "Strikeouts": strikeouts,
                    # Pitching
                    "Pitch_Outs": pitch_outs,
                    "Pitch_ER": pitch_er,
                    "Pitch_K": pitch_k,
                    "Pitch_BB": pitch_bb,
                    "Pitch_H": pitch_h,
                }
                result = merge_or_add_player(st.session_state.stats, entry)

                # Auto-add to lineup alphabetically if not already present
                if name not in st.session_state.lineup:
                    st.session_state.lineup.append(name)
                    st.session_state.lineup = sorted(st.session_state.lineup)

                if result == "added":
                    st.success(f"Added stats for {name}")
                else:
                    st.success(f"Merged stats for {name}")

    if st.session_state.stats:
        st.subheader("Current Stats")
        display = []
        for p in st.session_state.stats:
            ensure_player_fields(p)
            s_val = p["Singles"]
            d_val = p["Doubles"]
            t_val = p["Triples"]
            hr_val = p["Home Runs"]
            ab_val = p["At Bats"]
            bb_h = p["Walks"]

            avg = calculate_batting_average(s_val, d_val, t_val, hr_val, ab_val)
            obp = calculate_obp(s_val, d_val, t_val, hr_val, bb_h, ab_val)
            slg = calculate_slg(s_val, d_val, t_val, hr_val, ab_val)
            ops = obp + slg

            pitch_outs = p.get("Pitch_Outs", 0)
            er = p.get("Pitch_ER", 0)
            k_p = p.get("Pitch_K", 0)
            bb_p = p.get("Pitch_BB", 0)
            h_p = p.get("Pitch_H", 0)

            ip = calculate_ip(pitch_outs)
            era = calculate_era(er, pitch_outs)
            whip = calculate_whip(bb_p, h_p, pitch_outs)

            display.append({
                "Player": p["Player"],
                "AB": ab_val,
                "1B": s_val,
                "2B": d_val,
                "3B": t_val,
                "HR": hr_val,
                "SB": p["Stolen Bases"],
                "RBI": p["RBIs"],
                "BB": bb_h,
                "K": p["Strikeouts"],
                "AVG": format_batting_average(avg),
                "OBP": format_three_decimal_rate(obp),
                "SLG": format_three_decimal_rate(slg),
                "OPS": format_three_decimal_rate(ops),
                "IP": format_ip(ip),
                "ER": er,
                "K (P)": k_p,
                "BB (P)": bb_p,
                "H (P)": h_p,
                "ERA": format_rate(era),
                "WHIP": format_rate(whip),
            })
        st.table(display)

# ----------------------------------------
# TAB 3 — Game Mode (Fast Tap)
# ----------------------------------------
with tab_game:
    st.header("Game Mode (Fast Tap)")

    if not st.session_state.lineup:
        st.warning("No lineup set. Go to Set Lineup tab.")
    else:
        col_mode1, col_mode2 = st.columns(2)
        with col_mode1:
            if st.button("Hitting Mode"):
                st.session_state.fast_mode = "Hitting"
        with col_mode2:
            if st.button("Pitching Mode"):
                st.session_state.fast_mode = "Pitching"

        st.write(f"Current Mode: **{st.session_state.fast_mode}**")

        st.session_state.auto_advance = st.checkbox(
            "Auto-advance to next batter (hitting only)",
            value=st.session_state.auto_advance
        )

        lineup = st.session_state.lineup
        st.session_state.current_batter_index %= len(lineup)
        current_batter = lineup[st.session_state.current_batter_index]

        selected_batter = st.selectbox(
            "Player at the plate / pitching:",
            options=lineup,
            index=st.session_state.current_batter_index,
        )

        if selected_batter != current_batter:
            st.session_state.current_batter_index = lineup.index(selected_batter)
            current_batter = selected_batter

        mode = "hitting" if st.session_state.fast_mode == "Hitting" else "pitching"

        if mode == "hitting":
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Single"):
                    record_fast_tap_play(current_batter, "Single", mode="hitting")
                    st.rerun()
                if st.button("Home Run"):
                    record_fast_tap_play(current_batter, "Home Run", mode="hitting")
                    st.rerun()
                if st.button("RBI"):
                    record_fast_tap_play(current_batter, "RBI", mode="hitting")
                    st.rerun()

            with col2:
                if st.button("Double"):
                    record_fast_tap_play(current_batter, "Double", mode="hitting")
                    st.rerun()
                if st.button("Walk"):
                    record_fast_tap_play(current_batter, "Walk", mode="hitting")
                    st.rerun()
                if st.button("Stolen Base"):
                    record_fast_tap_play(current_batter, "Stolen Base", mode="hitting")
                    st.rerun()

            with col3:
                if st.button("Triple"):
                    record_fast_tap_play(current_batter, "Triple", mode="hitting")
                    st.rerun()
                if st.button("Strikeout"):
                    record_fast_tap_play(current_batter, "Strikeout", mode="hitting")
                    st.rerun()
                if st.button("Out"):
                    record_fast_tap_play(current_batter, "Out", mode="hitting")
                    st.rerun()

        else:  # pitching mode
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Pitch Strikeout"):
                    record_fast_tap_play(current_batter, "Pitch Strikeout", mode="pitching")
                    st.rerun()
                if st.button("Pitch Walk"):
                    record_fast_tap_play(current_batter, "Pitch Walk", mode="pitching")
                    st.rerun()
            with col2:
                if st.button("Pitch Hit Allowed"):
                    record_fast_tap_play(current_batter, "Pitch Hit Allowed", mode="pitching")
                    st.rerun()
                if st.button("Pitch Earned Run"):
                    record_fast_tap_play(current_batter, "Pitch Earned Run", mode="pitching")
                    st.rerun()
            with col3:
                if st.button("Pitch Out"):
                    record_fast_tap_play(current_batter, "Pitch Out", mode="pitching")
                    st.rerun()
                if st.button("Pitch Inning Complete"):
                    record_fast_tap_play(current_batter, "Pitch Inning Complete", mode="pitching")
                    st.rerun()

        if st.button("Undo Last Play"):
            undo_last_play()
            st.rerun()

        if st.session_state.stats:
            st.subheader("Live Summary")
            display = []
            for p in st.session_state.stats:
                ensure_player_fields(p)
                s_val = p["Singles"]
                d_val = p["Doubles"]
                t_val = p["Triples"]
                hr_val = p["Home Runs"]
                ab_val = p["At Bats"]
                bb_h = p["Walks"]

                avg = calculate_batting_average(s_val, d_val, t_val, hr_val, ab_val)
                obp = calculate_obp(s_val, d_val, t_val, hr_val, bb_h, ab_val)
                slg = calculate_slg(s_val, d_val, t_val, hr_val, ab_val)
                ops = obp + slg

                pitch_outs = p.get("Pitch_Outs", 0)
                er = p.get("Pitch_ER", 0)
                k_p = p.get("Pitch_K", 0)
                bb_p = p.get("Pitch_BB", 0)
                h_p = p.get("Pitch_H", 0)

                ip = calculate_ip(pitch_outs)
                era = calculate_era(er, pitch_outs)
                whip = calculate_whip(bb_p, h_p, pitch_outs)

                display.append({
                    "Player": p["Player"],
                    "AB": ab_val,
                    "1B": s_val,
                    "2B": d_val,
                    "3B": t_val,
                    "HR": hr_val,
                    "SB": p["Stolen Bases"],
                    "RBI": p["RBIs"],
                    "BB": bb_h,
                    "K": p["Strikeouts"],
                    "AVG": format_batting_average(avg),
                    "OBP": format_three_decimal_rate(obp),
                    "SLG": format_three_decimal_rate(slg),
                    "OPS": format_three_decimal_rate(ops),
                    "IP": format_ip(ip),
                    "ER": er,
                    "K (P)": k_p,
                    "BB (P)": bb_p,
                    "H (P)": h_p,
                    "ERA": format_rate(era),
                    "WHIP": format_rate(whip),
                })
            st.table(display)

# ----------------------------------------
# TAB 4 — Export Summary File (TXT + CSV)
# ----------------------------------------
with tab_export:
    st.header("Export Summary File")

    if not st.session_state.stats:
        st.warning("No stats available to export.")
    else:
        # TXT Export
        export_text = build_export_text(st.session_state.stats)
        filename_txt = generate_export_filename(st.session_state.stats)

        st.subheader("Download TXT Summary")
        st.download_button(
            label="Download TXT File",
            data=export_text,
            file_name=filename_txt,
            mime="text/plain"
        )

        # CSV Export
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)

        writer.writerow([
            # Hitting (MLB abbreviations)
            "Player", "AB", "1B", "2B", "3B", "HR",
            "SB", "RBI", "BB", "K", "AVG", "OBP", "SLG", "OPS",
            # Pitching
            "IP", "ER", "K (P)", "BB (P)", "H (P)", "ERA", "WHIP"
        ])

        for p in st.session_state.stats:
            ensure_player_fields(p)
            s_val = p["Singles"]
            d_val = p["Doubles"]
            t_val = p["Triples"]
            hr_val = p["Home Runs"]
            ab_val = p["At Bats"]
            bb_h = p["Walks"]

            avg = calculate_batting_average(s_val, d_val, t_val, hr_val, ab_val)
            obp = calculate_obp(s_val, d_val, t_val, hr_val, bb_h, ab_val)
            slg = calculate_slg(s_val, d_val, t_val, hr_val, ab_val)
            ops = obp + slg

            pitch_outs = p.get("Pitch_Outs", 0)
            er = p.get("Pitch_ER", 0)
            k_p = p.get("Pitch_K", 0)
            bb_p = p.get("Pitch_BB", 0)
            h_p = p.get("Pitch_H", 0)

            ip = calculate_ip(pitch_outs)
            era = calculate_era(er, pitch_outs)
            whip = calculate_whip(bb_p, h_p, pitch_outs)

            writer.writerow([
                p["Player"],
                ab_val,
                s_val,
                d_val,
                t_val,
                hr_val,
                p["Stolen Bases"],
                p["RBIs"],
                bb_h,
                p["Strikeouts"],
                format_batting_average(avg),
                format_three_decimal_rate(obp),
                format_three_decimal_rate(slg),
                format_three_decimal_rate(ops),
                format_ip(ip),
                er,
                k_p,
                bb_p,
                h_p,
                format_rate(era),
                format_rate(whip),
            ])

        csv_data = csv_buffer.getvalue()
        filename_csv = filename_txt.replace(".txt", ".csv")

        st.subheader("Download CSV Summary")
        st.download_button(
            label="Download CSV File",
            data=csv_data,
            file_name=filename_csv,
            mime="text/csv"
        )

# ----------------------------------------
# TAB 5 — FAQ / Formulas
# ----------------------------------------
with tab_faq:
    st.header("FAQ / Formulas")

    st.subheader("Hitting Formulas")
    st.markdown(
        "- **AVG** = Hits ÷ AB\n"
        "- **Hits** = 1B + 2B + 3B + HR\n"
        "- **OBP** = (Hits + BB) ÷ (AB + BB)\n"
        "- **SLG** = Total Bases ÷ AB\n"
        "- **Total Bases** = 1B + (2 × 2B) + (3 × 3B) + (4 × HR)\n"
        "- **OPS** = OBP + SLG\n"
    )

    st.subheader("Pitching Formulas")
    st.markdown(
        "- **IP** = Outs ÷ 3\n"
        "- **ERA** = (ER × 9) ÷ IP\n"
        "- **WHIP** = (BB + H) ÷ IP\n"
    )
