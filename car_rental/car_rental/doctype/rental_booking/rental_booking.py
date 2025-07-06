# -*- coding: utf-8 -*-
# Copyright (c) 2025, Hala and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RentalBooking(Document):

    def validate(self):
        """Validation before save/submit"""
        # Calculate number of days if dates are provided
        if self.rental_start and self.rental_end:
            from frappe.utils import date_diff
            self.no_days = date_diff(self.rental_end, self.rental_start)
            if self.no_days <= 0:
                frappe.throw("End date must be after start date")

    def on_update(self):
        """Handle updates after save"""
        if self.vehicle and not self.flags.ignore_vehicle_update:
            self.update_vehicle_status()

    def on_update_after_submit(self):
        """Handle status changes after document is submitted"""
        if self.vehicle and not self.flags.ignore_vehicle_update:
            self.update_vehicle_status()
            
        if self.rental_contract:
          self.update_contract_status()
    
    def update_vehicle_status(self):
        """Update vehicle status based on rental booking status"""
        if not self.vehicle:
            return
            
        try:
            vehicle_doc = frappe.get_doc('Vehicle', self.vehicle)
            current_vehicle_status = vehicle_doc.status
            new_vehicle_status = None
            
            # Determine new vehicle status based on rental booking status
            if self.status == 'Confirmed':
                new_vehicle_status = 'Booked'
            elif self.status == 'Out':
                new_vehicle_status = 'Rented'
            elif self.status in ['Completed', 'Cancelled', 'Returned']:
                new_vehicle_status = 'Available'
            
            # Update vehicle status if it needs to change
            if new_vehicle_status and current_vehicle_status != new_vehicle_status:
                vehicle_doc.status = new_vehicle_status
                vehicle_doc.flags.ignore_permissions = True
                vehicle_doc.save()
                
                frappe.msgprint(
                    f"Vehicle {self.vehicle} status updated from {current_vehicle_status} to {new_vehicle_status}",
                    alert=True
                )
        except Exception as e:
            frappe.log_error(f"Error updating vehicle status: {str(e)}")

    def on_submit(self):
        """Actions when document is submitted"""
        # Set status to Confirmed when submitted
        self.status = 'Confirmed'
        
        # Update vehicle status
        if self.vehicle:
            self.flags.ignore_vehicle_update = False
            self.update_vehicle_status()

    def on_cancel(self):
        """Actions when document is cancelled"""
       
        if self.rental_contract:
            try:
                 frappe.db.set_value('Rental Contract', self.rental_contract, {
                'rental_booking': None,
                'contract_status': 'Terminated'
            })
                 frappe.db.commit()
            
                 frappe.msgprint(
                f"Rental Contract {self.rental_contract} link removed and status updated to Terminated",
                alert=True,
                indicator='orange'
            )
            except Exception as e:
                 frappe.log_error(f"Error handling contract on cancel: {str(e)}")
          
        # Cancel related vehicle inspections
        self.cancel_related_inspections()
        
        # Update vehicle status to Available
        
        if self.vehicle:
            try:
                vehicle_doc = frappe.get_doc('Vehicle', self.vehicle)
                vehicle_doc.status = 'Available'
                vehicle_doc.flags.ignore_permissions = True
                vehicle_doc.save()
                
                frappe.msgprint(
                    f"Vehicle {self.vehicle} status updated to Available",
                    alert=True
                )
            except Exception as e:
                frappe.log_error(f"Error updating vehicle status on cancel: {str(e)}")
        
        self.status = "Cancelled"
        frappe.db.set_value('Rental Booking', self.name, 'status', 'Cancelled')
        frappe.db.commit()      
     

    def cancel_related_inspections(self):
        """Cancel related vehicle inspections when rental booking is cancelled"""
        try:
            # Find vehicle inspections linked to this rental booking
            inspections = frappe.get_all(
                'Vehicle Inspection',
                filters={
                    'rental_booking': self.name,
                    'docstatus': ['!=', 2]  # Not already cancelled
                },
                fields=['name', 'docstatus']
            )
            
            for inspection in inspections:
                if inspection.docstatus == 1:  # If submitted, cancel it
                    inspection_doc = frappe.get_doc('Vehicle Inspection', inspection.name)
                    inspection_doc.cancel()
                    frappe.msgprint(f"Vehicle Inspection {inspection.name} has been cancelled", alert=True)
                elif inspection.docstatus == 0:  # If draft, delete it
                    frappe.delete_doc('Vehicle Inspection', inspection.name)
                    frappe.msgprint(f"Vehicle Inspection {inspection.name} has been deleted", alert=True)
                    
        except Exception as e:
            frappe.log_error(f"Error cancelling related inspections: {str(e)}")

        
    def update_contract_status(self):
       """Update contract status based on rental booking status"""
       if self.rental_contract:
        try:
            contract_doc = frappe.get_doc('Rental Contract', self.rental_contract)
            
            # Update contract status based on rental booking status
            if self.status == 'Completed':
                if contract_doc.contract_status != 'Completed':
                    contract_doc.contract_status = 'Completed'
                    contract_doc.flags.ignore_permissions = True
                    contract_doc.flags.ignore_validate_update_after_submit = True
                    contract_doc.save()
                    
                    frappe.msgprint(
                        f"Contract {self.rental_contract} marked as completed",
                        alert=True,
                        indicator='green'
                    )
            
            elif self.status == 'Cancelled':
                if contract_doc.contract_status != 'Terminated':
                    contract_doc.contract_status = 'Terminated'
                    contract_doc.flags.ignore_permissions = True
                    contract_doc.flags.ignore_validate_update_after_submit = True
                    contract_doc.save()
                    
                    frappe.msgprint(
                        f"Contract {self.rental_contract} marked as terminated",
                        alert=True,
                        indicator='orange'
                    )
                    
        except Exception as e:
            frappe.log_error(f"Error updating contract status: {str(e)}")
            
            
        

@frappe.whitelist()
def get_vehicle_availability(vehicle, start_date, end_date, exclude_booking=None):
    """Enhanced vehicle availability checker with detailed status"""
    try:
        from frappe.utils import getdate
        
        start_date = getdate(start_date)
        end_date = getdate(end_date)
        
        filters = {
            'vehicle': vehicle,
            'docstatus': 1,  # Only submitted bookings
            'status': ['not in', ['Cancelled', 'Completed']]
        }
        
        if exclude_booking:
            filters['name'] = ['!=', exclude_booking]
        
        conflicting_bookings = frappe.get_all(
            'Rental Booking',
            filters=filters,
            fields=['name', 'rental_start', 'rental_end', 'status', 'customer']
        )
        
        conflicts = []
        for booking in conflicting_bookings:
            booking_start = getdate(booking.rental_start)
            booking_end = getdate(booking.rental_end)
            
            # Check for overlap
            if start_date <= booking_end and end_date >= booking_start:
                conflicts.append({
                    'booking_name': booking.name,
                    'start_date': booking.rental_start,
                    'end_date': booking.rental_end,
                    'status': booking.status,
                    'customer': booking.customer,
                    'overlap_type': 'full' if booking_start <= start_date and booking_end >= end_date else 'partial'
                })
        
        return {
            'available': len(conflicts) == 0,
            'conflicts': conflicts,
            'vehicle': vehicle,
            'requested_period': {
                'start': start_date,
                'end': end_date
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error checking enhanced vehicle availability: {str(e)}")
        return {
            'available': False,
            'error': str(e)
        }
        
        

@frappe.whitelist()
def create_sales_invoice_from_booking(rental_booking_name):
    """Create Sales Invoice from Rental Booking after post-inspection"""
    try:
        frappe.log_error(f"🔥 Creating sales invoice for rental booking: {rental_booking_name}", "Sales Invoice Debug")
        
        rental_doc = frappe.get_doc('Rental Booking', rental_booking_name)
        frappe.log_error(f"✅ Rental doc loaded: {rental_doc.name}", "Sales Invoice Debug")
        
        # Get settings safely
        try:
            settings = frappe.get_single('Car Rental Settings')
        except:
            settings = None
            frappe.log_error("⚠️ Car Rental Settings not found, using defaults", "Sales Invoice Debug")
    
        # Validate conditions
        if rental_doc.status != 'Returned':
            frappe.throw("Sales Invoice can only be created when rental status is 'Returned'")
            
        if not rental_doc.post_inspection:
            frappe.throw("Post-inspection must be completed before creating invoice")
 
        post_inspection = frappe.get_doc('Vehicle Inspection', rental_doc.post_inspection)
        if post_inspection.docstatus != 1:
            frappe.throw("Post-inspection must be submitted before creating invoice")
            
        if rental_doc.sales_invoice:
            frappe.throw("Sales Invoice already exists for this rental booking")
        
        frappe.log_error("✅ All validations passed, creating invoice", "Sales Invoice Debug")
        
        # Create invoice
        invoice = frappe.new_doc('Sales Invoice')
        invoice.customer = rental_doc.customer
        invoice.posting_date = frappe.utils.today()
        invoice.due_date = frappe.utils.add_days(frappe.utils.today(), 30)
        invoice.set_posting_time = 1
        invoice.remarks = f"Sales Invoice for Rental Booking: {rental_doc.name}"
        
        frappe.log_error("✅ Invoice header created", "Sales Invoice Debug")
        
        # Add rental service item
        rental_item = invoice.append('items', {})
        
        # Use a safe item code
        if settings and hasattr(settings, 'rental_service') and settings.rental_service:
            rental_item.item_code = settings.rental_service
        else:
            rental_item.item_code = 'VEHICLE-RENTAL-SERVICE'
            
        rental_item.item_name = f"Vehicle Rental - {rental_doc.vehicle}"
        rental_item.description = f"Rental of {rental_doc.vehicle} from {rental_doc.rental_start} to {rental_doc.rental_end}"
        rental_item.qty = rental_doc.no_days or 1
        rental_item.rate = rental_doc.rate_per_day or 0
        rental_item.amount = (rental_doc.no_days or 1) * (rental_doc.rate_per_day or 0)
        
        frappe.log_error(f"✅ Main rental item added: {rental_item.item_code}", "Sales Invoice Debug")
        
        # Add additional services if any
        if hasattr(rental_doc, 'additional_services') and rental_doc.additional_services:
            frappe.log_error(f"📋 Processing {len(rental_doc.additional_services)} additional services", "Sales Invoice Debug")
            
            for idx, service in enumerate(rental_doc.additional_services):
                try:
                    # Skip if service doesn't have required fields
                    if not hasattr(service, 'service_name') or not service.service_name:
                        frappe.log_error(f"⚠️ Service {idx+1} missing service_name, skipping", "Sales Invoice Debug")
                        continue
                    
                    service_item = invoice.append('items', {})
                    
                    # Use the "General Services" item code for all additional services
                    service_item.item_code = 'SERVICE-GENERAL'
                    service_item.item_name = service.service_name
                    service_item.description = f"{service.service_name} - {getattr(service, 'description', '')}"
                    service_item.qty = getattr(service, 'quantity', 1) or 1
                    service_item.rate = getattr(service, 'rate', 0) or 0
                    service_item.amount = getattr(service, 'total', 0) or (service_item.qty * service_item.rate)
                    
                    frappe.log_error(f"✅ Added service {idx+1}: {service_item.item_code} - {service_item.item_name} - Qty: {service_item.qty}, Rate: {service_item.rate}, Amount: {service_item.amount}", "Sales Invoice Debug")
                    
                except Exception as service_error:
                    frappe.log_error(f"⚠️ Error adding service {idx+1}: {str(service_error)}", "Sales Invoice Debug")
                    frappe.log_error(f"⚠️ Service data: {service}", "Sales Invoice Debug")
                    # Continue with other services
                    continue
        else:
            frappe.log_error("ℹ️ No additional services found", "Sales Invoice Debug")
        
        # Set rental booking reference if field exists
        try:
            if hasattr(invoice, 'rental_booking_reference'):
                invoice.rental_booking_reference = rental_doc.name
        except:
            pass
        
        frappe.log_error("🚀 Attempting to insert invoice", "Sales Invoice Debug")
        
        # Insert invoice
        invoice.insert()
        
        frappe.log_error(f"✅ Invoice created: {invoice.name}", "Sales Invoice Debug")
        
        # Update rental booking with invoice reference
        rental_doc.sales_invoice = invoice.name
        rental_doc.flags.ignore_permissions = True
        rental_doc.flags.ignore_validate_update_after_submit = True
        rental_doc.save()
        
        frappe.log_error(f"✅ Rental booking updated with invoice reference", "Sales Invoice Debug")
        
        return {
            'status': 'success',
            'invoice_name': invoice.name,
            'message': f'Sales Invoice {invoice.name} created successfully'
        }
        
    except Exception as e:
        frappe.log_error(f"❌ Error creating sales invoice: {str(e)}", "Sales Invoice Error")
        frappe.log_error(f"❌ Full traceback: {frappe.get_traceback()}", "Sales Invoice Error")
        
        return {
            'status': 'error',
            'message': str(e)
        }     
        
        
@frappe.whitelist()
def check_and_complete_if_paid(rental_booking_name):
    """Check if sales invoice is paid and complete rental if so"""
    try:
        rental_doc = frappe.get_doc('Rental Booking', rental_booking_name)
        
        if not rental_doc.sales_invoice:
            return {'status': 'error', 'message': 'No sales invoice found'}
            
        if rental_doc.status == 'Completed':
            return {'status': 'already_completed', 'message': 'Rental already completed'}
            
        if rental_doc.status != 'Returned':
            return {'status': 'error', 'message': 'Rental must be in Returned status'}
      
        invoice = frappe.get_doc('Sales Invoice', rental_doc.sales_invoice)
        
        if invoice.docstatus != 1:
            return {'status': 'error', 'message': 'Sales Invoice must be submitted first'}
            
        if invoice.outstanding_amount > 0:
            return {'status': 'pending_payment', 'message': f'Invoice has outstanding amount of {invoice.outstanding_amount}'}
            
        # Update rental booking status to Completed
        rental_doc.status = 'Completed'
        rental_doc.flags.ignore_permissions = True
        rental_doc.flags.ignore_validate_update_after_submit = True
        rental_doc.save()
        
        # Update vehicle status to Available
        if rental_doc.vehicle:
            vehicle_doc = frappe.get_doc('Vehicle', rental_doc.vehicle)
            vehicle_doc.status = 'Available'
            vehicle_doc.flags.ignore_permissions = True
            vehicle_doc.save()
            
            frappe.msgprint(
                f"Rental {rental_booking_name} completed automatically after payment confirmation. Vehicle {rental_doc.vehicle} is now available.",
                alert=True
            )
            
        # Update contract status to Completed
        if rental_doc.rental_contract:
            contract_doc = frappe.get_doc('Rental Contract', rental_doc.rental_contract)
            contract_doc.contract_status = 'Completed'
            contract_doc.flags.ignore_permissions = True
            contract_doc.flags.ignore_validate_update_after_submit = True
            contract_doc.save()
        
        return {
            'status': 'success',
            'message': 'Rental booking completed successfully after payment confirmation'
        }
        
    except Exception as e:
        frappe.log_error(f"Error completing rental after payment: {str(e)}")
        return {'status': 'error', 'message': str(e)}
def on_payment_entry_submit(doc, method):
    """Hook called when a Payment Entry is submitted"""
    try:
        for reference in doc.references:
            if reference.reference_doctype == 'Sales Invoice':
                rental_bookings = frappe.get_all(
                    'Rental Booking',
                    filters={
                        'sales_invoice': reference.reference_name,
                        'status': 'Returned' 
                    },
                    fields=['name']
                )
                
                for booking in rental_bookings:
                    result = check_and_complete_if_paid(booking.name)
                    if result['status'] == 'success':
                        frappe.log_error(f"Auto-completed rental: {booking.name}")
                        
    except Exception as e:
        frappe.log_error(f"Error in payment entry hook: {str(e)}")


def on_sales_invoice_update(doc, method):
    """Hook called when a Sales Invoice is updated after submit"""
    try:
        # Only process if outstanding amount changed to 0
        if doc.outstanding_amount == 0:
            # Check if this sales invoice is linked to any rental booking
            rental_bookings = frappe.get_all(
                'Rental Booking',
                filters={
                    'sales_invoice': doc.name,
                    'status': 'Returned'
                },
                fields=['name']
            )
            
            for booking in rental_bookings:
                result = check_and_complete_if_paid(booking.name)
                if result['status'] == 'success':
                    frappe.log_error(f"Auto-completed rental from invoice update: {booking.name}")
                        
    except Exception as e:
        frappe.log_error(f"Error in sales invoice update hook: {str(e)}")   
        
        
        
        