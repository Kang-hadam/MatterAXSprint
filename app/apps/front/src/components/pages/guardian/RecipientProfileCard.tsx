import { Box, Center, Flex, Image, Text, VStack } from '@devup-ui/react'

import { PulseDot } from '@/components/common/PulseDot'

/**
 * Header card for the guardian: who is being cared for, their state,
 * and a one-tap call button.
 */
export function RecipientProfileCard() {
  return (
    <VStack
      as="section"
      bg="$surface"
      borderRadius="12px"
      boxShadow="$sm"
      gap="8px"
      p="16px"
    >
      <Flex alignItems="center" justifyContent="space-between">
        <Flex alignItems="center" gap="8px">
          <Box
            bg="$surfaceContainer"
            borderRadius="9999px"
            boxSize="48px"
            flexShrink={0}
            overflow="hidden"
          >
            <Image
              alt="박순자 어르신 프로필 사진"
              boxSize="100%"
              objectFit="cover"
              src="/images/recipient-avatar.png"
            />
          </Box>
          <VStack>
            <Flex alignItems="baseline" gap="4px">
              <Text
                as="h1"
                color="$text"
                typography="subtitle"
                wordBreak="keep-all"
              >
                박순자 어르신
              </Text>
              <Text as="span" color="$textSub" typography="latinSubtitle">
                (81세)
              </Text>
            </Flex>
            <Text color="$textSub" typography="caption" wordBreak="keep-all">
              어머니 댁 · 마포구 연남동
            </Text>
          </VStack>
        </Flex>
        <Flex
          alignItems="center"
          bg="$secondaryContainer"
          borderRadius="9999px"
          flexShrink={0}
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
            안심 상태
          </Text>
        </Flex>
      </Flex>
      <Center
        _active={{ transform: 'scale(0.98)' }}
        _focusVisible={{
          outline: '2px solid var(--primary)',
          outlineOffset: '2px',
        }}
        _hover={{ bg: '$primaryContainer' }}
        as="button"
        bg="$primary"
        border="none"
        borderRadius="12px"
        boxShadow="$sm"
        cursor="pointer"
        gap="4px"
        h="56px"
        transition="all 0.2s ease"
        type="button"
        w="100%"
      >
        <Box
          bg="$onColor"
          boxSize="15px"
          maskImage="url(/icons/guardian-0-229.svg)"
          maskPos="center"
          maskRepeat="no-repeat"
          maskSize="contain"
        />
        <Text color="$onColor" typography="labelSemibold" wordBreak="keep-all">
          어머니께 안부 전화 걸기
        </Text>
      </Center>
    </VStack>
  )
}
