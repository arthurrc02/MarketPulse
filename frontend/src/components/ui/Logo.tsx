import { useId } from 'react'

interface LogoProps {
  className?: string
}

export function Logo({ className = '' }: LogoProps) {
  const gradientId = useId()

  return (
    <div className={['inline-flex items-center gap-2', className].join(' ')}>
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden="true">
        <rect width="28" height="28" rx="8" fill={`url(#${gradientId})`} />
        <path
          d="M7 17.5 11 12l3.5 4L21 8.5"
          stroke="white"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
        <defs>
          <linearGradient
            id={gradientId}
            x1="0"
            y1="0"
            x2="28"
            y2="28"
            gradientUnits="userSpaceOnUse"
          >
            <stop stopColor="#818cf8" />
            <stop offset="1" stopColor="#a78bfa" />
          </linearGradient>
        </defs>
      </svg>
      <span className="text-content text-lg font-semibold tracking-tight">MarketPulse</span>
    </div>
  )
}
