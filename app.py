import streamlit as st
import random
from datetime import datetime

# -----------------------------
# Helper Functions
# -----------------------------

def calculate_batting_average(s, d, t, hr, ab):
    hits = s + d + t + hr
    return hits / ab if ab > 0 else 0.0

def format_batting_average(avg):
    return f".{int(round(avg * 1000)):03d}"

def format_summary_table(stats):
    headers = ["Player", "At Bats", "Singles", "Doubles", "Triples", "Home Runs", "Stolen Bases", "Batting Avg"]
    col_widths = [
        max(len(str(row.get(h, h))) for row in stats + [dict(zip(headers, headers))])
        for h in headers
    ]

    def row_fmt(row, is_header=False):
        display_row = row.copy()
        if not is_header:
            avg = calculate_batting_average(
                display_row["Singles"], display_row["Doubles"], display_row["Triples"],
                display_row["Home Runs"], display_row["At Bats"]
            )
            display_row["Batting Avg"] = format_batting_average(avg)
        return " | ".join(f"{str(display_row.get(h, '')).ljust(w)}" for h, w in zip(headers, col_widths))

    table = [row_fmt(dict(zip(headers, headers)), is_header=True)]
    table.append("-+-".join("-" * w for w in col_widths))
    for row in stats:
        table.append(row_fmt(row))
    return "\n".join(table)

def merge_player(stats, new_entry):
    new_name = new_entry["Player"].strip().lower()
    for player in stats:
        if player["Player"].strip().lower() == new_name:
            for key in ["At Bats", "Singles", "Doubles", "Triples", "Home Runs", "Stolen Bases"]:
                player[key] += new_entry[key]
            return
    stats.append(new_entry)

# -----------------------------
# Export Helpers
# -----------------------------

def generate_export_filename(stats):
    names = [p["Player"].replace(" ", "_") for p in stats]
    name_part = "_".join(names)
    rand = random.randint(1, 1_000_000)
    date = datetime.now().strftime("%m-%d-%y")
    return f"{name_part}_stats_{rand}_{date}.txt"

def build_export_text(stats):
    lines = []
    lines.append("Baseball Stats Log\n")

    for p in stats:
        lines.append(f"Player: {p['Player']}")
        lines.append(f"At Bats: {p['At Bats']}")
        lines.append(f"Singles: {p['Singles']}")
        lines.append(f"Doubles: {p['Doubles']}")
        lines.append(f"Triples: {p['Triples']}")
        lines.append(f"Home Runs: {p['Home Runs']}")
        lines.append(f"Stolen Bases: {p['Stolen Bases']}")
        avg = calculate_batting_average(
            p["Singles"], p["Doubles"], p["Triples"], p["Home Runs"], p["At Bats"]
        )
        lines.append(f"Batting Avg: {format_batting_average(avg)}\n")

    lines.append("Summary Table (Sorted by Batting Avg):\n")
    lines.append(format_summary_table(stats))

    return "\n".join(lines)

# -----------------------------
# Streamlit App
# -----------------------------

st.title("⚾ Unified Baseball Stats Recorder & Merger")

# Initialize session state
if "stats" not in st.session_state:
    st.session_state.stats = []

# Tabs for the two modes
tab1, tab2 = st.tabs(["➕ Add Players", "🔄 Add More Players / Merge"])

# -----------------------------
# TAB 1 — Add Players
# -----------------------------
with tab1:
    st.header("Add New Player Stats")

    name = st.text_input("Player Name")
    ab = st.number_input("At Bats", min_value=0, step=1)
    s = st.number_input("Singles", min_value=0, step=1)
    d = st.number_input("Doubles", min_value=0, step=1)
    t = st.number_input("Triples", min_value=0, step=1)
    hr = st.number_input("Home Runs", min_value=0, step=1)
    sb = st.number_input("Stolen Bases", min_value=0, step=1)

    if st.button("Add Player", key="add_player_tab1"):
        try:
            if not name.strip():
                st.error("Player name is required.")
            elif s + d + t + hr > ab:
                st.error("Too many hits for At Bats.")
            elif sb > ab * 3:
                st.error("Too many stolen bases.")
            else:
                entry = {
                    "Player": name,
                    "At Bats": ab,
                    "Singles": s,
                    "Doubles": d,
                    "Triples": t,
                    "Home Runs": hr,
                    "Stolen Bases": sb
                }
                st.session_state.stats.append(entry)
                st.success(f"Added stats for {name}")
        except ValueError:
            st.error("Invalid input.")

    if st.session_state.stats:
        st.subheader("📊 Current Stats")
        display = []
        for p in st.session_state.stats:
            avg = calculate_batting_average(p["Singles"], p["Doubles"], p["Triples"], p["Home Runs"], p["At Bats"])
            display.append({**p, "Batting Avg": format_batting_average(avg)})
        st.table(display)

# -----------------------------
# TAB 2 — Merge Players
# -----------------------------
with tab2:
    st.header("Add More Players / Merge Stats")

    if not st.session_state.stats:
        st.info("No stats yet. Add players in the first tab.")
    else:
        name2 = st.text_input("Player Name (Merge Mode)")
        ab2 = st.number_input("At Bats", min_value=0, step=1, key="ab2")
        s2 = st.number_input("Singles", min_value=0, step=1, key="s2")
        d2 = st.number_input("Doubles", min_value=0, step=1, key="d2")
        t2 = st.number_input("Triples", min_value=0, step=1, key="t2")
        hr2 = st.number_input("Home Runs", min_value=0, step=1, key="hr2")
        sb2 = st.number_input("Stolen Bases", min_value=0, step=1, key="sb2")

        if st.button("Merge Player Stats", key="merge_player"):
            try:
                if not name2.strip():
                    st.error("Player name is required.")
                elif s2 + d2 + t2 + hr2 > ab2:
                    st.error("Too many hits for At Bats.")
                elif sb2 > ab2 * 3:
                    st.error("Too many stolen bases.")
                else:
                    new_entry = {
                        "Player": name2,
                        "At Bats": ab2,
                        "Singles": s2,
                        "Doubles": d2,
                        "Triples": t2,
                        "Home Runs": hr2,
                        "Stolen Bases": sb2
                    }
                    merge_player(st.session_state.stats, new_entry)
                    st.success(f"Merged stats for {name2}")
            except ValueError:
                st.error("Invalid input.")

        st.subheader("📋 Updated Summary")
        st.code(format_summary_table(st.session_state.stats))

        # -----------------------------
        # Export Button
        # -----------------------------
        export_text = build_export_text(st.session_state.stats)
        filename = generate_export_filename(st.session_state.stats)

        st.download_button(
            label="📥 Download Summary File",
            data=export_text,
            file_name=filename,
            mime="text/plain"
        )
