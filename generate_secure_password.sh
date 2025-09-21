#!/bin/bash
# Secure Password Generator and Database User Setup

# Generate a secure password (32 characters with letters, numbers, and symbols)
SECURE_PASSWORD=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)

echo "🔐 Generated Secure Password: $SECURE_PASSWORD"
echo "💾 Save this password securely!"
echo ""
echo "🔧 Database Setup Commands:"
echo ""

# PostgreSQL commands to create/update user
cat << EOF
-- Connect to PostgreSQL and run these commands:
sudo -u postgres psql

-- If user doesn't exist, create it:
CREATE USER timesheet_user WITH PASSWORD '$SECURE_PASSWORD';

-- If user already exists, update password:
ALTER USER timesheet_user WITH PASSWORD '$SECURE_PASSWORD';

-- Grant permissions:
GRANT ALL PRIVILEGES ON DATABASE timesheet TO timesheet_user;
ALTER USER timesheet_user CREATEDB;

-- Exit PostgreSQL:
\\q
EOF

echo ""
echo "📝 Update your .env file:"
echo "DATABASE_URL=postgresql://timesheet_user:$SECURE_PASSWORD@localhost:5432/timesheet"
echo ""
echo "🔒 Security Notes:"
echo "- This password contains letters, numbers, and is 24 characters long"
echo "- Save it in a password manager"
echo "- Never commit it to version control"
echo "- Keep your .env file secure"
