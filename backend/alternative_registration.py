# Alternative fix - update your registration endpoint to use existing columns
# Replace the existing @app.post("/api/register-developer") in your main.py with this:

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
        
        # Check if developer name already exists (using 'name' column instead of 'developer_id')
        existing_check = db.execute(
            text("SELECT id FROM developers WHERE name = :name"),
            {"name": registration.developer_name}
        ).fetchone()
        
        if existing_check:
            raise HTTPException(
                status_code=400,
                detail=f"Developer '{registration.developer_name}' already exists. Please use a different name."
            )
        
        # Insert new developer using existing table structure
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
            "email": f"{developer_id}@company.com",  # Generate email or leave null
            "api_token": registration.api_token,
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
            "monitoring_starts": "Data collection will begin immediately",
            "portal_access": f"Developer will appear in portal as '{registration.developer_name}'"
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
