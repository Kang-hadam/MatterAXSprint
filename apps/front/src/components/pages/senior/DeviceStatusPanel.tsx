import { Box, Flex, Text, VStack } from '@devup-ui/react'

import { PulseDot } from '@/components/common/PulseDot'

/**
 * Compact footer showing the in-home IoT devices and their health.
 */
export function DeviceStatusPanel() {
  return (
    <VStack
      as="section"
      bg="$surfaceLow"
      borderRadius="12px"
      gap="8px"
      p="16px"
    >
      <Flex alignItems="center" justifyContent="space-between">
        <Flex alignItems="center" gap="6px">
          <Box
            bg="$textSub"
            boxSize="13.5px"
            maskImage="url(/icons/senior-0-176.svg)"
            maskPos="center"
            maskRepeat="no-repeat"
            maskSize="contain"
          />
          <Text color="$textSub" typography="smallBold" wordBreak="keep-all">
            댁내 IoT 기기 상태
          </Text>
        </Flex>
        <Text color="$secondary" typography="caption" wordBreak="keep-all">
          모두 정상 동작 중
        </Text>
      </Flex>
      <Flex gap="4px" justifyContent="center">
        <Flex
          alignItems="center"
          bg="$surface"
          borderRadius="8px"
          boxShadow="$sm"
          flex="1"
          gap="4px"
          p="8px"
        >
          <PulseDot size="10px" />
          <VStack overflow="hidden">
            <Text color="$textSub" typography="caption" wordBreak="keep-all">
              레이더 센서
            </Text>
            <Text color="$text" typography="bodyBold" wordBreak="keep-all">
              정상 작동 (거실)
            </Text>
          </VStack>
        </Flex>
        <Flex
          alignItems="center"
          bg="$surface"
          borderRadius="8px"
          boxShadow="$sm"
          flex="1"
          gap="4px"
          p="8px"
        >
          <PulseDot size="10px" />
          <VStack overflow="hidden">
            <Text color="$textSub" typography="caption" wordBreak="keep-all">
              스마트 허브
            </Text>
            <Text color="$text" typography="latinBodyBold" wordBreak="keep-all">
              연결됨 (Wi-Fi 양호)
            </Text>
          </VStack>
        </Flex>
      </Flex>
    </VStack>
  )
}
