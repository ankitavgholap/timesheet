# FINAL CORRECT Registration Endpoint - Replace in your main.py

@app.post("/api/register-developer")
async def register_developer(
    registration: DeveloperRegistration,
    db: Session = Depends(get_db)
):
    """Developer registration with proper table structure"""
    try:
        # Generate developer ID from name
        developer_id = generate_developer_id(registration.developer_name)
        
        # Validate access token format
        if not registration.api_token.startswith('AWToken_'):
            raise HTTPException(
                status_code=400,
                detail="Invalid access token format. Token must start with 'AWToken_'"
            )
        
        # Check if developer_id already exists
        existing_dev = db.execute(
            text("SELECT id FROM developers WHERE developer_id = :dev_id"),
            {"dev_id": developer_id}
        ).fetchone()
        
        if existing_dev:
            raise HTTPException(
                status_code=400,
                detail=f"Developer ID '{developer_id}' already exists. Please use a different name."
            )
        
        # Check if name already exists
        existing_name = db.execute(
            text("SELECT id FROM developers WHERE name = :name"),
            {"name": registration.developer_name}
        ).fetchone()
        
        if existing_name:
            raise HTTPException(
                status_code=400,
                detail=f"Developer name '{registration.developer_name}' already exists. Please use a different name."
            )
        
        # Check if api_token already exists
        existing_token = db.execute(
            text("SELECT id FROM developers WHERE api_token = :token"),
            {"token": registration.api_token}
        ).fetchone()
        
        if existing_token:
            raise HTTPException(
                status_code=400,
                detail="This access token is already in use by another developer."
            )
        
        # Insert new developer using the correct table structure
        insert_query = text("""
            INSERT INTO developers (
                developer_id,
                name,
                email,
                active,
                api_token,
                created_at
            ) VALUES (
                :developer_id,
                :name,
                :email,
                :active,
                :api_token,
                :created_at
            )
        """)
        
        db.execute(insert_query, {
            "developer_id": developer_id,
            "name": registration.developer_name,
            "email": f"{developer_id}@company.com",
            "active": True,
            "api_token": registration.api_token,
            "created_at": datetime.now(timezone.utc)
        })
        
        db.commit()
        
        print(f"✅ Developer registered: {developer_id} ({registration.developer_name})")
        
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

@app.get("/register-developer")
async def serve_registration_form():
    """Serve the developer registration form"""
    return FileResponse("register-developer.html")
