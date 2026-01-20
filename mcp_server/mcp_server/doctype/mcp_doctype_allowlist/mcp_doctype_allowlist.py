import frappe
from frappe.model.document import Document

class MCPDoctypeAllowlist(Document):
    def validate(self):
        # Validate that fields exist in the target DocType
        if not self.doctype_ref:
            return
            
        meta = frappe.get_meta(self.doctype_ref)
        all_fields = [df.fieldname for df in meta.fields] + ['name', 'owner', 'creation', 'modified', 'modified_by', 'docstatus', 'idx']
        
        for row in self.allowed_fields_read:
            if row.fieldname not in all_fields:
                frappe.throw(f"Field {row.fieldname} not found in {self.doctype_ref}")

        for row in self.allowed_fields_write:
             if row.fieldname not in all_fields:
                frappe.throw(f"Field {row.fieldname} not found in {self.doctype_ref}")
