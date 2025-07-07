// Copyright (c) 2025, Hala and contributors
// For license information, please see license.txt

frappe.ui.form.on('Vehicle Inspection', {

    on_submit(frm) {
        if (frm.doc.rental_booking) {
            frappe.show_alert({
                message: __('Inspection submitted successfully. Rental booking status updated.'),
                indicator: 'green'
            });
            setTimeout(() => {
                frappe.set_route('Form', 'Rental Booking', frm.doc.rental_booking);
            }, 1500);
        }
    },

     on_cancel(frm) {
        // After inspection is cancelled, refresh the rental booking if we came from there
        if (frm.doc.rental_booking) {
            frappe.show_alert({
                message: __('Inspection cancelled. Rental booking status updated.'),
                indicator: 'orange'
            });
            
            // If we have a rental booking reference, go back to it
            setTimeout(() => {
                frappe.set_route('Form', 'Rental Booking', frm.doc.rental_booking);
            }, 1500);
        }
    },

    onload: function(frm) {
        if (frm.doc.__islocal && frappe.route_options) 
            console.log('Setting values from route options:', frappe.route_options);
            if (frappe.route_options.rental_booking) {
                frm.set_value('rental_booking', frappe.route_options.rental_booking);
            }
            if (frappe.route_options.inspection_type) {
                frm.set_value('inspection_type', frappe.route_options.inspection_type);
            }
            if (frappe.route_options.vehicle) {
                frm.set_value('vehicle', frappe.route_options.vehicle);
            }
              frm.set_value('inspection_date', frappe.route_options.inspection_date || frappe.datetime.now_datetime());
            frappe.route_options = null;
        
    },

    refresh: function(frm) {
        setup_rental_booking_link(frm);
    },


     after_save: function(frm) {
      
        if (frm.doc.rental_booking && frm.doc.inspection_type && frm.doc.docstatus === 0 && frm.doc.name) {
            frappe.db.get_value('Rental Booking', frm.doc.rental_booking, 
                frm.doc.inspection_type === 'Pre-Inspection' ? 'pre_inspection' : 'post_inspection')
            .then(r => {
                let field_name = frm.doc.inspection_type === 'Pre-Inspection' ? 'pre_inspection' : 'post_inspection';
                let existing_reference = r.message[field_name];
            
                if (!existing_reference || existing_reference !== frm.doc.name) {
                    update_rental_booking_reference_only(frm);
                }
            });
        }
    }
});

function setup_rental_booking_link(frm) {
    if (frm.doc.rental_booking && !frm.doc.__islocal) {
        frm.add_custom_button(__('View Rental Booking'), function() {
            frappe.set_route('Form', 'Rental Booking', frm.doc.rental_booking);
        });
    }
}
