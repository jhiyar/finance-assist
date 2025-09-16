# Frontend Architecture

This frontend is organized using a feature-based architecture for better maintainability and scalability.

## Directory Structure

```
src/
├── features/                    # Feature-based modules
│   ├── core/                   # Shared core components and utilities
│   │   ├── components/         # Reusable UI components
│   │   │   ├── MarkdownWidget.jsx
│   │   │   ├── Modal.jsx
│   │   │   └── index.js
│   │   ├── hooks/              # Custom React hooks (future)
│   │   └── utils/              # Utility functions (future)
│   ├── chat/                   # Chat feature module
│   │   └── components/
│   │       ├── ChatInterface.jsx
│   │       ├── MessageBubble.jsx
│   │       ├── RAGDetailsModal.jsx
│   │       └── index.js
│   └── profile/                # Profile feature module
│       └── components/
│           ├── ProfileForm.jsx
│           └── index.js
├── mainRoutes.js               # Main routing configuration
└── App.jsx                     # Main app component
```

## Features

### Core Components
- **MarkdownWidget**: Renders markdown content with custom styling
- **Modal**: Reusable modal component with different sizes

### Chat Feature
- **ChatInterface**: Main chat interface with message handling
- **MessageBubble**: Individual message display with RAG details
- **RAGDetailsModal**: Detailed RAG analysis modal

### Profile Feature
- **ProfileForm**: User profile update form

## Key Improvements

1. **Organized Structure**: Features are separated into their own modules
2. **Reusable Components**: Core components can be shared across features
3. **Clean App.jsx**: Main app file is now minimal and focused
4. **Scalable Architecture**: Easy to add new features and components
5. **Better Maintainability**: Each feature is self-contained

## Usage

The app uses the mainRoutes.js file to handle routing, making it easy to add new routes and features in the future.

## Dependencies

- React 18.3.1
- react-markdown 9.1.0
- remark-gfm 4.0.0
- Tailwind CSS for styling
