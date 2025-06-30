from __future__ import unicode_literals
from frappe import _

def get_data():
    return [
        {
            "label": _("Fleet Management"),
            "icon": "fa fa-car",
            "items": [
                {
                    "type": "doctype",
                    "name": "Vehicle",
                    "doctype": "Vehicle",
                    "description": _("Manage your vehicle fleet")
                },
                {
                    "type": "doctype", 
                    "name": "Vehicle Type",
                    "doctype": "Vehicle Type",
                    "description": _("Vehicle categories and types")
                }
            ]
        },
        {
            "label": _("Bookings & Contracts"),
            "icon": "fa fa-calendar",
            "items": [
                {
                    "type": "doctype",
                    "name": "Rental Booking",
                    "doctype": "Rental Booking",
                    "description": _("Customer rental bookings")
                },
                {
                    "type": "doctype",
                    "name": "Rental Contract", 
                    "doctype": "Rental Contract",
                    "description": _("Rental agreements and contracts")
                },
                {
                    "type": "doctype",
                    "name": "Customer",
                    "doctype": "Customer",
                    "description": _("Customer database")
                }
            ]
        }
        # {
        #     "label": _("Reports & Analytics"),
        #     "icon": "fa fa-bar-chart",
        #     "items": [
        #         {
        #             "type": "report",
        #             "name": "Fleet Utilization",
        #             "doctype": "Vehicle", 
        #             "is_query_report": True,
        #             "description": _("Vehicle utilization analysis")
        #         },
        #         {
        #             "type": "report", 
        #             "name": "Rental Revenue",
        #             "doctype": "Rental Booking",
        #             "is_query_report": True,
        #             "description": _("Revenue and earnings report")
        #         },
        #         {
        #             "type": "report",
        #             "name": "Active Rentals",
        #             "doctype": "Rental Booking", 
        #             "is_query_report": True,
        #             "description": _("Currently active rentals")
        #         }
        #     ]
        # }
    ]