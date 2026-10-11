import { Box, keyframes } from '@devup-ui/react'

interface PulseDotProps {
  size: '6px' | '8px' | '10px' | '14px'
}

const ping = keyframes({
  '0%': { transform: 'scale(1)', opacity: 0.6 },
  '80%, 100%': { transform: 'scale(2.4)', opacity: 0 },
})

/**
 * Live status indicator in the secondary colour with a soft ping ring.
 */
export function PulseDot({ size }: PulseDotProps) {
  return (
    <Box
      aria-hidden
      bg="$secondary"
      borderRadius="9999px"
      boxSize={size}
      flexShrink={0}
      pos="relative"
    >
      <Box
        _media={{
          '(prefers-reduced-motion: reduce)': { animation: 'none' },
        }}
        animation={`${ping} 2s cubic-bezier(0, 0, 0.2, 1) infinite`}
        bg="$secondary"
        borderRadius="9999px"
        inset="0"
        pos="absolute"
      />
    </Box>
  )
}
