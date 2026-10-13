import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  mock,
  spyOn,
} from 'bun:test'
import { act, render, screen, userEvent } from 'bun-test-env-dom'

import { DangerAlert } from '@/components/common/DangerAlert'

let danger = false

function mockDangerApi() {
  // Bun types `fetch` with a `preconnect` member, so the stub needs one too.
  return spyOn(globalThis, 'fetch').mockImplementation(
    Object.assign(async () => new Response(JSON.stringify({ danger })), {
      preconnect() {},
    }),
  )
}

function renderAlert() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  render(
    <QueryClientProvider client={queryClient}>
      <DangerAlert />
    </QueryClientProvider>,
  )
  return queryClient
}

// React Query hands results to components on a setTimeout(0), so wait one
// more macrotask inside act() before asserting on the DOM.
async function poll(queryClient: QueryClient) {
  await act(async () => {
    await queryClient.refetchQueries()
    await new Promise((resolve) => setTimeout(resolve, 0))
  })
}

describe('DangerAlert', () => {
  beforeEach(() => {
    danger = false
  })

  afterEach(() => {
    mock.restore()
  })

  it('stays hidden while safe and pops up on the next poll after danger', async () => {
    const fetchMock = mockDangerApi()
    const queryClient = renderAlert()

    await poll(queryClient)
    const [input] = fetchMock.mock.calls[0]
    expect(new URL(input instanceof Request ? input.url : input).pathname).toBe(
      '/danger',
    )
    expect(screen.queryByRole('alertdialog')).toBeNull()

    danger = true
    const dialog = await screen.findByRole('alertdialog', undefined, {
      timeout: 3000,
    })

    expect(dialog).toHaveTextContent('위험 상황이 감지되었어요')
    expect(screen.getByRole('link', { name: '바로 신고하기' })).toHaveAttribute(
      'href',
      'tel:119',
    )
  })

  it('stays closed after 닫기 until the danger clears and comes back', async () => {
    mockDangerApi()
    danger = true
    const queryClient = renderAlert()

    await userEvent.click(await screen.findByRole('button', { name: '닫기' }))
    expect(screen.queryByRole('alertdialog')).toBeNull()

    await poll(queryClient)
    expect(screen.queryByRole('alertdialog')).toBeNull()

    danger = false
    await poll(queryClient)
    danger = true
    await poll(queryClient)
    expect(screen.getByRole('alertdialog')).toBeInTheDocument()
  })
})
