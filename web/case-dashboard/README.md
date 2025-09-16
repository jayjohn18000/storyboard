# Legal Simulation Platform - Frontend

This is the frontend application for the Legal Simulation Platform built with React, TypeScript, and Tailwind CSS.

## Features

- **Cases Management**: Create, view, and manage legal cases
- **Evidence Upload**: Drag-and-drop file upload with SHA-256 hashing
- **Storyboard Editor**: Monaco Editor with StoryDoc syntax highlighting
- **Timeline Editor**: React Flow-based visual timeline editing
- **Render Monitor**: Real-time render progress tracking
- **User Profile**: Settings and preferences management

## Tech Stack

- **React 18** with TypeScript
- **Redux Toolkit** + RTK Query for state management
- **React Router v6** for routing
- **Tailwind CSS** for styling
- **Heroicons** for icons
- **Monaco Editor** for code editing
- **React Flow** for timeline visualization

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env.local
```

3. Start development server:
```bash
npm start
```

The app will be available at `http://localhost:3000`.

### Environment Variables

- `REACT_APP_API_URL`: Backend API URL (default: http://localhost:8000)
- `REACT_APP_USE_MOCKS`: Use mock data (default: true)
- `REACT_APP_ENABLE_DEBUG`: Enable debug mode (default: true)

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── auth/           # Authentication components
│   └── layout/         # Layout components (Header, Sidebar, etc.)
├── pages/              # Page components
│   ├── auth/           # Login page
│   ├── cases/          # Cases management
│   ├── evidence/       # Evidence management
│   ├── storyboard/     # Storyboard editor
│   ├── renders/        # Render monitoring
│   └── profile/        # User profile
├── store/              # Redux store configuration
│   ├── api/            # RTK Query API services
│   └── slices/         # Redux slices
├── hooks/              # Custom React hooks
├── utils/              # Utility functions
└── shared/             # Shared components from parent directory
```

## Available Scripts

- `npm start`: Start development server
- `npm build`: Build for production
- `npm test`: Run tests
- `npm run lint`: Run ESLint
- `npm run typecheck`: Run TypeScript compiler

## Authentication

The app uses a simple session-based authentication system with localStorage. In production, this should be replaced with proper JWT token management.

## API Integration

The app uses RTK Query for API integration with mock data enabled by default. To connect to a real backend:

1. Set `REACT_APP_USE_MOCKS=false` in your environment
2. Ensure your backend API is running on the configured URL
3. Update API endpoints in `src/store/api/` as needed

## Contributing

1. Follow the existing code style
2. Ensure all accessibility requirements are met
3. Add tests for new features
4. Update documentation as needed
