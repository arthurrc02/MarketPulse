import type { SVGAttributes } from 'react'

/**
 * Ícones do MarketPulse.
 *
 * Um único módulo, em vez de um arquivo por ícone: são ~15 glifos pequenos,
 * todos com o mesmo contrato (`viewBox 0 0 24 24`, traço 1.5-2, cantos
 * arredondados) — o que importa é a consistência visual entre eles, não a
 * reusabilidade individual fora deste catálogo.
 */

export type IconProps = SVGAttributes<SVGSVGElement>

function createIcon(path: React.ReactNode) {
  return function Icon({ className, ...props }: IconProps) {
    return (
      <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true" {...props}>
        {path}
      </svg>
    )
  }
}

export const DashboardIcon = createIcon(
  <path
    d="M4 4h7v7H4V4Zm9 0h7v4h-7V4Zm0 7h7v9h-7v-9ZM4 14h7v6H4v-6Z"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinejoin="round"
  />,
)

export const UploadsIcon = createIcon(
  <path
    d="M12 3v12m0-12 4 4m-4-4-4 4M5 17v2a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-2"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  />,
)

export const AnalyticsIcon = createIcon(
  <path
    d="M5 20V10m7 10V4m7 16v-7"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
  />,
)

export const InsightsIcon = createIcon(
  <path
    d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.4.3.6.8.6 1.3v.4h6v-.4c0-.5.2-1 .6-1.3A6 6 0 0 0 12 3Z"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  />,
)

export const SettingsIcon = createIcon(
  <>
    <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.5" />
    <path
      d="M19.4 13a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V19a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H4a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H10a1.65 1.65 0 0 0 1-1.51V4a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V10c.36.42.86.7 1.51.7H20a2 2 0 1 1 0 4h-.09c-.65 0-1.15.28-1.51.7Z"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </>,
)

export const MenuIcon = createIcon(
  <path
    d="M4 6h16M4 12h16M4 18h16"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
  />,
)

export const CloseIcon = createIcon(
  <path d="M6 6l12 12M18 6 6 18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />,
)

export const ChevronDownIcon = createIcon(
  <path
    d="m6 9 6 6 6-6"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  />,
)

export const CheckIcon = createIcon(
  <path
    d="M5 13l4 4L19 7"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  />,
)

export const SearchIcon = createIcon(
  <path
    d="m21 21-4.3-4.3M19 11a8 8 0 1 1-16 0 8 8 0 0 1 16 0Z"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  />,
)

export const InfoIcon = createIcon(
  <>
    <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.5" />
    <path d="M12 11v5m0-8h.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
  </>,
)

export const EyeIcon = createIcon(
  <>
    <path
      d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"
      stroke="currentColor"
      strokeWidth="1.5"
    />
    <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.5" />
  </>,
)

export const EyeOffIcon = createIcon(
  <path
    d="M3 3l18 18M10.6 10.6a3 3 0 0 0 4.24 4.24M9.4 5.5A10.4 10.4 0 0 1 12 5c6.5 0 10 7 10 7a13.6 13.6 0 0 1-3.1 3.9M6.6 6.6C4.3 8.1 2 12 2 12a13.6 13.6 0 0 0 5.1 5.4"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
  />,
)

export const InboxIcon = createIcon(
  <path
    d="M4 12h4l2 3h4l2-3h4M4 12l1.5-6.3A2 2 0 0 1 7.44 4h9.12a2 2 0 0 1 1.94 1.7L20 12M4 12v6a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-6"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  />,
)
