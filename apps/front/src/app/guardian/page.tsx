import { VStack } from '@devup-ui/react'
import type { Metadata } from 'next'

import { Reveal } from '@/components/common/Reveal'
import { AppHeader } from '@/components/layout/AppHeader'
import { ActivityTimeline } from '@/components/pages/guardian/ActivityTimeline'
import { CrisisResolutionRecord } from '@/components/pages/guardian/CrisisResolutionRecord'
import { RecipientProfileCard } from '@/components/pages/guardian/RecipientProfileCard'
import { SensorStatusPanel } from '@/components/pages/guardian/SensorStatusPanel'

export const metadata: Metadata = {
  title: '보호자 홈 | 안심루프',
  description: '위기 종료 사유 확인과 어르신 일상 안심 모니터링',
  openGraph: {
    title: '보호자 홈 | 안심루프',
    description: '위기 종료 사유 확인과 어르신 일상 안심 모니터링',
  },
}

export default function GuardianHomePage() {
  return (
    <>
      <AppHeader caption="Guardian Home" variant="guardian" />
      <VStack as="main" gap="16px" pb="32px" px="16px">
        <Reveal order={0}>
          <RecipientProfileCard />
        </Reveal>
        <Reveal order={1}>
          <CrisisResolutionRecord />
        </Reveal>
        <Reveal order={2}>
          <ActivityTimeline />
        </Reveal>
        <Reveal order={3}>
          <SensorStatusPanel />
        </Reveal>
      </VStack>
    </>
  )
}
