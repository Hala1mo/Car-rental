# -*- coding: utf-8 -*-
# Copyright (c) 2025, Hala and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class VehicleInspection(Document):
    
    def validate(self):
        """Validation before save/submit"""
        # Auto-set vehicle from rental booking if not provided
        if self.rental_booking and not self.vehicle:
            rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)
            self.vehicle = rental_doc.vehicle
     
        # Set inspection date if not provided
        if not self.inspection_date:
            self.inspection_date = frappe.utils.now()

    def on_submit(self):
        """Update rental booking status when inspection is submitted"""
        if not self.rental_booking or not self.inspection_type:
            return
            
        try:
            rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)

            if self.inspection_type == 'Pre-Inspection':
                 if rental_doc.docstatus == 0:  # If still draft, submit it first
                    rental_doc.docstatus = 1
                    rental_doc.status = 'Confirmed'  # Set to Confirmed first
                    rental_doc.flags.ignore_permissions = True
                    rental_doc.save()
                    rental_doc.submit()  # Submit the document
                
                # Now update to Out status
                    rental_doc.status = 'Out'
                    rental_doc.pre_inspection = self.name
            
            elif self.inspection_type == 'Post-Inspection':
                rental_doc.status = 'Returned'
                rental_doc.post_inspection = self.name

            # Save rental booking with updated status
            rental_doc.flags.ignore_permissions = True
            rental_doc.flags.ignore_validate_update_after_submit = True
            rental_doc.save()

            frappe.msgprint(
                f"Rental booking {self.rental_booking} status updated to: {rental_doc.status}",
                alert=True,
                indicator='green'
            )

        except Exception as e:
            frappe.log_error(f"Error updating rental booking from inspection: {str(e)}")
            frappe.msgprint(
                f"Inspection submitted successfully, but could not update rental booking status. Please update manually.",
                alert=True,
                indicator='orange'
            )

    def on_cancel(self):
        """Reset rental booking status when inspection is cancelled"""
        if not self.rental_booking:
            return
            
        try:
            rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)
            
            # Reset rental booking based on inspection type
            if self.inspection_type == 'Pre-Inspection' and rental_doc.pre_inspection == self.name:
                rental_doc.pre_inspection = None
                rental_doc.status = 'Confirmed'  # Reset to Confirmed
                        
            elif self.inspection_type == 'Post-Inspection' and rental_doc.post_inspection == self.name:
                rental_doc.post_inspection = None
                rental_doc.status = 'Out'  # Reset to Out
            
            # Save rental booking with reset status
            rental_doc.flags.ignore_permissions = True
            rental_doc.flags.ignore_validate_update_after_submit = True
            rental_doc.save()
            
            frappe.msgprint(
                f"Rental booking status reset due to inspection cancellation",
                alert=True,
                indicator='blue'
            )
            
        except Exception as e:
            frappe.log_error(f"Error updating rental booking on inspection cancel: {str(e)}")