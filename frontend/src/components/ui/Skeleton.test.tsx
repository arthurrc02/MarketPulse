import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Skeleton } from '@/components/ui/Skeleton'

describe('Skeleton', () => {
  it('is decorative and hidden from the accessibility tree', () => {
    const { container } = render(<Skeleton className="h-8 w-24" />)

    const skeleton = container.firstChild as HTMLElement
    expect(skeleton).toHaveAttribute('aria-hidden', 'true')
    expect(skeleton.className).toContain('animate-pulse')
  })
})
