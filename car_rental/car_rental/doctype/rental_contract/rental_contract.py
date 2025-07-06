# -*- coding: utf-8 -*-
# Copyright (c) 2025, Hala and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import today, formatdate

class RentalContract(Document):
    
    def validate(self):
        """Validation before save/submit"""
        
        if not self.contract_date:
            self.contract_date = frappe.utils.now()
        
        
        if not self.contract_number and self.name:
            self.contract_number = self.name
            
        if self.rental_booking:
            self.validate_rental_booking()
        
       
        if self.rental_booking and not self.get('_skip_auto_populate'):
            self.populate_from_rental_booking()
        
        
        if self.docstatus == 1 and not self.legal_and_terms:
            frappe.throw("Terms and conditions are required before submitting the contract")
    
    def validate_rental_booking(self):
        """Validate rental booking is in correct status for contract creation"""
        try:
            rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)
            
            
            if rental_doc.docstatus != 1:
                frappe.throw("Contract can only be created for submitted rental bookings")
            
        
            existing_contract = frappe.get_value('Rental Contract', 
                                                {'rental_booking': self.rental_booking, 'docstatus': ['!=', 2]}, 
                                                'name')
            if existing_contract and existing_contract != self.name:
                frappe.throw(f"Contract {existing_contract} already exists for this rental booking")
                
        except frappe.DoesNotExistError:
            frappe.throw("Rental booking does not exist")
    
    def populate_from_rental_booking(self):
        """Auto-populate contract fields from rental booking"""
        try:
            rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)
            
           
            self.customer = rental_doc.customer
            self.vehicle = rental_doc.vehicle
            self.rental_start_date = str(rental_doc.rental_start)
            self.rental_end_date = str(rental_doc.rental_end)
            self.rental_days = str(rental_doc.no_days or 0)
            self.rate_per_day = str(rental_doc.rate_per_day or 0)
            self.total_amount = str(rental_doc.amount or 0)
            
            
            if rental_doc.customer:
                customer_doc = frappe.get_doc('Customer', rental_doc.customer)
                self.customer_name = customer_doc.customer_name
                self.customer_email = getattr(customer_doc, 'email_id', '')
                self.customer_phone = getattr(customer_doc, 'mobile_no', '')
            
      
            if rental_doc.vehicle:
                vehicle_doc = frappe.get_doc('Vehicle', rental_doc.vehicle)
                self.vehicle_make = getattr(vehicle_doc, 'make', '')
                self.vehicle_model = getattr(vehicle_doc, 'model', '')
                self.license_plate = getattr(vehicle_doc, 'license_plate', '')
                
   
            self.set('additional_services', [])
            if rental_doc.additional_services:
                for service in rental_doc.additional_services:
                    self.append('additional_services', {
                        'service_name': service.service_name,
                        'quantity': service.quantity,
                        'rate': service.rate,
                        'total': service.total
                    })
            
            # Leave terms and conditions empty for user to fill
            # User will write their own terms and conditions
            
        except Exception as e:
            frappe.log_error(f"Error populating contract from rental booking: {str(e)}")
    
    def on_submit(self):
        """Actions when contract is submitted"""
        # Validate terms and conditions are provided
        if not self.legal_and_terms:
            frappe.throw("Terms and conditions must be provided before submitting the contract")
        
        # Set status to Active
        self.contract_status = 'Active'
        
        # Update rental booking with contract reference
        if self.rental_booking:
            try:
                rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)
                rental_doc.rental_contract = self.name
                rental_doc.flags.ignore_permissions = True
                rental_doc.flags.ignore_validate_update_after_submit = True
                rental_doc.save()
                
                frappe.msgprint(f"Rental booking {self.rental_booking} updated with contract reference", 
                              alert=True, indicator='green')
                
            except Exception as e:
                frappe.log_error(f"Error updating rental booking with contract reference: {str(e)}")
    
    def on_cancel(self):
        """Actions when contract is cancelled"""
        # Set status to Terminated
        self.contract_status = 'Terminated'
        
        # Remove contract reference from rental booking
        if self.rental_booking:
            try:
                rental_doc = frappe.get_doc('Rental Booking', self.rental_booking)
                rental_doc.rental_contract = None
                rental_doc.flags.ignore_permissions = True
                rental_doc.flags.ignore_validate_update_after_submit = True
                rental_doc.save()
                
            except Exception as e:
                frappe.log_error(f"Error removing contract reference from rental booking: {str(e)}")


@frappe.whitelist()
def create_contract_from_booking(rental_booking_name):
    """Create rental contract from rental booking"""
    try:
        # Validate rental booking
        rental_doc = frappe.get_doc('Rental Booking', rental_booking_name)
        
        # Check if rental booking is submitted
        if rental_doc.docstatus != 1:
            return {
                'status': 'error',
                'message': 'Rental booking must be submitted before creating contract'
            }
        
        # Check if contract already exists
        existing_contract = frappe.get_value('Rental Contract', 
                                           {'rental_booking': rental_booking_name, 'docstatus': ['!=', 2]}, 
                                           'name')
        if existing_contract:
            return {
                'status': 'exists',
                'contract_name': existing_contract,
                'message': f'Contract {existing_contract} already exists for this rental booking'
            }
        
        # Create new contract
        contract = frappe.new_doc('Rental Contract')
        contract.rental_booking = rental_booking_name
        contract.contract_status = 'Draft'
        contract.flags._skip_auto_populate = False  # Allow auto-population
        contract.insert()
        
        return {
            'status': 'success',
            'contract_name': contract.name,
            'message': f'Rental contract {contract.name} created successfully'
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating contract from booking: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }
    

  