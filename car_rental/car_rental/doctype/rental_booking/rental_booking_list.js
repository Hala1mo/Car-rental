frappe.listview_settings["Rental Booking"] = {
    get_indicator: function(doc) {
        let status_color = {
            "Draft": "red",
            "Confirmed": "blue",
            "Cancelled": "red",
            "Out": "orange",
            "Returned": "purple",
            "Completed": "green"
        };

        let color = status_color[doc.status?.trim()] || "gray";

        // Debug line to see what status is being read
        console.log("Status:", doc.status, "→ Color:", color);

        return [__(doc.status), color, "status,=," + doc.status];
    }
};
