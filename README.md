# Timesheet Application with ActivityWatch Integration

A comprehensive timesheet application that automatically tracks your computer activity using ActivityWatch and displays detailed analytics with beautiful charts and filtering capabilities.

## Features

- 🔐 **User Authentication**: Secure JWT-based login and registration
- 📊 **Activity Tracking**: Real-time data from ActivityWatch
- 📈 **Visual Analytics**: Interactive pie charts and detailed tables
- 🗓️ **Date Filtering**: Filter activities by custom date ranges
- 🌐 **Browser Tracking**: Track websites visited and time spent
- 💻 **Application Monitoring**: Monitor IDE usage, productivity apps, and more
- 🎨 **Modern UI**: Beautiful, responsive interface with smooth animations

## Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL/SQLite**: Database support
- **JWT Authentication**: Secure token-based authentication
- **ActivityWatch Integration**: Real-time activity data fetching

### Frontend
- **React 18**: Modern React with hooks
- **Recharts**: Beautiful, responsive charts
- **React Router**: Client-side routing
- **Axios**: HTTP client for API calls
- **Date-fns**: Date manipulation utilities
- **Styled Components**: CSS-in-JS styling

## Prerequisites

1. **ActivityWatch**: Download and install from [https://activitywatch.net/](https://activitywatch.net/)
2. **Python 3.8+**: For the backend
3. **Node.js 16+**: For the frontend
4. **PostgreSQL** (optional): For production database

## Installation

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd timesheet
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r ../requirements.txt

# Create environment file
cp ../.env.example .env

# Edit .env file with your settings
# For development, you can use SQLite:
DATABASE_URL=sqlite:///./timesheet.db
SECRET_KEY=your-super-secret-key-here
ACTIVITYWATCH_HOST=http://localhost:5600
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install
```

### 4. Database Setup

The application will automatically create the database tables on first run. For production, consider using PostgreSQL:

```bash
# Install PostgreSQL and create database
createdb timesheet_db

# Update .env file
DATABASE_URL=postgresql://username:password@localhost/timesheet_db
```

## Running the Application

### 1. Start ActivityWatch
Make sure ActivityWatch is running on your system. It should be available at `http://localhost:5600`.

### 2. Start the Backend
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

### 3. Start the Frontend
```bash
cd frontend
npm start
```

The application will be available at `http://localhost:3000`

## Usage

### 1. Register/Login
- Create a new account or login with existing credentials
- JWT tokens are used for secure authentication

### 2. Sync Activity Data
- Click "Sync from ActivityWatch" to fetch real-time activity data
- Data is automatically categorized (browser, development, productivity, etc.)
- Browser activities include website URLs

### 3. View Analytics
- **Pie Chart**: Visual representation of time distribution
- **Activity Table**: Detailed breakdown with sorting and filtering
- **Date Filtering**: Select custom date ranges
- **URL Tracking**: See which websites you visited (for browser activities)

### 4. Categories
Activities are automatically categorized:
- **Browser**: Chrome, Firefox, Safari, Edge, etc.
- **Development**: VS Code, PyCharm, IntelliJ, etc.
- **Productivity**: Office apps, Slack, Teams, etc.
- **Entertainment**: Spotify, YouTube, Netflix, etc.
- **System**: File explorer, terminal, etc.

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /token` - Login and get JWT token
- `GET /users/me` - Get current user info

### Activity Data
- `GET /activity-data` - Sync data from ActivityWatch
- `GET /activity-summary` - Get processed activity summary

## Configuration

### Environment Variables
```env
DATABASE_URL=sqlite:///./timesheet.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ACTIVITYWATCH_HOST=http://localhost:5600
```

### ActivityWatch Configuration
Ensure ActivityWatch is running with default settings:
- Web UI: `http://localhost:5600`
- API: `http://localhost:5600/api/0`

## Development

### Backend Development
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm start
```

### Database Migrations
For schema changes, use Alembic:
```bash
pip install alembic
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Troubleshooting

### ActivityWatch Connection Issues
- Ensure ActivityWatch is running
- Check if the web UI is accessible at `http://localhost:5600`
- Verify firewall settings

### Database Issues
- For SQLite: Ensure write permissions in the project directory
- For PostgreSQL: Verify connection string and database exists

### CORS Issues
- Backend CORS is configured for `http://localhost:3000`
- Update CORS settings in `main.py` if using different ports

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [ActivityWatch](https://activitywatch.net/) for the amazing activity tracking system
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [React](https://reactjs.org/) for the frontend framework
- [Recharts](https://recharts.org/) for the beautiful charts

