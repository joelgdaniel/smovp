from fastapi import FastAPI, HTTPException
from db import client, create_table
from models import TicketCreate
from typing import Optional
from datetime import datetime

app = FastAPI()

@app.on_event("startup")
def startup_event():
    print("[DEBUG] Startup event triggered")
    print(f"[DEBUG] client type: {type(client)}")
    create_table()
    print("[DEBUG] Table creation done")

# Create Ticket
@app.post("/tickets/")
def create_ticket(ticket: TicketCreate):
    try:
        client.insert(
            "tickets",
            [[
                ticket.ticket_number,
                ticket.buyer_name,
                ticket.buyer_phone,
                ticket.seller_name,
                ticket.payment_status.value,
                ticket.mode_of_payment.value,
                ticket.date_sold,
                ticket.date_of_payment,
                ticket.remarks or ""
            ]],
            column_names=[
                "ticket_number",
                "buyer_name",
                "buyer_phone",
                "seller_name",
                "payment_status",
                "mode_of_payment",
                "date_sold",
                "date_of_payment",
                "remarks"
            ]
        )
        return {"message": "Ticket created successfully"}
    except Exception as e:
        print("[ERROR] Create ticket failed:", e)
        raise HTTPException(status_code=500, detail=str(e))

# Get All Tickets
@app.get("/tickets")
def get_all_tickets(limit: Optional[int] = 500):
    try:
        result = client.query(f"""
            SELECT * FROM tickets
            ORDER BY ticket_number
            LIMIT {limit}
        """)
        rows = result.result_rows
        return [
            {
                "ticket_number": r[0],
                "buyer_name": r[1],
                "buyer_phone": r[2],
                "seller_name": r[3],
                "payment_status": r[4],
                "mode_of_payment": r[5],
                "date_sold": str(r[6]),
                "date_of_payment": str(r[7]) if r[7] else None,
                "remarks": r[8]
            }
            for r in rows
        ]
    except Exception as e:
        print("[ERROR] Get tickets failed:", e)
        raise HTTPException(status_code=500, detail=str(e))

# Mark Ticket as Paid
@app.put("/tickets/{ticket_number}/pay")
def mark_ticket_paid(ticket_number: int):
    try:
        date_now = datetime.now().date()
        client.command(f"""
            ALTER TABLE tickets UPDATE
                payment_status = 'paid',
                date_of_payment = '{date_now}'
            WHERE ticket_number = {ticket_number}
        """)
        return {"message": f"Ticket {ticket_number} marked as paid"}
    except Exception as e:
        print("[ERROR] Mark ticket paid failed:", e)
        raise HTTPException(status_code=500, detail=str(e))

# Delete Ticket
@app.delete("/tickets/{ticket_number}")
def delete_ticket(ticket_number: int):
    try:
        client.command(f"""
            ALTER TABLE tickets DELETE WHERE ticket_number = {ticket_number}
        """)
        return {"message": f"Ticket {ticket_number} deleted successfully"}
    except Exception as e:
        print("[ERROR] Delete ticket failed:", e)
        raise HTTPException(status_code=500, detail=str(e))
