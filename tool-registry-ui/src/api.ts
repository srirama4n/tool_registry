/** API client for Tool Registry */

import type { Tool } from './types'

const API_BASE = '/api/tools'

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = (await res.json().catch(() => ({ detail: res.statusText }))) as { detail?: string }
    throw new Error(typeof err.detail === 'string' ? err.detail : JSON.stringify(err))
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export async function listTools(params?: {
  category?: string
  tags?: string
  skip?: number
  limit?: number
}): Promise<Tool[]> {
  const search = new URLSearchParams()
  if (params?.category) search.set('category', params.category)
  if (params?.tags) search.set('tags', params.tags)
  if (params?.skip != null) search.set('skip', String(params.skip))
  if (params?.limit != null) search.set('limit', String(params.limit))
  const qs = search.toString()
  const url = qs ? `${API_BASE}?${qs}` : API_BASE
  return fetch(url).then((r) => handleResponse<Tool[]>(r))
}

export async function getTool(name: string): Promise<Tool> {
  return fetch(`${API_BASE}/${encodeURIComponent(name)}`).then((r) => handleResponse<Tool>(r))
}

export async function registerTool(tool: Tool): Promise<Tool> {
  return fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(tool),
  }).then((r) => handleResponse<Tool>(r))
}

export async function updateTool(name: string, tool: Tool): Promise<Tool> {
  return fetch(`${API_BASE}/${encodeURIComponent(name)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(tool),
  }).then((r) => handleResponse<Tool>(r))
}

export async function deregisterTool(name: string): Promise<void> {
  const res = await fetch(`${API_BASE}/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    const err = (await res.json().catch(() => ({ detail: res.statusText }))) as { detail?: string }
    throw new Error(typeof err.detail === 'string' ? err.detail : JSON.stringify(err))
  }
}
