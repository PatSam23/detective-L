# Detective-L Frontend

A modern Next.js dashboard for real-time multi-agent research intelligence.

## Overview

This frontend provides a beautiful, real-time interface to interact with the Detective-L backend API. Features include:

- **Live Query Input**: Submit research topics with a clean textarea interface
- **Real-time Agent Progress**: Watch 6 agents complete their work in parallel with live status indicators
- **Streaming Report Generation**: Reports appear in real-time as agents generate content
- **Structured Report Display**: Final reports with:
  - Title and summary
  - Key findings
  - Detailed analysis
  - Verified claims with confidence scores
  - Source citations
  - Overall confidence metrics
- **Error Handling**: User-friendly error messages with recovery options

## Architecture

```
frontend/
├── app/                    # Next.js 14 app directory
│   ├── layout.tsx         # Root layout with metadata
│   ├── page.tsx           # Main dashboard page
│   └── globals.css        # Tailwind + custom styles
├── components/            # React components
│   ├── ResearchForm.tsx   # Query input form
│   ├── AgentStatus.tsx    # Agent progress tracker
│   └── ReportDisplay.tsx  # Report rendering
├── hooks/                 # Custom React hooks
│   └── useResearch.ts     # SSE streaming hook
├── types/                 # TypeScript definitions
│   └── index.ts          # Type definitions
├── package.json           # Dependencies
├── tsconfig.json          # TypeScript config
├── tailwind.config.js     # Tailwind CSS config
├── next.config.js         # Next.js config
└── postcss.config.js      # PostCSS config
```

## Setup & Installation

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Backend running on `http://localhost:8000`

### Installation

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Create environment file:**
```bash
cp .env.local.example .env.local
```

4. **Update API URL if needed** (in `.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Frontend

### Development Mode
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the dashboard.

### Production Build
```bash
npm run build
npm start
```

## How It Works

### useResearch Hook
The core of the frontend is the `useResearch()` hook which:
1. Manages component state (agents, report tokens, errors)
2. Establishes SSE connection to `/research/stream` endpoint
3. Parses streaming events and updates agent status in real-time
4. Accumulates report tokens and displays final report

**Usage:**
```typescript
const { agents, reportTokens, isLoading, error, run, reset } = useResearch();

// Submit a query
await run("Your research query here");
```

### SSE Event Types

The frontend listens for these event types from the backend:

| Event Type | Purpose | Payload |
|-----------|---------|---------|
| `agent_start` | Agent begins work | `name: string` |
| `agent_update` | Agent status changed | `name: string, data: object` |
| `agent_complete` / `agent_done` | Agent finished | `name: string` |
| `token` | Report text token | `text: string` |
| `research_complete` | All research done | - |
| `error` | Error occurred | `message: string` |

### Agent Lifecycle

1. **Pending** (⭕) → Agent waiting to start
2. **Running** (🔄) → Agent actively working
3. **Complete** (✅) → Agent finished successfully
4. **Error** (❌) → Agent encountered an issue

## Components

### ResearchForm
- Textarea for multi-line query input
- Submit button with loading state
- Disabled while research is running

### AgentStatus
- Shows all 6 agents in order
- Displays agent name, description, status
- Progress bar for each agent
- Icons change based on status

### ReportDisplay
- Auto-detects JSON vs plain text reports
- Structured rendering for complete reports
- Live text scrolling for streaming content
- Confidence score badges (green/yellow/red)
- Flagged claim highlighting
- Source list with indexing

## Styling

Built with **Tailwind CSS**:
- Dark theme (slate-950 background)
- Blue/cyan gradient accents
- Responsive grid layout (1 col mobile, 3 col desktop)
- Smooth transitions and animations
- Custom scrollbar styling

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API endpoint |

Note: `NEXT_PUBLIC_` prefix makes the variable accessible in the browser.

## Troubleshooting

### "Connection refused" error
- Ensure backend is running on the configured API URL
- Check CORS settings in backend (`FastAPI CORSMiddleware`)

### Report not appearing
- Check browser console for streaming errors
- Verify `/research/stream` endpoint is working
- Check network tab in DevTools for SSE connection

### Styling issues
- Run `npm run build` to regenerate Tailwind classes
- Clear `.next/` cache: `rm -rf .next`
- Restart dev server

## Performance Tips

- Reports are streamed and rendered incrementally
- Agent status updates use React state batching
- Large reports auto-scroll to bottom with `max-height: 600px`
- CSS animations use GPU-accelerated properties (`opacity`, `transform`)

## Future Enhancements

- [ ] Save research reports to local storage
- [ ] Export reports as PDF
- [ ] Advanced query builder UI
- [ ] Report history/search
- [ ] Dark/light theme toggle
- [ ] Mobile-optimized layout
- [ ] Keyboard shortcuts

## Related

- **Backend**: See `backend/README.md`
- **Architecture**: See main `README.md`
- **Setup**: See `plan.md` for 4-week development plan
