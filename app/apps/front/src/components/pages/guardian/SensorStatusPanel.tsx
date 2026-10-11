import { Box, Flex, Text, VStack } from '@devup-ui/react'

import { PulseDot } from '@/components/common/PulseDot'

/**
 * Footer summary of the recipient's in-home sensors, battery and link.
 */
export function SensorStatusPanel() {
  return (
    <VStack
      as="section"
      bg="$surfaceLow"
      borderRadius="12px"
      gap="4px"
      p="16px"
    >
      <Flex alignItems="center" justifyContent="space-between">
        <Text color="$textSub" typography="smallSemibold" wordBreak="keep-all">
          댁내 안심루프 센서 상태
        </Text>
        <Flex alignItems="center" gap="4px">
          <PulseDot size="6px" />
          <Text
            color="$secondary"
            typography="captionMedium"
            wordBreak="keep-all"
          >
            전체 정상 작동 중
          </Text>
        </Flex>
      </Flex>
      <Flex gap="4px" justifyContent="center" pt="4px">
        <Flex
          alignItems="center"
          bg="$surface"
          borderRadius="8px"
          flex="1"
          justifyContent="space-between"
          p="8px"
        >
          <Flex alignItems="center" gap="8px">
            <Box
              bg="$primary"
              boxSize="16.67px"
              maskImage="url(/icons/guardian-0-377.svg)"
              maskPos="center"
              maskRepeat="no-repeat"
              maskSize="contain"
            />
            <VStack overflow="hidden">
              <Text color="$text" typography="caption" wordBreak="keep-all">
                레이더 센서
              </Text>
              <Text
                color="$secondary"
                typography="latinCaption"
                wordBreak="keep-all"
              >
                배터리 94%
              </Text>
            </VStack>
          </Flex>
          <Box
            bg="$secondary"
            h="13.33px"
            maskImage="url(/icons/guardian-0-384.svg)"
            maskPos="center"
            maskRepeat="no-repeat"
            maskSize="contain"
            w="6.67px"
          />
        </Flex>
        <Flex
          alignItems="center"
          bg="$surface"
          borderRadius="8px"
          flex="1"
          justifyContent="space-between"
          p="8px"
        >
          <Flex alignItems="center" gap="8px">
            <Box
              bg="$primary"
              h="15.83px"
              maskImage="url(/icons/guardian-0-388.svg)"
              maskPos="center"
              maskRepeat="no-repeat"
              maskSize="contain"
              w="15.54px"
            />
            <VStack overflow="hidden">
              <Text color="$text" typography="caption" wordBreak="keep-all">
                스마트 AI 허브
              </Text>
              <Text
                color="$secondary"
                typography="latinCaption"
                wordBreak="keep-all"
              >
                연결됨 (LTE)
              </Text>
            </VStack>
          </Flex>
          <Box
            bg="$secondary"
            h="11.33px"
            maskImage="url(/icons/guardian-0-395.svg)"
            maskPos="center"
            maskRepeat="no-repeat"
            maskSize="contain"
            w="16px"
          />
        </Flex>
      </Flex>
    </VStack>
  )
}
