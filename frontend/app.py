import os
import time
import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from datetime import date
from dotenv import load_dotenv

# Load .env from repo root (so it works when run from frontend folder or project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

BACKEND = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
# ensure no trailing slash
BACKEND = BACKEND.rstrip("/")

st.set_page_config(page_title="🎟️ Raffle Tracker", layout="wide")

st.title("🎟️ Raffle Ticket Tracker")

col1, col2 = st.columns([2, 1])

with col1:
    st.header("Add Ticket")

    with st.form("ticket_form", clear_on_submit=True):
        ticket_number = st.number_input("Ticket number", min_value=1, step=1)
        buyer_name = st.text_input("Buyer name")
        buyer_phone = st.text_input("Buyer phone")
        seller_name = st.text_input("Seller name")
        payment_status = st.radio("Payment status", options=["due", "paid"], horizontal=True)
        mode_of_payment = st.radio("Mode of payment", options=["upi", "cash"], horizontal=True)
        date_sold = st.date_input("Date sold", value=date.today())
        date_of_payment = st.date_input("Date of payment (optional)", value=None)
        remarks = st.text_area("Remarks (optional)", height=80)

        submitted = st.form_submit_button("Save ticket")

        if submitted:
            # Basic validation
            if not buyer_name.strip():
                st.error("Buyer name is required.")
            else:
                payload = {
                    "ticket_number": int(ticket_number),
                    "buyer_name": buyer_name.strip(),
                    "buyer_phone": buyer_phone.strip(),
                    "seller_name": seller_name.strip(),
                    "payment_status": payment_status,
                    "mode_of_payment": mode_of_payment,
                    "date_sold": date_sold.isoformat(),
                    "date_of_payment": date_of_payment.isoformat() if date_of_payment else None,
                    "remarks": remarks or ""
                }
                try:
                    resp = requests.post(f"{BACKEND}/tickets/", json=payload, timeout=10)
                    if resp.ok:
                        st.success("Saved ✓")
                    else:
                        st.error(f"Save failed: {resp.status_code} {resp.text}")
                except Exception as e:
                    st.error(f"Error connecting to backend: {e}")

with col2:
    st.header("Controls")
    live_refresh = st.checkbox("Live refresh (auto reload every N seconds)", value=False)
    refresh_interval = st.number_input("Refresh interval (seconds)", min_value=2, max_value=60, value=5)
    st.markdown("**Quick actions**")
    if st.button("Refresh now"):
        st.rerun()
    st.caption("If you enable Live refresh the page will reload every N seconds (JS-based).")

# If live refresh is enabled, embed a tiny JS to reload the page every `refresh_interval` seconds.
if live_refresh:
    # using a small HTML snippet to reload
    reload_html = f"""
    <script>
    const interval = {int(refresh_interval)} * 1000;
    setTimeout(()=>{{ window.location.reload(); }}, interval);
    </script>
    <div style="font-size:12px;color:gray">Auto reloading every {int(refresh_interval)}s — disable Live refresh to stop.</div>
    """
    components.html(reload_html, height=50)

st.markdown("---")
st.header("Tickets")

# Search/filter area
search_col1, search_col2 = st.columns([3, 1])
with search_col1:
    search_text = st.text_input("Search by ticket number or buyer name (partial) — leave empty to show all")
with search_col2:
    limit = st.number_input("Limit", min_value=10, max_value=2000, value=500, step=10)

# Fetch tickets from backend (simple GET)
def fetch_tickets(limit=500):
    try:
        r = requests.get(f"{BACKEND}/tickets?limit={limit}", timeout=10)
        r.raise_for_status()
        data = r.json()
        return data
    except Exception as e:
        st.error(f"Failed to fetch tickets from backend: {e}")
        return []

tickets = fetch_tickets(limit=int(limit))

# Convert to DataFrame (handle empty)
if tickets:
    df = pd.DataFrame(tickets)
    # normalize types / columns order if needed
    cols = ["ticket_number", "buyer_name", "buyer_phone", "seller_name", "payment_status", "mode_of_payment", "date_sold", "date_of_payment", "remarks"]
    df = df[[c for c in cols if c in df.columns]]

    # apply search filter
    if search_text and search_text.strip():
        q = str(search_text).strip().lower()
        # try numeric match for ticket_number
        try:
            tno = int(q)
            df = df[df["ticket_number"] == tno]
        except Exception:
            # fallback: partial match on buyer_name or seller_name
            df = df[
                df["buyer_name"].str.lower().str.contains(q, na=False) |
                df["seller_name"].str.lower().str.contains(q, na=False) |
                df["buyer_phone"].astype(str).str.contains(q, na=False)
            ]

    st.write(f"Showing {len(df)} tickets (limit={limit})")
    # Show as an editable table (read-only here)
    st.dataframe(df.reset_index(drop=True))

    st.markdown("### Actions (per row)")
    # Render action buttons per row
    for idx, row in df.reset_index(drop=True).iterrows():
        colA, colB, colC = st.columns([3, 2, 2])
        with colA:
            st.markdown(f"**Ticket #{row['ticket_number']}** — {row['buyer_name']} — {row['payment_status']}")
            if row.get("remarks"):
                st.caption(row.get("remarks"))
        with colB:
            # Mark paid button (only show if currently due)
            if row.get("payment_status") != "paid":
                if st.button("Mark Paid", key=f"pay_{row['ticket_number']}"):
                    try:
                        resp = requests.put(f"{BACKEND}/tickets/{row['ticket_number']}/pay", timeout=10)
                        if resp.ok:
                            st.success(f"Marked {row['ticket_number']} paid")
                            time.sleep(0.2)
                            st.rerun()
                        else:
                            st.error(f"Failed to mark paid: {resp.status_code} {resp.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.write("✅ Paid")

        with colC:
            if st.button("Delete", key=f"del_{row['ticket_number']}"):
                confirm = st.modal if False else True  # placeholder (Streamlit doesn't have simple modal API here)
                # Do a delete request to backend (ensure backend has DELETE endpoint)
                try:
                    resp = requests.delete(f"{BACKEND}/tickets/{row['ticket_number']}", timeout=10)
                    if resp.ok:
                        st.success(f"Deleted ticket {row['ticket_number']}")
                        time.sleep(0.2)
                        st.rerun()
                    else:
                        st.error(f"Failed to delete: {resp.status_code} {resp.text}")
                except Exception as e:
                    st.error(f"Error contacting backend: {e}")

else:
    st.info("No tickets found. Add one using the form above.")



