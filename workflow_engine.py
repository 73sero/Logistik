#!/usr/bin/env python3
"""
Workflow Engine - Orchestrates agent tasks based on events
Monitors DB for pending tasks and triggers appropriate agents
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List
from logistik_db import LogisticsDB

class WorkflowEngine:
    """Orchestrates multi-agent workflows"""
    
    def __init__(self):
        self.db = LogisticsDB()
        self.running = False
        self.last_check = datetime.now()
    
    def start(self):
        """Start the workflow engine (runs in background)"""
        self.running = True
        print("🚀 Workflow Engine started")
        print("⏰ Checking for tasks every 10 seconds...\n")
        
        try:
            while self.running:
                self.process_tasks()
                time.sleep(10)  # Check every 10 seconds
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the workflow engine"""
        self.running = False
        print("\n✋ Workflow Engine stopped")
    
    def process_tasks(self):
        """Process all pending tasks"""
        
        # Get pending tasks grouped by agent
        pending_tasks = self.db.get_pending_tasks()
        
        if not pending_tasks:
            return
        
        # Group by assigned_to
        tasks_by_agent = {}
        for task in pending_tasks:
            agent = task['assigned_to']
            if agent not in tasks_by_agent:
                tasks_by_agent[agent] = []
            tasks_by_agent[agent].append(task)
        
        # Route to appropriate handler
        for agent, tasks in tasks_by_agent.items():
            if agent == 'secretary':
                self._handle_secretary_tasks(tasks)
            elif agent == 'accounting':
                self._handle_accounting_tasks(tasks)
            elif agent == 'scheduler':
                self._handle_scheduler_tasks(tasks)
            elif agent == 'comms':
                self._handle_comms_tasks(tasks)
    
    # ============================================
    # SECRETARY TASKS
    # ============================================
    
    def _handle_secretary_tasks(self, tasks: List[Dict]):
        """Handle secretary agent tasks"""
        for task in tasks:
            task_type = task['task_type']
            
            print(f"📋 SECRETARY: {task['title']} (priority: {task['priority']})")
            
            if task_type == 'send_email':
                self._task_send_confirmation_email(task)
            elif task_type == 'send_thankyou_email':
                self._task_send_thankyou_email(task)
            elif task_type == 'prepare_contract':
                self._task_prepare_contract(task)
            
            # Mark as completed (in real system, agent would do this)
            # self.db.complete_task(task['id'])
    
    def _task_send_confirmation_email(self, task: Dict):
        """Send order confirmation to customer"""
        order = self.db.get_order(task['related_order_id'])
        customer = self.db.get_customer(task['related_customer_id'])
        
        if not order or not customer:
            return
        
        email_content = f"""
        Sehr geehrter {customer['name']},
        
        vielen Dank für deine Bestellung!
        
        Bestellung #{order['order_number']}
        Abhol-Adresse: {order['pickup_address']}
        Liefer-Adresse: {order['delivery_address']}
        Preis: €{order['total_price']}
        
        Dein Fahrer wird sich bald in Verbindung setzen.
        
        Beste Grüße,
        Logistics Team
        """
        
        print(f"  📧 Email an {customer['email']}")
        
        # In real system, this would call email API
        # self.send_email(customer['email'], "Bestellung bestätigt", email_content)
    
    def _task_send_thankyou_email(self, task: Dict):
        """Send thank you after delivery"""
        order = self.db.get_order(task['related_order_id'])
        customer = self.db.get_customer(task['related_customer_id'])
        
        if not order or not customer:
            return
        
        print(f"  📧 Thank you email an {customer['email']}")
    
    def _task_prepare_contract(self, task: Dict):
        """Prepare customer contract"""
        customer = self.db.get_customer(task['related_customer_id'])
        print(f"  📄 Contract prepared for {customer['name']}")
    
    # ============================================
    # ACCOUNTING TASKS
    # ============================================
    
    def _handle_accounting_tasks(self, tasks: List[Dict]):
        """Handle accounting agent tasks"""
        for task in tasks:
            task_type = task['task_type']
            
            print(f"💰 ACCOUNTING: {task['title']}")
            
            if task_type == 'create_invoice':
                self._task_create_invoice(task)
            elif task_type == 'send_payment_reminder':
                self._task_send_payment_reminder(task)
            elif task_type == 'calculate_driver_wage':
                self._task_calculate_driver_wage(task)
    
    def _task_create_invoice(self, task: Dict):
        """Create invoice for delivered order"""
        order = self.db.get_order(task['related_order_id'])
        customer = self.db.get_customer(task['related_customer_id'])
        
        if not order or not customer:
            return
        
        invoice_id = self.db.create_invoice(
            customer_id=customer['id'],
            order_id=order['id'],
            total_amount=float(order['total_price']),
            due_days=30
        )
        
        print(f"  💵 Invoice #{invoice_id} created for order #{order['id']}")
    
    def _task_send_payment_reminder(self, task: Dict):
        """Send payment reminder for overdue invoice"""
        print(f"  ⚠️ Payment reminder task: {task['title']}")
    
    def _task_calculate_driver_wage(self, task: Dict):
        """Calculate driver daily/weekly wage"""
        driver = self.db.get_driver(task['related_driver_id'])
        print(f"  💵 Wage calculated for {driver['name']}")
    
    # ============================================
    # SCHEDULER TASKS
    # ============================================
    
    def _handle_scheduler_tasks(self, tasks: List[Dict]):
        """Handle scheduler agent tasks"""
        for task in tasks:
            task_type = task['task_type']
            
            print(f"📅 SCHEDULER: {task['title']} (priority: {task['priority']})")
            
            if task_type == 'assign_driver':
                self._task_assign_driver(task)
            elif task_type == 'send_daily_reminder':
                self._task_send_daily_reminder(task)
            elif task_type == 'check_overdue':
                self._task_check_overdue(task)
    
    def _task_assign_driver(self, task: Dict):
        """Assign order to best available driver"""
        order = self.db.get_order(task['related_order_id'])
        
        if not order:
            return
        
        # Find best driver (simplified)
        drivers = self.db.get_active_drivers()
        
        if not drivers:
            print(f"  ⚠️ No drivers available for order #{order['id']}")
            return
        
        best_driver = drivers[0]  # In real system, calculate optimal
        
        self.db.assign_order(order['id'], best_driver['id'])
        
        print(f"  🚗 Order #{order['id']} assigned to {best_driver['name']}")
        
        # Create notification task for COMMS
        self.db.create_task(
            title=f"Notify {best_driver['name']} about order #{order['id']}",
            task_type='notify_driver',
            assigned_to='comms',
            related_order_id=order['id'],
            related_driver_id=best_driver['id'],
            priority='high'
        )
    
    def _task_send_daily_reminder(self, task: Dict):
        """Send daily reminder to drivers"""
        drivers = self.db.get_active_drivers()
        print(f"  📢 Daily reminder sent to {len(drivers)} drivers")
    
    def _task_check_overdue(self, task: Dict):
        """Check for overdue orders and flag them"""
        overdue = self.db.get_overdue_orders()
        
        if overdue:
            print(f"  ⚠️ {len(overdue)} overdue orders detected!")
            
            # Create escalation task
            for order in overdue:
                self.db.create_task(
                    title=f"URGENT: Order #{order['id']} overdue by {self._time_since(order['deadline'])}",
                    task_type='escalate',
                    assigned_to='dispatcher',  # Escalate to me
                    related_order_id=order['id'],
                    priority='critical'
                )
    
    # ============================================
    # COMMS TASKS
    # ============================================
    
    def _handle_comms_tasks(self, tasks: List[Dict]):
        """Handle communication agent tasks"""
        for task in tasks:
            task_type = task['task_type']
            
            print(f"💬 COMMS: {task['title']}")
            
            if task_type == 'notify_customer':
                self._task_notify_customer(task)
            elif task_type == 'notify_driver':
                self._task_notify_driver(task)
            elif task_type == 'send_status_update':
                self._task_send_status_update(task)
    
    def _task_notify_customer(self, task: Dict):
        """Notify customer about order status"""
        order = self.db.get_order(task['related_order_id'])
        customer = self.db.get_customer(task['related_customer_id'])
        
        if not order or not customer:
            return
        
        message = f"Update für Bestellung #{order['order_number']}: Status = {order['status']}"
        
        # In real system, send SMS/email
        print(f"  📱 SMS/Email to {customer['phone']}: {message}")
    
    def _task_notify_driver(self, task: Dict):
        """Notify driver about new assignment"""
        driver = self.db.get_driver(task['related_driver_id'])
        order = self.db.get_order(task['related_order_id'])
        
        if not driver or not order:
            return
        
        message = f"Neue Order: #{order['order_number']}, Pickup: {order['pickup_address']}"
        
        # In real system, send SMS/WhatsApp
        print(f"  💬 WhatsApp to {driver['name']} ({driver['phone']}): {message}")
    
    def _task_send_status_update(self, task: Dict):
        """Send status update to customer"""
        order = self.db.get_order(task['related_order_id'])
        print(f"  ✅ Status update sent for order #{order['id']}")
    
    # ============================================
    # DISPATCHER ESCALATIONS
    # ============================================
    
    def handle_dispatcher_escalation(self, task: Dict):
        """Handle critical escalations (complex decisions)"""
        print(f"\n🔴 DISPATCHER ESCALATION: {task['title']}")
        print(f"   Priority: {task['priority']}")
        print(f"   Task: {task}")
        
        # This is where human (or GPT-5.2) makes decision
        # In real system, would call OpenClaw with context
    
    # ============================================
    # HELPERS
    # ============================================
    
    def _time_since(self, timestamp_str: str) -> str:
        """Calculate time since timestamp"""
        if not timestamp_str:
            return "unknown"
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            delta = datetime.now() - timestamp
            minutes = delta.total_seconds() // 60
            if minutes < 60:
                return f"{int(minutes)}m"
            hours = minutes // 60
            return f"{int(hours)}h"
        except:
            return "?"
    
    def print_summary(self):
        """Print workflow summary"""
        summary = self.db.get_summary()
        print("\n📊 WORKFLOW SUMMARY:")
        print(f"  Pending Orders: {summary['pending_orders']}")
        print(f"  In Transit: {summary['in_transit']}")
        print(f"  Overdue: {summary['overdue_orders']}")
        print(f"  Unpaid Invoices: {summary['unpaid_invoices']}")
        print(f"  Active Drivers: {summary['active_drivers']}")

# ============================================
# STARTUP
# ============================================

if __name__ == "__main__":
    engine = WorkflowEngine()
    
    # Print startup info
    print("=" * 50)
    print("🚚 LOGISTICS WORKFLOW ENGINE")
    print("=" * 50)
    engine.print_summary()
    print("\nStarting automation...\n")
    
    # Start processing
    try:
        engine.start()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
