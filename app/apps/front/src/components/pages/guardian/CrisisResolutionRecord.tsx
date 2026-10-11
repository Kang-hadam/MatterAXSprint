import { Box, Flex, Text, VStack } from '@devup-ui/react'

import { ResolutionSteps } from './ResolutionSteps'

/**
 * Key section for the guardian: how the latest crisis alert was resolved.
 */
export function CrisisResolutionRecord() {
  return (
    <VStack as="section" gap="4px">
      <Flex alignItems="center" justifyContent="space-between" px="4px">
        <Flex alignItems="center" gap="6px">
          <Box
            bg="$primary"
            boxSize="16.67px"
            maskImage="url(/icons/guardian-0-236.svg)"
            maskPos="center"
            maskRepeat="no-repeat"
            maskSize="contain"
          />
          <Text
            as="h2"
            color="$primary"
            typography="label"
            wordBreak="keep-all"
          >
            최근 위기 대응 종료 기록
          </Text>
        </Flex>
        <Box bg="$surfaceHigh" borderRadius="9999px" px="8px" py="2px">
          <Text
            color="$textSub"
            typography="captionMedium"
            wordBreak="keep-all"
          >
            안전 확인 완료
          </Text>
        </Box>
      </Flex>
      <VStack
        bg="$surface"
        borderRadius="12px"
        boxShadow="$sm"
        gap="8px"
        p="16px"
      >
        <Flex gap="4px">
          <VStack pt="2px">
            <Box
              bg="$secondary"
              h="18.33px"
              maskImage="url(/icons/guardian-0-245.svg)"
              maskPos="center"
              maskRepeat="no-repeat"
              maskSize="contain"
              w="14.67px"
            />
          </VStack>
          <Text color="$text" typography="smallSemibold" wordBreak="keep-all">
            위기 대응이 안전하게 종결되었습니다
          </Text>
        </Flex>
        <ResolutionSteps />
      </VStack>
    </VStack>
  )
}
