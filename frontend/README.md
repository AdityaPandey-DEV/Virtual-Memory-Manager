# VMM Dashboard Frontend

A modern React dashboard for visualizing the Virtual Memory Manager backend with AI predictor capabilities.

## Features

- **Real-time Monitoring**: Live metrics and event streaming via Server-Sent Events
- **Interactive Charts**: Beautiful visualizations using Recharts
- **Control Panel**: Start/stop simulations and configure AI modes
- **Live Logs**: Color-coded log streaming with pause/resume functionality
- **Prediction Analytics**: Track AI prediction performance and outcomes
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **TailwindCSS** for styling
- **Recharts** for data visualization
- **Lucide React** for icons
- **Server-Sent Events** for real-time data

## Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend service running on `http://localhost:8000`

### Development

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Open browser**: Navigate to `http://localhost:3000`

### Production Build

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ControlPanel.tsx # Simulation controls
│   │   ├── MetricsChart.tsx # Charts and metrics
│   │   ├── LogPanel.tsx     # Live log streaming
│   │   └── PredictionTable.tsx # AI predictions table
│   ├── hooks/               # Custom React hooks
│   │   ├── useMetrics.ts    # Metrics data fetching
│   │   ├── useEventStream.ts # SSE event handling
│   │   └── useSimulation.ts # Simulation controls
│   ├── types/               # TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx             # Main application component
│   ├── main.tsx            # Application entry point
│   └── index.css           # Global styles
├── public/                 # Static assets
├── package.json           # Dependencies and scripts
├── vite.config.ts         # Vite configuration
├── tailwind.config.js     # TailwindCSS configuration
├── tsconfig.json          # TypeScript configuration
└── Dockerfile             # Docker configuration
```

## API Integration

The dashboard connects to the backend via these endpoints:

### Metrics API
- **GET** `/metrics` - Fetch current metrics (polled every 5s)
- **GET** `/health` - Check backend health status

### Simulation API
- **POST** `/simulate/start` - Start simulation with mode/workload
- **POST** `/simulate/stop` - Stop running simulation

### Event Stream
- **GET** `/events/stream` - Server-Sent Events for live logs

### Expected Data Formats

#### Metrics Response
```json
{
  "total_page_accesses": 1000,
  "page_faults_baseline": 50,
  "page_faults_ai": 30,
  "page_fault_rate": 0.05,
  "swap_io_throughput": 2.5,
  "predictor_cpu": 15.2,
  "predictor_latency": 0.001,
  "precision_at_k": 0.85,
  "recall": 0.78
}
```

#### Event Stream Format
```
[ACCESS] Page 123
[FAULT] Page 456
[AI] Predicted {123, 124, 125}
[EVICT] Frame -> Page 789
```

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# From project root
docker-compose up -d
```

This will start:
- Backend service on `http://localhost:8000`
- Frontend dashboard on `http://localhost:3000`
- AI predictor on `http://localhost:8001`

### Manual Docker Build

```bash
# Build frontend image
docker build -t vmm-dashboard ./frontend

# Run container
docker run -p 3000:80 vmm-dashboard
```

## Configuration

### Environment Variables

- `REACT_APP_API_URL` - Backend API URL (default: `http://localhost:8000`)

### Vite Proxy Configuration

The development server proxies API requests to the backend:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
}
```

## Development Guide

### Adding New Components

1. Create component in `src/components/`
2. Add TypeScript interfaces in `src/types/`
3. Create custom hooks in `src/hooks/` if needed
4. Import and use in `App.tsx`

### Styling Guidelines

- Use TailwindCSS utility classes
- Follow the design system colors defined in `tailwind.config.js`
- Use responsive prefixes (`sm:`, `md:`, `lg:`, `xl:`)
- Maintain consistent spacing and typography

### State Management

- Use React hooks for local state
- Custom hooks for API integration
- No external state management library needed

## Troubleshooting

### Common Issues

1. **Backend Connection Failed**
   - Ensure backend is running on `http://localhost:8000`
   - Check CORS settings in backend
   - Verify API endpoints are available

2. **Event Stream Not Working**
   - Check if `/events/stream` endpoint is accessible
   - Verify Server-Sent Events are properly configured
   - Check browser console for errors

3. **Charts Not Rendering**
   - Ensure Recharts is properly installed
   - Check if data is being fetched correctly
   - Verify responsive container sizing

### Debug Mode

Enable debug logging by setting:
```bash
REACT_APP_DEBUG=true npm run dev
```

## Performance Optimization

- **Lazy Loading**: Components are loaded on demand
- **Memoization**: Expensive calculations are memoized
- **Data Limits**: Logs and predictions are limited to prevent memory issues
- **Efficient Updates**: Only re-render when necessary

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Follow TypeScript best practices
2. Use meaningful component and variable names
3. Add proper error handling
4. Write responsive components
5. Test on multiple screen sizes

## License

This project is part of the Virtual Memory Manager system.

