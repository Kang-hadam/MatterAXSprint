import { Box, Center, Flex, Text, VStack } from '@devup-ui/react'

import { PulseDot } from '@/components/common/PulseDot'

/**
 * Calm-state summary for the recipient: status pill, greeting and
 * the live radar sensor reading.
 */
export function StatusSummaryCard() {
  return (
    <VStack
      as="section"
      bg="$surface"
      borderRadius="12px"
      boxShadow="$sm"
      gap="16px"
      p="24px"
    >
      <Flex alignItems="center" justifyContent="space-between">
        <Flex
          alignItems="center"
          bg="$secondaryContainer"
          borderRadius="9999px"
          gap="4px"
          px="16px"
          py="4px"
        >
          <PulseDot size="14px" />
          <Text color="$secondaryText" typography="label" wordBreak="keep-all">
            정상 · 평온한 상태
          </Text>
        </Flex>
        <Flex alignItems="center" gap="4px">
          <Box
            bg="$secondary"
            h="14.38px"
            maskImage="url(/icons/senior-0-103.svg)"
            maskPos="center"
            maskRepeat="no-repeat"
            maskSize="contain"
            w="16.67px"
          />
          <Text
            color="$textSub"
            typography="smallSemibold"
            wordBreak="keep-all"
          >
            실시간 연결
          </Text>
        </Flex>
      </Flex>
      <VStack gap="4px">
        <Text as="h1" color="$text" typography="title" wordBreak="keep-all">
          박순자 어르신,
          <br />
          현재 댁내가 평온합니다
        </Text>
        <Text color="$textSub" typography="lead" wordBreak="keep-all">
          오늘도 안심루프가 댁내를 든든하게 보살피고 있어요.
        </Text>
      </VStack>
      <Flex
        alignItems="center"
        bg="$surfaceLow"
        borderRadius="8px"
        gap="8px"
        justifyContent="space-between"
        p="16px"
      >
        <Flex alignItems="center" gap="8px">
          <Center
            bg="color-mix(in srgb, var(--secondaryContainer) 60%, transparent)"
            borderRadius="9999px"
            boxSize="48px"
            flexShrink={0}
          >
            <Box
              bg="$secondary"
              boxSize="23.33px"
              maskImage="url(/icons/senior-0-115.svg)"
              maskPos="center"
              maskRepeat="no-repeat"
              maskSize="contain"
            />
          </Center>
          <VStack>
            <Text
              color="$textSub"
              typography="smallSemibold"
              wordBreak="keep-all"
            >
              센서 감지 현황
            </Text>
            <Text color="$text" typography="subtitleLoose" wordBreak="keep-all">
              거실 레이더 센서 정상 감지 중
            </Text>
          </VStack>
        </Flex>
        <Box
          bg="color-mix(in srgb, var(--secondaryContainer) 50%, transparent)"
          borderRadius="4px"
          flexShrink={0}
          px="8px"
          py="2px"
        >
          <Text color="$secondary" typography="smallBold" whiteSpace="nowrap">
            안정 상태
          </Text>
        </Box>
      </Flex>
    </VStack>
  )
}
