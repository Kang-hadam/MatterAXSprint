import { describe, expect, it } from 'bun:test'
import { render, screen, userEvent } from 'bun-test-env-dom'

import { EmergencyStopPanel } from '@/components/pages/senior/EmergencyStopPanel'

describe('EmergencyStopPanel', () => {
  it('switches the stop button into its confirmed state', async () => {
    render(<EmergencyStopPanel />)
    const button = screen.getByRole('button', {
      name: /오작동 알림 중단하기/,
    })

    await userEvent.click(button)

    expect(button).toBeDisabled()
    expect(button).toHaveTextContent('알림을 중단했어요. 안심하세요')
  })

  it('toggles a quick reason chip', async () => {
    render(<EmergencyStopPanel />)
    const chip = screen.getByRole('button', { name: /단순 오작동이에요/ })

    expect(chip).toHaveAttribute('aria-pressed', 'false')
    await userEvent.click(chip)
    expect(chip).toHaveAttribute('aria-pressed', 'true')
    await userEvent.click(chip)
    expect(chip).toHaveAttribute('aria-pressed', 'false')
  })
})
