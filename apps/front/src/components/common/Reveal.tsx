import { Box, keyframes } from '@devup-ui/react'

interface RevealProps {
  children: React.ReactNode
  /** Stagger order. Each step delays the entrance by 70ms. */
  order?: 0 | 1 | 2 | 3 | 4 | 5 | 6
}

const fadeUp = keyframes({
  from: { opacity: 0, transform: 'translateY(12px)' },
  to: { opacity: 1, transform: 'translateY(0)' },
})

/**
 * Staggered fade-up entrance for page sections.
 * Disabled for users who prefer reduced motion.
 */
export function Reveal({ children, order = 0 }: RevealProps) {
  return (
    <Box
      _media={{
        '(prefers-reduced-motion: reduce)': { animation: 'none' },
      }}
      animation={`${fadeUp} 0.5s cubic-bezier(0.22, 1, 0.36, 1) both`}
      animationDelay={
        {
          0: '0ms',
          1: '70ms',
          2: '140ms',
          3: '210ms',
          4: '280ms',
          5: '350ms',
          6: '420ms',
        }[order]
      }
    >
      {children}
    </Box>
  )
}
