import { Box, Center, Flex, Text, VStack } from '@devup-ui/react'
import Link from 'next/link'

interface RoleCardProps {
  variant: 'senior' | 'guardian'
}

/**
 * Tappable demo-account card that navigates to the chosen role's home.
 */
export function RoleCard({ variant }: RoleCardProps) {
  return (
    <VStack
      _active={{ transform: 'scale(0.98)', boxShadow: '$sm' }}
      _focusVisible={{
        outline: '2px solid var(--primary)',
        outlineOffset: '2px',
      }}
      _hover={{
        transform: 'translateY(-2px)',
        boxShadow: '0 4px 8px -2px #0000001A, 0 12px 20px -4px #0000001F',
      }}
      as={Link}
      bg="$surface"
      borderRadius="12px"
      boxShadow="$card"
      color="inherit"
      cursor="pointer"
      data-group
      gap="12px"
      overflow="hidden"
      p="20px"
      pos="relative"
      props={{ href: { senior: '/senior', guardian: '/guardian' }[variant] }}
      textDecoration="none"
      transition="transform 0.25s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.25s ease"
      zIndex="0"
    >
      <Box
        _groupHover={{ transform: 'scale(1.35)' }}
        bg={
          {
            senior:
              'color-mix(in srgb, var(--secondaryContainer) 20%, transparent)',
            guardian:
              'color-mix(in srgb, var(--tertiaryContainer) 25%, transparent)',
          }[variant]
        }
        borderRadius="0px 0px 0px 9999px"
        boxSize="96px"
        pos="absolute"
        right="0px"
        top="0px"
        transformOrigin="top right"
        transition="transform 0.4s cubic-bezier(0.22, 1, 0.36, 1)"
        zIndex="-1"
      />
      <Flex alignItems="center" gap="12px">
        <Center
          bg={
            { senior: '$secondaryContainer', guardian: '$surfaceHigh' }[variant]
          }
          borderRadius="12px"
          p="10px"
        >
          <Box
            bg={{ senior: '$secondaryText', guardian: '$primary' }[variant]}
            h={{ senior: '25.08px', guardian: '23.33px' }[variant]}
            maskImage={
              {
                senior: 'url(/icons/login-0-40.svg)',
                guardian: 'url(/icons/login-0-69.svg)',
              }[variant]
            }
            maskPos="center"
            maskRepeat="no-repeat"
            maskSize="contain"
            w={{ senior: '16.33px', guardian: '23.92px' }[variant]}
          />
        </Center>
        <VStack gap="2px">
          <Flex alignItems="center" gap="8px">
            <Text color="$text" typography="subtitle" wordBreak="keep-all">
              {
                {
                  senior: '대상자(어르신) 모드',
                  guardian: '보호자(가족) 모드',
                }[variant]
              }
            </Text>
            <Box
              bg={
                { senior: '$secondary', guardian: '$primaryContainer' }[variant]
              }
              borderRadius="4px"
              px="8px"
              py="2px"
            >
              <Text
                color={
                  { senior: '$onColor', guardian: '$onPrimaryContainer' }[
                    variant
                  ]
                }
                typography="caption"
                wordBreak="keep-all"
              >
                {{ senior: '단말 전용', guardian: '원격 관리' }[variant]}
              </Text>
            </Box>
          </Flex>
          <Text
            color={
              { senior: '$primary', guardian: '$primaryContainer' }[variant]
            }
            typography="bodySemibold"
            wordBreak="keep-all"
          >
            {
              {
                senior: '박순자 어르신 (81세) 댁내 단말',
                guardian: '보호자 김민서 님 (따님)',
              }[variant]
            }
          </Text>
        </VStack>
      </Flex>
      <Flex
        alignItems="center"
        bg="color-mix(in srgb, var(--surfaceLow) 70%, transparent)"
        borderRadius="8px"
        gap="6px"
        p="12px"
      >
        <Box
          bg={{ senior: '$secondary', guardian: '$primary' }[variant]}
          flexShrink={0}
          h="16.67px"
          maskImage={
            {
              senior: 'url(/icons/login-0-52.svg)',
              guardian: 'url(/icons/login-0-81.svg)',
            }[variant]
          }
          maskPos="center"
          maskRepeat="no-repeat"
          maskSize="contain"
          w="13.33px"
        />
        <Text color="$textSub" typography="body" wordBreak="keep-all">
          {
            {
              senior: '위기 발생 시 오작동 즉시 중단 및 안심 상태 확인',
              guardian: '위기 종료 후 사유 확인 및 일상 안심 모니터링',
            }[variant]
          }
        </Text>
      </Flex>
      <Flex alignItems="center" justifyContent="space-between" pt="4px">
        <Text color="$textMuted" typography="caption" wordBreak="keep-all">
          {
            {
              senior: '터치하여 어르신 화면으로 시작',
              guardian: '터치하여 보호자 대시보드로 시작',
            }[variant]
          }
        </Text>
        <Flex alignItems="center" gap="4px">
          <Text
            color={{ senior: '$secondary', guardian: '$primary' }[variant]}
            typography="smallBold"
            wordBreak="keep-all"
          >
            바로 접속
          </Text>
          <Box
            _groupHover={{ transform: 'translateX(4px)' }}
            bg={{ senior: '$secondary', guardian: '$primary' }[variant]}
            boxSize="12px"
            maskImage={
              {
                senior: 'url(/icons/login-0-62.svg)',
                guardian: 'url(/icons/login-0-91.svg)',
              }[variant]
            }
            maskPos="center"
            maskRepeat="no-repeat"
            maskSize="contain"
            transition="transform 0.25s cubic-bezier(0.22, 1, 0.36, 1)"
          />
        </Flex>
      </Flex>
    </VStack>
  )
}
