'use client'

import { Flex, Text } from '@devup-ui/react'

interface ReasonChipProps<T extends string> {
  emoji: string
  label: string
  onSelect: (value: T) => void
  selected: boolean
  value: T
}

/**
 * Pill-shaped quick reason option used under the stop-alarm button.
 */
export function ReasonChip<T extends string>({
  emoji,
  label,
  onSelect,
  selected,
  value,
}: ReasonChipProps<T>) {
  function handleClick() {
    onSelect(value)
  }

  return (
    <Flex
      _active={{ transform: 'scale(0.97)' }}
      _focusVisible={{
        outline: '2px solid var(--primary)',
        outlineOffset: '2px',
      }}
      _hover={{ bg: selected ? '$secondaryContainer' : '$surfaceHigh' }}
      alignItems="center"
      alignSelf="flex-start"
      aria-pressed={selected}
      as="button"
      bg={selected ? '$secondaryContainer' : '$surfaceContainer'}
      border="none"
      borderRadius="9999px"
      boxShadow={selected ? 'inset 0 0 0 2px var(--secondary)' : 'none'}
      cursor="pointer"
      gap="6px"
      minH="48px"
      onClick={handleClick}
      pb="14px"
      pt="13.5px"
      px="16px"
      transition="all 0.2s ease"
      type="button"
    >
      <Text aria-hidden as="span" typography="small">
        {emoji}
      </Text>
      <Text
        as="span"
        color={selected ? '$secondaryText' : '$text'}
        typography="small"
        wordBreak="keep-all"
      >
        {label}
      </Text>
    </Flex>
  )
}
