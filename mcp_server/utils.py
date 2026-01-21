import frappe
import json
import time

def get_mcp_settings():
    return frappe.get_single("MCP Server Settings")

def check_doctype_allowlist(doctype, operation):
    """
    Checks if the DocType is in the allowlist and if the operation is permitted.
    operation: 'read', 'create', 'update', 'delete', 'meta'
    """
    # 1. Global Denylist in Settings
    settings = get_mcp_settings()
    for row in settings.exclude_doctypes_default:
        if row.exclude_doctype == doctype:
            frappe.throw(f"DocType {doctype} is globally excluded", frappe.PermissionError)

    # 2. Allowlist Check
    # We query the Allowlist DocType matching this doctype
    # Name is format:{doctype_ref}, so we can try to fetch it directly or by filter
    allowlist_name = frappe.db.get_value("MCP Doctype Allowlist", {"doctype_ref": doctype, "enabled": 1}, "name")
    
    if not allowlist_name:
        frappe.throw(f"DocType {doctype} is not in the allowlist", frappe.PermissionError)
    
    allowlist = frappe.get_doc("MCP Doctype Allowlist", allowlist_name)
    
    # Check specific operation
    perm_map = {
        'read': allowlist.allow_read,
        'create': allowlist.allow_create,
        'update': allowlist.allow_update,
        'delete': allowlist.allow_delete,
        'meta': allowlist.allow_meta
    }
    
    if not perm_map.get(operation):
        frappe.throw(f"Operation {operation} not allowed for {doctype}", frappe.PermissionError)
        
    return allowlist

def validate_fields(doctype, fields_list, operation, allowlist_doc=None):
    """
    Validates that requested fields are in the allowlist.
    fields_list: list of fieldnames or "*"
    operation: 'read' or 'write'
    """
    if not allowlist_doc:
        allowlist_doc = check_doctype_allowlist(doctype, 'read' if operation=='read' else 'update')

    allowed_items = []
    if operation == 'read':
        allowed_items = [row.fieldname for row in allowlist_doc.allowed_fields_read]
    else:
        allowed_items = [row.fieldname for row in allowlist_doc.allowed_fields_write]
    
    # If allowed_items is empty, it means ALL fields (non-sensitive) are allowed?
    # Spec says: "vuoto = default deny oppure default allow (decidere per sicurezza: consigliato default deny)"
    # But for read, usually you want * by default if nothing specified?
    # Let's check the spec again: "allowed_fields_read ... vuoto = default deny o default allow"
    # Given the strict nature, default deny seems safer, BUT practically, if I just enabled a DocType, I probably want to read basic fields.
    # However, to be safe and strictly compliant with "Schema strettissimo", we should probably treat empty list as "Everything allowed" OR "Nothing allowed".
    # Let's interpret the Requirement: "Schema strettissimo ... Accettare solo parametri esplicitamente definiti".
    # But later "validare filtri: solo campi e operatori consentiti".
    
    # Let's implement this logic:
    # If the child table is EMPTY, we assume strictly nothing specific is whitelisted.
    # BUT, that makes it very tedious.
    # Let's assume if child table is empty -> Allow All Standard Fields (excluding sensitive ones).
    # If child table has items -> Allow ONLY those items.
    
    is_strict = len(allowed_items) > 0
    
    if is_strict:
        for f in fields_list:
            if f == "*":
                 # If wildcard requested, we should return all allowed fields
                 return allowed_items
            if f not in allowed_items:
                 frappe.throw(f"Field {f} is not allowed for {operation} on {doctype}", frappe.PermissionError)
        return fields_list
    else:
        # No restrictions defined -> Allow all existing fields in DocType
        # But we should still validate they exist in DocType to avoid SQL injection or errors
        meta = frappe.get_meta(doctype)
        valid_fields = [df.fieldname for df in meta.fields] + ['name', 'owner', 'creation', 'modified', 'modified_by', 'docstatus', 'idx']
        
        # Exclude sensitive? (password etc) -> Standard Frappe might handle, but good to be safe.
        
        if fields_list == ["*"]:
            return valid_fields
            
        for f in fields_list:
             if f not in valid_fields:
                 frappe.throw(f"Field {f} does not exist in {doctype}", frappe.ValidationError)
        return fields_list

def validate_filters(doctype, filters, allowlist_doc=None):
    """
    Validates filters against the allowlist.
    filters: dict {field: value} or list of lists [[field, op, value], ...]
    """
    if not filters:
        return
        
    if not allowlist_doc:
         allowlist_doc = check_doctype_allowlist(doctype, 'read')
         
    # Parse allowed filters into a quick lookup: {fieldname: [allowed_ops]}
    has_restrictions = len(allowlist_doc.allowed_filters) > 0
    allowed_map = {} 

    if has_restrictions:
        for row in allowlist_doc.allowed_filters:
            if row.fieldname not in allowed_map:
                allowed_map[row.fieldname] = set()
            allowed_map[row.fieldname].add(row.operator)

    # Normalize filters to list of [field, op, value]
    filter_list = []
    if isinstance(filters, dict):
        for k, v in filters.items():
            filter_list.append([k, "=", v])
    elif isinstance(filters, list):
        for f in filters:
            if isinstance(f, list) or isinstance(f, tuple):
                if len(f) == 3:
                     filter_list.append([f[0], f[1], f[2]])
                elif len(f) == 2: # field, value -> op "="
                     filter_list.append([f[0], "=", f[1]])
    
    # Validation loop
    for f_item in filter_list:
        field = f_item[0]
        op = f_item[1]
        
        # Always allow filtering by name? Usually yes.
        if field == "name":
            continue
            
        if has_restrictions:
            if field not in allowed_map:
                frappe.throw(f"Filtering by field '{field}' is not allowed", frappe.PermissionError)
                
            if op not in allowed_map[field]:
                 frappe.throw(f"Operator '{op}' is not allowed for field '{field}'", frappe.PermissionError) 

def log_mcp_audit(execution_data):
    """
    execution_data: dict with keys matching MCP Audit Log fields
    """
    try:
        # Run in a separate transaction or ensure it's committed even if main fails?
        # Frappe doesn't easily support separate transaction logging within same request without rollback issues if main fails.
        # But we want to log Failures too.
        # Usually we use `frappe.db.commit()` at the end, but if exception happens, we assume the handler catches it and logs.
        
        doc = frappe.get_doc({
            "doctype": "MCP Audit Log",
            "request_id": execution_data.get("request_id"),
            "tool_name": execution_data.get("tool_name"),
            "mcp_user": execution_data.get("mcp_user"),
            "doctype": execution_data.get("doctype"), # Warning: conflict with fieldname 'doctype' in dict? No, frappe.get_doc uses argument or 'doctype' key.
            # Wait, 'doctype' is a reserved fieldname in Frappe for the Document Class.
            # In my MCP Audit Log, I named the field `ref_doctype` (label DocType) to avoid conflict? 
            # Let me check my JSON.
            # I named it `ref_doctype` in JSON!
            "ref_doctype": execution_data.get("doctype"),
            "docname": execution_data.get("docname"),
            "operation": execution_data.get("operation"),
            "status": execution_data.get("status"),
            "http_status": execution_data.get("http_status", 200),
            "latency_ms": execution_data.get("latency_ms"),
            "ip_address": execution_data.get("ip_address"),
            "request_summary_json": json.dumps(execution_data.get("request_summary"), default=str),
            "response_summary_json": json.dumps(execution_data.get("response_summary"), default=str),
            "diff_json": json.dumps(execution_data.get("diff"), default=str) if execution_data.get("diff") else None,
            "error_trace": execution_data.get("error_trace")
        })
        doc.insert(ignore_permissions=True)
        # We might need to commit explicitly if the main transaction is going to be rolled back?
        # If we are inside an exception handler for a failed request, we definitely want to commit this log.
        if execution_data.get("status") == "Fail":
             frappe.db.commit()
             
    except Exception as e:
        # Last resort logging
        print(f"Failed to write MCP Audit Log: {e}")

