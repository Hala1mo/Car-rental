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
        self.status = 'Cancelled'
        
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

    def complete_rental(self):
        """Complete the rental booking"""
        # Check if both inspections are completed
        if not self.pre_inspection:
            frappe.throw("Pre-inspection must be completed before completing the rental")
            
        if not self.post_inspection:
            frappe.throw("Post-inspection must be completed before completing the rental")
        
        # Check if both inspections are submitted
        pre_inspection_doc = frappe.get_doc('Vehicle Inspection', self.pre_inspection)
        post_inspection_doc = frappe.get_doc('Vehicle Inspection', self.post_inspection)
        
        if pre_inspection_doc.docstatus != 1:
            frappe.throw("Pre-inspection must be submitted before completing the rental")
            
        if post_inspection_doc.docstatus != 1:
            frappe.throw("Post-inspection must be submitted before completing the rental")
        
        self.status = 'Completed'
        
        # Make vehicle available again
        if self.vehicle:
            try:
                vehicle_doc = frappe.get_doc('Vehicle', self.vehicle)
                vehicle_doc.status = 'Available'
                vehicle_doc.flags.ignore_permissions = True
                vehicle_doc.save()
            except Exception as e:
                frappe.log_error(f"Error updating vehicle status on completion: {str(e)}")
        
        self.save()
        frappe.msgprint("Rental booking completed successfully", alert=True)


@frappe.whitelist()
def create_vehicle_inspection(rental_booking_name, inspection_type):
    """Server method to create vehicle inspection"""
    try:
        rental_doc = frappe.get_doc('Rental Booking', rental_booking_name)
        
        # Check permissions
        if not frappe.has_permission('Rental Booking', 'write', rental_doc):
            frappe.throw("You don't have permission to update this rental booking")
        
        # Validate inspection type and status
        if inspection_type == 'Pre-Inspection':
            if rental_doc.status not in ['Draft', 'Confirmed']:
                frappe.throw("Pre-inspection can only be created when status is Draft or Confirmed")
            if rental_doc.pre_inspection:
                frappe.throw("Pre-inspection already exists for this rental booking")
                
        elif inspection_type == 'Post-Inspection':
            if rental_doc.status != 'Out':
                frappe.throw("Post-inspection can only be created when status is Out")
            if rental_doc.post_inspection:
                frappe.throw("Post-inspection already exists for this rental booking")
            if not rental_doc.pre_inspection:
                frappe.throw("Pre-inspection must be completed before creating post-inspection")
        
        # Create new vehicle inspection
        inspection_doc = frappe.new_doc('Vehicle Inspection')
        inspection_doc.rental_booking = rental_booking_name
        inspection_doc.inspection_type = inspection_type
        inspection_doc.inspection_date = frappe.utils.now()
        inspection_doc.vehicle = rental_doc.vehicle
        inspection_doc.customer = rental_doc.customer
        inspection_doc.insert()
        
        # Update rental booking with inspection reference
        if inspection_type == 'Pre-Inspection':
            rental_doc.pre_inspection = inspection_doc.name
        elif inspection_type == 'Post-Inspection':
            rental_doc.post_inspection = inspection_doc.name
            
        rental_doc.flags.ignore_permissions = True
        rental_doc.save()
        
        return {
            'status': 'success',
            'message': f'{inspection_type} created successfully',
            'inspection_name': inspection_doc.name
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating vehicle inspection: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


@frappe.whitelist()
def update_status_from_inspection(rental_booking_name, inspection_type, inspection_name):
    """Update rental booking status when inspection is completed"""
    try:
        rental_doc = frappe.get_doc('Rental Booking', rental_booking_name)
        inspection_doc = frappe.get_doc('Vehicle Inspection', inspection_name)
        
        # Check if inspection is submitted
        if inspection_doc.docstatus != 1:
            return {
                'status': 'error',
                'message': 'Inspection must be submitted first'
            }
        
        # Update rental booking status
        if inspection_type == 'Pre-Inspection':
            rental_doc.status = 'Out'
            rental_doc.pre_inspection = inspection_name
        elif inspection_type == 'Post-Inspection':
            rental_doc.status = 'Returned'
            rental_doc.post_inspection = inspection_name
        
        rental_doc.flags.ignore_permissions = True
        rental_doc.save()
        
        return {
            'status': 'success',
            'message': f'Rental booking status updated to {rental_doc.status}',
            'new_status': rental_doc.status
        }
        
    except Exception as e:
        frappe.log_error(f"Error updating status from inspection: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


@frappe.whitelist()
def get_rental_booking_summary(rental_booking_name):
    """Get summary of rental booking with inspection status"""
    try:
        doc = frappe.get_doc('Rental Booking', rental_booking_name)
        
        summary = {
            'name': doc.name,
            'customer': doc.customer,
            'vehicle': doc.vehicle,
            'status': doc.status,
            'rental_start': doc.rental_start,
            'rental_end': doc.rental_end,
            'total_amount': doc.amount,
            'pre_inspection': None,
            'post_inspection': None
        }
        
        # Get pre-inspection details
        if doc.pre_inspection:
            pre_inspection = frappe.get_doc('Vehicle Inspection', doc.pre_inspection)
            summary['pre_inspection'] = {
                'name': pre_inspection.name,
                'status': 'Submitted' if pre_inspection.docstatus == 1 else 'Draft',
                'inspection_date': pre_inspection.inspection_date,
            }
        
        # Get post-inspection details
        if doc.post_inspection:
            post_inspection = frappe.get_doc('Vehicle Inspection', doc.post_inspection)
            summary['post_inspection'] = {
                'name': post_inspection.name,
                'status': 'Submitted' if post_inspection.docstatus == 1 else 'Draft',
                'inspection_date': post_inspection.inspection_date
            }
        
        return summary
        
    except Exception as e:
        frappe.log_error(f"Error getting rental booking summary: {str(e)}")
        return {
            'error': str(e)
        }


@frappe.whitelist()
def get_status_flow():
    """Return the status flow for rental booking"""
    return {
        'Draft': 'Initial state - can create pre-inspection',
        'Confirmed': 'After submission - can create pre-inspection',
        'Out': 'After pre-inspection submitted - can create post-inspection',
        'Returned': 'After post-inspection submitted - can complete rental',
        'Completed': 'Rental completed - all done',
        'Cancelled': 'Rental cancelled - inspections cancelled/deleted'
    }


@frappe.whitelist()
def get_vehicle_availability(vehicle, start_date, end_date, exclude_booking=None):
    """Check vehicle availability for given dates"""
    try:
        filters = {
            'vehicle': vehicle,
            'status': ['not in', ['Cancelled', 'Completed', 'Draft']],
            'docstatus': ['!=', 2]  # Not cancelled
        }
        
        if exclude_booking:
            filters['name'] = ['!=', exclude_booking]
        
        conflicting_bookings = frappe.get_all(
            'Rental Booking',
            filters=filters,
            fields=['name', 'rental_start', 'rental_end', 'status', 'customer']
        )
        
        # Check for date conflicts
        conflicts = []
        for booking in conflicting_bookings:
            booking_start = booking.rental_start
            booking_end = booking.rental_end
            
            # Check if dates overlap
            if (start_date <= booking_end and end_date >= booking_start):
                conflicts.append(booking)
        
        return {
            'available': len(conflicts) == 0,
            'conflicts': conflicts
        }
    except Exception as e:
        frappe.log_error(f"Error checking vehicle availability: {str(e)}")
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
        
     
        invoice = frappe.new_doc('Sales Invoice')
        invoice.customer = rental_doc.customer
        invoice.posting_date = frappe.utils.today()
        invoice.due_date = frappe.utils.add_days(frappe.utils.today(), 30)
        invoice.set_posting_time = 1
        
        invoice.remarks = f"Sales Invoice for Rental Booking: {rental_doc.name}"
        
        frappe.log_error("✅ Invoice header created", "Sales Invoice Debug")
        
     
        rental_item = invoice.append('items', {})
        
        # Use a safe item code
        if settings and hasattr(settings, 'rental_service') and settings.rental_service:
            rental_item.item_code = settings.rental_service
        else:
            # Use a generic service item or create one
            rental_item.item_code = 'VEHICLE-RENTAL-SERVICE'
            
        rental_item.item_name = f"Vehicle Rental - {rental_doc.vehicle}"
        rental_item.description = f"Rental of {rental_doc.vehicle} from {rental_doc.rental_start} to {rental_doc.rental_end}"
        rental_item.qty = rental_doc.no_days or 1
        rental_item.rate = rental_doc.rate_per_day or 0
        rental_item.amount = (rental_doc.no_days or 1) * (rental_doc.rate_per_day or 0)
        
        frappe.log_error(f"✅ Main rental item added: {rental_item.item_code}", "Sales Invoice Debug")
        
        # Add additional services if any
        # if rental_doc.additional_services:
        #     frappe.log_error(f"📋 Processing {len(rental_doc.additional_services)} additional services", "Sales Invoice Debug")
            
        #     for idx, service in enumerate(rental_doc.additional_services):
        #         try:
        #             if service.service_name:
        #                 service_item = invoice.append('items', {})
                        
        #                 # Use service_name as item_code, but ensure it's valid
        #                 service_item.item_code = service.service_name.replace(' ', '-').upper()
        #                 service_item.item_name = service.service_name
        #                 service_item.description = getattr(service, 'description', service.service_name)
        #                 service_item.qty = service.quantity or 1
        #                 service_item.rate = service.rate or 0
        #                 service_item.amount = service.total or 0
                        
        #                 frappe.log_error(f"✅ Added service {idx+1}: {service_item.item_code}", "Sales Invoice Debug")
                        
        #         except Exception as service_error:
        #             frappe.log_error(f"⚠️ Error adding service {idx+1}: {str(service_error)}", "Sales Invoice Debug")
        #             # Continue with other services
        #             continue
        
      
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
            
        # Check if invoice is submitted and paid
        invoice = frappe.get_doc('Sales Invoice', rental_doc.sales_invoice)
        
        if invoice.docstatus != 1:
            return {'status': 'error', 'message': 'Sales Invoice must be submitted first'}
            
        if invoice.outstanding_amount > 0:
            return {'status': 'pending_payment', 'message': f'Invoice has outstanding amount of {invoice.outstanding_amount}'}
            
        # Invoice is paid, complete the rental
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
        frappe.log_error(f"Payment Entry submitted: {doc.name}", "Rental Booking Auto Complete")
        
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
                    frappe.log_error(f"Checking rental booking: {booking.name}", "Rental Booking Auto Complete")
                    result = check_and_complete_if_paid(booking.name)
                    
                    if result['status'] == 'success':
                        frappe.log_error(f"Successfully completed rental: {booking.name}", "Rental Booking Auto Complete")
                    else:
                        frappe.log_error(f"Could not complete rental {booking.name}: {result['message']}", "Rental Booking Auto Complete")
                        
    except Exception as e:
        frappe.log_error(f"Error in payment entry hook: {str(e)}", "Rental Booking Auto Complete Error")


def on_sales_invoice_update(doc, method):
    """Hook called when a Sales Invoice is updated after submit (e.g., when payment is applied)"""
    try:
        # Only process if outstanding amount changed to 0
        if doc.outstanding_amount == 0:
            frappe.log_error(f"Sales Invoice {doc.name} fully paid", "Rental Booking Auto Complete")
            
            # Check if this sales invoice is linked to any rental booking
            rental_bookings = frappe.get_all(
                'Rental Booking',
                filters={
                    'sales_invoice': doc.name,
                    'status': 'Returned'  # Only check returned rentals
                },
                fields=['name']
            )
            
            for booking in rental_bookings:
                frappe.log_error(f"Checking rental booking from invoice update: {booking.name}", "Rental Booking Auto Complete")
                result = check_and_complete_if_paid(booking.name)
                
                if result['status'] == 'success':
                    frappe.log_error(f"Successfully completed rental from invoice update: {booking.name}", "Rental Booking Auto Complete")
                        
    except Exception as e:
        frappe.log_error(f"Error in sales invoice update hook: {str(e)}", "Rental Booking Auto Complete Error")


# Alternative method using Journal Entry hook (if you use Journal Entries for payments)
def on_journal_entry_submit(doc, method):
    """Hook called when a Journal Entry is submitted"""
    try:
        for account in doc.accounts:
            # Check if this is a payment against a sales invoice
            if account.reference_type == 'Sales Invoice' and account.reference_name:
                # Check if this sales invoice is linked to any rental booking
                rental_bookings = frappe.get_all(
                    'Rental Booking',
                    filters={
                        'sales_invoice': account.reference_name,
                        'status': 'Returned'
                    },
                    fields=['name']
                )
                
                for booking in rental_bookings:
                    result = check_and_complete_if_paid(booking.name)
                    
                    if result['status'] == 'success':
                        frappe.log_error(f"Successfully completed rental via Journal Entry: {booking.name}", "Rental Booking Auto Complete")
                        
    except Exception as e:
        frappe.log_error(f"Error in journal entry hook: {str(e)}", "Rental Booking Auto Complete Error")
        
        
        
        
@frappe.whitelist()
def complete_rental_from_invoice(rental_booking_name):
    """Complete rental when sales invoice is submitted"""
    try:
        rental_doc = frappe.get_doc('Rental Booking', rental_booking_name)
        
        # Validate conditions
        if not rental_doc.sales_invoice:
            frappe.throw("Sales Invoice must exist before completing rental")
            
        # Check if invoice is submitted
        invoice = frappe.get_doc('Sales Invoice', rental_doc.sales_invoice)
        if invoice.docstatus != 1:
            frappe.throw("Sales Invoice must be submitted before completing rental")
        
        # Complete the rental
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
        
        return {
            'status': 'success',
            'message': 'Rental booking completed successfully'
        }
        
    except Exception as e:
        frappe.log_error(f"Error completing rental from invoice: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }        