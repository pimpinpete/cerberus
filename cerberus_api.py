"""Shared API/data layer for Cerberus apps."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# Database path
DB_PATH = Path.home() / ".cerberus" / "business.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_database():
    """Initialize SQLite database for business tracking."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # Clients table
    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            company TEXT,
            source TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    ''')

    # Jobs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            agent_type TEXT,
            price REAL DEFAULT 0,
            paid REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            started_at TEXT,
            completed_at TEXT,
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    ''')

    # Revenue/transactions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            amount REAL NOT NULL,
            type TEXT DEFAULT 'income',
            description TEXT,
            date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    ''')

    # Notes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            category TEXT DEFAULT 'general',
            pinned INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Job requests/leads table
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            client_name TEXT,
            email TEXT,
            description TEXT,
            budget TEXT,
            status TEXT DEFAULT 'new',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    ''')

    conn.commit()
    conn.close()


class CerberusAPI:
    """API for the Cerberus dashboard."""

    def __init__(self):
        init_database()
        self.cerberus = None
        self._init_cerberus()

    def _init_cerberus(self):
        """Initialize Cerberus platform."""
        try:
            from cerberus import Cerberus
            self.cerberus = Cerberus()
        except Exception as e:
            print(f"Warning: Could not initialize Cerberus: {e}")

    def _get_conn(self):
        return sqlite3.connect(str(DB_PATH))

    # ============ DASHBOARD ============

    def get_dashboard_stats(self):
        """Get dashboard statistics."""
        conn = self._get_conn()
        c = conn.cursor()

        # Total revenue
        c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='income'")
        total_revenue = c.fetchone()[0]

        # This month revenue
        month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        c.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type='income' AND date >= ?", (month_start,))
        month_revenue = c.fetchone()[0]

        # Total clients
        c.execute("SELECT COUNT(*) FROM clients")
        total_clients = c.fetchone()[0]

        # Active jobs
        c.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('pending', 'in_progress')")
        active_jobs = c.fetchone()[0]

        # Completed jobs
        c.execute("SELECT COUNT(*) FROM jobs WHERE status='completed'")
        completed_jobs = c.fetchone()[0]

        # New leads
        c.execute("SELECT COUNT(*) FROM leads WHERE status='new'")
        new_leads = c.fetchone()[0]

        # Recent jobs
        c.execute('''
            SELECT j.id, j.title, j.status, j.price, c.name as client_name, j.created_at
            FROM jobs j
            LEFT JOIN clients c ON j.client_id = c.id
            ORDER BY j.created_at DESC LIMIT 5
        ''')
        recent_jobs = [
            {"id": r[0], "title": r[1], "status": r[2], "price": r[3], "client": r[4], "date": r[5]}
            for r in c.fetchall()
        ]

        conn.close()

        return {
            "total_revenue": total_revenue,
            "month_revenue": month_revenue,
            "total_clients": total_clients,
            "active_jobs": active_jobs,
            "completed_jobs": completed_jobs,
            "new_leads": new_leads,
            "recent_jobs": recent_jobs
        }

    # ============ CLIENTS ============

    def get_clients(self):
        """Get all clients."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute('''
            SELECT c.*,
                   (SELECT COUNT(*) FROM jobs WHERE client_id=c.id) as job_count,
                   (SELECT COALESCE(SUM(price), 0) FROM jobs WHERE client_id=c.id AND status='completed') as total_spent
            FROM clients c ORDER BY created_at DESC
        ''')
        columns = [d[0] for d in c.description]
        clients = [dict(zip(columns, row)) for row in c.fetchall()]
        conn.close()
        return clients

    def add_client(self, name, email="", company="", source="", notes=""):
        """Add a new client."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO clients (name, email, company, source, notes) VALUES (?, ?, ?, ?, ?)",
            (name, email, company, source, notes)
        )
        client_id = c.lastrowid
        conn.commit()
        conn.close()
        return {"id": client_id, "success": True}

    def update_client(self, client_id, name, email, company, source, notes):
        """Update a client."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            "UPDATE clients SET name=?, email=?, company=?, source=?, notes=? WHERE id=?",
            (name, email, company, source, notes, client_id)
        )
        conn.commit()
        conn.close()
        return {"success": True}

    def delete_client(self, client_id):
        """Delete a client."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM clients WHERE id=?", (client_id,))
        conn.commit()
        conn.close()
        return {"success": True}

    # ============ JOBS ============

    def get_jobs(self, status=None):
        """Get all jobs, optionally filtered by status."""
        conn = self._get_conn()
        c = conn.cursor()
        if status:
            c.execute('''
                SELECT j.*, c.name as client_name
                FROM jobs j LEFT JOIN clients c ON j.client_id = c.id
                WHERE j.status = ? ORDER BY j.created_at DESC
            ''', (status,))
        else:
            c.execute('''
                SELECT j.*, c.name as client_name
                FROM jobs j LEFT JOIN clients c ON j.client_id = c.id
                ORDER BY j.created_at DESC
            ''')
        columns = [d[0] for d in c.description]
        jobs = [dict(zip(columns, row)) for row in c.fetchall()]
        conn.close()
        return jobs

    def add_job(self, client_id, title, description="", agent_type="", price=0, notes=""):
        """Add a new job."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            """INSERT INTO jobs (client_id, title, description, agent_type, price, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (client_id, title, description, agent_type, price, notes)
        )
        job_id = c.lastrowid
        conn.commit()
        conn.close()
        return {"id": job_id, "success": True}

    def update_job_status(self, job_id, status):
        """Update job status."""
        conn = self._get_conn()
        c = conn.cursor()

        timestamp_field = None
        if status == "in_progress":
            timestamp_field = "started_at"
        elif status == "completed":
            timestamp_field = "completed_at"

        if timestamp_field:
            c.execute(f"UPDATE jobs SET status=?, {timestamp_field}=? WHERE id=?",
                     (status, datetime.now().isoformat(), job_id))
        else:
            c.execute("UPDATE jobs SET status=? WHERE id=?", (status, job_id))

        # If completed, add transaction
        if status == "completed":
            c.execute("SELECT price, title FROM jobs WHERE id=?", (job_id,))
            row = c.fetchone()
            if row and row[0] > 0:
                c.execute(
                    "INSERT INTO transactions (job_id, amount, type, description) VALUES (?, ?, 'income', ?)",
                    (job_id, row[0], f"Payment for: {row[1]}")
                )

        conn.commit()
        conn.close()
        return {"success": True}

    def update_job(self, job_id, title, description, agent_type, price, notes):
        """Update job details."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            "UPDATE jobs SET title=?, description=?, agent_type=?, price=?, notes=? WHERE id=?",
            (title, description, agent_type, price, notes, job_id)
        )
        conn.commit()
        conn.close()
        return {"success": True}

    def delete_job(self, job_id):
        """Delete a job."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM jobs WHERE id=?", (job_id,))
        c.execute("DELETE FROM transactions WHERE job_id=?", (job_id,))
        conn.commit()
        conn.close()
        return {"success": True}

    # ============ LEADS ============

    def get_leads(self):
        """Get all leads/job requests."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM leads ORDER BY created_at DESC")
        columns = [d[0] for d in c.description]
        leads = [dict(zip(columns, row)) for row in c.fetchall()]
        conn.close()
        return leads

    def add_lead(self, source, client_name, email, description, budget="", notes=""):
        """Add a new lead."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO leads (source, client_name, email, description, budget, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (source, client_name, email, description, budget, notes)
        )
        lead_id = c.lastrowid
        conn.commit()
        conn.close()
        return {"id": lead_id, "success": True}

    def convert_lead_to_client(self, lead_id):
        """Convert a lead to a client and job."""
        conn = self._get_conn()
        c = conn.cursor()

        # Get lead info
        c.execute("SELECT * FROM leads WHERE id=?", (lead_id,))
        lead = c.fetchone()
        if not lead:
            conn.close()
            return {"success": False, "error": "Lead not found"}

        # Create client
        c.execute(
            "INSERT INTO clients (name, email, source, notes) VALUES (?, ?, ?, ?)",
            (lead[2], lead[3], lead[1], lead[8])
        )
        client_id = c.lastrowid

        # Create job
        price = 0
        try:
            budget_str = lead[5] or "0"
            price = float(''.join(c for c in budget_str if c.isdigit() or c == '.') or 0)
        except Exception:
            pass

        c.execute(
            "INSERT INTO jobs (client_id, title, description, price) VALUES (?, ?, ?, ?)",
            (client_id, f"Project for {lead[2]}", lead[4], price)
        )

        # Update lead status
        c.execute("UPDATE leads SET status='converted' WHERE id=?", (lead_id,))

        conn.commit()
        conn.close()
        return {"success": True, "client_id": client_id}

    def update_lead_status(self, lead_id, status):
        """Update lead status."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("UPDATE leads SET status=? WHERE id=?", (status, lead_id))
        conn.commit()
        conn.close()
        return {"success": True}

    # ============ NOTES ============

    def get_notes(self):
        """Get all notes."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM notes ORDER BY pinned DESC, updated_at DESC")
        columns = [d[0] for d in c.description]
        notes = [dict(zip(columns, row)) for row in c.fetchall()]
        conn.close()
        return notes

    def add_note(self, title, content, category="general"):
        """Add a new note."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO notes (title, content, category) VALUES (?, ?, ?)",
            (title, content, category)
        )
        note_id = c.lastrowid
        conn.commit()
        conn.close()
        return {"id": note_id, "success": True}

    def update_note(self, note_id, title, content, category):
        """Update a note."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            "UPDATE notes SET title=?, content=?, category=?, updated_at=? WHERE id=?",
            (title, content, category, datetime.now().isoformat(), note_id)
        )
        conn.commit()
        conn.close()
        return {"success": True}

    def toggle_note_pin(self, note_id):
        """Toggle note pinned status."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("UPDATE notes SET pinned = NOT pinned WHERE id=?", (note_id,))
        conn.commit()
        conn.close()
        return {"success": True}

    def delete_note(self, note_id):
        """Delete a note."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM notes WHERE id=?", (note_id,))
        conn.commit()
        conn.close()
        return {"success": True}

    # ============ AGENTS ============

    def get_agents(self):
        """Get all available agents."""
        if self.cerberus:
            return self.cerberus.list_agents()
        return []

    def get_agent_status(self):
        """Get Cerberus status."""
        if self.cerberus:
            return self.cerberus.status()
        return {"status": "not_initialized", "agents_loaded": 0}

    # ============ REVENUE ============

    def get_revenue_chart(self, days=30):
        """Get revenue data for chart."""
        conn = self._get_conn()
        c = conn.cursor()

        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        c.execute('''
            SELECT DATE(date) as day, SUM(amount) as total
            FROM transactions
            WHERE type='income' AND date >= ?
            GROUP BY DATE(date)
            ORDER BY day
        ''', (start_date,))

        data = [{"date": r[0], "amount": r[1]} for r in c.fetchall()]
        conn.close()
        return data

    def get_transactions(self, limit=50):
        """Get recent transactions."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute('''
            SELECT t.*, j.title as job_title
            FROM transactions t
            LEFT JOIN jobs j ON t.job_id = j.id
            ORDER BY t.date DESC LIMIT ?
        ''', (limit,))
        columns = [d[0] for d in c.description]
        transactions = [dict(zip(columns, row)) for row in c.fetchall()]
        conn.close()
        return transactions

    def add_transaction(self, amount, type_="income", description="", job_id=None):
        """Add a manual transaction."""
        conn = self._get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO transactions (job_id, amount, type, description) VALUES (?, ?, ?, ?)",
            (job_id, amount, type_, description)
        )
        conn.commit()
        conn.close()
        return {"success": True}
