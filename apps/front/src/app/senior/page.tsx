import { VStack } from '@devup-ui/react'
import type { Metadata } from 'next'

import { Reveal } from '@/components/common/Reveal'
import { AppHeader } from '@/components/layout/AppHeader'
import { DeviceStatusPanel } from '@/components/pages/senior/DeviceStatusPanel'
import { EmergencyControlCard } from '@/components/pages/senior/EmergencyControlCard'
import { GuardianContactCard } from '@/components/pages/senior/GuardianContactCard'
import { StatusSummaryCard } from '@/components/pages/senior/StatusSummaryCard'

export const metadata: Metadata = {
  title: '어르신 홈 | 안심루프',
  description: '댁내 안심 상태 확인과 오작동 위기 알림 즉시 중단',
  openGraph: {
    title: '어르신 홈 | 안심루프',
    description: '댁내 안심 상태 확인과 오작동 위기 알림 즉시 중단',
  },
}

export default function SeniorHomePage() {
  return (
    <>
      <AppHeader caption="Recipient Home" variant="senior" />
      <VStack as="main" gap="24px" pb="72px" px="16px">
        <Reveal order={0}>
          <StatusSummaryCard />
        </Reveal>
        <Reveal order={1}>
          <EmergencyControlCard />
        </Reveal>
        <Reveal order={2}>
          <GuardianContactCard />
        </Reveal>
        <Reveal order={3}>
          <DeviceStatusPanel />
        </Reveal>
      </VStack>
    </>
  )
}
