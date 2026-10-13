'use client'

import { Box, Center, Text, VStack } from '@devup-ui/react'
import { useState } from 'react'

import { queryApi } from '@/api'

/**
 * Polls the server's danger flag every 2 seconds. While it is true, covers
 * the screen with an alert whose main action dials 119 right away.
 */
export function DangerAlert() {
  const { data } = queryApi.useQuery(
    'get',
    '/danger',
    {},
    { refetchInterval: 2000 },
  )
  const [dismissed, setDismissed] = useState(false)
  const danger = data?.danger ?? false

  // Re-arm once the danger clears, so the next one pops up again.
  if (dismissed && !danger) setDismissed(false)

  function handleClose() {
    setDismissed(true)
  }

  if (!danger || dismissed) return null

  return (
    <Center
      bg="color-mix(in srgb, var(--text) 60%, transparent)"
      inset="0"
      pos="fixed"
      px="16px"
      zIndex="100"
    >
      <VStack
        alignItems="center"
        aria-describedby="danger-alert-description"
        aria-labelledby="danger-alert-title"
        aria-modal="true"
        bg="$surface"
        borderRadius="12px"
        boxShadow="$danger"
        gap="16px"
        maxW="448px"
        p="24px"
        role="alertdialog"
        w="100%"
      >
        <Center
          bg="$errorContainer"
          borderRadius="9999px"
          boxSize="64px"
          flexShrink={0}
        >
          <Box
            bg="$errorDeep"
            h="30px"
            maskImage="url(/icons/senior-0-128.svg)"
            maskPos="center"
            maskRepeat="no-repeat"
            maskSize="contain"
            w="23px"
          />
        </Center>
        <VStack alignItems="center" gap="4px">
          <Text
            as="h2"
            color="$text"
            id="danger-alert-title"
            textAlign="center"
            typography="heading"
            wordBreak="keep-all"
          >
            위험 상황이 감지되었어요
          </Text>
          <Text
            color="$textSub"
            id="danger-alert-description"
            textAlign="center"
            typography="body"
            wordBreak="keep-all"
          >
            댁내 센서가 위기 신호를 보냈어요. 지금 바로 119에 신고해 주세요.
          </Text>
        </VStack>
        <Center
          _active={{ transform: 'scale(0.97)' }}
          _focusVisible={{
            outline: '3px solid var(--errorContainer)',
            outlineOffset: '2px',
          }}
          _hover={{ filter: 'brightness(1.08)' }}
          as="a"
          bg="$error"
          borderRadius="12px"
          boxShadow="$danger"
          gap="8px"
          href="tel:119"
          minH="68px"
          px="16px"
          py="8px"
          textDecoration="none"
          transition="transform 0.15s ease, filter 0.2s ease"
          w="100%"
        >
          <Box
            bg="$onColor"
            boxSize="20px"
            flexShrink={0}
            maskImage="url(/icons/senior-0-169.svg)"
            maskPos="center"
            maskRepeat="no-repeat"
            maskSize="contain"
          />
          <Text
            as="span"
            color="$onColor"
            typography="brand"
            wordBreak="keep-all"
          >
            바로 신고하기
          </Text>
        </Center>
        <Center
          _focusVisible={{
            outline: '2px solid var(--primary)',
            outlineOffset: '2px',
          }}
          _hover={{ bg: '$surfaceLow' }}
          as="button"
          bg="transparent"
          border="none"
          borderRadius="8px"
          cursor="pointer"
          minH="48px"
          onClick={handleClose}
          px="16px"
          transition="background-color 0.2s ease"
          type="button"
          w="100%"
        >
          <Text as="span" color="$textSub" typography="bodySemibold">
            닫기
          </Text>
        </Center>
      </VStack>
    </Center>
  )
}
