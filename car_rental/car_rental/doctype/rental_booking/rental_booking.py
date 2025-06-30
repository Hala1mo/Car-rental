# -*- coding: utf-8 -*-
# Copyright (c) 2025, Hala and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document

class RentalBooking(Document):


    def before_save(self):
        # Auto-update status when pre-inspection is done
        if (self.pre_inspection_done and 
            self.status in ['Confirmed', 'Draft']):
            self.status = 'Out'
            
            # Set pre-inspection details if not already set
            if not self.pre_inspection_date:
                self.pre_inspection_date = frappe.utils.now()
    

    def on_update(self):
        # Handle vehicle status updates based on rental booking status
        if self.vehicle:
            self.update_vehicle_status()


    def on_update_after_submit(self):
        # Handle status changes after document is submitted
        if self.vehicle:
            self.update_vehicle_status()
    
    def update_vehicle_status(self):
        """Update vehicle status based on rental booking status"""
        if not self.vehicle:
            return
            
        vehicle_doc = frappe.get_doc('Vehicle', self.vehicle)
        current_vehicle_status = vehicle_doc.status
        new_vehicle_status = None
        
        # Determine new vehicle status based on rental booking status
        if self.status == 'Confirmed':
            new_vehicle_status = 'Booked'
        elif self.status == 'Out':
            new_vehicle_status = 'Rented'
        elif self.status in ['Completed', 'Cancelled']:
            new_vehicle_status = 'Available'
        
        # Update vehicle status if it needs to change
        if new_vehicle_status and current_vehicle_status != new_vehicle_status:
            vehicle_doc.status = new_vehicle_status
            vehicle_doc.save()
            
            frappe.msgprint(
                f"Vehicle {self.vehicle} status updated from {current_vehicle_status} to {new_vehicle_status}",
                alert=True
            )


    def on_submit(self):
        self.status = 'Confirmed'
        self.submitted_date = frappe.utils.now()
        if self.vehicle:
            self.update_vehicle_status()

            
    def on_cancel(self):
     self.status = 'Cancelled'
     if self.vehicle:
            vehicle_doc = frappe.get_doc('Vehicle', self.vehicle)
            vehicle_doc.status = 'Available'
            vehicle_doc.save()
            
            frappe.msgprint(
                f"Vehicle {self.vehicle} status updated to Available",
                alert=True
            )


    def complete_rental(self):
        if not self.post_inspection_done:
            frappe.throw("Post-inspection must be completed before completing the rental")
        
        self.status = 'Completed'
        self.completed_date = frappe.utils.now()
        
        # Make vehicle available again
        if self.vehicle:
            vehicle_doc = frappe.get_doc('Vehicle', self.vehicle)
            vehicle_doc.status = 'Available'
            vehicle_doc.save()
        
        self.save()
        frappe.msgprint("Rental booking completed successfully", alert=True)

def complete_pre_inspection(rental_booking_name, inspection_notes=None):
    """Server method to complete pre-inspection"""
    doc = frappe.get_doc('Rental Booking', rental_booking_name)
    
    # Update pre-inspection fields
    doc.pre_inspection_done = 1
    doc.pre_inspection_date = frappe.utils.now()
    
    if inspection_notes:
        doc.pre_inspection_notes = inspection_notes
    
    # This will trigger before_save and update status to 'Out'
    doc.save()
    
    return {
        'status': 'success',
        'message': 'Pre-inspection completed successfully',
        'new_status': doc.status
    }


def complete_post_inspection(rental_booking_name, inspection_notes=None, fuel_level=None, condition_summary=None):
    """Server method to complete post-inspection"""
    doc = frappe.get_doc('Rental Booking', rental_booking_name)
    
    # Check permissions
    if not frappe.has_permission('Rental Booking', 'write', doc):
        frappe.throw("You don't have permission to update this rental booking")
    
    # Update post-inspection fields
    doc.post_inspection_done = 1
    doc.post_inspection_date = frappe.utils.now()
    doc.post_inspection_by = frappe.session.user
    
    if inspection_notes:
        doc.post_inspection_notes = inspection_notes
    if fuel_level:
        doc.fuel_level = fuel_level
    if condition_summary:
        doc.condition_summary = condition_summary
    
    doc.save()
    
    return {
        'status': 'success',
        'message': 'Post-inspection completed successfully'
    }

def get_status_flow():
    """Return the status flow for rental booking"""
    return {
        'Draft': 'Initial state',
        'Confirmed': 'After submission',
        'Out': 'After pre-inspection',
        'Completed': 'After post-inspection and return',
        'Cancelled': 'If cancelled'
    }
    
    
    