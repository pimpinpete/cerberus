#!/usr/bin/env python3
"""
Cerberus Dashboard App
Desktop application for managing AI agent business.
"""

import os
import sys
import json
import sqlite3
import webview
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Add cerberus to path
CERBERUS_PATH = Path(__file__).parent
sys.path.insert(0, str(CERBERUS_PATH))

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
            (lead[2], lead[3], lead[1], lead[8])  # client_name, email, source, notes
        )
        client_id = c.lastrowid

        # Create job
        price = 0
        try:
            # Try to parse budget
            budget_str = lead[5] or "0"
            price = float(''.join(c for c in budget_str if c.isdigit() or c == '.') or 0)
        except:
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


# HTML Template
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Cerberus Command Center</title>
    <style>
        @import url("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap");

        :root {
            color-scheme: dark;
            --bg-0: #06070d;
            --bg-1: #0b1021;
            --bg-2: #101a32;
            --glass: rgba(16, 24, 44, 0.6);
            --glass-strong: rgba(16, 24, 44, 0.75);
            --line: rgba(255, 255, 255, 0.08);
            --text: #eaf2ff;
            --muted: #98a3c7;
            --accent: #57e2e5;
            --accent-2: #f2b880;
            --accent-3: #9ef0b0;
            --danger: #ff6b6b;
            --warn: #ffd166;
            --success: #2fe3a6;
            --shadow: 0 24px 60px rgba(5, 10, 24, 0.65);
            --glow: 0 0 30px rgba(87, 226, 229, 0.25);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: "Space Grotesk", "Sora", "Manrope", system-ui, sans-serif;
            background: radial-gradient(circle at 10% 10%, #1b2b53 0%, transparent 45%),
                        radial-gradient(circle at 80% 20%, #2a1345 0%, transparent 40%),
                        radial-gradient(circle at 80% 90%, #133d38 0%, transparent 50%),
                        linear-gradient(160deg, var(--bg-0), var(--bg-1) 40%, var(--bg-2));
            color: var(--text);
            min-height: 100vh;
            overflow: hidden;
        }

        body::before {
            content: "";
            position: fixed;
            inset: 0;
            background: radial-gradient(circle at 20% 20%, rgba(87, 226, 229, 0.08), transparent 45%),
                        radial-gradient(circle at 70% 80%, rgba(242, 184, 128, 0.08), transparent 50%);
            pointer-events: none;
            z-index: 0;
        }

        .app-shell {
            display: flex;
            height: 100vh;
            position: relative;
            z-index: 1;
        }

        /* Sidebar */
        .sidebar {
            width: 250px;
            padding: 28px 22px;
            background: rgba(7, 12, 26, 0.75);
            border-right: 1px solid var(--line);
            backdrop-filter: blur(18px);
            display: flex;
            flex-direction: column;
            gap: 18px;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 700;
            letter-spacing: 0.6px;
            font-size: 20px;
        }

        .logo-mark {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: linear-gradient(145deg, rgba(20, 25, 35, 0.95), rgba(30, 40, 55, 0.9));
            border: 1.5px solid rgba(87, 226, 229, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow:
                0 0 20px rgba(87, 226, 229, 0.3),
                0 0 40px rgba(87, 226, 229, 0.1),
                inset 0 1px 1px rgba(255, 255, 255, 0.05);
        }

        .logo-mark svg {
            width: 18px;
            height: 18px;
            stroke: var(--accent);
            stroke-width: 2;
            fill: none;
            filter: drop-shadow(0 0 3px rgba(87, 226, 229, 0.5));
        }

        .logo span { color: var(--accent); }

        .nav {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .nav-item {
            border: 1px solid transparent;
            padding: 12px 14px;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 10px;
            background: transparent;
            color: var(--text);
            font-size: 14px;
        }

        .nav-item:hover {
            background: rgba(87, 226, 229, 0.08);
            border-color: rgba(87, 226, 229, 0.3);
        }

        .nav-item.active {
            background: linear-gradient(135deg, rgba(87, 226, 229, 0.25), rgba(87, 226, 229, 0.05));
            border-color: rgba(87, 226, 229, 0.5);
            box-shadow: var(--glow);
        }

        .nav-badge {
            margin-left: auto;
            background: rgba(255, 107, 107, 0.2);
            color: #ffd4d4;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 999px;
            border: 1px solid rgba(255, 107, 107, 0.4);
        }

        .sidebar-footer {
            margin-top: auto;
            padding: 14px;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--line);
        }

        .sidebar-footer p {
            font-size: 12px;
            color: var(--muted);
            line-height: 1.4;
        }

        /* Main */
        .main {
            flex: 1;
            padding: 28px 32px 32px;
            overflow-y: auto;
        }

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 22px;
        }

        .page-title {
            font-size: 24px;
            font-weight: 700;
            letter-spacing: 0.4px;
        }

        .page-sub {
            color: var(--muted);
            margin-top: 6px;
            font-size: 13px;
        }

        .topbar-right {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .chip {
            padding: 8px 12px;
            border-radius: 999px;
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.03);
            color: var(--muted);
            font-size: 12px;
        }

        .page { display: none; }
        .page.active { display: block; animation: fadeIn 0.4s ease; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        h2 { margin: 20px 0 12px; font-size: 16px; color: var(--muted); font-weight: 600; }

        /* Panels */
        .panel-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 18px;
            margin-bottom: 24px;
        }

        .card {
            background: var(--glass);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 20px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(18px);
        }

        .stat-card {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .stat-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .stat-value {
            font-size: 28px;
            font-weight: 700;
        }

        .stat-label {
            color: var(--muted);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }

        .stat-pill {
            font-size: 11px;
            padding: 4px 10px;
            border-radius: 999px;
            border: 1px solid rgba(87, 226, 229, 0.4);
            color: var(--accent);
            background: rgba(87, 226, 229, 0.08);
        }

        /* Charts */
        .spark-wrap {
            height: 120px;
        }

        canvas {
            width: 100%;
            height: 100%;
        }

        /* Tables */
        .table-container {
            background: var(--glass-strong);
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid var(--line);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        th, td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }

        th { color: var(--muted); font-weight: 500; background: rgba(255,255,255,0.02); }
        tr:hover { background: rgba(255,255,255,0.04); }

        /* Status badges */
        .status {
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .status.pending { background: rgba(255, 209, 102, 0.2); color: var(--warn); border: 1px solid rgba(255, 209, 102, 0.5); }
        .status.in_progress { background: rgba(87, 226, 229, 0.2); color: var(--accent); border: 1px solid rgba(87, 226, 229, 0.5); }
        .status.completed { background: rgba(47, 227, 166, 0.2); color: var(--success); border: 1px solid rgba(47, 227, 166, 0.5); }
        .status.new { background: rgba(255, 107, 107, 0.2); color: var(--danger); border: 1px solid rgba(255, 107, 107, 0.5); }
        .status.converted { background: rgba(158, 240, 176, 0.2); color: var(--accent-3); border: 1px solid rgba(158, 240, 176, 0.5); }

        /* Buttons */
        .btn {
            padding: 10px 18px;
            border: 1px solid transparent;
            border-radius: 10px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s ease;
            background: rgba(255, 255, 255, 0.08);
            color: var(--text);
        }

        .btn-primary {
            background: linear-gradient(135deg, rgba(87, 226, 229, 0.6), rgba(87, 226, 229, 0.2));
            border-color: rgba(87, 226, 229, 0.6);
            color: #07131c;
        }
        .btn-primary:hover { transform: translateY(-1px); box-shadow: var(--glow); }

        .btn-secondary { background: rgba(255,255,255,0.06); border-color: var(--line); }
        .btn-secondary:hover { background: rgba(255,255,255,0.12); }

        .btn-danger { background: rgba(255, 107, 107, 0.2); color: #ffdcdc; border-color: rgba(255, 107, 107, 0.5); }
        .btn-small { padding: 6px 12px; font-size: 11px; }

        /* Forms */
        .form-group { margin-bottom: 15px; }

        .form-group label {
            display: block;
            margin-bottom: 6px;
            color: var(--muted);
            font-size: 12px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--line);
            border-radius: 10px;
            background: rgba(7, 12, 26, 0.6);
            color: var(--text);
            font-size: 14px;
        }

        .form-group textarea { min-height: 110px; resize: vertical; }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(5, 10, 24, 0.85);
            justify-content: center;
            align-items: center;
            z-index: 1000;
            backdrop-filter: blur(4px);
        }

        .modal.active { display: flex; }

        .modal-content {
            background: rgba(10, 16, 34, 0.95);
            padding: 26px;
            border-radius: 18px;
            width: 90%;
            max-width: 520px;
            max-height: 80vh;
            overflow-y: auto;
            border: 1px solid var(--line);
            box-shadow: var(--shadow);
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .modal-close {
            background: none;
            border: none;
            color: var(--text);
            font-size: 24px;
            cursor: pointer;
        }

        /* Notes */
        .notes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
            gap: 14px;
        }

        .note-card {
            background: rgba(255,255,255,0.04);
            padding: 16px;
            border-radius: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            border: 1px solid var(--line);
        }

        .note-card:hover { transform: translateY(-2px); box-shadow: var(--glow); }
        .note-card.pinned { border-left: 3px solid var(--accent); }

        .note-title { font-weight: 600; margin-bottom: 8px; }
        .note-preview { color: var(--muted); font-size: 13px; }
        .note-meta { color: #6f7aa6; font-size: 11px; margin-top: 10px; }

        /* Agent cards */
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 16px;
        }

        .agent-card {
            background: rgba(255,255,255,0.05);
            padding: 18px;
            border-radius: 16px;
            border: 1px solid var(--line);
        }

        .agent-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .agent-name { font-weight: 600; font-size: 15px; }
        .agent-status { width: 10px; height: 10px; border-radius: 50%; background: var(--success); }
        .agent-type { color: var(--muted); font-size: 12px; }

        /* Actions */
        .actions { display: flex; gap: 8px; align-items: center; }

        .mono { font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace; }
    </style>
</head>
<body>
    <div class="app-shell">
        <aside class="sidebar">
            <div class="logo">
                <div class="logo-mark">
                    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 4 L21 20 L3 20 Z" stroke-linejoin="round"/>
                    </svg>
                </div>
                <div>Cerberus <span>Command</span></div>
            </div>
            <div class="nav">
                <button class="nav-item active" data-page="dashboard">Command Center</button>
                <button class="nav-item" data-page="leads">
                    Job Requests
                    <span class="nav-badge" id="leads-badge">0</span>
                </button>
                <button class="nav-item" data-page="jobs">Jobs</button>
                <button class="nav-item" data-page="clients">Clients</button>
                <button class="nav-item" data-page="agents">Agents</button>
                <button class="nav-item" data-page="revenue">Revenue</button>
                <button class="nav-item" data-page="notes">Notes</button>
            </div>
            <div class="sidebar-footer">
                <p>AI automation agency ops hub. Track revenue, clients, and delivery momentum in one place.</p>
            </div>
        </aside>

        <main class="main">
            <header class="topbar">
                <div>
                    <div class="page-title" id="page-title">Command Center</div>
                    <div class="page-sub" id="page-sub">Real-time revenue, workload, and pipeline health</div>
                </div>
                <div class="topbar-right">
                    <div class="chip" id="today-chip"></div>
                    <button class="btn btn-secondary" onclick="showModal('lead')">New Lead</button>
                </div>
            </header>

            <!-- Dashboard -->
            <div id="page-dashboard" class="page active">
                <div class="panel-grid" id="stats-grid"></div>

                <div class="panel-grid">
                    <div class="card">
                        <div class="stat-row" style="margin-bottom:12px;">
                            <div>
                                <div class="stat-label">Revenue Momentum</div>
                                <div class="stat-value" id="spark-total">$0</div>
                            </div>
                            <div class="stat-pill">Last 30 days</div>
                        </div>
                        <div class="spark-wrap">
                            <canvas id="revenue-spark"></canvas>
                        </div>
                    </div>
                    <div class="card">
                        <h2>Recent Jobs</h2>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr><th>Job</th><th>Client</th><th>Status</th><th>Price</th></tr>
                                </thead>
                                <tbody id="recent-jobs"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Leads -->
            <div id="page-leads" class="page">
                <div class="panel-grid">
                    <div class="card">
                        <div class="stat-row" style="margin-bottom:12px;">
                            <div>
                                <div class="stat-label">Inbound Requests</div>
                                <div class="stat-value" id="leads-count">0</div>
                            </div>
                            <button class="btn btn-primary" onclick="showModal('lead')">Add Lead</button>
                        </div>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr><th>Source</th><th>Client</th><th>Description</th><th>Budget</th><th>Status</th><th>Actions</th></tr>
                                </thead>
                                <tbody id="leads-table"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Jobs -->
            <div id="page-jobs" class="page">
                <div class="panel-grid">
                    <div class="card">
                        <div class="stat-row" style="margin-bottom:12px;">
                            <div>
                                <div class="stat-label">Active Delivery</div>
                                <div class="stat-value" id="jobs-count">0</div>
                            </div>
                            <button class="btn btn-primary" onclick="showModal('job')">New Job</button>
                        </div>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr><th>Job</th><th>Client</th><th>Agent</th><th>Price</th><th>Status</th><th>Actions</th></tr>
                                </thead>
                                <tbody id="jobs-table"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Clients -->
            <div id="page-clients" class="page">
                <div class="panel-grid">
                    <div class="card">
                        <div class="stat-row" style="margin-bottom:12px;">
                            <div>
                                <div class="stat-label">Client Roster</div>
                                <div class="stat-value" id="clients-count">0</div>
                            </div>
                            <button class="btn btn-primary" onclick="showModal('client')">Add Client</button>
                        </div>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr><th>Name</th><th>Email</th><th>Company</th><th>Source</th><th>Jobs</th><th>Total</th><th>Actions</th></tr>
                                </thead>
                                <tbody id="clients-table"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Agents -->
            <div id="page-agents" class="page">
                <div class="panel-grid">
                    <div class="card">
                        <div class="stat-row" style="margin-bottom:12px;">
                            <div>
                                <div class="stat-label">Automation Fleet</div>
                                <div class="stat-value" id="agents-count">0</div>
                            </div>
                        </div>
                        <div class="agents-grid" id="agents-grid"></div>
                    </div>
                </div>
            </div>

            <!-- Revenue -->
            <div id="page-revenue" class="page">
                <div class="panel-grid">
                    <div class="card">
                        <div class="stat-row" style="margin-bottom:12px;">
                            <div>
                                <div class="stat-label">Total Revenue</div>
                                <div class="stat-value" id="total-revenue">$0</div>
                            </div>
                            <div>
                                <div class="stat-label">This Month</div>
                                <div class="stat-value" id="month-revenue">$0</div>
                            </div>
                        </div>
                        <div class="spark-wrap" style="height:160px;">
                            <canvas id="revenue-chart"></canvas>
                        </div>
                        <h2>Recent Transactions</h2>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr><th>Date</th><th>Description</th><th>Amount</th></tr>
                                </thead>
                                <tbody id="transactions-table"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Notes -->
            <div id="page-notes" class="page">
                <div class="panel-grid">
                    <div class="card">
                        <div class="stat-row" style="margin-bottom:12px;">
                            <div>
                                <div class="stat-label">Notes Vault</div>
                                <div class="stat-value" id="notes-count">0</div>
                            </div>
                            <button class="btn btn-primary" onclick="showModal('note')">Add Note</button>
                        </div>
                        <div class="notes-grid" id="notes-grid"></div>
                    </div>
                </div>
            </div>

        </main>
    </div>

    <!-- Modals -->
    <div class="modal" id="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modal-title">Add</h2>
                <button class="modal-close" onclick="hideModal()">&times;</button>
            </div>
            <div id="modal-body"></div>
        </div>
    </div>

    <script>
        const PAGE_META = {
            dashboard: { title: "Command Center", sub: "Real-time revenue, workload, and pipeline health" },
            leads: { title: "Job Requests", sub: "Inbound opportunities and lead conversions" },
            jobs: { title: "Jobs", sub: "Delivery pipeline and status control" },
            clients: { title: "Clients", sub: "Account history and relationship detail" },
            agents: { title: "Agents", sub: "Automation fleet readiness and availability" },
            revenue: { title: "Revenue", sub: "Financial performance and transaction history" },
            notes: { title: "Notes", sub: "Operational context, ideas, and playbooks" }
        };

        function formatCurrency(value) {
            return "$" + Number(value || 0).toLocaleString();
        }

        function setTopbar(page) {
            const meta = PAGE_META[page];
            if (!meta) return;
            document.getElementById("page-title").textContent = meta.title;
            document.getElementById("page-sub").textContent = meta.sub;
        }

        function showPage(page, el) {
            document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
            document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
            document.getElementById("page-" + page).classList.add("active");
            if (el) el.classList.add("active");
            setTopbar(page);
            loadPageData(page);
        }

        document.querySelectorAll(".nav-item").forEach(item => {
            item.addEventListener("click", () => showPage(item.dataset.page, item));
        });

        function drawSparkline(canvasId, points, color) {
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;
            const ctx = canvas.getContext("2d");
            const ratio = window.devicePixelRatio || 1;
            const w = canvas.clientWidth * ratio;
            const h = canvas.clientHeight * ratio;
            canvas.width = w;
            canvas.height = h;
            ctx.clearRect(0, 0, w, h);

            if (!points || points.length === 0) {
                ctx.fillStyle = "rgba(255,255,255,0.08)";
                ctx.fillRect(0, 0, w, h);
                return;
            }

            const max = Math.max(...points.map(p => p.amount));
            const min = Math.min(...points.map(p => p.amount));
            const range = max - min || 1;
            const pad = 8 * ratio;
            const step = (w - pad * 2) / Math.max(points.length - 1, 1);

            ctx.beginPath();
            points.forEach((p, i) => {
                const x = pad + i * step;
                const y = h - pad - ((p.amount - min) / range) * (h - pad * 2);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });

            ctx.strokeStyle = color || "rgba(87,226,229,0.9)";
            ctx.lineWidth = 2 * ratio;
            ctx.shadowBlur = 12 * ratio;
            ctx.shadowColor = "rgba(87,226,229,0.6)";
            ctx.stroke();
        }

        async function loadPageData(page) {
            if (page === "dashboard") await loadDashboard();
            else if (page === "leads") await loadLeads();
            else if (page === "jobs") await loadJobs();
            else if (page === "clients") await loadClients();
            else if (page === "agents") await loadAgents();
            else if (page === "revenue") await loadRevenue();
            else if (page === "notes") await loadNotes();
        }

        async function loadDashboard() {
            const stats = await pywebview.api.get_dashboard_stats();
            const chart = await pywebview.api.get_revenue_chart(30);

            document.getElementById("stats-grid").innerHTML = `
                <div class="card stat-card">
                    <div class="stat-label">Total Revenue</div>
                    <div class="stat-row">
                        <div class="stat-value">${formatCurrency(stats.total_revenue)}</div>
                        <div class="stat-pill">All time</div>
                    </div>
                </div>
                <div class="card stat-card">
                    <div class="stat-label">This Month</div>
                    <div class="stat-row">
                        <div class="stat-value">${formatCurrency(stats.month_revenue)}</div>
                        <div class="stat-pill">MTD</div>
                    </div>
                </div>
                <div class="card stat-card">
                    <div class="stat-label">Clients</div>
                    <div class="stat-row">
                        <div class="stat-value">${stats.total_clients}</div>
                        <div class="stat-pill">Accounts</div>
                    </div>
                </div>
                <div class="card stat-card">
                    <div class="stat-label">Active Jobs</div>
                    <div class="stat-row">
                        <div class="stat-value">${stats.active_jobs}</div>
                        <div class="stat-pill">In flight</div>
                    </div>
                </div>
                <div class="card stat-card">
                    <div class="stat-label">Completed</div>
                    <div class="stat-row">
                        <div class="stat-value">${stats.completed_jobs}</div>
                        <div class="stat-pill">Delivered</div>
                    </div>
                </div>
                <div class="card stat-card">
                    <div class="stat-label">New Leads</div>
                    <div class="stat-row">
                        <div class="stat-value">${stats.new_leads}</div>
                        <div class="stat-pill">Untriaged</div>
                    </div>
                </div>
            `;

            document.getElementById("leads-badge").textContent = stats.new_leads;
            document.getElementById("spark-total").textContent = formatCurrency(stats.month_revenue);

            document.getElementById("recent-jobs").innerHTML = stats.recent_jobs.map(j => `
                <tr>
                    <td>${j.title}</td>
                    <td>${j.client || "N/A"}</td>
                    <td><span class="status ${j.status}">${j.status}</span></td>
                    <td class="mono">${formatCurrency(j.price)}</td>
                </tr>
            `).join("");

            drawSparkline("revenue-spark", chart, "rgba(87,226,229,0.9)");
        }

        async function loadLeads() {
            const leads = await pywebview.api.get_leads();
            document.getElementById("leads-count").textContent = leads.length;
            document.getElementById("leads-table").innerHTML = leads.map(l => `
                <tr>
                    <td>${l.source || "Direct"}</td>
                    <td>${l.client_name}</td>
                    <td>${(l.description || "").substring(0, 50)}...</td>
                    <td>${l.budget || "TBD"}</td>
                    <td><span class="status ${l.status}">${l.status}</span></td>
                    <td class="actions">
                        ${l.status === "new" ? `<button class="btn btn-small btn-primary" onclick="convertLead(${l.id})">Convert</button>` : ""}
                    </td>
                </tr>
            `).join("");
        }

        async function convertLead(id) {
            await pywebview.api.convert_lead_to_client(id);
            loadLeads();
            loadDashboard();
        }

        async function loadJobs() {
            const jobs = await pywebview.api.get_jobs();
            document.getElementById("jobs-count").textContent = jobs.length;

            document.getElementById("jobs-table").innerHTML = jobs.map(j => `
                <tr>
                    <td>${j.title}</td>
                    <td>${j.client_name || "N/A"}</td>
                    <td>${j.agent_type || "Custom"}</td>
                    <td class="mono">${formatCurrency(j.price)}</td>
                    <td><span class="status ${j.status}">${j.status}</span></td>
                    <td class="actions">
                        <select onchange="updateJobStatus(${j.id}, this.value)" style="padding:6px;border-radius:8px;background:rgba(255,255,255,0.08);color:#eaf2ff;border:1px solid rgba(255,255,255,0.1);">
                            <option value="pending" ${j.status==="pending"?"selected":""}>Pending</option>
                            <option value="in_progress" ${j.status==="in_progress"?"selected":""}>In Progress</option>
                            <option value="completed" ${j.status==="completed"?"selected":""}>Completed</option>
                        </select>
                    </td>
                </tr>
            `).join("");
        }

        async function updateJobStatus(id, status) {
            await pywebview.api.update_job_status(id, status);
            loadJobs();
            loadDashboard();
        }

        async function loadClients() {
            const clients = await pywebview.api.get_clients();
            document.getElementById("clients-count").textContent = clients.length;
            document.getElementById("clients-table").innerHTML = clients.map(c => `
                <tr>
                    <td>${c.name}</td>
                    <td>${c.email || "-"}</td>
                    <td>${c.company || "-"}</td>
                    <td>${c.source || "Direct"}</td>
                    <td>${c.job_count}</td>
                    <td class="mono">${formatCurrency(c.total_spent)}</td>
                    <td class="actions">
                        <button class="btn btn-small btn-danger" onclick="deleteClient(${c.id})">Delete</button>
                    </td>
                </tr>
            `).join("");
        }

        async function deleteClient(id) {
            if (confirm("Delete this client?")) {
                await pywebview.api.delete_client(id);
                loadClients();
            }
        }

        async function loadAgents() {
            const agents = await pywebview.api.get_agents();
            document.getElementById("agents-count").textContent = agents.length;
            document.getElementById("agents-grid").innerHTML = agents.map(a => `
                <div class="agent-card">
                    <div class="agent-header">
                        <span class="agent-name">${a.name}</span>
                        <span class="agent-status" style="background:${a.enabled ? "var(--success)" : "var(--danger)"}"></span>
                    </div>
                    <div class="agent-type">${a.type}</div>
                </div>
            `).join("");
        }

        async function loadRevenue() {
            const stats = await pywebview.api.get_dashboard_stats();
            const transactions = await pywebview.api.get_transactions();
            const chart = await pywebview.api.get_revenue_chart(90);

            document.getElementById("total-revenue").textContent = formatCurrency(stats.total_revenue);
            document.getElementById("month-revenue").textContent = formatCurrency(stats.month_revenue);

            document.getElementById("transactions-table").innerHTML = transactions.map(t => `
                <tr>
                    <td>${t.date?.split("T")[0] || "N/A"}</td>
                    <td>${t.description || t.job_title || "Payment"}</td>
                    <td style="color:${t.type==="income" ? "var(--success)" : "var(--danger)"}">
                        ${t.type==="income" ? "+" : "-"}${formatCurrency(Math.abs(t.amount))}
                    </td>
                </tr>
            `).join("");

            drawSparkline("revenue-chart", chart, "rgba(242,184,128,0.9)");
        }

        async function loadNotes() {
            const notes = await pywebview.api.get_notes();
            document.getElementById("notes-count").textContent = notes.length;
            document.getElementById("notes-grid").innerHTML = notes.map(n => `
                <div class="note-card ${n.pinned ? "pinned" : ""}" onclick="editNote(${n.id})">
                    <div class="note-title">${n.pinned ? "📌 " : ""}${n.title || "Untitled"}</div>
                    <div class="note-preview">${(n.content || "").substring(0, 100)}</div>
                    <div class="note-meta">${n.category} • ${n.updated_at?.split("T")[0]}</div>
                </div>
            `).join("");
        }

        function showModal(type) {
            const modal = document.getElementById("modal");
            const title = document.getElementById("modal-title");
            const body = document.getElementById("modal-body");

            if (type === "lead") {
                title.textContent = "Add Job Request";
                body.innerHTML = `
                    <div class="form-group">
                        <label>Source</label>
                        <select id="lead-source">
                            <option value="Upwork">Upwork</option>
                            <option value="Fiverr">Fiverr</option>
                            <option value="Referral">Referral</option>
                            <option value="Website">Website</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Client Name</label>
                        <input type="text" id="lead-name">
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" id="lead-email">
                    </div>
                    <div class="form-group">
                        <label>Description</label>
                        <textarea id="lead-desc"></textarea>
                    </div>
                    <div class="form-group">
                        <label>Budget</label>
                        <input type="text" id="lead-budget" placeholder="$500">
                    </div>
                    <button class="btn btn-primary" onclick="saveLead()">Save</button>
                `;
            } else if (type === "client") {
                title.textContent = "Add Client";
                body.innerHTML = `
                    <div class="form-group">
                        <label>Name</label>
                        <input type="text" id="client-name">
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" id="client-email">
                    </div>
                    <div class="form-group">
                        <label>Company</label>
                        <input type="text" id="client-company">
                    </div>
                    <div class="form-group">
                        <label>Source</label>
                        <input type="text" id="client-source" placeholder="Upwork, Referral, etc.">
                    </div>
                    <button class="btn btn-primary" onclick="saveClient()">Save</button>
                `;
            } else if (type === "job") {
                loadClientsForJob();
            } else if (type === "note") {
                title.textContent = "Add Note";
                body.innerHTML = `
                    <div class="form-group">
                        <label>Title</label>
                        <input type="text" id="note-title">
                    </div>
                    <div class="form-group">
                        <label>Content</label>
                        <textarea id="note-content"></textarea>
                    </div>
                    <div class="form-group">
                        <label>Category</label>
                        <select id="note-category">
                            <option value="general">General</option>
                            <option value="ideas">Ideas</option>
                            <option value="todo">To-Do</option>
                            <option value="client">Client</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" onclick="saveNote()">Save</button>
                `;
            }

            modal.classList.add("active");
        }

        async function loadClientsForJob() {
            const clients = await pywebview.api.get_clients();
            const title = document.getElementById("modal-title");
            const body = document.getElementById("modal-body");

            title.textContent = "Add Job";
            body.innerHTML = `
                <div class="form-group">
                    <label>Client</label>
                    <select id="job-client">
                        ${clients.map(c => `<option value="${c.id}">${c.name}</option>`).join("")}
                    </select>
                </div>
                <div class="form-group">
                    <label>Title</label>
                    <input type="text" id="job-title">
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea id="job-desc"></textarea>
                </div>
                <div class="form-group">
                    <label>Agent Type</label>
                    <select id="job-agent">
                        <option value="email_manager">Email Manager</option>
                        <option value="data_entry">Data Entry</option>
                        <option value="doc_processor">Document Processor</option>
                        <option value="custom">Custom</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Price ($)</label>
                    <input type="number" id="job-price" value="500">
                </div>
                <button class="btn btn-primary" onclick="saveJob()">Save</button>
            `;
        }

        function hideModal() {
            document.getElementById("modal").classList.remove("active");
        }

        async function saveLead() {
            await pywebview.api.add_lead(
                document.getElementById("lead-source").value,
                document.getElementById("lead-name").value,
                document.getElementById("lead-email").value,
                document.getElementById("lead-desc").value,
                document.getElementById("lead-budget").value
            );
            hideModal();
            loadLeads();
            loadDashboard();
        }

        async function saveClient() {
            await pywebview.api.add_client(
                document.getElementById("client-name").value,
                document.getElementById("client-email").value,
                document.getElementById("client-company").value,
                document.getElementById("client-source").value
            );
            hideModal();
            loadClients();
        }

        async function saveJob() {
            await pywebview.api.add_job(
                parseInt(document.getElementById("job-client").value),
                document.getElementById("job-title").value,
                document.getElementById("job-desc").value,
                document.getElementById("job-agent").value,
                parseFloat(document.getElementById("job-price").value)
            );
            hideModal();
            loadJobs();
            loadDashboard();
        }

        async function saveNote() {
            await pywebview.api.add_note(
                document.getElementById("note-title").value,
                document.getElementById("note-content").value,
                document.getElementById("note-category").value
            );
            hideModal();
            loadNotes();
        }

        window.addEventListener("pywebviewready", () => {
            const now = new Date();
            document.getElementById("today-chip").textContent = now.toLocaleDateString(undefined, {
                weekday: "short",
                month: "short",
                day: "numeric"
            });
            setTopbar("dashboard");
            loadDashboard();
        });
    </script>
</body>
</html>
'''


def main():
    """Launch the Cerberus dashboard app."""
    api = CerberusAPI()

    window = webview.create_window(
        'Cerberus Dashboard',
        html=HTML,
        js_api=api,
        width=1200,
        height=800,
        min_size=(900, 600)
    )

    webview.start()


if __name__ == "__main__":
    main()
