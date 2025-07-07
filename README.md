# 🚗 Car Rental Management System

A complete car rental management system built with Frappe Framework that automates the entire rental workflow from booking to payment completion.

## 📋 Overview

This system manages the complete car rental business process with automated workflows, intelligent vehicle status tracking, quality control inspections, contract generation, and financial integration. Built for efficiency and scalability using Frappe Framework.

## ⭐ Core Features

- **🔄 Automated Rental Workflow**: Complete booking-to-completion automation
- **🧠 Smart Vehicle Management**: Real-time status tracking and conflict prevention
- **🔍 Quality Control**: Mandatory pre/post rental inspections
- **📄 Contract Generation**: Automated legal contract creation with templates
- **💰 Financial Integration**: Invoice generation and payment tracking
- **⚡ Status Automation**: Intelligent updates across all related documents

## 🏗️ System Architecture

### 🐍 Backend (Python/Frappe)
- Document models with business logic
- API endpoints for client integration
- Automated workflow engines
- Cross-document status synchronization

### 🌐 Frontend (JavaScript/Frappe UI)
- Dynamic forms with real-time validation
- Smart navigation between documents
- Auto-population and calculations
- Context-aware user interface

## 📊 Essential DocTypes

### 1. 📝 Rental Booking
**Purpose**: Core rental management document

**Key Features**:
- Vehicle availability checking with conflict detection
- Automatic day and amount calculations
- Additional services management
- Smart vehicle status updates based on the current date and all active bookings
- Integration with inspections, contracts, and invoices

**Workflow States**: Draft → Confirmed → Out → Returned → Completed

**Key Methods**:
- `validate()`: Date validation and calculations
- `on_submit()`: Status progression and vehicle updates
- `update_vehicle_status_smart()`: Intelligent status algorithm
- `on_cancel()`: Cleanup and status rollback

### 2. 🔍 Vehicle Inspection
**Purpose**: Quality control for vehicle condition

**Key Features**:
- Pre-inspection (before rental) and Post-inspection (after return)
- Automatic rental booking status updates
- Vehicle condition and fuel level tracking
- Smart document linking and reference management

**Workflow Impact**:
- Pre-inspection submission → Rental status becomes "Out"
- Post-inspection submission → Rental status becomes "Returned"

**Key Methods**:
- `on_submit()`: Triggers rental booking status changes
- `on_cancel()`: Intelligent status rollback
- Auto-population from rental booking data

### 3. 📄 Rental Contract
**Purpose**: Legal contract generation and management

**Key Features**:
- Auto-population from rental booking data
- Dynamic legal template generation with real data
- Customer and vehicle details integration
- Professional contract formatting

**Key Methods**:
- `populate_from_rental_booking()`: Data aggregation from multiple sources
- `validate()`: Business rule enforcement
- Template generation with comprehensive legal terms

### 4. 🛠️ Additional Services
**Purpose**: Extra services for rentals (GPS, insurance, etc.)

**Key Features**:
- Quantity and rate management
- Automatic total calculations
- Integration with invoicing

**Usage**: Child table within Rental Booking

### 5. ⚙️ Car Rental Settings
**Purpose**: System configuration

**Key Features**:
- Default item codes for invoicing
- Payment terms configuration
- System-wide defaults

**Type**: Single DocType (one record only)

## 🔄 Business Workflow

```
1. 📝 Create Rental Booking
   ↓
2. 🔍 Pre-Inspection Required
   ↓ (Status: Draft → Confirmed → Out)
3. 🚗 Vehicle Released to Customer
   ↓
4. 🔙 Customer Returns Vehicle
   ↓
5. 🔍 Post-Inspection Required
   ↓ (Status: Out → Returned)
6. 🧾 Sales Invoice Auto-Created
   ↓
7. 💳 Payment Received
   ↓ (Status: Returned → Completed)
8. ✅ Rental Automatically Completed
```

## 🔌 Key API Methods

### 📝 Rental Booking APIs
```python
@frappe.whitelist()
def create_sales_invoice_from_booking(rental_booking_name)
def check_and_complete_if_paid(rental_booking_name)
def get_vehicle_availability(vehicle, start_date, end_date)
def update_all_vehicle_statuses()
```

### 📄 Contract APIs
```python
@frappe.whitelist()
def create_contract_from_booking(rental_booking_name)
```

## 🧠 Smart Vehicle Status Management

The system uses an intelligent algorithm that considers:
- All active bookings for each vehicle
- Current date
- Booking statuses (Confirmed, Out, Returned)
- Future reservations

**Status Logic**:
- **✅ Available**: No active bookings
- **📅 Booked**: Future confirmed booking exists
- **🚗 Rented**: Currently within rental period and status is "Out"

## 💳 Payment Integration

Automatic rental completion when:
1. 🧾 Sales invoice is created after post-inspection
2. 💰 Payment entry is submitted against the invoice
3. ✅ Invoice outstanding amount becomes zero
4. 🔄 System automatically completes rental and frees vehicle

## ⚡ Installation

1. 📥 Clone the repository to Frappe bench apps folder
2. 🔧 Install app: `bench --site [site-name] install-app car_rental`
3. 📊 Setup master data (Vehicles, Customers)
4. ⚙️ Configure Car Rental Settings
5. 🛠️ Create required Items for invoicing

## 🔧 Configuration

### 📦 Required Items
- **🚗 VEHICLE-RENTAL-SERVICE**: Main rental service item
- **🛠️ SERVICE-GENERAL**: Additional services item

### ⚙️ Car Rental Settings
- Default rental service item
- Default additional service item

## 👨‍💻 Author

**Hala1mo** - Full Stack Developer specializing in Frappe Framework and enterprise business applications.
