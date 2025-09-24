# Add these endpoints to your main.py for the web-based token manager

@app.get("/token-manager")
async def serve_token_manager():
    """Serve the token management interface"""
    return FileResponse("token-manager.html")

@app.post("/api/admin/create-token")
async def create_developer_token(
    request: dict,
    db: Session = Depends(get_db)
):
    """Create a single developer token"""
    try:
        import secrets
        
        developer_name = request.get('developer_name', '').strip()
        token_name = request.get('token_name', '').strip()
        
        if not developer_name:
            raise HTTPException(status_code=400, detail="Developer name is required")
        
        token_name = token_name or f"{developer_name} Token"
        
        # Generate secure token
        token = f"AWToken_{secrets.token_urlsafe(32)}"
        
        # Check if developer already has a token
        existing_query = text("""
            SELECT api_token FROM developer_api_tokens 
            WHERE developer_id = :dev_id AND is_active = true
        """)
        existing = db.execute(existing_query, {"dev_id": developer_name}).fetchone()
        
        if existing:
            # Deactivate old token
            db.execute(text("""
                UPDATE developer_api_tokens 
                SET is_active = false 
                WHERE developer_id = :dev_id
            """), {"dev_id": developer_name})
        
        # Insert new token
        insert_query = text("""
            INSERT INTO developer_api_tokens (developer_id, api_token, token_name)
            VALUES (:dev_id, :token, :name)
        """)
        
        db.execute(insert_query, {
            "dev_id": developer_name,
            "token": token,
            "name": token_name
        })
        
        db.commit()
        
        return {
            "success": True,
            "developer_name": developer_name,
            "token": token,
            "token_name": token_name,
            "message": "Token created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating token: {str(e)}")

@app.post("/api/admin/bulk-create-tokens")
async def bulk_create_developer_tokens(
    request: dict,
    db: Session = Depends(get_db)
):
    """Create tokens for multiple developers"""
    try:
        import secrets
        
        developer_names = request.get('developer_names', [])
        
        if not developer_names:
            raise HTTPException(status_code=400, detail="Developer names are required")
        
        created_tokens = []
        
        for dev_name in developer_names:
            dev_name = dev_name.strip()
            if not dev_name:
                continue
            
            # Generate secure token
            token = f"AWToken_{secrets.token_urlsafe(32)}"
            token_name = f"{dev_name} Token"
            
            try:
                # Check if developer already has a token
                existing_query = text("""
                    SELECT api_token FROM developer_api_tokens 
                    WHERE developer_id = :dev_id AND is_active = true
                """)
                existing = db.execute(existing_query, {"dev_id": dev_name}).fetchone()
                
                if existing:
                    # Deactivate old token
                    db.execute(text("""
                        UPDATE developer_api_tokens 
                        SET is_active = false 
                        WHERE developer_id = :dev_id
                    """), {"dev_id": dev_name})
                
                # Insert new token
                insert_query = text("""
                    INSERT INTO developer_api_tokens (developer_id, api_token, token_name)
                    VALUES (:dev_id, :token, :name)
                """)
                
                db.execute(insert_query, {
                    "dev_id": dev_name,
                    "token": token,
                    "name": token_name
                })
                
                created_tokens.append({
                    "developer_name": dev_name,
                    "token": token,
                    "token_name": token_name
                })
                
            except Exception as e:
                print(f"Error creating token for {dev_name}: {e}")
                continue
        
        db.commit()
        
        return {
            "success": True,
            "created_count": len(created_tokens),
            "tokens": created_tokens,
            "message": f"Created {len(created_tokens)} tokens successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating tokens: {str(e)}")

@app.get("/api/admin/list-tokens")
async def list_developer_tokens(db: Session = Depends(get_db)):
    """List all developer tokens"""
    try:
        query = text("""
            SELECT developer_id, api_token, token_name, created_at, is_active
            FROM developer_api_tokens 
            ORDER BY created_at DESC
        """)
        
        result = db.execute(query)
        tokens = []
        
        for row in result:
            tokens.append({
                "developer_name": row[0],
                "token": row[1],
                "token_name": row[2],
                "created_at": row[3].isoformat() if row[3] else None,
                "is_active": row[4]
            })
        
        return {
            "success": True,
            "tokens": tokens,
            "total_count": len(tokens)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing tokens: {str(e)}")
