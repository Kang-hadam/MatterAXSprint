import {
  Box,
  Center,
  Flex,
  Image,
  keyframes,
  Text,
  VStack,
} from '@devup-ui/react'

import { PulseDot } from '@/components/common/PulseDot'

const breathe = keyframes({
  '0%, 100%': { transform: 'scale(1)', opacity: 0.7 },
  '50%': { transform: 'scale(1.12)', opacity: 0.45 },
})

const float = keyframes({
  '0%, 100%': { transform: 'translateY(0)' },
  '50%': { transform: 'translateY(-4px)' },
})

/**
 * Brand block on the role selection screen: logo with ambient glow,
 * live-monitoring pill, service name and tagline.
 */
export function BrandHero() {
  return (
    <VStack alignItems="center" pb="16px" pt="24px" textAlign="center">
      <VStack pb="8px">
        <Center pos="relative" zIndex="0">
          <Box
            _media={{
              '(prefers-reduced-motion: reduce)': { animation: 'none' },
            }}
            animation={`${breathe} 4s ease-in-out infinite`}
            bg="color-mix(in srgb, var(--secondaryContainer) 40%, transparent)"
            borderRadius="9999px"
            boxSize="120px"
            filter="blur(24px)"
            left="-12px"
            opacity="0.7"
            pos="absolute"
            top="-12px"
            zIndex="-1"
          />
          <Image
            _media={{
              '(prefers-reduced-motion: reduce)': { animation: 'none' },
            }}
            alt="안심루프 로고"
            animation={`${float} 4s ease-in-out infinite`}
            borderRadius="12px"
            boxShadow="$sm"
            boxSize="96px"
            objectFit="cover"
            src="/images/login-0-33.png"
          />
        </Center>
      </VStack>
      <VStack pb="8px">
        <Flex
          alignItems="center"
          bg="$secondaryContainer"
          borderRadius="9999px"
          gap="6px"
          px="12px"
          py="4px"
        >
          <PulseDot size="8px" />
          <Text
            color="$secondaryText"
            typography="caption"
            wordBreak="keep-all"
          >
            안심 24시간 실시간 모니터링
          </Text>
        </Flex>
      </VStack>
      <Text as="h1" color="$primary" typography="display" wordBreak="keep-all">
        안심루프
      </Text>
      <VStack alignItems="center" maxW="320px" pt="4px">
        <Text color="$textSub" typography="body" wordBreak="keep-all">
          IoT 스마트 안심 돌봄 케어 솔루션
        </Text>
      </VStack>
    </VStack>
  )
}
