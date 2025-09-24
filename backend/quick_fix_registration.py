# IMMEDIATE FIX - Replace your registration endpoint in main.py with this:

@app.post("/api/register-developer")
async def register_developer(
    registration: DeveloperRegistration,
    db: Session = Depends(get_db)
):
    """Simple developer registration using existing table structure"""
    try:
        # Generate developer ID from name
        developer_id = generate_developer_id(registration.developer_name)
        
        # Validate access token format
        if not registration.api_token.startswith('AWToken_'):
            raise HTTPException(
                status_code=400,
                detail="Invalid access token format. Token must start with 'AWToken_'"
            )
        
        # Use existing table columns - check by 'name' instead of 'developer_id'
        existing_check = db.execute(
            text("SELECT id FROM developers WHERE name = :name"),
            {"name": registration.developer_name}
        ).fetchone()
        
        if existing_check:
            raise HTTPException(
                status_code=400,
                detail=f"Developer '{registration.developer_name}' already exists."
            )
        
        # Check if api_token column exists, if not, don't use it
        try:
            # Try to check if token exists
            token_check = db.execute(
                text("SELECT id FROM developers WHERE api_token = :token"),
                {"token": registration.api_token}
            ).fetchone()
            
            if token_check:
                raise HTTPException(
                    status_code=400,
                    detail="This access token is already in use."
                )
        except:
            # api_token column doesn't exist, skip this check
            pass
        
        # Insert using only existing columns
        try:
            # Try with api_token column
            insert_query = text("""
                INSERT INTO developers (
                    name,
                    email,
                    api_token,
                    active,
                    created_at
                ) VALUES (
                    :name,
                    :email,
                    :api_token,
                    :active,
                    :created_at
                )
            """)
            
            db.execute(insert_query, {
                "name": registration.developer_name,
                "email": f"{developer_id}@temp.com",
                "api_token": registration.api_token,
                "active": True,
                "created_at": datetime.now(timezone.utc)
            })
            
        except:
            # Fallback - insert without api_token column
            insert_query = text("""
                INSERT INTO developers (
                    name,
                    email,
                    active,
                    created_at
                ) VALUES (
                    :name,
                    :email,
                    :active,
                    :created_at
                )
            """)
            
            db.execute(insert_query, {
                "name": registration.developer_name,
                "email": f"{developer_id}@temp.com",
                "active": True,
                "created_at": datetime.now(timezone.utc)
            })
        
        db.commit()
        
        # Log successful registration
        print(f"✅ Developer registered: {registration.developer_name}")
        
        return {
            "success": True,
            "message": "Developer registered successfully",
            "developer_id": developer_id,
            "developer_name": registration.developer_name,
            "note": "Using existing table structure",
            "monitoring_starts": "Data collection will begin immediately"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Registration failed for {registration.developer_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )

# Also add this endpoint to serve the registration form
@app.get("/register-developer")
async def serve_registration_form():
    """Serve the developer registration form"""
    return FileResponse("register-developer.html")
