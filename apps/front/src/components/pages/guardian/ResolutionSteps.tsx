import { Box, Center, Flex, Text, VStack } from '@devup-ui/react'

import { PulseDot } from '@/components/common/PulseDot'

/**
 * Four-step breakdown of the resolved crisis: detection, how it was ended,
 * the recorded reason with AI voice verdict, and the 119 dispatch outcome.
 */
export function ResolutionSteps() {
  return (
    <VStack bg="$surfaceLow" borderRadius="12px" gap="8px" p="16px">
      <Flex gap="12px">
        <VStack flexShrink={0} pt="2px">
          <Center bg="$surfaceContainer" borderRadius="9999px" boxSize="32px">
            <Box
              bg="$textSub"
              h="10.61px"
              maskImage="url(/icons/guardian-0-253.svg)"
              maskPos="center"
              maskRepeat="no-repeat"
              maskSize="contain"
              w="15px"
            />
          </Center>
        </VStack>
        <VStack>
          <Text color="$textSub" typography="caption" wordBreak="keep-all">
            발생 감지
          </Text>
          <Text color="$text" typography="bodyMedium" wordBreak="keep-all">
            오늘 15:24 거실 바닥 충격 감지
          </Text>
          <Text color="$textSub" typography="caption" wordBreak="keep-all">
            레이더 파형 분석: 급격한 중력가속도 변화 (낙상 의심)
          </Text>
        </VStack>
      </Flex>
      <Box bg="$divider" h="1px" />
      <Flex gap="12px">
        <VStack flexShrink={0} pt="2px">
          <Center bg="$secondaryContainer" borderRadius="9999px" boxSize="32px">
            <Box
              bg="$secondaryText"
              h="15.75px"
              maskImage="url(/icons/guardian-0-266.svg)"
              maskPos="center"
              maskRepeat="no-repeat"
              maskSize="contain"
              w="12.99px"
            />
          </Center>
        </VStack>
        <VStack>
          <Text color="$textSub" typography="caption" wordBreak="keep-all">
            종료 방식
          </Text>
          <Flex alignItems="center" flexWrap="wrap" gap="8px">
            <Text color="$text" typography="bodySemibold" wordBreak="keep-all">
              어르신 직접 해제 완료
            </Text>
            <Box bg="$surfaceContainer" borderRadius="4px" px="8px" py="2px">
              <Text
                color="$primary"
                typography="latinCaptionBold"
                wordBreak="keep-all"
              >
                42초 내
              </Text>
            </Box>
          </Flex>
          <Text color="$textSub" typography="caption" wordBreak="keep-all">
            벽면 안심 단말기 확인 터치패드 입력
          </Text>
        </VStack>
      </Flex>
      <Box bg="$divider" h="1px" />
      <Flex gap="12px">
        <VStack flexShrink={0} pt="2px">
          <Center bg="$surfaceContainer" borderRadius="9999px" boxSize="32px">
            <Box
              bg="$primary"
              h="14.21px"
              maskImage="url(/icons/guardian-0-282.svg)"
              maskPos="center"
              maskRepeat="no-repeat"
              maskSize="contain"
              w="16.5px"
            />
          </Center>
        </VStack>
        <VStack>
          <Text color="$textSub" typography="caption" wordBreak="keep-all">
            해제 사유 및 AI 음성 판정
          </Text>
          <VStack pt="2px">
            <Text
              color="$primary"
              typography="bodySemibold"
              wordBreak="keep-all"
            >
              “실수로 물건을 떨어뜨렸어요 (단순 착오 및 안전)”
            </Text>
          </VStack>
          <VStack pt="2px">
            <Text color="$textSub" typography="caption" wordBreak="keep-all">
              AI 허브 실시간 판별: 어르신 “괜찮아, 안 다쳤어” 음성 화자 일치율
              98.4%
            </Text>
          </VStack>
        </VStack>
      </Flex>
      <Box bg="$divider" h="1px" />
      <Flex gap="12px">
        <VStack flexShrink={0} pt="2px">
          <Center bg="$surfaceContainer" borderRadius="9999px" boxSize="32px">
            <Box
              bg="$secondary"
              boxSize="13.5px"
              maskImage="url(/icons/guardian-0-297.svg)"
              maskPos="center"
              maskRepeat="no-repeat"
              maskSize="contain"
            />
          </Center>
        </VStack>
        <VStack>
          <Text color="$textSub" typography="caption" wordBreak="keep-all">
            119 긴급 출동 연계
          </Text>
          <Flex alignItems="center" gap="6px" pt="2px">
            <PulseDot size="8px" />
            <Text
              color="$secondary"
              typography="smallBold"
              wordBreak="keep-all"
            >
              정상 차단 (불필요한 출동 방지 완료)
            </Text>
          </Flex>
          <Text color="$textSub" typography="caption" wordBreak="keep-all">
            상황실 골든타임 프로토콜 카운트다운 자동 정지
          </Text>
        </VStack>
      </Flex>
    </VStack>
  )
}
