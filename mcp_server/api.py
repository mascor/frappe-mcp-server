import frappe
from frappe import _
from functools import wraps
import json
import time
from mcp_server.utils import (
    get_mcp_settings, 
    check_doctype_allowlist, 
    validate_fields, 
    validate_filters, 
    log_mcp_audit
)

def handle_mcp_auth():
    settings = get_mcp_settings()
    if not settings.enabled:
        frappe.throw(_("MCP Server is disabled"), frappe.PermissionError)

    if settings.auth_mode == "Token":
        token = frappe.request.headers.get("X-MCP-Token")
        if not token:
            # Fallback for clients sending "Authorization: token <token>"
            auth_header = frappe.request.headers.get("Authorization", "")
            if auth_header.startswith("token "):
                token = auth_header.split(" ")[1]

        if not token or token != settings.get_password("token_secret"):
            frappe.throw(_("Invalid MCP Token"), frappe.AuthenticationError)
        
        # Impersonate MCP User
        frappe.set_user(settings.mcp_user)
    
    elif settings.auth_mode == "API Key":
        if frappe.session.user != settings.mcp_user:
             frappe.throw(_("User {0} is not authorized for MCP access").format(frappe.session.user), frappe.PermissionError)

    # Basic security checks & setup
    frappe.local.mcp_request_id = frappe.generate_hash(length=10)
    frappe.local.mcp_start_time = time.time()
    frappe.local.mcp_user = settings.mcp_user
    
    return settings

def mcp_tool(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        tool_name = func.__name__
        execution_data = {
            "request_id": None,
            "tool_name": tool_name,
            "mcp_user": None,
            "doctype": kwargs.get("doctype"),
            "docname": kwargs.get("name") or kwargs.get("docname"),
            "operation": tool_name, # Map later?
            "status": "Success",
            "request_summary": kwargs,
            "response_summary": None,
            "error_trace": None,
            "diff": None,
            "ip_address": frappe.local.request.remote_addr if frappe.local.request else None
        }
        
        try:
            settings = handle_mcp_auth()
            execution_data["request_id"] = frappe.local.mcp_request_id
            execution_data["mcp_user"] = frappe.local.mcp_user
            
            # Additional validation?
            
            result = func(*args, **kwargs)
            
            execution_data["response_summary"] = result
            
            # If update logic populated diff, use it
            if getattr(frappe.local, 'mcp_diff', None):
                 execution_data["diff"] = frappe.local.mcp_diff
                 
            return result
            
        except Exception as e:
            execution_data["status"] = "Fail"
            execution_data["error_trace"] = frappe.get_traceback()
            if not execution_data["request_id"]:
                 execution_data["request_id"] = "unknown-" + frappe.generate_hash(length=5)
            
            # Rethrow but log first?
            # We must log the failure.
            # Calculate latency until now
            start_time = getattr(frappe.local, 'mcp_start_time', time.time())
            execution_data["latency_ms"] = int((time.time() - start_time) * 1000)
            
            if hasattr(e, "http_status_code"):
                 execution_data["http_status"] = e.http_status_code
            else:
                 execution_data["http_status"] = 500
                 
            log_mcp_audit(execution_data)
            raise e
            
        finally:
            if execution_data["status"] == "Success":
                 start_time = getattr(frappe.local, 'mcp_start_time', time.time())
                 execution_data["latency_ms"] = int((time.time() - start_time) * 1000)
                 log_mcp_audit(execution_data)
    
    # Register wrapper in frappe's whitelist registry (same as @frappe.whitelist() does)
    if func in frappe.whitelisted:
        frappe.whitelisted.append(wrapper)
    if func in frappe.guest_methods:
        frappe.guest_methods.append(wrapper)
    if func in frappe.allowed_http_methods_for_whitelisted_func:
        frappe.allowed_http_methods_for_whitelisted_func[wrapper] = frappe.allowed_http_methods_for_whitelisted_func[func]
                 
    return wrapper

@frappe.whitelist(allow_guest=True)
def ping_simple():
    """Simple ping for connectivity test - no MCP auth required."""
    return {"message": "pong", "site": frappe.local.site}

@frappe.whitelist(allow_guest=True)
@mcp_tool
def ping():
    return {
        "status": "ok",
        "site": frappe.local.site,
        "version": frappe.get_attr("mcp_server.__version__"),
        "user": frappe.session.user
    }

@frappe.whitelist(allow_guest=True)
@mcp_tool
def list_allowed_doctypes():
    settings = get_mcp_settings()
    # List all enabled allowed doctypes
    allowed = frappe.get_all("MCP Doctype Allowlist", 
        filters={"enabled": 1}, 
        fields=["doctype_ref", "allow_read", "allow_create", "allow_update", "allow_delete", "allow_meta", "name"]
    )
    
    # Filter out globally excluded ones (redundant if setup correctly but good to be safe)
    valid = []
    denylist = [d.exclude_doctype for d in settings.exclude_doctypes_default]
    
    for a in allowed:
        if a.doctype_ref not in denylist:
            valid.append(a)
            
    return valid

@frappe.whitelist(allow_guest=True)
@mcp_tool
def get_meta(doctype):
    check_doctype_allowlist(doctype, 'meta')
    
    meta = frappe.get_meta(doctype)
    # Filter sensitive fields? 
    # Use allowlist? 
    # Spec: "Output: schema filtrato secondo allowlist (solo campi consentiti)"
    # We should look at allowed_fields_read? Or is there a separate list for meta?
    # Spec says: "allow_meta (Check) — accesso a metadati/schema"
    # Typically meta includes all fields.
    # But strictly speaking, if I can't read a field, I probably shouldn't see it in meta?
    # Let's use validate_fields(..., operation='read') to get the list of allowed fields.
    
    allowlist_doc = check_doctype_allowlist(doctype, 'meta') # Check permission
    
    # Use read allowlist to filter fields
    allowed_fields = validate_fields(doctype, ["*"], 'read', allowlist_doc=allowlist_doc)
    
    # Construct filtered meta
    filtered_fields = []
    for df in meta.fields:
        if df.fieldname in allowed_fields:
            filtered_fields.append({
                "fieldname": df.fieldname,
                "label": df.label,
                "fieldtype": df.fieldtype,
                "options": df.options,
                "reqd": df.reqd,
                "default": df.default
            })
            
    return {
        "doctype": doctype,
        "fields": filtered_fields,
        "issingle": meta.issingle,
        "istable": meta.istable
    }

@frappe.whitelist(allow_guest=True)
@mcp_tool
def get_doc(doctype, name, fields=None):
    allowlist_doc = check_doctype_allowlist(doctype, 'read')
    
    # Validate fields
    if fields:
        if isinstance(fields, str):
            fields = json.loads(fields)
    else:
        fields = ["*"]
        
    requested_fields = validate_fields(doctype, fields, 'read', allowlist_doc=allowlist_doc)
    
    # Fetch doc
    # Use frappe.get_doc? Or frappe.db.get_value?
    # get_doc returns generic object.
    # We should return a dict with only allowed fields.
    
    doc = frappe.get_doc(doctype, name)
    doc.check_permission("read")
    
    result = {}
    
    # If standard fields (*), we need to expand it manually because we might not want to show sensitive system fields
    # or just show what's in requested_fields which we verified.
    
    if requested_fields == ["*"]:
        # Get all fields that are allowed
        # Re-resolve allowed fields
        requested_fields = validate_fields(doctype, ["*"], 'read', allowlist_doc=allowlist_doc)
        
    for f in requested_fields:
        if hasattr(doc, f):
            result[f] = getattr(doc, f)
            
    # Always include name?
    result["name"] = doc.name
            
    return result

@frappe.whitelist(allow_guest=True)
@mcp_tool
def search_docs(doctype, filters=None, fields=None, order_by=None, page_length=20, page_start=0):
    allowlist_doc = check_doctype_allowlist(doctype, 'read')
    
    if filters and isinstance(filters, str):
        filters = json.loads(filters)
    
    if fields and isinstance(fields, str):
        fields = json.loads(fields)
        
    # Validate filters
    validate_filters(doctype, filters, allowlist_doc=allowlist_doc)
    
    # Validate fields
    if not fields:
        fields = ["name"] # Default minimal? Or all allowed?
        # Spec says: "lista documenti (name + fields consentiti)"
        # Let's Default to Name + Title? or just Name.
        # Let's use ["name"] as safe default.
    
    requested_fields = validate_fields(doctype, fields, 'read', allowlist_doc=allowlist_doc)
    
    # Enforce Page Limits
    settings = get_mcp_settings()
    max_limit = allowlist_doc.max_page_length or settings.default_max_page_length or 20
    if int(page_length) > int(max_limit):
        page_length = max_limit
        
    docs = frappe.get_list(doctype, 
        filters=filters, 
        fields=requested_fields, 
        order_by=order_by, 
        start=page_start, 
        page_length=page_length,
        ignore_permissions=False # Enforce standard permissions
    )
    
    return docs

@frappe.whitelist(allow_guest=True)
@mcp_tool
def create_doc(doctype, data):
    allowlist_doc = check_doctype_allowlist(doctype, 'create')
    
    if isinstance(data, str):
        data = json.loads(data)
        
    # Validate write fields
    # We want to ensure passed data ONLY contains allowed fields.
    allowed_write_fields = validate_fields(doctype, ["*"], 'write', allowlist_doc=allowlist_doc)
    
    clean_data = {"doctype": doctype}
    for k, v in data.items():
        if k in allowed_write_fields:
            clean_data[k] = v
        else:
            frappe.throw(f"Field {k} is not allowed for creation on {doctype}", frappe.PermissionError)
            
    doc = frappe.get_doc(clean_data)
    doc.insert()
    
    # Return snapshot (read permissions)
    return doc.as_dict()

@frappe.whitelist(allow_guest=True)
@mcp_tool
def update_doc(doctype, name, data):
    allowlist_doc = check_doctype_allowlist(doctype, 'update')
    
    if isinstance(data, str):
        data = json.loads(data)
        
    allowed_write_fields = validate_fields(doctype, ["*"], 'write', allowlist_doc=allowlist_doc)
    
    clean_data = {}
    for k, v in data.items():
        if k in allowed_write_fields:
            clean_data[k] = v
        else:
            frappe.throw(f"Field {k} is not allowed for update on {doctype}", frappe.PermissionError)
            
    doc = frappe.get_doc(doctype, name)
    
    # Diff logging?
    settings = get_mcp_settings()
    if settings.enable_diff_logging:
        # Calculate diff manually? or use frappe's
        # We can store old values
        old_values = {}
        for k in clean_data.keys():
            old_values[k] = getattr(doc, k, None)
            
        frappe.local.mcp_diff = {
            "old": old_values,
            "new": clean_data
        }
    
    doc.update(clean_data)
    doc.save()
    
    return doc.as_dict()

@frappe.whitelist(allow_guest=True)
@mcp_tool
def delete_doc(doctype, name):
    check_doctype_allowlist(doctype, 'delete')
    
    if not frappe.db.exists(doctype, name):
        frappe.throw(f"Document {doctype} {name} not found", frappe.DoesNotExistError)

    frappe.delete_doc(doctype, name, ignore_permissions=True)
    
    return {"status": "deleted", "name": name}
