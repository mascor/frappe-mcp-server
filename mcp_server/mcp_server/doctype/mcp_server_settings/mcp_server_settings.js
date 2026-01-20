// Copyright (c) 2025, Me and contributors
// For license information, please see license.txt

frappe.ui.form.on("MCP Server Settings", {
    refresh(frm) {
        if (frm.doc.auth_mode === "Token" && !frm.doc.token_secret) {
            frm.set_value("token_secret", frappe.utils.get_random(32));
        }
    },
});
