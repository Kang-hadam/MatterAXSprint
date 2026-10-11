import { Box, Center, Flex, Text, VStack } from '@devup-ui/react'

import { EmergencyStopPanel } from './EmergencyStopPanel'

/**
 * Core feature card: lets the recipient cancel a false crisis alarm
 * and report the reason in one tap.
 */
export function EmergencyControlCard() {
  return (
    <VStack
      as="section"
      bg="$surface"
      borderRadius="12px"
      boxShadow="$card"
      gap="16px"
      p="24px"
    >
      <Flex alignItems="center" gap="8px" pb="4px">
        <Center
          bg="$errorContainer"
          borderRadius="9999px"
          boxSize="40px"
          flexShrink={0}
        >
          <Box
            bg="$errorDeep"
            h="22px"
            maskImage="url(/icons/senior-0-128.svg)"
            maskPos="center"
            maskRepeat="no-repeat"
            maskSize="contain"
            w="17px"
          />
        </Center>
        <VStack>
          <Text
            color="$error"
            textTransform="uppercase"
            typography="overline"
            wordBreak="keep-all"
          >
            비상 알림 제어
          </Text>
          <Text as="h2" color="$text" typography="heading" wordBreak="keep-all">
            혹시 위기 알림이 울렸나요?
          </Text>
        </VStack>
      </Flex>
      <EmergencyStopPanel />
    </VStack>
  )
}
