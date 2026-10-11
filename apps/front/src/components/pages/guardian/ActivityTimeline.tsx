import { Box, Center, Flex, Text, VStack } from '@devup-ui/react'

/**
 * Today's key activity entries reported by the in-home sensors.
 */
export function ActivityTimeline() {
  return (
    <VStack as="section" gap="4px" pt="4px">
      <Flex alignItems="center" justifyContent="space-between" px="4px">
        <Text as="h2" color="$primary" typography="label" wordBreak="keep-all">
          오늘의 주요 활동 타임라인
        </Text>
        <Text color="$textSub" typography="caption" wordBreak="keep-all">
          안심 센서 로그
        </Text>
      </Flex>
      <VStack
        as="ol"
        bg="$surface"
        borderRadius="12px"
        boxShadow="$sm"
        gap="16px"
        listStyle="none"
        m="0"
        p="16px"
      >
        <Flex as="li" gap="8px">
          <VStack alignItems="center" flexShrink={0}>
            <Center
              bg="$secondaryContainer"
              borderRadius="9999px"
              boxSize="28px"
            >
              <Box
                bg="$secondaryText"
                h="14.33px"
                maskImage="url(/icons/guardian-0-320.svg)"
                maskPos="center"
                maskRepeat="no-repeat"
                maskSize="contain"
                w="8.67px"
              />
            </Center>
            <VStack h="44px" pt="4px" w="2px">
              <Box bg="$surfaceContainer" h="40px" w="2px" />
            </VStack>
          </VStack>
          <VStack pt="2px">
            <Flex alignItems="center" gap="8px">
              <Text as="time" color="$primary" typography="latinCaptionBold">
                15:25
              </Text>
              <Text
                color="$secondary"
                typography="captionMedium"
                wordBreak="keep-all"
              >
                활동 재개
              </Text>
            </Flex>
            <Text color="$text" typography="body" wordBreak="keep-all">
              낙상 오감지 해제 후 정상 보행 감지됨
            </Text>
            <Text color="$textSub" typography="caption" wordBreak="keep-all">
              거실 → 주방으로 안정적인 걸음걸이 이동
            </Text>
          </VStack>
        </Flex>
        <Flex as="li" gap="8px">
          <VStack alignItems="center" flexShrink={0}>
            <Center bg="$surfaceHigh" borderRadius="9999px" boxSize="28px">
              <Box
                bg="$primary"
                h="12px"
                maskImage="url(/icons/guardian-0-337.svg)"
                maskPos="center"
                maskRepeat="no-repeat"
                maskSize="contain"
                w="9.33px"
              />
            </Center>
            <VStack h="44px" pt="4px" w="2px">
              <Box bg="$surfaceContainer" h="40px" w="2px" />
            </VStack>
          </VStack>
          <VStack pt="2px">
            <Flex alignItems="center" gap="8px">
              <Text as="time" color="$primary" typography="latinCaptionBold">
                12:40
              </Text>
              <Text color="$textSub" typography="caption" wordBreak="keep-all">
                복약 안심
              </Text>
            </Flex>
            <Text color="$text" typography="body" wordBreak="keep-all">
              점심 복약 완료 (혈압약 보관함 개폐)
            </Text>
            <Text color="$textSub" typography="caption" wordBreak="keep-all">
              스마트 약통 1회분 투약 정상 확인
            </Text>
          </VStack>
        </Flex>
        <Flex as="li" gap="8px">
          <VStack alignItems="center" flexShrink={0}>
            <Center bg="$surfaceHigh" borderRadius="9999px" boxSize="28px">
              <Box
                bg="$primary"
                h="13.33px"
                maskImage="url(/icons/guardian-0-354.svg)"
                maskPos="center"
                maskRepeat="no-repeat"
                maskSize="contain"
                w="10.67px"
              />
            </Center>
          </VStack>
          <VStack pt="2px">
            <Flex alignItems="center" gap="8px">
              <Text as="time" color="$primary" typography="latinCaptionBold">
                08:15
              </Text>
              <Text color="$textSub" typography="caption" wordBreak="keep-all">
                식사 감지
              </Text>
            </Flex>
            <Text color="$text" typography="body" wordBreak="keep-all">
              주방 냉장고 문 열림 및 아침 식사 활동
            </Text>
            <Text color="$textSub" typography="caption" wordBreak="keep-all">
              기상 후 정상적인 조간 일과 유지 중
            </Text>
          </VStack>
        </Flex>
      </VStack>
    </VStack>
  )
}
