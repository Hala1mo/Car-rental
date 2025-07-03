# -*- coding: utf-8 -*-
# Copyright (c) 2025, Hala and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class VehicleInspection(Document):
    
    def validate(self):
        """Validation before save/submit"""
        if self.rental_booking:
            rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)
            if not self.vehicle:
                self.vehicle = rental_doc.vehicle
     
        if not self.inspection_date:
            self.inspection_date = frappe.utils.now()

    def on_submit(self):
      if self.rental_booking and self.inspection_type:
        try:
            rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)

            if self.inspection_type == 'Pre-Inspection':
                rental_doc.status = 'Out'
                if not rental_doc.pre_inspection:
                    rental_doc.pre_inspection = self.name
            elif self.inspection_type == 'Post-Inspection':
                rental_doc.status = 'Returned'
                if not rental_doc.post_inspection:
                    rental_doc.post_inspection = self.name

            rental_doc.flags.ignore_permissions = True
            rental_doc.flags.ignore_validate_update_after_submit = True
            rental_doc.flags.ignore_mandatory = True
            rental_doc.save()

            # ✅ Set Vehicle Inspection status to "Submitted" or similar
            self.db_set('status', 'Submitted')

            frappe.msgprint(
                f"Rental booking status updated to: {rental_doc.status}",
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
        """Handle actions when inspection is cancelled"""
        if self.rental_booking:
            try:
                rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)
                
                # Clear the inspection reference from rental booking
                if self.inspection_type == 'Pre-Inspection' and rental_doc.pre_inspection == self.name:
                    rental_doc.pre_inspection = None
                    # Reset status back to Confirmed if this was a pre-inspection
                    if rental_doc.status == 'Out':
                        rental_doc.status = 'Confirmed'
                        
                elif self.inspection_type == 'Post-Inspection' and rental_doc.post_inspection == self.name:
                    rental_doc.post_inspection = None
                    # Reset status back to Out if this was a post-inspection
                    if rental_doc.status == 'Returned':
                        rental_doc.status = 'Out'
                
                rental_doc.flags.ignore_permissions = True
                rental_doc.save()
                
                frappe.msgprint(
                    f"Rental booking status updated due to inspection cancellation",
                    alert=True,
                    indicator='blue'
                )
                
            except Exception as e:
                frappe.log_error(f"Error updating rental booking on inspection cancel: {str(e)}")

    def before_insert(self):
        """Set naming series and other defaults before insert"""
        # Set naming based on inspection type
        if self.inspection_type == 'Pre-Inspection':
            self.naming_series = 'PI-YYYY-MM-.####'
        elif self.inspection_type == 'Post-Inspection':
            self.naming_series = 'PTI-YYYY-MM-.####'
        else:
            self.naming_series = 'VI-YYYY-MM-.####'


@frappe.whitelist()
def get_rental_booking_details(rental_booking_name):
    """Get rental booking details for inspection form"""
    try:
        rental_doc = frappe.get_doc('Rental Booking', rental_booking_name)
        return {
            'vehicle': rental_doc.vehicle,
            'rental_start': rental_doc.rental_start,
            'rental_end': rental_doc.rental_end,
            'status': rental_doc.status
        }
    except Exception as e:
        frappe.throw(f"Error fetching rental booking details: {str(e)}")


@frappe.whitelist()
def create_inspection_from_rental(rental_booking_name, inspection_type):
    """Create inspection directly from rental booking"""
    try:
        rental_doc = frappe.get_doc('Rental Booking', rental_booking_name)
        
        # Validate conditions
        if inspection_type == 'Pre-Inspection':
            if rental_doc.status not in ['Draft', 'Confirmed']:
                frappe.throw("Pre-inspection can only be created when rental status is Draft or Confirmed")
            if rental_doc.pre_inspection:
                frappe.throw("Pre-inspection already exists for this rental booking")
                
        elif inspection_type == 'Post-Inspection':
            if rental_doc.status != 'Out':
                frappe.throw("Post-inspection can only be created when rental status is Out")
            if rental_doc.post_inspection:
                frappe.throw("Post-inspection already exists for this rental booking")
        
        # Create new inspection
        inspection = frappe.new_doc('Vehicle Inspection')
        inspection.rental_booking = rental_booking_name
        inspection.inspection_type = inspection_type
        inspection.vehicle = rental_doc.vehicle
        inspection.inspection_date = frappe.utils.now()
        
        inspection.insert()
        
        # Update rental booking with inspection reference
        if inspection_type == 'Pre-Inspection':
            rental_doc.pre_inspection = inspection.name
        elif inspection_type == 'Post-Inspection':
            rental_doc.post_inspection = inspection.name
            
        rental_doc.flags.ignore_permissions = True
        rental_doc.save()
        
        return {
            'status': 'success',
            'inspection_name': inspection.name,
            'message': f'{inspection_type} created successfully'
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating inspection from rental: {str(e)}")
        frappe.throw(str(e))