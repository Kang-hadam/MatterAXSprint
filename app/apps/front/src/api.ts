import { createApi } from '@devup-api/fetch'
import { createQueryClient } from '@devup-api/react-query'

export const client = createApi({
  baseUrl: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000',
})
export const queryApi = createQueryClient(client)
