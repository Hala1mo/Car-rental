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
      self.status = 'Submitted'
      frappe.db.set_value('Vehicle Inspection', self.name, 'status', 'Submitted')
      frappe.db.commit()  
      if not self.rental_booking or not self.inspection_type:
        return

      try:
        rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)

        if self.inspection_type == 'Pre-Inspection':
           
            if not rental_doc.pre_inspection:  
                rental_doc.pre_inspection = self.name
                frappe.db.set_value('Rental Booking', self.rental_booking, 'pre_inspection', self.name)
                frappe.db.commit()
                
            if rental_doc.docstatus == 0:
                rental_doc.reload()
                rental_doc.status = 'Confirmed'
                rental_doc.flags.ignore_permissions = True
                rental_doc.submit()

            # After submission, update to 'Out'
            rental_doc.reload()
            rental_doc.status = 'Out'
            rental_doc.flags.ignore_permissions = True
            rental_doc.flags.ignore_validate_update_after_submit = True
            rental_doc.save()
            rental_doc.reload()
            if rental_doc.status == 'Out' and rental_doc.pre_inspection == self.name:
                    frappe.msgprint(f"Rental booking {self.rental_booking} status updated to 'Out'", alert=True, indicator='green')
            else:
                    frappe.log_error(f"Status update verification failed for {self.rental_booking}")
        
        elif self.inspection_type == 'Post-Inspection':
            rental_doc.reload()
            rental_doc.status = 'Returned'
            rental_doc.post_inspection = self.name
            rental_doc.flags.ignore_permissions = True
            rental_doc.flags.ignore_validate_update_after_submit = True
            rental_doc.save()
            rental_doc.update_vehicle_status_smart()

        frappe.msgprint(
            f"Rental booking {self.rental_booking} status updated to: {rental_doc.status}",
            alert=True,
            indicator='green'
        )

      except Exception as e:
        frappe.log_error(f"Error updating rental booking from inspection: {str(e)}")
        frappe.log_error(f"Traceback:\n{frappe.get_traceback()}", "Vehicle Inspection Submission Error")
        frappe.throw(f"Could not update rental booking: {str(e)}")

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
            print(f"Error updating rental booking on inspection cancel: {str(e)}")

    def before_insert(self):
        """Set naming series based on inspection type"""
        if self.inspection_type == 'Pre-Inspection':
            self.naming_series = 'PI-YYYY-MM-.####'
        elif self.inspection_type == 'Post-Inspection':
            self.naming_series = 'PTI-YYYY-MM-.####'
        else:
            self.naming_series = 'VI-YYYY-MM-.####'            