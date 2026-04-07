# Aura Reface – AI Face Swap SaaS

Premium-grade, production-ready Next.js platform for AI face swap / reface workflows. Built with modern app router, strong typing, Stripe monetization, and extensible AI/provider abstractions. Database and model hooks are stubbed with clear TODOs for integration.

## Stack
- Next.js 15 (App Router), React 19, TypeScript, Server Actions
- Tailwind CSS + shadcn/ui + Framer Motion for cinematic UI
- Zustand for state, React Hook Form + Zod for forms
- NextAuth (email/password + Google OAuth)
- Stripe subscriptions & credit packs (webhooks, billing portal, price IDs)
- Prisma schema ready for Neon/Postgres (`DATABASE_URL` driven)
- Redis-ready queue + provider-based AI adapter layer
- Internationalization-ready (next-intl skeleton)
- Theme toggle ready via next-themes, toasts via sonner

## Getting Started
1) Install deps: `npm install`
2) Copy `.env.example` to `.env.local` and fill values (keep fake if offline).
3) Generate Prisma client: `npx prisma generate`
4) Push schema to your Neon database: `npx prisma db push` (uses `DATABASE_URL`)
5) Run dev server: `npm run dev`
6) Open http://localhost:3000

Neon-specific: the provided `DATABASE_URL` works with `sslmode=require`; Neon auto-scales, so prefer pooling if you hit connection limits.

## Conventions
- `src/lib/env.ts` centralizes env validation.
- `src/lib/ai/*` provider-based AI execution; replace `mock` with real engines.
- `src/lib/queue.ts` placeholder for Redis-backed jobs.
- `src/lib/stripe.ts` wraps Stripe client + checkout/session helpers.
- `src/lib/auth.ts` configures NextAuth; DB/user lookup marked with TODO.
- UI uses shadcn-style primitives in `src/components/ui/*`.
- Feature-local server actions/APIs live beside routes (see `src/app/api/*`).
- Security: rate limiting scaffold, upload validation, webhook verification.
- Middleware guards protected routes and admin-only access.

## Deployment Notes
- Use Vercel/Edge where possible; ensure `NEXTAUTH_URL` matches domain.
- Set Stripe webhook endpoint to `/api/stripe/webhook`.
- Plug real storage (S3, GCS) in `src/app/api/uploads/route.ts`.
- Attach Redis connection in `src/lib/queue.ts`.
- Swap AI provider in `src/lib/ai/index.ts`.

## TODO hooks
- Connect Prisma to your DB.
- Implement user persistence for credentials auth.
- Wire real AI model/provider and storage.
- Configure email transport (production-grade provider).
- Add rate limit backend (Upstash/Redis) in `src/lib/rate-limit.ts`.
