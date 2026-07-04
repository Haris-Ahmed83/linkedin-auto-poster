Template: Data & Numbers
Pillar: Tools & Builds
Format: Numbers + architecture

I built a live sports scoreboard. Real-time. WebSocket. Zero-cost infra.

Here's the stack and the numbers:

Frontend: Next.js 14 + TypeScript + Tailwind
Backend: Express + WebSocket server
Real-time updates: Native WebSocket (no third-party service)
Sports covered: Football, Cricket, Basketball
Deploy: Free tier on Vercel

The challenge:
Sports data APIs are expensive. Real-time WebSocket infra costs money.
I needed it to run on $0.

The solution:
Self-hosted WebSocket server that pushes updates to the frontend.
No polling. No expensive data pipelines.
Just clean, real-time architecture for free.

The result:
Updates arrive in under 200ms.
Runs on free hosting.
Zero recurring cost.

Why I built this:
Because most "real-time" apps are over-engineered.
A simple WebSocket server + lightweight frontend handles 95% of use cases.

The best architecture isn't the most complex one.
It's the one that solves the problem and costs nothing to run.

What's the most over-engineered system you've seen?
