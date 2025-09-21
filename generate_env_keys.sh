#!/bin/bash
# Secure Key Generator for .env Configuration

echo "🔐 Generating Secure Keys for Your .env File"
echo "================================================"
echo ""

# Generate SECRET_KEY (for JWT tokens)
SECRET_KEY=$(openssl rand -hex 32)
echo "SECRET_KEY (for JWT authentication):"
echo "$SECRET_KEY"
echo ""

# Generate MASTER_SECRET (for stateless developer tokens)
MASTER_SECRET=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
echo "MASTER_SECRET (for developer token generation):"
echo "$MASTER_SECRET"
echo ""

# Generate database password
DB_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
echo "DATABASE_PASSWORD (for PostgreSQL user):"
echo "$DB_PASSWORD"
echo ""

echo "📝 Your complete .env file should look like:"
echo "============================================="

cat << EOF
# Database Configuration
DATABASE_URL=postgresql://timesheet_user:$DB_PASSWORD@localhost:5432/timesheet

# JWT Authentication Settings
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ActivityWatch Configuration
ACTIVITYWATCH_HOST=http://localhost:5600

# Stateless System Configuration  
MASTER_SECRET=$MASTER_SECRET
SERVER_URL=https://your-domain.com
# or for local testing: SERVER_URL=http://localhost:8000
EOF

echo ""
echo "🔒 Security Information:"
echo "========================"
echo "SECRET_KEY:    Used for JWT token signing/verification (user login)"
echo "MASTER_SECRET: Used for deterministic developer token generation"
echo "DB_PASSWORD:   Your PostgreSQL database password"
echo ""
echo "💾 Save these values securely!"
echo "⚠️  Never commit these to version control!"
echo "🔄 You can regenerate these anytime if needed"
