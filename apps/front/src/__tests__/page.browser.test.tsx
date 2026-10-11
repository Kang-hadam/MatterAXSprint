import { ThemeScript } from '@devup-ui/react'
import { describe, expect, it } from 'bun:test'
import { render, screen } from 'bun-test-env-dom'

import GuardianHomePage from '@/app/guardian/page'
import HomePage from '@/app/page'
import SeniorHomePage from '@/app/senior/page'

describe('ThemeScript', () => {
  it('should render', () => {
    const { container } = render(<ThemeScript />)
    expect(container).toMatchSnapshot()
  })
})

describe('HomePage', () => {
  it('should render both role cards linking to their homes', () => {
    const { container } = render(<HomePage />)
    expect(container).toMatchSnapshot()

    const links = screen.getAllByRole('link')
    expect(links.map((link) => link.getAttribute('href'))).toEqual([
      '/senior',
      '/guardian',
    ])
  })
})

describe('SeniorHomePage', () => {
  it('should render the recipient home', () => {
    const { container } = render(<SeniorHomePage />)
    expect(container).toMatchSnapshot()
    expect(
      screen.getByRole('link', { name: '역할 선택으로 돌아가기' }),
    ).toHaveAttribute('href', '/')
  })
})

describe('GuardianHomePage', () => {
  it('should render the guardian home', () => {
    const { container } = render(<GuardianHomePage />)
    expect(container).toMatchSnapshot()
    expect(screen.getByText('최근 위기 대응 종료 기록')).toBeInTheDocument()
  })
})
