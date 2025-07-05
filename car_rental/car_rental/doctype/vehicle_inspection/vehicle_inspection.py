# -*- coding: utf-8 -*-
# Copyright (c) 2025, Hala and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

# class VehicleInspection(Document):
    
#     def validate(self):
#         """Validation before save/submit"""
#         # Auto-set vehicle from rental booking if not provided
#         if self.rental_booking and not self.vehicle:
#             rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)
#             self.vehicle = rental_doc.vehicle
     
#         # Set inspection date if not provided
#         if not self.inspection_date:
#             self.inspection_date = frappe.utils.now()
            

#     def on_submit(self):
#      """Update rental booking status when inspection is submitted"""
#      if not self.rental_booking or not self.inspection_type:
#         return
        
#     try:
#         rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)

#         # Update rental booking based on inspection type
#         if self.inspection_type == 'Pre-Inspection':
#             # If rental booking is still draft, submit it first
#             if rental_doc.docstatus == 0:
#                 # Set status to Confirmed for submission
#                 rental_doc.status = 'Confirmed'
#                 rental_doc.pre_inspection = self.name
#                 rental_doc.flags.ignore_permissions = True
#                 rental_doc.save()
                
#                 try:
#                     rental_doc.submit()
#                     frappe.db.commit()  # Ensure submission is committed
#                 except Exception as submit_error:
#                     frappe.log_error(f"Error submitting rental booking: {str(submit_error)}")
#                     frappe.throw(f"Could not submit rental booking: {str(submit_error)}")
                
#                 # Reload the document after submission
#                 rental_doc.reload()
                
#                 # Now update status to Out after submission
#                 rental_doc.status = 'Out'
#                 rental_doc.flags.ignore_permissions = True
#                 rental_doc.flags.ignore_validate_update_after_submit = True
#                 rental_doc.save()
#             else:
#                 # If already submitted, just update status
#                 rental_doc.status = 'Out'
#                 rental_doc.pre_inspection = self.name
#                 rental_doc.flags.ignore_permissions = True
#                 rental_doc.flags.ignore_validate_update_after_submit = True
#                 rental_doc.save()
            
#         elif self.inspection_type == 'Post-Inspection':
#             rental_doc.status = 'Returned'
#             rental_doc.post_inspection = self.name
#             rental_doc.flags.ignore_permissions = True
#             rental_doc.flags.ignore_validate_update_after_submit = True
#             rental_doc.save()

#         frappe.msgprint(
#             f"Rental booking {self.rental_booking} status updated to: {rental_doc.status}",
#             alert=True,
#             indicator='green'
#         )

#     except Exception as e:
#         frappe.log_error(f"Error updating rental booking from inspection: {str(e)}")
#         frappe.log_error(f"Full traceback: {frappe.get_traceback()}", "Vehicle Inspection Error")
#         frappe.throw(f"Could not update rental booking status: {str(e)}")
    
   


#     def on_cancel(self):
#         """Reset rental booking status when inspection is cancelled"""
#         if not self.rental_booking:
#             return
            
#         try:
#             rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)
            
#             # Reset rental booking based on inspection type
#             if self.inspection_type == 'Pre-Inspection' and rental_doc.pre_inspection == self.name:
#                 rental_doc.pre_inspection = None
#                 rental_doc.status = 'Confirmed'  # Reset to Confirmed
                        
#             elif self.inspection_type == 'Post-Inspection' and rental_doc.post_inspection == self.name:
#                 rental_doc.post_inspection = None
#                 rental_doc.status = 'Out'  # Reset to Out
            
#             # Save rental booking with reset status
#             rental_doc.flags.ignore_permissions = True
#             rental_doc.flags.ignore_validate_update_after_submit = True
#             rental_doc.save()
            
#             frappe.msgprint(
#                 f"Rental booking status reset due to inspection cancellation",
#                 alert=True,
#                 indicator='blue'
#             )
            
#         except Exception as e:
#             frappe.log_error(f"Error updating rental booking on inspection cancel: {str(e)}")

#     def before_insert(self):

        # """Set naming series based on inspection type"""
        # if self.inspection_type == 'Pre-Inspection':
        #     self.naming_series = 'PI-YYYY-MM-.####'
        # elif self.inspection_type == 'Post-Inspection':
        #     self.naming_series = 'PTI-YYYY-MM-.####'
        # else:
        #     self.naming_series = 'VI-YYYY-MM-.####'
            
            
            
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

    # def on_submit(self):
    #     """Update rental booking status when inspection is submitted"""
    #     if not self.rental_booking or not self.inspection_type:
    #         return
            
    #     try:
    #         rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)

    #         # Update rental booking based on inspection type
    #         if self.inspection_type == 'Pre-Inspection':
    #             # If rental booking is still draft, submit it first
    #             if rental_doc.docstatus == 0:
    #                 # Set status to Confirmed for submission
    #                 rental_doc.status = 'Confirmed'
    #                 rental_doc.pre_inspection = self.name
    #                 rental_doc.flags.ignore_permissions = True
    #                 rental_doc.save()
                    
    #                 try:
    #                     rental_doc.submit()
    #                     frappe.db.commit()  # Ensure submission is committed
    #                 except Exception as submit_error:
    #                     frappe.log_error(f"Error submitting rental booking: {str(submit_error)}")
    #                     frappe.throw(f"Could not submit rental booking: {str(submit_error)}")
                    
    #                 # Reload the document after submission
    #                 rental_doc.reload()
                    
    #                 # Now update status to Out after submission
    #                 rental_doc.status = 'Out'
    #                 rental_doc.flags.ignore_permissions = True
    #                 rental_doc.flags.ignore_validate_update_after_submit = True
    #                 rental_doc.save()
    #             else:
    #                 # If already submitted, just update status
    #                 rental_doc.status = 'Out'
    #                 rental_doc.pre_inspection = self.name
    #                 rental_doc.flags.ignore_permissions = True
    #                 rental_doc.flags.ignore_validate_update_after_submit = True
    #                 rental_doc.save()
                
    #         elif self.inspection_type == 'Post-Inspection':
    #             rental_doc.status = 'Returned'
    #             rental_doc.post_inspection = self.name
    #             rental_doc.flags.ignore_permissions = True
    #             rental_doc.flags.ignore_validate_update_after_submit = True
    #             rental_doc.save()

    #         frappe.msgprint(
    #             f"Rental booking {self.rental_booking} status updated to: {rental_doc.status}",
    #             alert=True,
    #             indicator='green'
    #         )

    #     except Exception as e:
    #         frappe.log_error(f"Error updating rental booking from inspection: {str(e)}")
    #         frappe.log_error(f"Full traceback: {frappe.get_traceback()}", "Vehicle Inspection Error")
    #         frappe.throw(f"Could not update rental booking status: {str(e)}")






    def on_submit(self):
       """Update rental booking status when inspection is submitted"""
       frappe.log_error(f"🔥 VEHICLE INSPECTION ON_SUBMIT STARTED: {self.name}", "Vehicle Inspection Debug")
       frappe.log_error(f"📊 Inspection details - Type: {self.inspection_type}, Rental: {self.rental_booking}", "Vehicle Inspection Debug")
    
       if not self.rental_booking or not self.inspection_type:
           frappe.log_error("❌ Missing rental_booking or inspection_type, returning early", "Vehicle Inspection Debug")
           return
        
       try:
        frappe.log_error(f"📋 Getting rental booking: {self.rental_booking}", "Vehicle Inspection Debug")
        rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)
        frappe.log_error(f"✅ Rental booking loaded - Status: {rental_doc.status}, DocStatus: {rental_doc.docstatus}", "Vehicle Inspection Debug")

        # Update rental booking based on inspection type
        if self.inspection_type == 'Pre-Inspection':
            frappe.log_error("🔧 Processing Pre-Inspection logic", "Vehicle Inspection Debug")
            
            # If rental booking is still draft, submit it first
            if rental_doc.docstatus == 0:
                frappe.log_error("📝 Rental booking is draft, submitting it first", "Vehicle Inspection Debug")
                # Set status to Confirmed for submission
                rental_doc.status = 'Confirmed'
                rental_doc.pre_inspection = self.name
                rental_doc.flags.ignore_permissions = True
                rental_doc.save()
                frappe.log_error("✅ Rental booking saved with Confirmed status", "Vehicle Inspection Debug")
                
                try:
                    rental_doc.submit()
                    frappe.db.commit()  # Ensure submission is committed
                    frappe.log_error("✅ Rental booking submitted successfully", "Vehicle Inspection Debug")
                except Exception as submit_error:
                    frappe.log_error(f"❌ Error submitting rental booking: {str(submit_error)}", "Vehicle Inspection Debug")
                    frappe.throw(f"Could not submit rental booking: {str(submit_error)}")
                
                # Reload the document after submission
                rental_doc.reload()
                frappe.log_error("✅ Rental booking reloaded after submission", "Vehicle Inspection Debug")
                
                # Now update status to Out after submission
                rental_doc.status = 'Out'
                rental_doc.flags.ignore_permissions = True
                rental_doc.flags.ignore_validate_update_after_submit = True
                rental_doc.save()
                frappe.log_error("✅ Rental booking status updated to 'Out'", "Vehicle Inspection Debug")
            else:
                frappe.log_error("📝 Rental booking already submitted, just updating status", "Vehicle Inspection Debug")
                # If already submitted, just update status
                rental_doc.status = 'Out'
                rental_doc.pre_inspection = self.name
                rental_doc.flags.ignore_permissions = True
                rental_doc.flags.ignore_validate_update_after_submit = True
                rental_doc.save()
                frappe.log_error("✅ Rental booking status updated to 'Out' (already submitted)", "Vehicle Inspection Debug")
            
        elif self.inspection_type == 'Post-Inspection':
            frappe.log_error("🔧 Processing Post-Inspection logic", "Vehicle Inspection Debug")
            rental_doc.status = 'Returned'
            rental_doc.post_inspection = self.name
            rental_doc.flags.ignore_permissions = True
            rental_doc.flags.ignore_validate_update_after_submit = True
            rental_doc.save()
            frappe.log_error("✅ Rental booking status updated to 'Returned'", "Vehicle Inspection Debug")

        frappe.msgprint(
            f"Rental booking {self.rental_booking} status updated to: {rental_doc.status}",
            alert=True,
            indicator='green'
        )
        
        frappe.log_error(f"🎉 VEHICLE INSPECTION ON_SUBMIT COMPLETED SUCCESSFULLY: {self.name}", "Vehicle Inspection Debug")

       except Exception as e:
        frappe.log_error(f"❌ Error in on_submit: {str(e)}", "Vehicle Inspection Debug")
        frappe.log_error(f"❌ Full traceback: {frappe.get_traceback()}", "Vehicle Inspection Debug")
        frappe.throw(f"Could not update rental booking status: {str(e)}")
        
        
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

    def before_insert(self):
        """Set naming series based on inspection type"""
        if self.inspection_type == 'Pre-Inspection':
            self.naming_series = 'PI-YYYY-MM-.####'
        elif self.inspection_type == 'Post-Inspection':
            self.naming_series = 'PTI-YYYY-MM-.####'
        else:
            self.naming_series = 'VI-YYYY-MM-.####'            