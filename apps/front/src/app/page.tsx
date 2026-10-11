import { VStack } from '@devup-ui/react'

import { Reveal } from '@/components/common/Reveal'
import { BrandHero } from '@/components/pages/home/BrandHero'
import { DemoNotice } from '@/components/pages/home/DemoNotice'
import { RoleCard } from '@/components/pages/home/RoleCard'
import { RoleSelectTitle } from '@/components/pages/home/RoleSelectTitle'

export default function HomePage() {
  return (
    <VStack as="main" pb="32px" px="16px">
      <Reveal order={0}>
        <BrandHero />
      </Reveal>
      <Reveal order={1}>
        <RoleSelectTitle />
      </Reveal>
      <VStack gap="16px">
        <Reveal order={2}>
          <RoleCard variant="senior" />
        </Reveal>
        <Reveal order={3}>
          <RoleCard variant="guardian" />
        </Reveal>
      </VStack>
      <VStack pt="24px">
        <Reveal order={4}>
          <DemoNotice />
        </Reveal>
      </VStack>
    </VStack>
  )
}
