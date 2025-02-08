# Technical Context: Gym Class Rotation Scheduler

## Development Environment

### Core Technologies
- **Frontend**:
  - **Node.js**: Runtime environment
  - **TypeScript**: Programming language
  - **React**: UI framework
  - **Vite**: Build tool and dev server
- **Backend**:
  - **Python 3.11**: Runtime environment (required for OR-Tools)
  - **FastAPI**: Web framework
  - **OR-Tools**: Constraint programming solver
  - **Pydantic**: Data validation

### Key Dependencies
```json
{
  "Frontend Framework": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "State Management": {
    "zustand": "^4.5.2"
  },
  "UI Components": {
    "@tanstack/react-table": "^8.13.2",
    "lucide-react": "^0.344.0"
  },
  "Date Handling": {
    "date-fns": "^3.3.1"
  },
  "Scheduling": {
    "logic-solver": "^2.0.1"
  },
  "Styling": {
    "tailwindcss": "^3.4.1",
    "postcss": "^8.4.35",
    "autoprefixer": "^10.4.18"
  }
}
```

## Project Structure
```
/
├── src/
│   ├── components/        # React components
│   │   ├── Calendar.tsx
│   │   ├── ClassEditor.tsx
│   │   ├── ConstraintsForm.tsx
│   │   ├── FileUpload.tsx
│   │   ├── ScheduleDebugPanel.tsx
│   │   └── TeacherAvailability.tsx
│   ├── lib/              # Core business logic
│   │   ├── csvParser.ts
│   │   ├── scheduler.ts
│   │   └── schedulerWorker.ts
│   ├── store/            # State management
│   │   ├── scheduleStore.ts
│   │   └── testData.ts
│   ├── types/            # TypeScript definitions
│   │   └── index.ts
│   ├── App.tsx           # Root component
│   ├── index.css         # Global styles
│   └── main.tsx          # Entry point
├── public/               # Static assets
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript config
├── vite.config.ts        # Vite config
└── tailwind.config.js    # Tailwind config
```

## Development Setup

### Prerequisites
- **Frontend**:
  - Node.js (LTS version)
  - npm/yarn package manager
  - Modern web browser
  - Code editor with TypeScript support
- **Backend**:
  - Python 3.11 (required for OR-Tools compatibility)
  - Homebrew (recommended for Python installation)
  - Virtual environment for Python dependencies

### Build Scripts
#### Frontend
```json
{
  "dev": "vite",              // Development server
  "build": "vite build",      // Production build
  "lint": "eslint .",         // Code linting
  "preview": "vite preview"   // Preview build
}
```

#### Backend
```bash
# Create virtual environment
/opt/homebrew/bin/python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload

# Run tests
python -m app.test_class_limits
```

## Technical Constraints

### Browser Support
- Modern browsers with ES6+ support
- No IE11 support required
- CSS Grid and Flexbox support required

### Performance Requirements
- Fast schedule generation (<5s for typical scenarios)
- Responsive UI updates
- Efficient state management
- Optimized re-renders

### Data Handling
- CSV import support
- JSON data structures
- Local state persistence
- Type-safe data management

## Development Patterns

### Code Style
- Functional React components
- TypeScript strict mode
- ESLint for code quality
- Tailwind for styling

### State Management
- Zustand store
- Immutable state updates
- TypeScript type safety
- Centralized store pattern

### Testing Strategy
- Component testing
- Algorithm validation
- Constraint verification
- Debug panel for monitoring

### Build Process
- Vite development server
- TypeScript compilation
- PostCSS processing
- Tailwind CSS compilation
