# FIXED Registration Endpoint - Replace in your main.py

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
        
        # Check if developer already exists
        existing_check = db.execute(
            text("SELECT id FROM developers WHERE name = :name"),
            {"name": registration.developer_name}
        ).fetchone()
        
        if existing_check:
            raise HTTPException(
                status_code=400,
                detail=f"Developer '{registration.developer_name}' already exists."
            )
        
        # Check what columns exist in the developers table
        columns_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'developers'
        """)
        
        result = db.execute(columns_query)
        existing_columns = [row[0] for row in result]
        
        print(f"Available columns in developers table: {existing_columns}")
        
        # Build insert query based on available columns
        base_columns = ["name", "active", "created_at"]
        base_values = [":name", ":active", ":created_at"]
        
        params = {
            "name": registration.developer_name,
            "active": True,
            "created_at": datetime.now(timezone.utc)
        }
        
        # Add optional columns if they exist
        if "email" in existing_columns:
            base_columns.append("email")
            base_values.append(":email")
            params["email"] = f"{developer_id}@temp.com"
        
        if "api_token" in existing_columns:
            # Check if token already exists
            token_check = db.execute(
                text("SELECT id FROM developers WHERE api_token = :token"),
                {"token": registration.api_token}
            ).fetchone()
            
            if token_check:
                raise HTTPException(
                    status_code=400,
                    detail="This access token is already in use."
                )
            
            base_columns.append("api_token")
            base_values.append(":api_token")
            params["api_token"] = registration.api_token
        
        # Build the insert query
        columns_str = ", ".join(base_columns)
        values_str = ", ".join(base_values)
        
        insert_query = text(f"""
            INSERT INTO developers ({columns_str}) 
            VALUES ({values_str})
        """)
        
        # Execute the insert
        db.execute(insert_query, params)
        db.commit()
        
        print(f"✅ Developer registered: {registration.developer_name}")
        
        return {
            "success": True,
            "message": "Developer registered successfully",
            "developer_id": developer_id,
            "developer_name": registration.developer_name,
            "available_columns": existing_columns,
            "monitoring_starts": "Data collection will begin immediately"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Rollback the transaction on any error
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
