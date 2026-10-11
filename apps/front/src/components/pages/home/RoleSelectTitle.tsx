import { Flex, Text } from '@devup-ui/react'

/**
 * Section title row above the role cards.
 */
export function RoleSelectTitle() {
  return (
    <Flex alignItems="center" justifyContent="space-between" py="8px">
      <Text as="h2" color="$text" typography="label" wordBreak="keep-all">
        접속 역할을 선택해 주세요
      </Text>
      <Text color="$textMuted" typography="caption" wordBreak="keep-all">
        데모 모드
      </Text>
    </Flex>
  )
}
