'use client'

import { Box, Center, keyframes, Text, VStack } from '@devup-ui/react'
import { useState } from 'react'

import { ReasonChip } from './ReasonChip'

type Reason = 'dropped' | 'malfunction' | 'unhurt'

const pop = keyframes({
  '0%': { transform: 'scale(0.96)' },
  '60%': { transform: 'scale(1.02)' },
  '100%': { transform: 'scale(1)' },
})

/**
 * Stop-alarm button and quick reason chips. Stopping the alarm switches the
 * button into its confirmed state; a reason can be picked before or after.
 */
export function EmergencyStopPanel() {
  const [stopped, setStopped] = useState(false)
  const [reason, setReason] = useState<Reason | null>(null)

  function handleStop() {
    setStopped(true)
  }

  function handleSelect(value: Reason) {
    setReason((prev) => (prev === value ? null : value))
  }

  return (
    <>
      <Center
        _active={{ transform: 'scale(0.97)' }}
        _disabled={{ cursor: 'default' }}
        _focusVisible={{
          outline: '3px solid var(--errorContainer)',
          outlineOffset: '2px',
        }}
        _hover={{ filter: 'brightness(1.08)' }}
        animation={
          stopped ? `${pop} 0.4s cubic-bezier(0.22, 1, 0.36, 1)` : 'none'
        }
        aria-live="polite"
        as="button"
        bg={stopped ? '$secondary' : '$error'}
        border="none"
        borderRadius="12px"
        boxShadow={stopped ? '$sm' : '$danger'}
        cursor="pointer"
        disabled={stopped}
        gap="8px"
        minH="68px"
        onClick={handleStop}
        px="16px"
        py="8px"
        transition="background-color 0.3s ease, box-shadow 0.3s ease, transform 0.15s ease, filter 0.2s ease"
        type="button"
        w="100%"
      >
        <Box
          bg="$onColor"
          flexShrink={0}
          h="31.17px"
          maskImage="url(/icons/senior-0-137.svg)"
          maskPos="center"
          maskRepeat="no-repeat"
          maskSize="contain"
          w="28.05px"
        />
        <Text
          color="$onColor"
          textAlign="center"
          typography="brand"
          wordBreak="keep-all"
        >
          {stopped
            ? '알림을 중단했어요. 안심하세요'
            : '괜찮아요! 오작동 알림 중단하기'}
        </Text>
      </Center>
      <VStack gap="4px" pt="4px">
        <Text color="$textSub" typography="smallSemibold" wordBreak="keep-all">
          간편 사유 선택 :
        </Text>
        <VStack aria-label="간편 사유 선택" gap="4px" pt="4px">
          <ReasonChip
            emoji="📦"
            label="실수로 물건을 떨어뜨렸어요"
            onSelect={handleSelect}
            selected={reason === 'dropped'}
            value="dropped"
          />
          <ReasonChip
            emoji="🔔"
            label="단순 오작동이에요"
            onSelect={handleSelect}
            selected={reason === 'malfunction'}
            value="malfunction"
          />
          <ReasonChip
            emoji="👵"
            label="저는 다치지 않고 괜찮아요"
            onSelect={handleSelect}
            selected={reason === 'unhurt'}
            value="unhurt"
          />
        </VStack>
      </VStack>
    </>
  )
}
