# Lasso Frontend

Next.js frontend for the Lasso Monte Carlo credit risk assessment platform.

## Prerequisites

- Node.js 18+
- npm (comes with Node.js)

## Getting Started (Local Development)

1. Install dependencies:

```bash
npm install
```

2. Create a `.env.local` file with your API key:

```bash
cp .env.local.example .env.local
# Then edit .env.local and add your Anthropic API key
```

3. Run the development server:

```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) with your browser.

5. To access the Risk Console, use password: `Test123`

## Deploy to Vercel

### Option 1: One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/minuuva/placeholder/tree/main/frontend)

### Option 2: Manual Deploy

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. From the `frontend` directory, run:
```bash
vercel
```

3. Follow the prompts to link to your Vercel account.

4. Set environment variables in Vercel Dashboard:
   - Go to your project settings → Environment Variables
   - Add `ANTHROPIC_API_KEY` with your API key

5. Deploy to production:
```bash
vercel --prod
```

### Environment Variables for Vercel

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key for Claude |
| `USE_PYTHON_BACKEND` | No | Set to "true" to use real Monte Carlo backend |

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run typecheck` - Run TypeScript type checking

## Tech Stack

- Next.js 16
- React 19
- Tailwind CSS v4
- GSAP for animations
- Three.js / React Three Fiber for 3D globe
- Recharts for data visualization
- Anthropic Claude API for AI features

## Access Control

The Risk Console (`/simulate`) is protected with a demo password.
- Password: `Test123`
- This is session-based (clears when browser closes)
