frappe.ui.form.on('Rental Booking', {
    rental_start(frm) {
        validate_start_date(frm);
        if (frm.doc.rental_start) {
            frm.set_df_property('rental_end', 'min_date', frm.doc.rental_start);
            if (frm.doc.rental_end && frm.doc.rental_end <= frm.doc.rental_start) {
                frm.set_value('rental_end', '');
                frappe.msgprint(__('End date must be after start date. Please select a new end date.'));
            }
        }

        check_vehicle_availability(frm);
        calculate_days(frm);
    },
    
    rental_end(frm) {
        validate_end_date(frm);
        check_vehicle_availability(frm);
        calculate_days(frm);
    },
    
    rate_per_day(frm) {
        calculate_total_amount(frm);
    },
    
    no_days(frm) {
        calculate_total_amount(frm);
    },
    
    vehicle(frm) {
        check_vehicle_availability(frm);
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
        setup_date_restrictions(frm);
        check_and_submit_if_needed(frm);
        if (!frm.doc.__islocal && frm.doc.name) {
            setTimeout(() => {
                add_action_buttons(frm);
            }, 500);
        }
    },
    
    refresh(frm) {
        calculate_total_amount(frm); 
        frm.set_query("vehicle", function() {
            return {};
        });
    
        setup_date_restrictions(frm);
        if (!frm.doc.__islocal && frm.doc.name) {
            add_action_buttons(frm);
        }
    },

    after_save(frm) {
        console.log('Document saved, adding action buttons');
        setTimeout(() => {
            add_action_buttons(frm);
        }, 500);
    },

    status(frm) {
        if (!frm.doc.__islocal && frm.doc.name) {
            setTimeout(() => {
                add_action_buttons(frm);
            }, 500);
        }
    },

    before_submit(frm) {
        if (frm.doc.status === 'Draft') {
            frm.set_value('status', 'Confirmed');
        }
    },

    on_submit(frm) {
        frappe.show_alert({
            message: __('Rental booking submitted successfully'),
            indicator: 'green'
        });
        setTimeout(() => {
            add_action_buttons(frm);
        }, 1000);
    },

     pre_inspection(frm) {
        if (!frm.doc.__islocal) {
            setTimeout(() => {
                add_action_buttons(frm);
            }, 300);
        }
    },
    
    post_inspection(frm) {
        if (!frm.doc.__islocal) {
            setTimeout(() => {
                add_action_buttons(frm);
            }, 300);
        }
    },

    on_cancel(frm) {
        frappe.db.set_value('Rental Booking', frm.doc.name, 'status', 'Cancelled')
            .then(() => {
                frm.reload_doc();
            });
            
        if (frm.doc.vehicle) {
            frappe.db.set_value('Vehicle', frm.doc.vehicle, 'status', 'Available')
                .then(() => {
                    frappe.show_alert({
                        message: __('Vehicle status updated to Available'),
                        indicator: 'green'
                    });
                })
                .catch(err => {
                    frappe.msgprint(__('Error updating vehicle status: ') + err.message);
                });
        }
    }
});


function create_rental_contract(frm) {
    console.log('Creating rental contract for booking:', frm.doc.name);
    if (!frm.doc.customer) {
        frappe.msgprint({
            title: __('Missing Information'),
            message: __('Customer is required to create contract'),
            indicator: 'red'
        });
        return;
    }
    
    if (!frm.doc.vehicle) {
        frappe.msgprint({
            title: __('Missing Information'),
            message: __('Vehicle is required to create contract'),
            indicator: 'red'
        });
        return;
    }
    
    if (frm.doc.docstatus !== 1) {
        frappe.msgprint({
            title: __('Document Not Submitted'),
            message: __('Rental booking must be submitted before creating contract'),
            indicator: 'red'
        });
        return;
    }
    
    frappe.call({
        method: 'car_rental.car_rental.doctype.rental_contract.rental_contract.create_contract_from_booking',
        args: {
            rental_booking_name: frm.doc.name
        },
        callback: function(response) {
            if (response.message && response.message.status === 'success') {
                frappe.set_route('Form', 'Rental Contract', response.message.contract_name);
            
                frappe.show_alert({
                    message: response.message.message,
                    indicator: 'green'
                });
                
                setTimeout(() => {
                    frm.reload_doc();
                }, 1000);
                
            } else if (response.message && response.message.status === 'exists') {
                frappe.confirm(
                    __('Contract already exists. Do you want to view it?'),
                    () => {
                        frappe.set_route('Form', 'Rental Contract', response.message.contract_name);
                    }
                );
                
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: response.message ? response.message.message : __('Failed to create rental contract'),
                    indicator: 'red'
                });
            }
        },
        error: function(error) {
            console.log('Error creating rental contract:', error);
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to create rental contract: ') + (error.message || 'Unknown error'),
                indicator: 'red'
            });
        }
    });
}


function create_sales_invoice(frm) {
    console.log('Creating sales invoice for rental booking:', frm.doc.name);

    if (!frm.doc.customer) {
        frappe.msgprint({
            title: __('Missing Information'),
            message: __('Customer is required to create invoice'),
            indicator: 'red'
        });
        return;
    }
    
    if (!frm.doc.vehicle) {
        frappe.msgprint({
            title: __('Missing Information'),
            message: __('Vehicle is required to create invoice'),
            indicator: 'red'
        });
        return;
    }
    
    
    frappe.call({
        method: 'car_rental.car_rental.doctype.rental_booking.rental_booking.create_sales_invoice_from_booking',
        args: {
            rental_booking_name: frm.doc.name
        },
        callback: function(response) {
            if (response.message && response.message.status === 'success') {
            
                frappe.set_route('Form', 'Sales Invoice', response.message.invoice_name);
                
        
                frappe.show_alert({
                    message: response.message.message,
                    indicator: 'green'
                });
                
    
                setTimeout(() => {
                    frm.reload_doc();
                }, 1000);
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: response.message ? response.message.message : __('Failed to create sales invoice'),
                    indicator: 'red'
                });
            }
        },
        error: function(error) {
            console.log('Error creating sales invoice:', error);
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to create sales invoice: ') + (error.message || 'Unknown error'),
                indicator: 'red'
            });
        }
    });
}



function add_action_buttons(frm) {
    console.log('=== ADD ACTION BUTTONS DEBUG ===');
    console.log('Document Name:', frm.doc.name);
    console.log('Status:', frm.doc.status);
    console.log('DocStatus:', frm.doc.docstatus);
    console.log('Pre-Inspection:', frm.doc.pre_inspection);
    console.log('Post-Inspection:', frm.doc.post_inspection);
    console.log('================================');
    
    if (!frm.doc.name || frm.doc.__islocal) {
        console.log('❌ Document not saved yet, skipping buttons');
        return;
    }
    
 
    frm.clear_custom_buttons();
    
    // Create Contract button for submitted documents without contract
    if (frm.doc.docstatus === 1 && !frm.doc.rental_contract) {
        console.log('✅ Adding Create Contract button');
        frm.add_custom_button(__('Create Contract'), () => {
            create_rental_contract(frm);
        }).addClass("btn-success");
    }
    
    // View Contract button if contract exists
    if (frm.doc.rental_contract) {
        console.log('✅ Adding View Contract button');
        frm.add_custom_button(__('View Contract'), () => {
            frappe.set_route('Form', 'Rental Contract', frm.doc.rental_contract);
        });
    }

    
    if (frm.doc.pre_inspection) {
        console.log('✅ Adding View Pre-Inspection button');
        frm.add_custom_button(__('View Pre-Inspection'), () => {
            frappe.set_route('Form', 'Vehicle Inspection', frm.doc.pre_inspection);
        });
        
        // Check if we should show post-inspection button
        frappe.db.get_value('Vehicle Inspection', frm.doc.pre_inspection, 'docstatus')
        .then(r => {
            console.log('Pre-inspection docstatus:', r.message.docstatus);
            
            if (frm.doc.status === 'Out' && 
                !frm.doc.post_inspection && 
                r.message.docstatus === 1) {
                
                console.log('✅ Adding Create Post-Inspection button (async)');
                frm.add_custom_button(__('Create Post-Inspection'), () => {
                    create_inspection_with_type(frm, 'Post-Inspection');
                }).addClass("btn-primary");
            }
        });
    } else {
        if (frm.doc.status === 'Draft' || frm.doc.status === 'Confirmed') {
            console.log('✅ Adding Create Vehicle Inspection (Pre-Inspection) button');
            frm.add_custom_button(__('Create Vehicle Inspection'), () => {
                create_inspection_with_type(frm, 'Pre-Inspection');
            }).addClass("btn-primary");
        }
    }
    
    if (frm.doc.post_inspection) {
        console.log('✅ Adding View Post-Inspection button');
        frm.add_custom_button(__('View Post-Inspection'), () => {
            frappe.set_route('Form', 'Vehicle Inspection', frm.doc.post_inspection);
        });
        
        if (frm.doc.status === 'Returned' && !frm.doc.sales_invoice) {
            console.log('✅ Checking if we can add Create Sales Invoice button');
            
            frappe.db.get_value('Vehicle Inspection', frm.doc.post_inspection, 'docstatus')
            .then(r => {
                if (r.message.docstatus === 1) { // 1 = Submitted
                    frm.add_custom_button(__('Create Sales Invoice'), () => {
                        create_sales_invoice(frm);
                    }).addClass("btn-success");
                    console.log('✅ Create Sales Invoice button added (async)');
                }
            });
        }
    }
    
    if (frm.doc.sales_invoice) {
        console.log('✅ Adding View Sales Invoice button');
        frm.add_custom_button(__('View Sales Invoice'), () => {
            frappe.set_route('Form', 'Sales Invoice', frm.doc.sales_invoice);
        });
    }
}

// ✅ ADD THIS NEW FUNCTION to refresh buttons after form reload
function refresh_buttons_after_reload(frm) {
    // Wait a bit for the form to fully load, then refresh buttons
    setTimeout(() => {
        add_action_buttons(frm);
    }, 500);
}

function create_inspection_with_type(frm, inspection_type) {
    console.log('Creating inspection:', inspection_type);
    
    // Validate before creating
    if (!frm.doc.vehicle) {
        frappe.msgprint({
            title: __('Missing Information'),
            message: __('Please select a vehicle before creating inspection'),
            indicator: 'red'
        });
        return;
    }
    
    if (!frm.doc.customer) {
        frappe.msgprint({
            title: __('Missing Information'),
            message: __('Please select a customer before creating inspection'),
            indicator: 'red'
        });
        return;
    }
    

    frappe.route_options = {
        'rental_booking': frm.doc.name,
        'inspection_type': inspection_type,
        'vehicle': frm.doc.vehicle,
        'customer': frm.doc.customer,
        'inspection_date': frappe.datetime.now_datetime()
    };
    
    frappe.new_doc('Vehicle Inspection');
}

function setup_date_restrictions(frm) {
    const today = frappe.datetime.get_today();
    frm.set_df_property('rental_start', 'min_date', today);
    
    if (frm.doc.rental_start) {
        frm.set_df_property('rental_end', 'min_date', frm.doc.rental_start);
    }
}

function validate_start_date(frm) {
    if (frm.doc.rental_start) {
        const today = frappe.datetime.get_today();
        const start_date = frm.doc.rental_start;
        
        if (start_date < today) {
            frappe.msgprint({
                title: __('Invalid Date'),
                message: __('Rental start date cannot be in the past. Please select today or a future date.'),
                indicator: 'red'
            });
            frm.set_value('rental_start', '');
            return false;
        }
    }
    return true;
}

function validate_end_date(frm) {
    const today = frappe.datetime.get_today();
    const start_date = frm.doc.rental_end;
    if (start_date < today) {
        frappe.msgprint({
            title: __('Invalid Date'),
            message: __('Rental end date cannot be in the past. Please select future date.'),
            indicator: 'red'
        });
        frm.set_value('rental_end', '');
        return false;
    }

    if (frm.doc.rental_start && frm.doc.rental_end) {
        const start_date = frm.doc.rental_start;
        const end_date = frm.doc.rental_end;
    
        if (end_date <= start_date) {
            frappe.msgprint({
                title: __('Invalid Date Range'),
                message: __('Rental end date must be after the start date.'),
                indicator: 'red'
            });
            frm.set_value('rental_end', '');
            return false;
        }
    }
    return true;
}

function check_vehicle_availability(frm) {
    return new Promise((resolve) => {
        if (!frm.doc.vehicle || !frm.doc.rental_start || !frm.doc.rental_end) {
            resolve(true);
            return;
        }
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Rental Booking',
                filters: {
                    'vehicle': frm.doc.vehicle,
                    'status': ['not in', ['Cancelled', 'Completed', 'Draft']],
                    'name': ['!=', frm.doc.name || ''] 
                },
                fields: ['name', 'rental_start', 'rental_end', 'status', 'customer']
            },
            callback: function(response) {
                if (response.message) {
                    const conflicting_bookings = response.message.filter(booking => {
                        const booking_start = booking.rental_start;
                        const booking_end = booking.rental_end;
                        const selected_start = frm.doc.rental_start;
                        const selected_end = frm.doc.rental_end;
                    
                        return (
                            (selected_start <= booking_end && selected_end >= booking_start) ||
                            (booking_start <= selected_end && booking_end >= selected_start)
                        );
                    });
                    
                    if (conflicting_bookings.length > 0) {
                        let conflict_details = conflicting_bookings.map(booking => 
                            `• ${booking.name} (${booking.rental_start} to ${booking.rental_end}) - Status: ${booking.status}`
                        ).join('<br>');
                        
                        frappe.msgprint({
                            title: __('Vehicle Not Available'),
                            message: __(`This vehicle is already booked for the selected dates:<br><br>${conflict_details}<br><br>Please select different dates or choose another vehicle.`),
                            indicator: 'red'
                        });
                        
                        frm.set_value('vehicle', '');
                        frm.set_value('rate_per_day', 0);
                        calculate_total_amount(frm);
                        resolve(false);
                    } else {
                        frappe.show_alert({
                            message: __('Vehicle is available for selected dates'),
                            indicator: 'green'
                        });
                        resolve(true);
                    }
                } else {
                    resolve(true);
                }
            },
            error: function() {
                frappe.msgprint(__('Error checking vehicle availability'));
                resolve(false);
            }
        });
    });
}

function calculate_days(frm) {
    if (frm.doc.rental_start && frm.doc.rental_end) {
        const start = frappe.datetime.str_to_obj(frm.doc.rental_start);
        const end = frappe.datetime.str_to_obj(frm.doc.rental_end);
        const diff = frappe.datetime.get_diff(end, start);
        const days = Math.ceil(diff) || 0;
        frm.set_value('no_days', days);
        calculate_total_amount(frm);
    }
}

function calculate_total_amount(frm) {
    const base_rent = (frm.doc.no_days || 0) * (frm.doc.rate_per_day || 0);
    let services_total = 0;

    (frm.doc.additional_services || []).forEach(row => {
        const row_total = (row.rate || 0) * (row.quantity || 0);
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
    const row = locals[cdt][cdn];
    const total = (row.rate || 0) * (row.quantity || 0);
    frappe.model.set_value(cdt, cdn, 'total', total);
}


function check_and_submit_if_needed(frm) {
    // Auto-submit if status is Out but document is still draft
    if (frm.doc.status === 'Out' && frm.doc.docstatus === 0) {
        console.log('Auto-submitting rental booking because pre-inspection is completed');
        
        // Set status to Confirmed first (required for submission)
        frm.set_value('status', 'Confirmed');
        
        // Save and submit
        frm.save().then(() => {
            frm.submit().then(() => {
                // After submission, update status to Out
                setTimeout(() => {
                    frappe.call({
                        method: 'frappe.client.set_value',
                        args: {
                            doctype: 'Rental Booking',
                            name: frm.doc.name,
                            fieldname: 'status',
                            value: 'Out'
                        },
                        callback: function() {
                            frm.reload_doc();
                        }
                    });
                }, 1000);
            });
        });
    }
}


