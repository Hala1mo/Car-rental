# -*- coding: utf-8 -*-
# Copyright (c) 2025, Hala and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document

class AdditionalServices(Document):
	
 def validate(self):
        if self.rate < 0:
            frappe.throw("Rate cannot be negative")
        
        if not self.service_name:
            frappe.throw("Service name is required")

def before_insert(self):
        # Set default values
        if not self.quantity:
            self.quantity = 1
    
def on_update(self):
        # Recalculate parent totals
        if self.parent and self.parenttype == 'Rental Booking':
            parent_doc = frappe.get_doc(self.parenttype, self.parent)
            parent_doc.calculate_totals()
            parent_doc.save()