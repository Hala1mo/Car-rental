frappe.ui.form.on('Rental Booking', {
    rental_start(frm) {
        calculate_days(frm);
    },
    rental_end(frm) {
        calculate_days(frm);
    },
    rate_per_day(frm) {
        calculate_total_amount(frm);
    },
    no_days(frm) {
        calculate_total_amount(frm);
    },
    vehicle(frm) {
        if (frm.doc.vehicle) {
            frappe.db.get_doc('Vehicle', frm.doc.vehicle)
                .then(vehicle => {
                    frm.set_value('rate_per_day', vehicle.rate_per_day);
                    calculate_total_amount(frm);
                });
        } else {
            frm.set_value('rate_per_day', 0);
        }
    },
    additional_services(frm) {
        calculate_total_amount(frm);
    },

       onload(frm) {
        if (frm.doc.__islocal) {
            frm.set_value('status', 'Draft');
        }
        toggle_inspection_fields(frm);
    },
    refresh(frm) {
          frm.toggle_display('no_days', true);
        if (!frm.doc.no_days && frm.doc.no_days !== 0) {
            frm.set_value('no_days', 0);
        }
        
        calculate_total_amount(frm); 
		  frm.set_query("vehicle", function() {
            return {
                filters: {
                    status: "Available"
                }
            };
        });
          toggle_inspection_fields(frm);
    },

     status(frm) {
        toggle_inspection_fields(frm);
    },

	 before_submit(frm) {
        frm.set_value('status', 'Confirmed');
        if (frm.doc.vehicle) {
            frappe.db.set_value('Vehicle', frm.doc.vehicle, 'status', 'Booked')
                .then(() => {
                    frappe.show_alert({
                        message  : __('Vehicle status updated to Booked'),
                        indicator: 'green'
                    });
                })
                .catch(err => {
                    frappe.msgprint(__('Error updating vehicle status: ') + err.message);
                });
        }
    },

	pre_inspection_done(frm) {
        if (frm.doc.pre_inspection_done && 
            (frm.doc.status === 'Confirmed' || frm.doc.status === 'Draft')) {
           
            frm.set_value('pre_inspection_date', frappe.datetime.now_datetime());
            frm.set_value('status', 'Out');
            if (frm.doc.vehicle) {
                frappe.db.set_value('Vehicle', frm.doc.vehicle, 'status', 'Rented')
                    .then(() => {
                        frappe.show_alert({
                            message  : __('Vehicle status updated to Rented'),
                            indicator: 'green'
                        });
                    });
            }
            
            frappe.show_alert({
                message  : __('Pre-inspection completed. Status updated to "Out"'),
                indicator: 'green'
            });
            
              // Refresh to hide/show fields
            setTimeout(() => {
                toggle_inspection_fields(frm);
            }, 1000);
        }
    },
    
	post_inspection_done(frm) {
        if (frm.doc.post_inspection_done) {
            frm.set_value('post_inspection_date', frappe.datetime.now_datetime());
            frm.set_value('status', 'Returned');
            if (frm.doc.vehicle) {
                frappe.db.set_value('Vehicle', frm.doc.vehicle, 'status', 'Available')
                    .then(() => {
                        frappe.show_alert({
                            message  : __('Vehicle status updated to Avaialble'),
                            indicator: 'green'
                        });
                    });
            }
            frappe.show_alert({
                message  : __('Post-inspection completed'),
                indicator: 'green'
            });
        }
    }

    
	
});


function toggle_inspection_fields(frm) {
    if (frm.doc.status === 'Out' || frm.doc.status === 'Returned' || frm.doc.status === 'Completed') {
        frm.toggle_display('pre_break', false);
        frm.toggle_display('pre_inspection_done', false);
        frm.toggle_display('pre_inspection_date', false);
        frm.toggle_display('pre_inspecton_condition_summary', false);
        frm.toggle_display('pre_inspection_fuel_level', false);

        frm.toggle_display('post_break', true);
        frm.toggle_display('post_inspection_done', true);
        frm.toggle_display('post_inspection_date', true);
        frm.toggle_display('post_inspecton_condition_summary', true);
		frm.toggle_display('post_inspection_fuel_level', true);
    } else {
        frm.toggle_display('pre_break', true);
        frm.toggle_display('pre_inspection_done', true);
        frm.toggle_display('pre_inspection_date', true);
        frm.toggle_display('pre_inspecton_condition_summary', true);
        frm.toggle_display('pre_inspection_fuel_level', true);

        frm.toggle_display('post_break', false);
        frm.toggle_display('post_inspection_done', false);
        frm.toggle_display('post_inspection_date', false);
        frm.toggle_display('post_inspecton_condition_summary', false);
        frm.toggle_display('post_inspection_fuel_level', false);
    }
}



function calculate_days(frm) {
    if (frm.doc.rental_start && frm.doc.rental_end) {
        const start = frappe.datetime.str_to_obj(frm.doc.rental_start);
        const end   = frappe.datetime.str_to_obj(frm.doc.rental_end);
        const diff  = frappe.datetime.get_diff(end, start);
        const days  = Math.ceil(diff) || 0;
        frm.set_value('no_days', days);
        calculate_total_amount(frm);
    }
}


function calculate_total_amount(frm) {
    const base_rent      = (frm.doc.no_days || 0) * (frm.doc.rate_per_day || 0);
    let   services_total = 0;

    (frm.doc.additional_services || []).forEach(row => {
        const row_total       = (row.rate || 0) * (row.quantity || 0);
              services_total += row_total;
    });

    const grand_total = base_rent + services_total;
    frm.set_value('amount', grand_total);
}

frappe.ui.form.on('Additional Services', {
    rate(frm, cdt, cdn) {
        calculate_row_total(cdt, cdn);
        calculate_total_amount(frm);
    },
    quantity(frm, cdt, cdn) {
        calculate_row_total(cdt, cdn);
        calculate_total_amount(frm);
    },
    additional_services_remove(frm) {
        calculate_total_amount(frm);
    }
});

function calculate_row_total(cdt, cdn) {
    const row   = locals[cdt][cdn];
    const total = (row.rate || 0) * (row.quantity || 0);
    frappe.model.set_value(cdt, cdn, 'total', total);
}



