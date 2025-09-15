package legal_sim

# Default deny
default allow = false

# Allow access to health endpoints
allow if {
    input.path == "/health"
}

# Allow access to root endpoints
allow if {
    input.path == "/"
}

# Allow access to API documentation
allow if {
    input.path == "/docs"
}

# Allow access to OpenAPI spec
allow if {
    input.path == "/openapi.json"
}

# Case access policies
allow if {
    input.resource == "case"
    input.action == "read"
    input.user.role in ["admin", "attorney", "paralegal", "viewer"]
}

allow if {
    input.resource == "case"
    input.action == "create"
    input.user.role in ["admin", "attorney", "paralegal"]
}

allow if {
    input.resource == "case"
    input.action in ["update", "delete"]
    input.user.role in ["admin", "attorney"]
    input.case.created_by == input.user.id
}

# Evidence access policies
allow if {
    input.resource == "evidence"
    input.action in ["read", "download"]
    input.user.role in ["admin", "attorney", "paralegal", "viewer"]
}

allow if {
    input.resource == "evidence"
    input.action in ["create", "upload"]
    input.user.role in ["admin", "attorney", "paralegal"]
}

allow if {
    input.resource == "evidence"
    input.action in ["update", "delete", "lock"]
    input.user.role in ["admin", "attorney"]
    input.evidence.uploaded_by == input.user.id
}

# Storyboard access policies
allow if {
    input.resource == "storyboard"
    input.action in ["read", "list"]
    input.user.role in ["admin", "attorney", "paralegal", "viewer"]
}

allow if {
    input.resource == "storyboard"
    input.action == "create"
    input.user.role in ["admin", "attorney", "paralegal"]
}

allow if {
    input.resource == "storyboard"
    input.action in ["update", "delete", "validate", "compile"]
    input.user.role in ["admin", "attorney"]
    input.storyboard.created_by == input.user.id
}

# Render access policies
allow if {
    input.resource == "render"
    input.action in ["read", "list", "download"]
    input.user.role in ["admin", "attorney", "paralegal", "viewer"]
}

allow if {
    input.resource == "render"
    input.action == "create"
    input.user.role in ["admin", "attorney", "paralegal"]
}

allow if {
    input.resource == "render"
    input.action in ["update", "delete", "cancel"]
    input.user.role in ["admin", "attorney"]
    input.render.created_by == input.user.id
}

# Export access policies
allow if {
    input.resource == "export"
    input.action in ["read", "list", "download"]
    input.user.role in ["admin", "attorney", "paralegal", "viewer"]
}

allow if {
    input.resource == "export"
    input.action == "create"
    input.user.role in ["admin", "attorney", "paralegal"]
}

allow if {
    input.resource == "export"
    input.action == "delete"
    input.user.role in ["admin", "attorney"]
    input.export.created_by == input.user.id
}
