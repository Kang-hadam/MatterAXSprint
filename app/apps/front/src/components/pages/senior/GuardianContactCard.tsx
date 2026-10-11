import { Box, Center, Flex, Text, VStack } from '@devup-ui/react'

/**
 * Quick-dial card that connects the recipient to their guardian.
 */
export function GuardianContactCard() {
  return (
    <Flex
      alignItems="center"
      as="section"
      bg="$surfaceContainer"
      borderRadius="12px"
      justifyContent="space-between"
      p="16px"
    >
      <Flex alignItems="center" gap="8px">
        <Center
          bg="$surface"
          borderRadius="9999px"
          boxShadow="$sm"
          boxSize="48px"
        >
          <Box
            bg="$primary"
            boxSize="19.5px"
            maskImage="url(/icons/senior-0-161.svg)"
            maskPos="center"
            maskRepeat="no-repeat"
            maskSize="contain"
          />
        </Center>
        <VStack>
          <Text color="$textSub" typography="caption" wordBreak="keep-all">
            보호자 바로 연결
          </Text>
          <Text color="$text" typography="subtitleLoose" wordBreak="keep-all">
            딸 김은지 님
          </Text>
        </VStack>
      </Flex>
      <Flex
        _active={{ transform: 'scale(0.96)' }}
        _focusVisible={{
          outline: '2px solid var(--primary)',
          outlineOffset: '2px',
        }}
        _hover={{ bg: '$primaryContainer', transform: 'translateY(-1px)' }}
        alignItems="center"
        as="button"
        bg="$primary"
        border="none"
        borderRadius="8px"
        boxShadow="$sm"
        cursor="pointer"
        gap="4px"
        minH="48px"
        px="16px"
        py="14px"
        transition="all 0.2s ease"
        type="button"
      >
        <Box
          bg="$onColor"
          boxSize="15px"
          maskImage="url(/icons/senior-0-169.svg)"
          maskPos="center"
          maskRepeat="no-repeat"
          maskSize="contain"
        />
        <Text color="$onColor" typography="smallBold" wordBreak="keep-all">
          전화하기
        </Text>
      </Flex>
    </Flex>
  )
}
