import { Box, Flex, Text, VStack } from '@devup-ui/react'

/**
 * Informational card explaining that the accounts are demo accounts.
 */
export function DemoNotice() {
  return (
    <Flex bg="$surfaceContainer" borderRadius="12px" gap="12px" p="16px">
      <VStack pt="2px">
        <Box
          bg="$primary"
          boxSize="18.33px"
          maskImage="url(/icons/login-0-14.svg)"
          maskPos="center"
          maskRepeat="no-repeat"
          maskSize="contain"
        />
      </VStack>
      <VStack>
        <Text color="$text" typography="smallBold" wordBreak="keep-all">
          안내 사항
        </Text>
        <VStack pt="2px">
          <Text color="$textSub" typography="bodyRelaxed" wordBreak="keep-all">
            테스트용 간이 계정입니다. 역할을 선택하면 해당 화면으로 즉시
            전환됩니다.
          </Text>
        </VStack>
      </VStack>
    </Flex>
  )
}
