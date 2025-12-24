# fastgame.py

import streamlit as st
import random
from datetime import datetime

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

def format_summary_table(stats):
    headers = [
        "Player", "At Bats", "Singles", "Doubles", "Triples", "Home Runs",
        "Stolen Bases", "RBIs", "Walks", "Strikeouts", "Batting Avg"
    ]

    col_widths = [
        max(len(str(row.get(h, h))) for row in stats + [dict(zip(headers, headers))])
        for h in headers
    ]

    def row_fmt(row, is_header=False):
        display_row = row.copy()
        if not is_header:
            avg = calculate_batting_average(
                display_row.get("Singles", 0),
                display_row.get("Doubles", 0),
                display_row.get("Triples", 0),
                display_row.get("Home Runs", 0),
                display_row.get("At Bats", 0),
            )
            display_row["Batting Avg"] = format_batting_average(avg)
        return " | ".join(
            f"{str(display_row.get(h, '')).ljust(w)}"
            for h, w in zip(headers, col_widths)
        )

    table = [row_fmt(dict(zip(headers, headers)), is_header=True)]
    table.append("-+-".join("-" * w for w in col_widths))
    for row in stats:
        table.append(row_fmt(row))
    return "\n".join(table)

def merge_or_add_player(stats, new_entry):
    """If player exists, merge stats; otherwise add as new."""
    new_name = new_entry["Player"].strip().lower()
    for player in stats:
        if player["Player"].strip().lower() == new_name:
            for key in [
                "At Bats", "Singles", "Doubles", "Triples",
                "Home Runs", "Stolen Bases", "RBIs", "Walks", "Strikeouts"
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
        lines.append(f"At Bats: {p.get('At Bats', 0)}")
        lines.append(f"Singles: {p.get('Singles', 0)}")
        lines.append(f"Doubles: {p.get('Doubles', 0)}")
        lines.append(f"Triples: {p.get('Triples', 0)}")
        lines.append(f"Home Runs: {p.get('Home Runs', 0)}")
        lines.append(f"Stolen Bases: {p.get('Stolen Bases', 0)}")
        lines.append(f"RBIs: {p.get('RBIs', 0)}")
        lines.append(f"Walks: {p.get('Walks', 0)}")
        lines.append(f"Strikeouts: {p.get('Strikeouts', 0)}")
        avg = calculate_batting_average(
            p.get("Singles", 0),
            p.get("Doubles", 0),
            p.get("Triples", 0),
            p.get("Home Runs", 0),
            p.get("At Bats", 0),
        )
        lines.append(f"Batting Avg: {format_batting_average(avg)}\n")

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
        "At Bats", "Singles", "Doubles", "Triples", "Home Runs",
        "Stolen Bases", "RBIs", "Walks", "Strikeouts"
    ]:
        player.setdefault(key, 0)

def record_fast_tap_play(player_name, play_type):
    player = get_player_by_name(player_name)

    # Auto-create player if they don't exist yet
    if player is None:
        player = {
            "Player": player_name,
            "At Bats": 0,
            "Singles": 0,
            "Doubles": 0,
            "Triples": 0,
            "Home Runs": 0,
            "Stolen Bases": 0,
            "RBIs": 0,
            "Walks": 0,
            "Strikeouts": 0,
        }
        st.session_state.stats.append(player)

    ensure_player_fields(player)

    ab_delta = 0
    stat_deltas = {}

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
    for k, v in stat_deltas.items():
        player[k] += v

    # Store undo info
    st.session_state.last_play = {
        "player_name": player_name,
        "ab_delta": ab_delta,
        "stat_deltas": stat_deltas,
        "batter_index_before": st.session_state.current_batter_index,
    }

    # Auto-advance logical index (UI will follow on st.rerun)
    if st.session_state.auto_advance and st.session_state.lineup:
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

    player["At Bats"] -= lp["ab_delta"]
    for k, v in lp["stat_deltas"].items():
        player[k] -= v

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

if "current_batter_index" not in st.session_state:
    st.session_state.current_batter_index = 0

if "last_play" not in st.session_state:
    st.session_state.last_play = None

if "auto_advance" not in st.session_state:
    st.session_state.auto_advance = True

# Tabs
tab_lineup, tab_add_merge, tab_game = st.tabs([
    "📝 Set Lineup",
    "➕ Add / Merge Players",
    "⚡ Game Mode (Fast Tap)"
])

# ----------------------------------------
# TAB 1 — Set Lineup
# ----------------------------------------
with tab_lineup:
    st.header("Set Lineup")

    added_players = [p["Player"] for p in st.session_state.stats]
    all_players = sorted(set(DEFAULT_PLAYERS + added_players))

    selected = st.multiselect(
        "Select players for the lineup (alphabetical):",
        options=all_players,
        default=st.session_state.lineup
    )

    if st.button("Save Lineup"):
        st.session_state.lineup = selected
        st.session_state.current_batter_index = 0
        st.success("Lineup saved.")

# ----------------------------------------
# TAB 2 — Add / Merge Players
# ----------------------------------------
with tab_add_merge:
    st.header("Add or Update Player Stats")

    # Build dropdown options from lineup + existing stats
    lineup_names = st.session_state.lineup
    existing_names = [p["Player"] for p in st.session_state.stats]
    combined_names = sorted(set(lineup_names + existing_names))

    name_options = [
        "Reset selection (use new name field)",
        "Type a new name..."
    ] + combined_names

    # Option B: Text input at top
    new_name_input = st.text_input(
        "New player name (if adding someone new):",
        key="add_new_name"
    )

    selected_option = st.selectbox(
        "Choose an existing player or reset:",
        options=name_options,
        key="add_merge_selector"
    )

    # Resolve final name
    if selected_option in ["Reset selection (use new name field)", "Type a new name..."]:
        name = new_name_input.strip()
    else:
        name = selected_option.strip()

    ab = st.number_input("At Bats", min_value=0, step=1)
    s = st.number_input("Singles", min_value=0, step=1)
    d = st.number_input("Doubles", min_value=0, step=1)
    t = st.number_input("Triples", min_value=0, step=1)
    hr = st.number_input("Home Runs", min_value=0, step=1)
    sb = st.number_input("Stolen Bases", min_value=0, step=1)
    rbis = st.number_input("RBIs", min_value=0, step=1)
    walks = st.number_input("Walks", min_value=0, step=1)
    strikeouts = st.number_input("Strikeouts", min_value=0, step=1)

    if st.button("Add / Merge Player Stats"):
        if not name:
            st.error("Please select a player or enter a new player name.")
        else:
            is_new = get_player_by_name(name) is None

            if is_new and (ab + s + d + t + hr + sb + rbis + walks + strikeouts == 0):
                st.error("Please enter stats for a new player.")
            elif s + d + t + hr > ab:
                st.error("Too many hits for At Bats.")
            else:
                entry = {
                    "Player": name,
                    "At Bats": ab,
                    "Singles": s,
                    "Doubles": d,
                    "Triples": t,
                    "Home Runs": hr,
                    "Stolen Bases": sb,
                    "RBIs": rbis,
                    "Walks": walks,
                    "Strikeouts": strikeouts,
                }
                result = merge_or_add_player(st.session_state.stats, entry)

                if result == "added":
                    st.success(f"Added stats for {name}")
                else:
                    st.success(f"Merged stats for {name}")

    if st.session_state.stats:
        st.subheader("Current Stats")
        display = []
        for p in st.session_state.stats:
            avg = calculate_batting_average(
                p["Singles"], p["Doubles"], p["Triples"], p["Home Runs"], p["At Bats"]
            )
            display.append({**p, "Batting Avg": format_batting_average(avg)})
        st.table(display)

        st.subheader("Export Summary File")
        export_text = build_export_text(st.session_state.stats)
        filename = generate_export_filename(st.session_state.stats)

        st.download_button(
            label="Download Summary File",
            data=export_text,
            file_name=filename,
            mime="text/plain"
        )

# ----------------------------------------
# TAB 3 — Game Mode (Fast Tap)
# ----------------------------------------
with tab_game:
    st.header("Game Mode (Fast Tap)")

    if not st.session_state.lineup:
        st.warning("No lineup set. Go to Set Lineup tab.")
    else:
        st.session_state.auto_advance = st.checkbox(
            "Auto-advance to next batter",
            value=st.session_state.auto_advance
        )

        lineup = st.session_state.lineup
        st.session_state.current_batter_index %= len(lineup)
        current_batter = lineup[st.session_state.current_batter_index]

        selected_batter = st.selectbox(
            "Batter at the plate:",
            options=lineup,
            index=st.session_state.current_batter_index,
        )

        if selected_batter != current_batter:
            st.session_state.current_batter_index = lineup.index(selected_batter)
            current_batter = selected_batter

        st.markdown(f"**At Bat:** {current_batter}")

        # --- FAST TAP BUTTONS ---
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Single"):
                record_fast_tap_play(current_batter, "Single")
                st.rerun()
            if st.button("Home Run"):
                record_fast_tap_play(current_batter, "Home Run")
                st.rerun()
            if st.button("RBI"):
                record_fast_tap_play(current_batter, "RBI")
                st.rerun()

        with col2:
            if st.button("Double"):
                record_fast_tap_play(current_batter, "Double")
                st.rerun()
            if st.button("Walk"):
                record_fast_tap_play(current_batter, "Walk")
                st.rerun()
            if st.button("Stolen Base"):
                record_fast_tap_play(current_batter, "Stolen Base")
                st.rerun()

        with col3:
            if st.button("Triple"):
                record_fast_tap_play(current_batter, "Triple")
                st.rerun()
            if st.button("Strikeout"):
                record_fast_tap_play(current_batter, "Strikeout")
                st.rerun()
            if st.button("Out"):
                record_fast_tap_play(current_batter, "Out")
                st.rerun()

        if st.button("Undo Last Play"):
            undo_last_play()
            st.rerun()

        if st.session_state.stats:
            st.subheader("Live Summary")
            display = []
            for p in st.session_state.stats:
                avg = calculate_batting_average(
                    p["Singles"], p["Doubles"], p["Triples"], p["Home Runs"], p["At Bats"]
                )
                display.append({**p, "Batting Avg": format_batting_average(avg)})
            st.table(display)
