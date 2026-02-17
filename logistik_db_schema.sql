-- ============================================
-- LOGISTIK BACKOFFICE - SQLite Database Schema
-- ============================================
-- Created for Sero's AI Logistics Agent Team

-- CUSTOMERS TABLE
CREATE TABLE IF NOT EXISTS customers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT NOT NULL,
  address TEXT NOT NULL,
  city TEXT,
  postal_code TEXT,
  country TEXT DEFAULT 'Germany',
  company_name TEXT,
  tax_id TEXT,
  payment_terms TEXT DEFAULT '30', -- days
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(email, phone)
);

-- DRIVERS TABLE
CREATE TABLE IF NOT EXISTS drivers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  phone TEXT NOT NULL UNIQUE,
  email TEXT,
  vehicle_type TEXT, -- e.g., 'bike', 'van', 'truck'
  vehicle_registration TEXT,
  license_plate TEXT UNIQUE,
  license_number TEXT,
  insurance_until DATE,
  status TEXT DEFAULT 'offline', -- online, offline, on_delivery, break
  current_location TEXT, -- GPS or address
  current_order_id INTEGER,
  total_deliveries INTEGER DEFAULT 0,
  rating REAL DEFAULT 5.0,
  last_active TIMESTAMP,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(current_order_id) REFERENCES orders(id)
);

-- ORDERS TABLE (Core)
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_number TEXT NOT NULL UNIQUE, -- e.g., '2024-001', auto-generated
  customer_id INTEGER NOT NULL,
  
  -- Pickup Details
  pickup_address TEXT NOT NULL,
  pickup_city TEXT,
  pickup_postal TEXT,
  pickup_contact_name TEXT,
  pickup_contact_phone TEXT,
  pickup_notes TEXT,
  pickup_time_window TEXT, -- e.g., '09:00-12:00'
  
  -- Delivery Details
  delivery_address TEXT NOT NULL,
  delivery_city TEXT,
  delivery_postal TEXT,
  delivery_contact_name TEXT,
  delivery_contact_phone TEXT,
  delivery_notes TEXT,
  delivery_time_window TEXT,
  
  -- Parcel Info
  parcel_description TEXT,
  weight_kg REAL,
  dimensions_cm TEXT, -- e.g., '30x20x15'
  fragile BOOLEAN DEFAULT 0,
  requires_signature BOOLEAN DEFAULT 1,
  
  -- Status & Tracking
  status TEXT DEFAULT 'pending', -- pending, assigned, picked_up, in_transit, delivered, failed, cancelled
  priority TEXT DEFAULT 'normal', -- low, normal, high, urgent
  assigned_driver_id INTEGER,
  
  -- Timeline
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  assigned_at TIMESTAMP,
  pickup_time TIMESTAMP,
  delivery_time TIMESTAMP,
  deadline TIMESTAMP,
  
  -- Revenue
  base_price DECIMAL(10, 2) NOT NULL,
  surcharge DECIMAL(10, 2) DEFAULT 0, -- rush fee, distance, etc.
  total_price DECIMAL(10, 2) NOT NULL,
  
  -- Proof
  signature_path TEXT, -- image path
  photo_path TEXT, -- delivery proof
  
  FOREIGN KEY(customer_id) REFERENCES customers(id),
  FOREIGN KEY(assigned_driver_id) REFERENCES drivers(id)
);

-- DRIVER ASSIGNMENTS (History tracking)
CREATE TABLE IF NOT EXISTS driver_assignments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  driver_id INTEGER NOT NULL,
  order_id INTEGER NOT NULL,
  assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  status TEXT DEFAULT 'assigned', -- assigned, started, completed, failed
  reason_if_failed TEXT,
  driver_notes TEXT,
  FOREIGN KEY(driver_id) REFERENCES drivers(id),
  FOREIGN KEY(order_id) REFERENCES orders(id)
);

-- INVOICES TABLE
CREATE TABLE IF NOT EXISTS invoices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  invoice_number TEXT NOT NULL UNIQUE, -- e.g., 'INV-2024-001'
  order_id INTEGER,
  customer_id INTEGER NOT NULL,
  
  -- Invoice Details
  issue_date DATE NOT NULL,
  due_date DATE NOT NULL,
  payment_terms_days INTEGER DEFAULT 30,
  
  -- Amounts
  subtotal DECIMAL(10, 2) NOT NULL,
  tax_rate REAL DEFAULT 0.19, -- Germany VAT
  tax_amount DECIMAL(10, 2),
  total_amount DECIMAL(10, 2) NOT NULL,
  
  -- Payment
  status TEXT DEFAULT 'draft', -- draft, sent, viewed, paid, overdue, cancelled
  paid_amount DECIMAL(10, 2) DEFAULT 0,
  paid_at TIMESTAMP,
  payment_method TEXT, -- bank_transfer, credit_card, cash
  
  -- Tracking
  sent_at TIMESTAMP,
  viewed_at TIMESTAMP,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY(order_id) REFERENCES orders(id),
  FOREIGN KEY(customer_id) REFERENCES customers(id)
);

-- EXPENSES TABLE
CREATE TABLE IF NOT EXISTS expenses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  driver_id INTEGER,
  category TEXT NOT NULL, -- fuel, maintenance, toll, parking, other
  description TEXT,
  amount DECIMAL(10, 2) NOT NULL,
  receipt_path TEXT,
  expense_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(driver_id) REFERENCES drivers(id)
);

-- MESSAGES TABLE (Fahrer + Kunden Kommunikation)
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER,
  from_type TEXT NOT NULL, -- 'driver', 'customer', 'system'
  from_id INTEGER, -- driver_id or customer_id
  to_type TEXT NOT NULL,
  to_id INTEGER,
  
  message_text TEXT NOT NULL,
  message_type TEXT DEFAULT 'text', -- text, image, location, signature
  attachment_path TEXT,
  
  -- Channel
  channel TEXT DEFAULT 'sms', -- sms, whatsapp, email, in_app
  
  -- Delivery Status
  sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  delivered_at TIMESTAMP,
  read_at TIMESTAMP,
  
  FOREIGN KEY(order_id) REFERENCES orders(id)
);

-- TASKS TABLE (Internal agent tasks)
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  task_type TEXT, -- 'follow_up', 'reminder', 'contact_customer', 'contact_driver', 'invoice_issue'
  assigned_to TEXT, -- agent name ('secretary', 'accounting', 'scheduler', 'comms')
  
  related_order_id INTEGER,
  related_customer_id INTEGER,
  related_driver_id INTEGER,
  
  priority TEXT DEFAULT 'normal', -- low, normal, high, critical
  status TEXT DEFAULT 'pending', -- pending, in_progress, completed, cancelled
  
  deadline TIMESTAMP,
  completed_at TIMESTAMP,
  notes TEXT,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY(related_order_id) REFERENCES orders(id),
  FOREIGN KEY(related_customer_id) REFERENCES customers(id),
  FOREIGN KEY(related_driver_id) REFERENCES drivers(id)
);

-- DAILY METRICS TABLE (For analytics)
CREATE TABLE IF NOT EXISTS daily_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  metric_date DATE NOT NULL UNIQUE,
  
  -- Orders
  orders_created INTEGER DEFAULT 0,
  orders_delivered INTEGER DEFAULT 0,
  orders_failed INTEGER DEFAULT 0,
  
  -- Revenue
  total_revenue DECIMAL(10, 2) DEFAULT 0,
  total_costs DECIMAL(10, 2) DEFAULT 0,
  total_profit DECIMAL(10, 2) DEFAULT 0,
  
  -- Drivers
  drivers_active INTEGER DEFAULT 0,
  total_km REAL DEFAULT 0,
  
  -- Customer
  customers_new INTEGER DEFAULT 0,
  
  -- Quality
  on_time_deliveries INTEGER DEFAULT 0,
  failed_deliveries INTEGER DEFAULT 0,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DOCUMENTS TABLE (Contracts, agreements, etc.)
CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  document_type TEXT NOT NULL, -- 'contract', 'agreement', 'terms', 'invoice_template'
  related_customer_id INTEGER,
  related_driver_id INTEGER,
  
  document_name TEXT NOT NULL,
  file_path TEXT NOT NULL,
  version INTEGER DEFAULT 1,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  signed_at TIMESTAMP,
  signed_by TEXT,
  
  FOREIGN KEY(related_customer_id) REFERENCES customers(id),
  FOREIGN KEY(related_driver_id) REFERENCES drivers(id)
);

-- ============================================
-- INDEXES (for performance)
-- ============================================

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_driver ON orders(assigned_driver_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_deadline ON orders(deadline);

CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date);

CREATE INDEX IF NOT EXISTS idx_messages_order ON messages(order_id);
CREATE INDEX IF NOT EXISTS idx_messages_channel ON messages(channel);

CREATE INDEX IF NOT EXISTS idx_drivers_status ON drivers(status);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(deadline);

-- ============================================
-- SAMPLE DATA (optional, for testing)
-- ============================================

-- Customer Example
INSERT OR IGNORE INTO customers (name, email, phone, address, city, postal_code, company_name, payment_terms)
VALUES 
  ('Max Müller', 'max@example.de', '+49123456789', 'Hauptstr. 10', 'Berlin', '10115', 'Müller GmbH', '30'),
  ('Anna Schmidt', 'anna@example.de', '+49987654321', 'Nebenstr. 5', 'Munich', '80331', 'Schmidt AG', '14');

-- Driver Example
INSERT OR IGNORE INTO drivers (name, phone, vehicle_type, vehicle_registration, license_plate, status)
VALUES 
  ('Ahmed', '+49711123456', 'van', 'DE-123456', 'B-AH-123', 'online'),
  ('Sarah', '+49711234567', 'bike', 'DE-234567', 'B-SA-456', 'online'),
  ('Tom', '+49711345678', 'car', 'DE-345678', 'B-TO-789', 'offline');
