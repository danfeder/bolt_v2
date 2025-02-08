# Technical Context: Gym Class Rotation Scheduler

## Development Environment

### Core Technologies
- **Node.js**: Runtime environment
- **TypeScript**: Programming language
- **React**: UI framework
- **Vite**: Build tool and dev server

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
- Node.js (LTS version)
- npm/yarn package manager
- Modern web browser
- Code editor with TypeScript support

### Build Scripts
```json
{
  "dev": "vite",              // Development server
  "build": "vite build",      // Production build
  "lint": "eslint .",         // Code linting
  "preview": "vite preview"   // Preview build
}
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
