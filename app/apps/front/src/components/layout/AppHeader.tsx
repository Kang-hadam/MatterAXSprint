import { Box, Center, Flex, Image, Text } from '@devup-ui/react'
import Link from 'next/link'

interface AppHeaderProps {
  /** Latin caption after the brand name, e.g. "Recipient Home". */
  caption: string
  variant: 'senior' | 'guardian'
}

/**
 * Sticky translucent app bar shared by the recipient and guardian homes.
 * The primary round button returns to role selection.
 */
export function AppHeader({ caption, variant }: AppHeaderProps) {
  return (
    <Box
      as="header"
      backdropFilter="blur(24px)"
      bg="color-mix(in srgb, var(--bg) 90%, transparent)"
      boxShadow="$header"
      pos="sticky"
      top="0"
      zIndex="10"
    >
      <Flex
        alignItems="center"
        h="64px"
        justifyContent="space-between"
        px="16px"
      >
        <Flex alignItems="center" gap="8px">
          <Image
            alt="안심루프 로고"
            aspectRatio="1"
            boxSize="32px"
            objectFit="cover"
            src="/images/brand-logo.png"
          />
          <Flex alignItems="center" gap="4px">
            <Text color="$primary" typography="brand" wordBreak="keep-all">
              안심루프
            </Text>
            <Text color="$textSub" typography="latinSmall">
              · {caption}
            </Text>
          </Flex>
        </Flex>
        <Flex alignItems="center" gap="8px">
          <Box
            bg={
              { senior: 'transparent', guardian: '$surfaceContainer' }[variant]
            }
            borderRadius="9999px"
            boxSize="32px"
          />
          <Link aria-label="역할 선택으로 돌아가기" href="/">
            <Center
              _active={{ transform: 'scale(0.92)' }}
              _hover={{ bg: '$primaryContainer', transform: 'rotate(-8deg)' }}
              bg="$primary"
              borderRadius="9999px"
              boxSize="32px"
              cursor="pointer"
              transition="all 0.2s ease"
            >
              <Box
                bg="$onColor"
                boxSize="12px"
                maskImage={
                  {
                    senior: 'url(/icons/senior-0-208.svg)',
                    guardian: 'url(/icons/guardian-0-409.svg)',
                  }[variant]
                }
                maskPos="center"
                maskRepeat="no-repeat"
                maskSize="contain"
              />
            </Center>
          </Link>
        </Flex>
      </Flex>
    </Box>
  )
}
