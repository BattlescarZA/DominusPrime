---
metadata: { "dominusprime": { "emoji": "📋" } }
---

# Kanban Project Management Skill

Comprehensive skill for managing and interacting with the Quanta Kanban Platform - a multi-tenant, enterprise-grade Kanban system for project and task management.

## Overview

This skill enables DominusPrime to:
- 🚀 **Setup & Deploy**: Clone, install, and run the Kanban platform
- 📋 **Project Management**: Create and manage Kanban boards, lists, and cards
- 👥 **Team Collaboration**: Manage users, assignments, and permissions
- 📊 **Analytics**: Track project progress and team performance
- 🔍 **Search & Filter**: Find and organize tasks efficiently
- 💬 **Communication**: Add comments, attachments, and activity tracking

## Installation & Setup

### Prerequisites

Before using this skill, ensure the following are installed:
- **Node.js** (v16 or higher)
- **MongoDB** (v5 or higher)
- **npm** or **yarn**
- **Git**

### Quick Start

#### 1. Clone the Kanban Repository

```bash
# Clone the repository
git clone https://github.com/BattlescarZA/kanban.git kanban_platform
cd kanban_platform
```

#### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies
npm install

# Create .env file
cat > .env << EOF
MONGODB_BASE_URL=mongodb://localhost:27017
MONGODB_AUTH_SOURCE=admin
PORT=5000
JWT_SECRET=your-super-secret-jwt-key-change-this
JWT_EXPIRE=7d
FRONTEND_URL=http://localhost:3000
EOF

# Start the backend server
npm run dev
# The API will be available at http://localhost:5000
```

#### 3. Frontend Setup

```bash
# Navigate to frontend (open new terminal)
cd frontend

# Install dependencies
npm install

# Create .env file
cat > .env << EOF
VITE_API_URL=http://localhost:5000/api
VITE_COMPANY_NAME=yourcompany
EOF

# Start the frontend
npm run dev
# The application will be available at http://localhost:3000
```

## API Integration

### Authentication

All API requests require:
1. **JWT Token**: Obtained via login
2. **Company Name Header**: `x-company-name` header for multi-tenant isolation

#### Login Example

```python
import requests

API_BASE_URL = "https://bffkanban.quantanova.ai/api"
COMPANY_NAME = "yourcompany"

# Login to get token
response = requests.post(
    f"{API_BASE_URL}/auth/login",
    headers={"x-company-name": COMPANY_NAME},
    json={
        "email": "user@company.com",
        "password": "password123",
        "companyName": COMPANY_NAME
    }
)

data = response.json()
if data["success"]:
    AUTH_TOKEN = data["data"]["token"]
    USER_DATA = data["data"]["user"]
    
    # Use this token for all subsequent requests
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "x-company-name": COMPANY_NAME,
        "Content-Type": "application/json"
    }
```

### Common Operations

#### 1. Create a New Project (Board)

```python
# Create a new Kanban board
response = requests.post(
    f"{API_BASE_URL}/boards",
    headers=headers,
    json={
        "title": "Website Redesign Project",
        "description": "Complete redesign of company website",
        "color": "#6366f1",
        "visibility": "private"
    }
)

board = response.json()["data"]
board_id = board["_id"]
```

#### 2. Create Lists (Columns)

```python
# Create "To Do", "In Progress", "Done" lists
lists = ["To Do", "In Progress", "Done"]
list_ids = []

for i, list_title in enumerate(lists):
    response = requests.post(
        f"{API_BASE_URL}/lists/board/{board_id}",
        headers=headers,
        json={
            "title": list_title,
            "position": i
        }
    )
    list_ids.append(response.json()["data"]["_id"])

todo_list_id = list_ids[0]
```

#### 3. Create Tasks (Cards)

```python
# Create a new task card
response = requests.post(
    f"{API_BASE_URL}/cards/list/{todo_list_id}",
    headers=headers,
    json={
        "title": "Design homepage mockup",
        "description": "Create high-fidelity mockups for the new homepage",
        "priority": "high",
        "dueDate": "2026-03-15T00:00:00.000Z",
        "assignedTo": ["user_id_1", "user_id_2"],
        "labels": ["design", "urgent"],
        "estimatedHours": 16
    }
)

card = response.json()["data"]
card_id = card["_id"]
```

#### 4. Move Card Between Lists

```python
# Move card from "To Do" to "In Progress"
response = requests.patch(
    f"{API_BASE_URL}/cards/{card_id}/move",
    headers=headers,
    json={
        "listId": list_ids[1],  # In Progress list
        "position": 0
    }
)
```

#### 5. Add Comments

```python
# Add a comment to a card
response = requests.post(
    f"{API_BASE_URL}/cards/{card_id}/comments",
    headers=headers,
    json={
        "text": "I've completed the initial wireframes. Ready for review!"
    }
)
```

#### 6. Assign Team Members

```python
# Assign users to a card
response = requests.post(
    f"{API_BASE_URL}/cards/{card_id}/assign",
    headers=headers,
    json={
        "userId": "user_id_3"
    }
)
```

#### 7. Update Card Priority

```python
# Change card priority
response = requests.patch(
    f"{API_BASE_URL}/cards/{card_id}/priority",
    headers=headers,
    json={
        "priority": "urgent"  # Options: low, medium, high, urgent
    }
)
```

#### 8. Archive/Close Card

```python
# Archive (close) a completed card
response = requests.patch(
    f"{API_BASE_URL}/cards/{card_id}/archive",
    headers=headers,
    json={
        "archived": True
    }
)
```

#### 9. Get Board Analytics

```python
# Get project analytics
response = requests.get(
    f"{API_BASE_URL}/analytics/board/{board_id}",
    headers=headers
)

analytics = response.json()["data"]
print(f"Total Cards: {analytics['overview']['totalCards']}")
print(f"Completion Rate: {analytics['overview']['completionRate']}%")
```

#### 10. Search Cards

```python
# Search for cards globally
response = requests.get(
    f"{API_BASE_URL}/search",
    headers=headers,
    params={"q": "design"}
)

cards = response.json()["data"]["cards"]
```

### User Management

#### Get All Users

```python
response = requests.get(
    f"{API_BASE_URL}/users",
    headers=headers
)

users = response.json()["data"]["users"]
```

#### Add Member to Board

```python
response = requests.post(
    f"{API_BASE_URL}/boards/{board_id}/members",
    headers=headers,
    json={
        "userId": "user_id_4",
        "role": "member"  # Options: admin, member
    }
)
```

## Complete API Reference

### Authentication Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user profile
- `PUT /api/auth/profile` - Update profile
- `PUT /api/auth/change-password` - Change password

### Board Endpoints

- `GET /api/boards` - Get all boards
- `POST /api/boards` - Create board
- `GET /api/boards/:id` - Get board by ID
- `PUT /api/boards/:id` - Update board
- `DELETE /api/boards/:id` - Delete board
- `PATCH /api/boards/:id/archive` - Archive/unarchive board
- `POST /api/boards/:id/members` - Add member to board
- `DELETE /api/boards/:id/members/:userId` - Remove member

### List Endpoints

- `GET /api/lists/board/:boardId` - Get lists by board
- `POST /api/lists/board/:boardId` - Create list
- `PUT /api/lists/:id` - Update list
- `DELETE /api/lists/:id` - Delete list
- `PATCH /api/lists/board/:boardId/reorder` - Reorder lists

### Card/Ticket Endpoints

- `GET /api/cards/board/:boardId` - Get all cards in board
- `GET /api/cards/board/:boardId/archived` - Get archived cards
- `GET /api/cards/list/:listId` - Get cards by list
- `POST /api/cards/list/:listId` - Create card/ticket
- `GET /api/cards/:id` - Get card by ID
- `PUT /api/cards/:id` - Update card
- `PATCH /api/cards/:id/move` - Move card to different list
- `DELETE /api/cards/:id` - Delete card
- `PATCH /api/cards/:id/archive` - Close/reopen ticket
- `POST /api/cards/:id/assign` - Assign users to card
- `DELETE /api/cards/:id/assign/:userId` - Unassign user
- `POST /api/cards/:id/labels` - Add label to card
- `DELETE /api/cards/:id/labels/:labelId` - Remove label
- `PATCH /api/cards/:id/priority` - Update card priority
- `POST /api/cards/:id/comments` - Add comment
- `POST /api/cards/:id/subtasks` - Add subtask
- `PATCH /api/cards/:id/subtasks/:subtaskId/toggle` - Toggle subtask
- `PATCH /api/cards/bulk-update` - Bulk update multiple cards

### User Endpoints

- `GET /api/users` - Get all users
- `GET /api/users/:id` - Get user by ID
- `PUT /api/users/:id` - Update user (admin only)
- `DELETE /api/users/:id` - Delete user (admin only)
- `GET /api/users/stats` - Get user statistics

### Search & Analytics

- `GET /api/search?q=query` - Global search
- `POST /api/search/advanced` - Advanced search
- `GET /api/analytics/board/:boardId` - Board analytics
- `GET /api/analytics/users` - User statistics
- `GET /api/activities/board/:boardId` - Board activities
- `GET /api/activities` - All activities

## Multi-Tenant Architecture

The Kanban platform uses a **database-per-tenant** approach:

- Each company gets its own MongoDB database
- Company name is passed via `x-company-name` header
- Middleware automatically routes to the correct database
- Complete data isolation between tenants

### Database Naming Convention

For company name `testc3`, the system connects to database: `testc3`

**All API requests MUST include the `x-company-name` header.**

## Security Features

- ✅ JWT Authentication with token expiry
- ✅ Password hashing with bcrypt
- ✅ Rate limiting (100 requests per 15 minutes)
- ✅ Helmet.js security headers
- ✅ CORS protection
- ✅ Input validation
- ✅ Multi-tenant data isolation

## User Roles

### Admin
- Full system access
- Manage all users
- Create/delete boards
- Manage company settings

### Manager
- Create and manage boards
- Assign team members
- View staff statistics
- Manage projects

### Member
- Access assigned boards
- Create and manage cards
- Collaborate with team
- Update profile

## Example Workflows

### Workflow 1: Complete Project Setup

```python
import requests

class KanbanManager:
    def __init__(self, api_url, company_name, email, password):
        self.api_url = api_url
        self.company_name = company_name
        self.headers = {"x-company-name": company_name}
        self.login(email, password)
    
    def login(self, email, password):
        response = requests.post(
            f"{self.api_url}/auth/login",
            headers=self.headers,
            json={"email": email, "password": password, "companyName": self.company_name}
        )
        data = response.json()
        if data["success"]:
            self.token = data["data"]["token"]
            self.headers["Authorization"] = f"Bearer {self.token}"
            self.headers["Content-Type"] = "application/json"
            return True
        return False
    
    def create_project(self, name, description, tasks):
        # Create board
        board = requests.post(
            f"{self.api_url}/boards",
            headers=self.headers,
            json={"title": name, "description": description, "color": "#6366f1"}
        ).json()["data"]
        
        # Create lists
        lists = {}
        for i, list_name in enumerate(["To Do", "In Progress", "Done"]):
            list_data = requests.post(
                f"{self.api_url}/lists/board/{board['_id']}",
                headers=self.headers,
                json={"title": list_name, "position": i}
            ).json()["data"]
            lists[list_name] = list_data["_id"]
        
        # Create tasks
        for task in tasks:
            requests.post(
                f"{self.api_url}/cards/list/{lists['To Do']}",
                headers=self.headers,
                json=task
            )
        
        return board

# Usage
kanban = KanbanManager(
    "https://bffkanban.quantanova.ai/api",
    "mycompany",
    "admin@mycompany.com",
    "password123"
)

project = kanban.create_project(
    "Website Redesign",
    "Complete redesign of company website",
    [
        {"title": "Design mockups", "priority": "high"},
        {"title": "Develop frontend", "priority": "medium"},
        {"title": "Testing & QA", "priority": "medium"}
    ]
)

print(f"Project created: {project['title']}")
```

### Workflow 2: Daily Standup Report

```python
def get_standup_report(kanban, board_id):
    # Get all cards
    response = requests.get(
        f"{kanban.api_url}/cards/board/{board_id}",
        headers=kanban.headers
    )
    
    cards = response.json()["data"]
    
    # Organize by status
    report = {
        "in_progress": [],
        "blocked": [],
        "completed_yesterday": []
    }
    
    for card in cards:
        if card["list"]["title"] == "In Progress":
            report["in_progress"].append(card["title"])
        if card["priority"] == "blocked":
            report["blocked"].append(card["title"])
        # Add more logic for completed cards...
    
    return report
```

### Workflow 3: Automated Task Creation from Email

```python
def create_task_from_ticket(kanban, board_id, list_id, ticket_data):
    """Create Kanban card from external ticket/email"""
    
    card = requests.post(
        f"{kanban.api_url}/cards/list/{list_id}",
        headers=kanban.headers,
        json={
            "title": f"Ticket #{ticket_data['id']}: {ticket_data['subject']}",
            "description": ticket_data['body'],
            "priority": "high" if ticket_data['urgent'] else "medium",
            "labels": ["customer-support", "ticket"],
            "assignedTo": [ticket_data['assigned_agent_id']]
        }
    ).json()["data"]
    
    # Add comment with ticket details
    requests.post(
        f"{kanban.api_url}/cards/{card['_id']}/comments",
        headers=kanban.headers,
        json={"text": f"Customer: {ticket_data['customer_email']}"}
    )
    
    return card
```

## Best Practices

### 1. Token Management
- Store tokens securely (environment variables, not hardcoded)
- Tokens expire after 7 days (default) - implement refresh logic
- Never log tokens or expose them client-side

### 2. Rate Limiting
- Respect the 100 requests per 15 minutes limit
- Implement exponential backoff for failed requests
- Use bulk operations when available

### 3. Error Handling
```python
def safe_api_call(url, method="GET", **kwargs):
    try:
        response = requests.request(method, url, **kwargs)
        data = response.json()
        
        if not data.get("success"):
            print(f"API Error: {data.get('error')}")
            return None
        
        return data["data"]
    except Exception as e:
        print(f"Request failed: {e}")
        return None
```

### 4. Data Validation
- Always validate card data before creation
- Check required fields (title, etc.)
- Validate priority values: low, medium, high, urgent
- Validate date formats

### 5. Multi-Tenant Considerations
- Always include `x-company-name` header
- Verify company name matches database
- Ensure data isolation in all operations

## Troubleshooting

### Common Issues

**Issue**: 401 Unauthorized
- **Solution**: Token expired or invalid. Re-login to get new token.

**Issue**: 404 Not Found
- **Solution**: Check resource ID exists and user has access.

**Issue**: 400 Bad Request
- **Solution**: Validate request body matches API requirements.

**Issue**: Missing `x-company-name` header
- **Solution**: Add header to all requests: `{'x-company-name': 'yourcompany'}`

**Issue**: Database connection failed
- **Solution**: Check MongoDB is running and credentials are correct.

## Environment Configuration

### Production Deployment

#### Backend `.env`
```env
MONGODB_BASE_URL=mongodb://username:password@host:27017
MONGODB_AUTH_SOURCE=admin
PORT=5000
JWT_SECRET=change-this-to-secure-random-string
JWT_EXPIRE=7d
FRONTEND_URL=https://your-frontend-domain.com
NODE_ENV=production
```

#### Frontend `.env`
```env
VITE_API_URL=https://your-api-domain.com/api
VITE_COMPANY_NAME=yourcompany
```

## Resources

- **Repository**: https://github.com/BattlescarZA/kanban
- **API Documentation**: See `AI_AGENT_API_GUIDE.md` in repository
- **Production API**: https://bffkanban.quantanova.ai/api

## Skill Commands

When using this skill, DominusPrime can help you:

- 🚀 **Setup**: "Set up the kanban platform locally"
- 📋 **Create**: "Create a new project board for website redesign"
- ✅ **Task**: "Add a task 'Design homepage' to the To Do list"
- 🔄 **Move**: "Move card X to In Progress"
- 👥 **Assign**: "Assign John to the homepage design task"
- 📊 **Report**: "Show me the project analytics for board X"
- 🔍 **Search**: "Find all high priority tasks"
- 💬 **Comment**: "Add a comment to card X"

## Integration with DominusPrime

This skill can be invoked automatically when users request project management, task tracking, or team collaboration features. The agent will:

1. Authenticate with the Kanban API
2. Perform the requested operation
3. Return results in a user-friendly format
4. Handle errors gracefully

---

**Skill Version**: 1.0.0  
**Last Updated**: 2026-03-08  
**Maintained by**: QuantaNova Development Team
