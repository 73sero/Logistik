#!/usr/bin/env python3
"""
Logistics API - REST endpoints for driver app, webhooks, etc.
Run: python logistik_api.py
"""

from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
from pathlib import Path
import json
from logistik_db import LogisticsDB

app = Flask(__name__)
DASHBOARD_PATH = Path(__file__).parent / 'dashboard'
JARVIS_PATH = Path(__file__).parent / 'jarvis_dashboard'

# CORS Headers
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response
db = LogisticsDB()

# ============================================
# DASHBOARD ENDPOINTS
# ============================================

@app.route('/')
def root():
    """Serve main dashboard"""
    return send_from_directory(DASHBOARD_PATH, 'index.html')

@app.route('/dashboard')
def dashboard():
    """Logistics dashboard"""
    return send_from_directory(DASHBOARD_PATH, 'index.html')

@app.route('/dashboard/<path:path>')
def serve_dashboard(path):
    """Serve dashboard assets"""
    return send_from_directory(DASHBOARD_PATH, path)

# ============================================
# JARVIS ENDPOINTS
# ============================================

@app.route('/jarvis')
def jarvis_desktop():
    """Jarvis desktop dashboard"""
    return send_from_directory(JARVIS_PATH, 'index.html')

@app.route('/jarvis/mobile')
def jarvis_mobile():
    """Jarvis mobile dashboard"""
    return send_from_directory(JARVIS_PATH, 'mobile.html')

@app.route('/jarvis_dashboard')
def jarvis_redirect():
    """Redirect to jarvis desktop"""
    return send_from_directory(JARVIS_PATH, 'index.html')

@app.route('/jarvis_dashboard/mobile.html')
def jarvis_mobile_html():
    """Jarvis mobile dashboard (direct path)"""
    return send_from_directory(JARVIS_PATH, 'mobile.html')

@app.route('/jarvis_dashboard/<path:path>')
def serve_jarvis(path):
    """Serve jarvis assets"""
    return send_from_directory(JARVIS_PATH, path)

# ============================================
# DRIVER ENDPOINTS
# ============================================

@app.route('/api/driver/login', methods=['POST'])
def driver_login():
    """Driver logs in, gets today's orders"""
    data = request.json
    driver_id = data.get('driver_id')
    phone = data.get('phone')
    
    if not driver_id or not phone:
        return jsonify({'error': 'Missing driver_id or phone'}), 400
    
    driver = db.get_driver(driver_id)
    if not driver or driver['phone'] != phone:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Update status to online
    db.update_driver_status(driver_id, 'online')
    
    # Get today's orders
    orders = db.get_orders_by_driver(driver_id)
    
    return jsonify({
        'success': True,
        'driver': driver,
        'orders': orders
    }), 200

@app.route('/api/driver/status', methods=['POST'])
def update_driver_status():
    """Update driver status (online/offline/on_delivery)"""
    data = request.json
    driver_id = data.get('driver_id')
    status = data.get('status')  # online, offline, on_delivery
    location = data.get('location')  # optional GPS
    
    if not driver_id or not status:
        return jsonify({'error': 'Missing driver_id or status'}), 400
    
    db.update_driver_status(driver_id, status, location)
    
    return jsonify({'success': True, 'message': f'Status updated to {status}'}), 200

@app.route('/api/driver/orders/<int:driver_id>', methods=['GET'])
def get_driver_orders(driver_id):
    """Get all orders for driver"""
    orders = db.get_orders_by_driver(driver_id)
    return jsonify({
        'success': True,
        'orders': orders,
        'count': len(orders)
    }), 200

@app.route('/api/driver/order/<int:order_id>/start', methods=['POST'])
def start_delivery(order_id):
    """Driver starts delivery"""
    data = request.json
    driver_id = data.get('driver_id')
    
    order = db.get_order(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    db.update_order_status(order_id, 'in_transit')
    
    # Log message
    db.log_message(
        order_id=order_id,
        from_type='driver',
        from_id=driver_id,
        message_text=f'Started delivery to {order["delivery_address"]}',
        channel='system'
    )
    
    return jsonify({
        'success': True,
        'message': 'Delivery started',
        'order': db.get_order(order_id)
    }), 200

@app.route('/api/driver/order/<int:order_id>/complete', methods=['POST'])
def complete_delivery(order_id):
    """Driver marks delivery as complete"""
    data = request.json
    driver_id = data.get('driver_id')
    photo_path = data.get('photo_path')  # proof of delivery
    signature_path = data.get('signature_path')
    notes = data.get('notes', '')
    
    order = db.get_order(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    # Update order
    update_data = {
        'status': 'delivered',
        'delivery_time': datetime.now().isoformat()
    }
    if photo_path:
        update_data['photo_path'] = photo_path
    if signature_path:
        update_data['signature_path'] = signature_path
    
    db.update('orders', order_id, update_data)
    
    # Log message
    db.log_message(
        order_id=order_id,
        from_type='driver',
        from_id=driver_id,
        message_text=f'Delivery completed. Notes: {notes}',
        channel='system'
    )
    
    # Create invoice automatically
    invoice_id = db.create_invoice(
        customer_id=order['customer_id'],
        order_id=order_id,
        total_amount=float(order['total_price']),
        due_days=30
    )
    
    # Create task for SECRETARY to send thank-you email
    db.create_task(
        title=f'Send delivery confirmation to {order["customer_id"]}',
        task_type='send_email',
        assigned_to='secretary',
        related_order_id=order_id,
        related_customer_id=order['customer_id']
    )
    
    return jsonify({
        'success': True,
        'message': 'Delivery completed',
        'invoice_id': invoice_id,
        'order': db.get_order(order_id)
    }), 200

@app.route('/api/driver/order/<int:order_id>/update', methods=['POST'])
def update_order_message(order_id):
    """Driver sends location/status update"""
    data = request.json
    driver_id = data.get('driver_id')
    message = data.get('message')  # e.g., "Delayed, traffic jam"
    location = data.get('location')  # GPS location
    
    order = db.get_order(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    # Log the message
    db.log_message(
        order_id=order_id,
        from_type='driver',
        from_id=driver_id,
        message_text=message,
        channel='sms'
    )
    
    # Update driver location
    if location:
        db.update_driver_status(driver_id, 'on_delivery', location)
    
    # Create task for COMMS agent to notify customer
    db.create_task(
        title=f'Notify customer: {message}',
        task_type='notify_customer',
        assigned_to='comms',
        related_order_id=order_id,
        related_customer_id=order['customer_id'],
        priority='high'
    )
    
    return jsonify({
        'success': True,
        'message': 'Update logged, customer will be notified'
    }), 200

# ============================================
# CUSTOMER ENDPOINTS
# ============================================

@app.route('/api/customer/order', methods=['POST'])
def create_new_order():
    """Customer creates new order"""
    data = request.json
    
    # Find or create customer
    customer = db.find_customer(email=data.get('email'))
    if not customer:
        customer_id = db.create_customer(
            name=data.get('name'),
            phone=data.get('phone'),
            email=data.get('email'),
            address=data.get('address'),
            city=data.get('city')
        )
    else:
        customer_id = customer['id']
    
    # Create order
    order_id = db.create_order(
        customer_id=customer_id,
        pickup_address=data.get('pickup_address'),
        delivery_address=data.get('delivery_address'),
        base_price=float(data.get('price', 50.0)),
        parcel_description=data.get('description'),
        weight_kg=float(data.get('weight_kg', 0))
    )
    
    # Create task for SCHEDULER to assign driver
    db.create_task(
        title=f'Assign driver for order #{order_id}',
        task_type='assign_driver',
        assigned_to='scheduler',
        related_order_id=order_id,
        priority='high'
    )
    
    return jsonify({
        'success': True,
        'order_id': order_id,
        'customer_id': customer_id,
        'status': 'pending'
    }), 201

@app.route('/api/customer/order/<int:order_id>', methods=['GET'])
def get_order_status(order_id):
    """Customer checks order status"""
    order = db.get_order(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    # Get messages (for customer communication)
    messages = db.get_order_messages(order_id)
    
    # Get driver info if assigned
    driver = None
    if order['assigned_driver_id']:
        driver = db.get_driver(order['assigned_driver_id'])
    
    return jsonify({
        'success': True,
        'order': order,
        'driver': driver,
        'messages': messages
    }), 200

# ============================================
# ADMIN/BACKOFFICE ENDPOINTS
# ============================================

@app.route('/api/admin/dashboard', methods=['GET'])
def get_dashboard():
    """Get admin dashboard summary"""
    summary = db.get_summary()
    return jsonify({
        'success': True,
        'summary': summary,
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/admin/tasks', methods=['GET'])
def get_pending_tasks():
    """Get all pending tasks for agents"""
    agent = request.args.get('agent')  # filter by agent if provided
    tasks = db.get_pending_tasks(assigned_to=agent)
    return jsonify({
        'success': True,
        'tasks': tasks,
        'count': len(tasks)
    }), 200

@app.route('/api/admin/invoices/unpaid', methods=['GET'])
def get_unpaid_invoices():
    """Get unpaid invoices"""
    invoices = db.get_unpaid_invoices()
    return jsonify({
        'success': True,
        'invoices': invoices,
        'total_amount': sum(inv['total_amount'] for inv in invoices)
    }), 200

@app.route('/api/admin/drivers', methods=['GET'])
def get_all_drivers():
    """Get all drivers"""
    drivers = db.get_active_drivers()
    return jsonify({
        'success': True,
        'drivers': drivers,
        'online_count': sum(1 for d in drivers if d['status'] == 'online')
    }), 200

# ============================================
# WEBHOOK ENDPOINTS (for external integrations)
# ============================================

@app.route('/webhook/order/update', methods=['POST'])
def webhook_order_update():
    """Webhook for external order updates"""
    data = request.json
    
    # Log to messages
    db.log_message(
        order_id=data.get('order_id'),
        from_type='system',
        from_id=0,
        message_text=f"Webhook update: {data.get('message', 'Status changed')}",
        channel='webhook'
    )
    
    return jsonify({'success': True}), 200

# ============================================
# AGENT COMMUNICATION ENDPOINTS
# ============================================

@app.route('/api/agent/acknowledge-task', methods=['POST'])
def acknowledge_task():
    """Agent acknowledges task completion"""
    data = request.json
    task_id = data.get('task_id')
    
    db.complete_task(task_id)
    
    return jsonify({'success': True, 'message': 'Task completed'}), 200

@app.route('/api/agent/send-message', methods=['POST'])
def agent_send_message():
    """Agent sends message (email/SMS to driver/customer)"""
    data = request.json
    
    # Log to database
    db.log_message(
        order_id=data.get('order_id'),
        from_type='system',
        from_id=0,
        message_text=data.get('message'),
        channel=data.get('channel', 'email')
    )
    
    # TODO: Actually send via email/SMS API
    # For now, just log
    
    return jsonify({
        'success': True,
        'message': 'Message queued for sending'
    }), 200

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================
# STARTUP
# ============================================

if __name__ == '__main__':
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Logistics API Server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on (default: 5000)')
    args = parser.parse_args()
    
    port = args.port
    
    print("\n" + "="*60)
    print("🚀 LOGISTICS API + JARVIS DASHBOARDS STARTING...")
    print("="*60)
    print("\n📍 MAIN ENDPOINTS:")
    print(f"  🚚 Logistics: http://localhost:{port}/dashboard")
    print(f"  ⚡ Jarvis Desktop: http://localhost:{port}/jarvis")
    print(f"  📱 Jarvis Mobile: http://localhost:{port}/jarvis/mobile")
    print("\n🔌 API ENDPOINTS:")
    print("  GET  /api/admin/dashboard")
    print("  POST /api/customer/order")
    print("  POST /api/driver/order/{id}/complete")
    print("  POST /api/agent/send-message")
    print("\n⚡ DASHBOARD FEATURES:")
    print("  ✅ Logistics Backoffice")
    print("  ✅ Jarvis Desktop Control Center")
    print("  ✅ Jarvis Mobile App (native feel)")
    print("\n" + "="*60)
    print("Press CTRL+C to stop")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=port)
