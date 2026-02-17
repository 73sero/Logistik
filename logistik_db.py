#!/usr/bin/env python3
"""
Logistics Database - Agent Library
Simple API for agents to read/write data
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

DB_PATH = Path("/data/.openclaw/workspace/logistik.db")

class LogisticsDB:
    """Simple SQLite wrapper for agents"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
    
    def query(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute SELECT query, return list of dicts"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def insert(self, table: str, data: Dict) -> int:
        """Insert row, return id"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        try:
            cursor.execute(sql, tuple(data.values()))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def update(self, table: str, id: int, data: Dict) -> bool:
        """Update row by id"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        set_clause = ', '.join(f"{k}=?" for k in data.keys())
        sql = f"UPDATE {table} SET {set_clause}, updated_at=CURRENT_TIMESTAMP WHERE id=?"
        
        try:
            cursor.execute(sql, tuple(list(data.values()) + [id]))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    # ========== CUSTOMER FUNCTIONS ==========
    
    def get_customer(self, customer_id: int) -> Optional[Dict]:
        """Get customer by ID"""
        results = self.query("SELECT * FROM customers WHERE id=?", (customer_id,))
        return results[0] if results else None
    
    def find_customer(self, email: str = None, phone: str = None) -> Optional[Dict]:
        """Find customer by email or phone"""
        if email:
            results = self.query("SELECT * FROM customers WHERE email=?", (email,))
        elif phone:
            results = self.query("SELECT * FROM customers WHERE phone=?", (phone,))
        else:
            return None
        return results[0] if results else None
    
    def create_customer(self, name: str, phone: str, address: str, 
                       email: str = None, city: str = None, company_name: str = None) -> int:
        """Create new customer"""
        data = {
            'name': name,
            'phone': phone,
            'address': address,
            'email': email or '',
            'city': city or '',
            'company_name': company_name or ''
        }
        return self.insert('customers', data)
    
    # ========== ORDER FUNCTIONS ==========
    
    def get_order(self, order_id: int) -> Optional[Dict]:
        """Get order by ID"""
        results = self.query("SELECT * FROM orders WHERE id=?", (order_id,))
        return results[0] if results else None
    
    def get_orders_by_status(self, status: str) -> List[Dict]:
        """Get all orders with specific status"""
        return self.query("SELECT * FROM orders WHERE status=? ORDER BY deadline", (status,))
    
    def get_orders_by_driver(self, driver_id: int) -> List[Dict]:
        """Get all orders for driver"""
        return self.query(
            "SELECT * FROM orders WHERE assigned_driver_id=? ORDER BY deadline",
            (driver_id,)
        )
    
    def get_overdue_orders(self) -> List[Dict]:
        """Get all overdue orders"""
        return self.query(
            "SELECT * FROM orders WHERE status != 'delivered' AND deadline < CURRENT_TIMESTAMP"
        )
    
    def create_order(self, customer_id: int, pickup_address: str, delivery_address: str,
                    base_price: float, deadline: str = None, **kwargs) -> int:
        """Create new order"""
        import uuid
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        data = {
            'order_number': order_number,
            'customer_id': customer_id,
            'pickup_address': pickup_address,
            'delivery_address': delivery_address,
            'base_price': base_price,
            'total_price': base_price,
            'status': 'pending',
            'deadline': deadline or (datetime.now() + timedelta(days=1)).isoformat()
        }
        data.update(kwargs)  # Merge additional fields
        
        return self.insert('orders', data)
    
    def assign_order(self, order_id: int, driver_id: int) -> bool:
        """Assign order to driver"""
        return self.update('orders', order_id, {
            'assigned_driver_id': driver_id,
            'status': 'assigned',
            'assigned_at': datetime.now().isoformat()
        })
    
    def update_order_status(self, order_id: int, status: str, **kwargs) -> bool:
        """Update order status"""
        data = {'status': status}
        
        if status == 'delivered':
            data['delivery_time'] = datetime.now().isoformat()
        elif status == 'in_transit':
            data['pickup_time'] = datetime.now().isoformat()
        
        data.update(kwargs)
        return self.update('orders', order_id, data)
    
    # ========== DRIVER FUNCTIONS ==========
    
    def get_driver(self, driver_id: int) -> Optional[Dict]:
        """Get driver by ID"""
        results = self.query("SELECT * FROM drivers WHERE id=?", (driver_id,))
        return results[0] if results else None
    
    def get_active_drivers(self) -> List[Dict]:
        """Get all online drivers"""
        return self.query("SELECT * FROM drivers WHERE status='online' ORDER BY name")
    
    def update_driver_status(self, driver_id: int, status: str, location: str = None) -> bool:
        """Update driver status"""
        data = {'status': status, 'last_active': datetime.now().isoformat()}
        if location:
            data['current_location'] = location
        return self.update('drivers', driver_id, data)
    
    # ========== INVOICE FUNCTIONS ==========
    
    def get_invoice(self, invoice_id: int) -> Optional[Dict]:
        """Get invoice by ID"""
        results = self.query("SELECT * FROM invoices WHERE id=?", (invoice_id,))
        return results[0] if results else None
    
    def create_invoice(self, customer_id: int, order_id: int, 
                      total_amount: float, due_days: int = 30) -> int:
        """Create invoice for order"""
        import uuid
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        due_date = (datetime.now() + timedelta(days=due_days)).date()
        
        data = {
            'invoice_number': invoice_number,
            'customer_id': customer_id,
            'order_id': order_id,
            'subtotal': total_amount / 1.19,  # Remove VAT
            'tax_amount': total_amount - (total_amount / 1.19),
            'total_amount': total_amount,
            'issue_date': datetime.now().date(),
            'due_date': due_date,
            'status': 'draft'
        }
        return self.insert('invoices', data)
    
    def get_unpaid_invoices(self) -> List[Dict]:
        """Get all unpaid invoices"""
        return self.query(
            "SELECT * FROM invoices WHERE status IN ('sent', 'viewed', 'overdue') ORDER BY due_date"
        )
    
    def get_overdue_invoices(self) -> List[Dict]:
        """Get overdue invoices"""
        return self.query(
            "SELECT * FROM invoices WHERE due_date < CURRENT_DATE AND status != 'paid'"
        )
    
    # ========== MESSAGE FUNCTIONS ==========
    
    def log_message(self, order_id: int, from_type: str, from_id: int,
                   message_text: str, channel: str = 'sms') -> int:
        """Log communication message"""
        data = {
            'order_id': order_id,
            'from_type': from_type,
            'from_id': from_id,
            'to_type': 'system',
            'to_id': 0,
            'message_text': message_text,
            'channel': channel
        }
        return self.insert('messages', data)
    
    def get_order_messages(self, order_id: int) -> List[Dict]:
        """Get all messages for order"""
        return self.query(
            "SELECT * FROM messages WHERE order_id=? ORDER BY sent_at DESC",
            (order_id,)
        )
    
    # ========== TASK FUNCTIONS ==========
    
    def create_task(self, title: str, task_type: str, assigned_to: str,
                   deadline: str = None, **kwargs) -> int:
        """Create task for agent"""
        data = {
            'title': title,
            'task_type': task_type,
            'assigned_to': assigned_to,
            'deadline': deadline or (datetime.now() + timedelta(hours=24)).isoformat(),
            'status': 'pending'
        }
        data.update(kwargs)
        return self.insert('tasks', data)
    
    def get_pending_tasks(self, assigned_to: str = None) -> List[Dict]:
        """Get pending tasks"""
        if assigned_to:
            return self.query(
                "SELECT * FROM tasks WHERE status='pending' AND assigned_to=? ORDER BY deadline",
                (assigned_to,)
            )
        return self.query("SELECT * FROM tasks WHERE status='pending' ORDER BY deadline")
    
    def complete_task(self, task_id: int) -> bool:
        """Mark task as completed"""
        return self.update('tasks', task_id, {
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        })
    
    # ========== ANALYTICS ==========
    
    def get_daily_metrics(self, date: str = None) -> Optional[Dict]:
        """Get metrics for specific day"""
        if not date:
            date = datetime.now().date()
        results = self.query("SELECT * FROM daily_metrics WHERE metric_date=?", (date,))
        return results[0] if results else None
    
    def get_summary(self) -> Dict:
        """Get quick business summary"""
        summary = {
            'pending_orders': len(self.get_orders_by_status('pending')),
            'in_transit': len(self.get_orders_by_status('in_transit')),
            'overdue_orders': len(self.get_overdue_orders()),
            'unpaid_invoices': len(self.get_unpaid_invoices()),
            'overdue_invoices': len(self.get_overdue_invoices()),
            'active_drivers': len(self.get_active_drivers()),
        }
        return summary

# ========== QUICK USAGE EXAMPLES ==========

if __name__ == "__main__":
    db = LogisticsDB()
    
    print("🚚 Logistics DB Ready!")
    print("\nQuick Summary:")
    summary = db.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Example: Create new order
    print("\n📦 Creating sample order...")
    order_id = db.create_order(
        customer_id=1,
        pickup_address="Hauptstr. 10, 10115 Berlin",
        delivery_address="Nebenstr. 5, 80331 Munich",
        base_price=50.00,
        parcel_description="Electronics package",
        weight_kg=2.5
    )
    print(f"✅ Order created: #{order_id}")
