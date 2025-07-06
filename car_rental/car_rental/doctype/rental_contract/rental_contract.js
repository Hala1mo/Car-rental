// Rental Contract JavaScript

frappe.ui.form.on('Rental Contract', {
    refresh(frm) {
        // Add custom buttons
        add_contract_buttons(frm);
        
        // Set queries
        setup_queries(frm);
        
        // Update contract status display
        update_status_display(frm);
    },
    
    onload(frm) {
        // Set default values for new contracts
        if (frm.doc.__islocal) {
            frm.set_value('contract_date', frappe.datetime.now_datetime());
            frm.set_value('contract_status', 'Draft');
            
            // Add helpful placeholder for terms and conditions
            if (!frm.doc.legal_and_terms) {
                frm.fields_dict.legal_and_terms.$wrapper.find('textarea').attr('placeholder', 
                    'Please enter the terms and conditions for this rental contract...\n\n' +
                    'You may include:\n' +
                    '• Vehicle condition requirements\n' +
                    '• Payment terms\n' +
                    '• Insurance details\n' +
                    '• Driver requirements\n' +
                    '• Cancellation policy\n' +
                    '• Liability terms\n' +
                    '• Return conditions'
                );
            }
        }
    },
    
    rental_booking(frm) {
        // Auto-populate fields when rental booking is selected
        if (frm.doc.rental_booking) {
            populate_from_rental_booking(frm);
        } else {
            // Clear fields if rental booking is removed
            clear_rental_fields(frm);
        }
    },
    
    before_submit(frm) {
        // Validate terms and conditions are provided
        if (!frm.doc.legal_and_terms || frm.doc.legal_and_terms.trim() === '') {
            frappe.msgprint({
                title: __('Missing Terms and Conditions'),
                message: __('Please provide the terms and conditions before submitting the contract'),
                indicator: 'red'
            });
            frappe.validated = false;
            return;
        }
        
        // Set status to Active when submitted
        frm.set_value('contract_status', 'Active');
    },
    
    on_submit(frm) {
        frappe.show_alert({
            message: __('Rental contract submitted successfully'),
            indicator: 'green'
        });
        
        // Refresh to show updated status
        setTimeout(() => {
            frm.reload_doc();
        }, 1000);
    },
    
    on_cancel(frm) {
        // Update status to Terminated
        frm.set_value('contract_status', 'Terminated');
        
        frappe.show_alert({
            message: __('Rental contract cancelled'),
            indicator: 'orange'
        });
    }
});

function add_contract_buttons(frm) {
    if (!frm.doc.__islocal) {
        // Add Print Contract button
        frm.add_custom_button(__('Print Contract'), () => {
            print_contract(frm);
        }).addClass('btn-primary');
        
        // Add View Rental Booking button if linked
        if (frm.doc.rental_booking) {
            frm.add_custom_button(__('View Rental Booking'), () => {
                frappe.set_route('Form', 'Rental Booking', frm.doc.rental_booking);
            });
        }
    }
    
    // Add Template Terms button if terms are empty (for both new and existing drafts)
    if (frm.doc.docstatus === 0 && (!frm.doc.legal_and_terms || frm.doc.legal_and_terms.trim() === '')) {
        frm.add_custom_button(__('Add Template Terms'), () => {
            add_template_terms(frm);
        }).addClass('btn-secondary');
    }
}

function populate_from_rental_booking(frm) {
    if (!frm.doc.rental_booking) return;
    
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Rental Booking',
            name: frm.doc.rental_booking
        },
        callback: function(r) {
            if (r.message) {
                const booking = r.message;
                
                // Populate basic fields (no calculation, just copy totals)
                frm.set_value('customer', booking.customer);
                frm.set_value('vehicle', booking.vehicle);
                frm.set_value('rental_start_date', booking.rental_start || '');
                frm.set_value('rental_end_date', booking.rental_end || '');
                frm.set_value('rental_days', booking.no_days || '');
                frm.set_value('rate_per_day', booking.rate_per_day || '');
                frm.set_value('total_amount', booking.amount || ''); // Take final total from booking
                
                // Get customer details
                if (booking.customer) {
                    get_customer_details(frm, booking.customer);
                }
                
                // Get vehicle details
                if (booking.vehicle) {
                    get_vehicle_details(frm, booking.vehicle);
                }
                
                // Copy additional services (with their calculated totals)
                frm.clear_table('additional_services');
                if (booking.additional_services) {
                    booking.additional_services.forEach(service => {
                        const row = frm.add_child('additional_services');
                        row.service_name = service.service_name;
                        row.quantity = service.quantity;
                        row.rate = service.rate;
                        row.total = service.total; 
                    });
                    frm.refresh_field('additional_services');
                }
                
                frappe.show_alert({
                    message: __('Contract populated from rental booking'),
                    indicator: 'green'
                });
            }
        }
    });
}

function get_customer_details(frm, customer) {
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Customer',
            name: customer
        },
        callback: function(r) {
            if (r.message) {
                const customer_doc = r.message;
                frm.set_value('customer_name', customer_doc.customer_name || '');
                frm.set_value('customer_email', customer_doc.email_id || '');
                frm.set_value('customer_phone', customer_doc.mobile_no || '');
            }
        }
    });
}

function get_vehicle_details(frm, vehicle) {
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Vehicle',
            name: vehicle
        },
        callback: function(r) {
            if (r.message) {
                const vehicle_doc = r.message;
                frm.set_value('vehicle_make', vehicle_doc.make || '');
                frm.set_value('vehicle_model', vehicle_doc.model || '');
                frm.set_value('license_plate', vehicle_doc.license_plate || '');
            }
        }
    });
}

function clear_rental_fields(frm) {
    const fields_to_clear = [
        'customer', 'vehicle', 'rental_start_date', 'rental_end_date',
        'rental_days', 'rate_per_day', 'total_amount', 'customer_name',
        'customer_email', 'customer_phone', 'vehicle_make', 'vehicle_model',
        'license_plate'
    ];
    
    fields_to_clear.forEach(field => {
        frm.set_value(field, '');
    });
    
    frm.clear_table('additional_services');
    frm.refresh_field('additional_services');
}

function update_status_display(frm) {
    // Add visual indicators based on status
    if (frm.doc.contract_status === 'Active') {
        frm.dashboard.add_indicator(__('Active Contract'), 'green');
    } else if (frm.doc.contract_status === 'Completed') {
        frm.dashboard.add_indicator(__('Completed Contract'), 'blue');
    } else if (frm.doc.contract_status === 'Terminated') {
        frm.dashboard.add_indicator(__('Terminated Contract'), 'red');
    }
}

function print_contract(frm) {
    // Open print dialog
    window.open(`/printview?doctype=Rental Contract&name=${frm.doc.name}&format=Standard`, '_blank');
}

function add_template_terms(frm) {
    frappe.confirm(
        __('This will add template terms and conditions. You can modify them as needed. Continue?'),
        () => {
            const template_terms = `RENTAL AGREEMENT TERMS AND CONDITIONS

Contract Details:
- Contract Number: ${frm.doc.name || 'To be assigned'}
- Contract Date: ${frappe.datetime.get_today()}
- Customer: ${frm.doc.customer_name || ''}
- Vehicle: ${frm.doc.vehicle_make || ''} ${frm.doc.vehicle_model || ''} (${frm.doc.license_plate || ''})

RENTAL PERIOD:
- Start Date: ${frm.doc.rental_start_date || ''}
- End Date: ${frm.doc.rental_end_date || ''}
- Total Days: ${frm.doc.rental_days || ''}
- Rate per Day: ${frm.doc.rate_per_day || ''}
- Total Amount: ${frm.doc.total_amount || ''}

TERMS AND CONDITIONS:

1. VEHICLE CONDITION
   - The vehicle is provided in good working condition
   - Customer must return vehicle in the same condition as received
   - Pre and post-rental inspections will be conducted
   - Any damages will be charged to the customer

2. DRIVER REQUIREMENTS
   - Customer must have a valid driver's license
   - Driver must be at least 21 years old
   - Only authorized drivers may operate the vehicle

3. RESPONSIBILITIES
   - Customer is responsible for vehicle safety and security
   - Customer is responsible for all traffic violations
   - Vehicle must not be used for illegal purposes
   - No smoking allowed in the vehicle

4. PAYMENT TERMS
   - Full payment required as per rental booking
   - Late payment charges may apply for overdue payments
   - Security deposit may be required

5. INSURANCE
   - Vehicle is covered under company insurance
   - Customer may be liable for insurance deductibles
   - Customer should verify personal insurance coverage

6. FUEL POLICY
   - Vehicle should be returned with the same fuel level
   - Fuel charges will apply if returned with less fuel

7. MILEAGE
   - Unlimited mileage within agreed area
   - Additional charges for excessive mileage (if applicable)

8. CANCELLATION
   - Cancellation terms as per company policy
   - Advance notice required for cancellations
   - Cancellation fees may apply

9. LIABILITY
   - Customer is liable for any damage or loss
   - Company not responsible for personal belongings
   - Customer responsible for towing charges if applicable

10. GOVERNING LAW
    - This agreement is governed by local laws
    - Any disputes subject to local jurisdiction

SIGNATURES:
By signing below, both parties agree to these terms and conditions.

Customer Signature: _____________________ Date: ___________

Company Representative: _________________ Date: ___________`;

            frm.set_value('legal_and_terms', template_terms);
            
            frappe.show_alert({
                message: __('Template terms added. Please review and modify as needed.'),
                indicator: 'green'
            });
        }
    );
}

// Additional Services child table events - Just for display, no calculation needed
frappe.ui.form.on('Additional Services', {
    // Remove all calculation functions since we get totals from rental booking
    additional_services_remove(frm) {
        // Just refresh the table display
        frm.refresh_field('additional_services');
    }
});

