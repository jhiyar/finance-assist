# Finance Assistant - Django Backend

This is a Django REST Framework backend for the Finance Assistant application with a dedicated chat app.

## Features

- **Chat App**: Dedicated app for handling chatbot functionality
- **Generic Views**: Uses DRF generic views for clean, maintainable code
- **Intent Detection**: AI-powered intent detection for chat messages
- **Profile Management**: CRUD operations for user profiles
- **Transaction History**: View transaction history
- **Balance Information**: Get current account balance
- **Admin Interface**: Django admin for data management

## API Endpoints

- `POST /api/chat/` - Chat with the finance assistant
- `GET /api/profile/` - Get user profile
- `PATCH /api/profile/` - Update user profile
- `GET /api/transactions/` - Get transaction history
- `GET /api/balance/` - Get current balance

## Setup Instructions

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Populate initial data**:
   ```bash
   python manage.py populate_data
   ```

4. **Create superuser** (optional):
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

The server will be available at `http://localhost:8000`

### Docker

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

## Models

### Profile
- `name`: User's full name
- `address`: User's address
- `email`: User's email address
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Transaction
- `date`: Transaction date
- `description`: Transaction description
- `amount_minor`: Amount in minor units (pennies)
- `created_at`: Creation timestamp

### Balance
- `amount_minor`: Current balance in minor units (pennies)
- `updated_at`: Last update timestamp

## Intent Detection

The system can detect the following intents from user messages:

- **get_balance**: When user asks about their balance
- **get_transactions**: When user asks about transaction history
- **update_profile**: When user wants to change their address
- **help**: Default intent for unrecognized messages

## Admin Interface

Access the Django admin at `http://localhost:8000/admin/` to manage:
- User profiles
- Transactions
- Balance information

## Development

### Adding New Intents

1. Update the `detect_intent` function in `chat/utils.py`
2. Add corresponding logic in `ChatView` in `chat/views.py`
3. Update tests if applicable

### Adding New Models

1. Create the model in `chat/models.py`
2. Create a serializer in `chat/serializers.py`
3. Create generic views in `chat/views.py`
4. Add URL patterns in `chat/urls.py`
5. Register in admin in `chat/admin.py`
6. Run migrations

## Testing

Run tests with:
```bash
python manage.py test
```
