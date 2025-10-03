# Financial Contract Drift Monitor - Frontend

A modern React frontend for the Financial Contract Drift Monitor, built with TypeScript, Tailwind CSS, and Vite.

## Features

- **Real-time Dashboard**: Live monitoring of contract violations and drift detection
- **Interactive Charts**: Visual representation of violation trends over time
- **Advanced Filtering**: Search and filter violations by severity, status, and other criteria
- **Detailed Views**: Comprehensive violation details with evidence and diff views
- **Policy Management**: View and download policy packs
- **Responsive Design**: Mobile-friendly interface that works on all devices

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Recharts** for data visualization
- **Lucide React** for icons
- **Axios** for API communication

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser and navigate to `http://localhost:3000`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
src/
├── components/
│   ├── ui/                 # Reusable UI components
│   └── dashboard/          # Dashboard-specific components
├── services/
│   └── api.ts             # API service layer
├── types/
│   └── index.ts           # TypeScript type definitions
├── lib/
│   └── utils.ts           # Utility functions
├── App.tsx                # Main application component
└── main.tsx               # Application entry point
```

## API Integration

The frontend integrates with the backend API through the `services/api.ts` file. Key endpoints include:

- `GET /api/health` - Health check
- `GET /api/alerts` - Get violations
- `PATCH /api/alerts/:id` - Update violation status
- `GET /api/contracts` - Get contracts
- `POST /api/upload` - Upload contracts
- `GET /api/dashboard/stats` - Get dashboard statistics

## Real-time Updates

The application supports real-time updates through WebSocket connections. When live mode is enabled, the dashboard will automatically update with new violations and changes.

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Environment Variables

Create a `.env.local` file for local development:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is part of the Pathway × LandingAI hackathon.
