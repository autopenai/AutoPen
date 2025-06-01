import type { Test, NewTestResponse, PentestEvent } from "@/types/pentest"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://be38-12-94-170-82.ngrok-free.app"

// Helper function to make API requests with proper error handling and timeout
async function makeApiRequest(url: string, options: RequestInit = {}): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout

  const defaultHeaders = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true",
    Accept: "application/json",
    ...options.headers,
  }

  const requestOptions: RequestInit = {
    ...options,
    headers: defaultHeaders,
    mode: "cors",
    signal: controller.signal,
  }

  console.log(`Making API request to: ${url}`)

  try {
    const response = await fetch(url, requestOptions)
    clearTimeout(timeoutId)
    console.log(`Response status: ${response.status} ${response.statusText}`)
    return response
  } catch (error) {
    clearTimeout(timeoutId)

    if (error instanceof Error) {
      if (error.name === "AbortError") {
        throw new Error("Request timeout - API server may be unavailable")
      }
      if (error.message.includes("Failed to fetch")) {
        throw new Error("Network error - Cannot reach API server")
      }
      throw new Error(`Network error: ${error.message}`)
    }

    throw new Error("Unknown network error occurred")
  }
}

export async function getAllTests(): Promise<Test[]> {
  const response = await makeApiRequest(`${API_BASE_URL}/tests`)

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  const data = await response.json()
  console.log("Tests data received:", data)
  return Array.isArray(data) ? data : []
}

export async function getTestById(testId: string): Promise<Test | null> {
  const response = await makeApiRequest(`${API_BASE_URL}/tests/${testId}`)

  if (!response.ok) {
    if (response.status === 404) {
      console.warn(`Test ${testId} not found`)
      return null
    }
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  const data = await response.json()
  console.log("Test details received:", data)
  return data
}

export async function startNewTest(url: string): Promise<NewTestResponse | null> {
  const response = await makeApiRequest(`${API_BASE_URL}/tests`, {
    method: "POST",
    body: JSON.stringify({ url }),
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  const data = await response.json()
  console.log("New test created:", data)
  return data
}

export function subscribeToTestEvents(
  testId: string,
  onEvent: (event: PentestEvent) => void,
  onError?: (error: Event) => void,
  onOpen?: () => void,
): () => void {
  console.log("Subscribing to SSE events for test:", testId)

  const eventSource = new EventSource(`${API_BASE_URL}/tests/${testId}/events`)

  eventSource.onopen = () => {
    console.log(`SSE connection opened for test ${testId}`)
    onOpen?.()
  }

  eventSource.onmessage = (event) => {
    try {
      console.log("SSE event received:", event.data)
      const data = JSON.parse(event.data) as PentestEvent
      onEvent(data)
    } catch (error) {
      console.error("Error parsing SSE event:", error)
    }
  }

  eventSource.onerror = (error) => {
    console.error("SSE error:", error)
    onError?.(error)
  }

  // Return cleanup function
  return () => {
    console.log(`Closing SSE connection for test ${testId}`)
    eventSource.close()
  }
}
