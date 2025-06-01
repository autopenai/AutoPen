import type { Test, NewTestResponse, PentestEvent } from "@/types/pentest";

const API_BASE_URL = "https://sf-hackathon-p0-production.up.railway.app";

// Helper function to make API requests with proper error handling and timeout
async function makeApiRequest(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

  const defaultHeaders = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true",
    Accept: "application/json",
    ...options.headers,
  };

  const requestOptions: RequestInit = {
    ...options,
    headers: defaultHeaders,
    mode: "cors",
    signal: controller.signal,
  };

  console.log(`Making API request to: ${url}`);

  try {
    const response = await fetch(url, requestOptions);
    clearTimeout(timeoutId);
    console.log(`Response status: ${response.status} ${response.statusText}`);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof Error) {
      if (error.name === "AbortError") {
        throw new Error("Request timeout - API server may be unavailable");
      }
      if (error.message.includes("Failed to fetch")) {
        throw new Error("Network error - Cannot reach API server");
      }
      throw new Error(`Network error: ${error.message}`);
    }

    throw new Error("Unknown network error occurred");
  }
}

export async function getAllTests(): Promise<Test[]> {
  const response = await makeApiRequest(`${API_BASE_URL}/tests`);

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  console.log("Tests data received:", data);
  return Array.isArray(data) ? data : [];
}

export async function getTestById(testId: string): Promise<Test | null> {
  const response = await makeApiRequest(`${API_BASE_URL}/tests/${testId}`);

  if (!response.ok) {
    if (response.status === 404) {
      console.warn(`Test ${testId} not found`);
      return null;
    }
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  console.log("Test details received:", data);
  return data;
}

export async function startNewTest(
  url: string
): Promise<NewTestResponse | null> {
  const response = await makeApiRequest(`${API_BASE_URL}/tests`, {
    method: "POST",
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  console.log("New test created:", data);
  return data;
}

export function subscribeToTestEvents(
  testId: string,
  onEvent: (event: PentestEvent) => void,
  onError?: (error: Event) => void,
  onOpen?: () => void
): () => void {
  console.log("Starting polling for test:", testId);

  let isPolling = true;
  let timeoutId: NodeJS.Timeout;
  let lastEventCount = 0;

  // Call onOpen immediately to indicate connection started
  onOpen?.();

  const poll = async () => {
    if (!isPolling) return;

    try {
      console.log(`Polling test ${testId} for updates...`);
      const testData = await getTestById(testId);

      if (testData) {
        // Emit any new events that we haven't seen before
        if (testData.events && testData.events.length > lastEventCount) {
          const newEvents = testData.events.slice(lastEventCount);
          newEvents.forEach((event) => onEvent(event));
          lastEventCount = testData.events.length;
        }

        // Stop polling if status is no longer pending or running
        if (
          testData.status &&
          testData.status !== "pending" &&
          testData.status !== "running"
        ) {
          console.log(
            `Test ${testId} completed with status: ${testData.status}`
          );
          isPolling = false;

          //TODO
          const finalTestData = await getTestById(testId);
          console.log("Final test details received:", finalTestData);
          return;
        }
      }

      // Schedule next poll in 5 seconds if still polling
      if (isPolling) {
        timeoutId = setTimeout(poll, 5000);
      }
    } catch (error) {
      console.error("Polling error:", error);
      // Create a mock error event for compatibility with SSE interface
      const errorEvent = new Event("error");
      onError?.(errorEvent);

      // Continue polling even on error, schedule next poll in 5 seconds
      if (isPolling) {
        timeoutId = setTimeout(poll, 5000);
      }
    }
  };

  // Start the first poll immediately
  poll();

  // Return cleanup function
  return () => {
    console.log(`Stopping polling for test ${testId}`);
    isPolling = false;
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  };
}
