import { Box, globalCss } from '@devup-ui/react'
import { resetCss } from '@devup-ui/reset-css'
import type { Metadata } from 'next'

resetCss()

globalCss({
  body: {
    bg: '$bg',
    color: '$text',
  },
})

export const metadata: Metadata = {
  title: '안심루프',
  description: 'IoT 스마트 안심 돌봄 케어 솔루션',
  openGraph: {
    title: '안심루프',
    description: 'IoT 스마트 안심 돌봄 케어 솔루션',
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body>
        <Box bg="$bg" maxW="480px" minH="100dvh" mx="auto" pos="relative">
          {children}
        </Box>
      </body>
    </html>
  )
}
