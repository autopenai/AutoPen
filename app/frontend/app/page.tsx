"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Shield, Loader2, RefreshCw, AlertCircle } from "lucide-react"
import AddressBar from "@/components/AddressBar"
import ScanHistoryComponent from "@/components/ScanHistory"
import ScanInterface from "@/components/ScanInterface"
import { Button } from "@/components/ui/button"
import { getAllTests } from "@/lib/api"

export default function HomePage() {
  const [currentView, setCurrentView] = useState<"home" | "scanning">("home")
  const [targetUrl, setTargetUrl] = useState("")
  const [currentTestId, setCurrentTestId] = useState<string | undefined>()
  const [scanHistory, setScanHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch scan history from API
  const fetchHistory = async () => {
    setLoading(true)
    setError(null)

    try {
      console.log("Fetching tests from API...")
      const tests = await getAllTests()
      console.log("Tests received:", tests)
      setScanHistory(tests)
    } catch (error) {
      console.error("Error fetching scan history:", error)
      setError(error instanceof Error ? error.message : "Failed to fetch scan history")
      setScanHistory([]) // Clear history on error
    } finally {
      setLoading(false)
    }
  }

  // Initial load
  useEffect(() => {
    fetchHistory()
  }, [])

  const handleScan = (url: string, testId?: string) => {
    setTargetUrl(url)
    setCurrentTestId(testId)
    setCurrentView("scanning")
  }

  const handleBack = () => {
    setCurrentView("home")
    setTargetUrl("")
    setCurrentTestId(undefined)
    // Refresh scan history when returning to home
    fetchHistory()
  }

  const handleRetry = () => {
    fetchHistory()
  }

  if (currentView === "scanning") {
    return <ScanInterface initialUrl={targetUrl} testId={currentTestId} onBack={handleBack} />
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-center min-h-screen text-center space-y-8">
            {/* Logo and Title */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className="space-y-6"
            >
              <div className="flex items-center justify-center space-x-3 mb-8">
                <div className="relative">
                  <Shield className="h-12 w-12 text-primary" />
                  <motion.div
                    className="absolute inset-0 rounded-full border-2 border-primary/30"
                    animate={{
                      scale: [1, 1.2, 1],
                      opacity: [0.5, 0, 0.5],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Number.POSITIVE_INFINITY,
                      ease: "easeInOut",
                    }}
                  />
                </div>
                <h1 className="text-4xl md:text-6xl font-bold bg-gradient-to-r from-foreground to-muted-foreground bg-clip-text text-transparent">
                  AutoPen
                </h1>
              </div>

              <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl">
                Automated penetration testing for modern web applications
              </p>
            </motion.div>

            {/* Address Bar */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="w-full max-w-4xl"
            >
              <AddressBar onScan={(url) => handleScan(url)} />
            </motion.div>

            {/* Error Display */}
            {error && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-4xl">
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <AlertCircle className="h-5 w-5 text-red-500" />
                    <span className="text-sm font-medium text-red-500">Connection Error</span>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">{error}</p>
                  <Button size="sm" variant="outline" onClick={handleRetry} disabled={loading}>
                    <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
                    Retry
                  </Button>
                </div>
              </motion.div>
            )}

            {/* Scan History Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.7 }}
              className="w-full max-w-4xl mt-8"
            >
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-primary mr-2" />
                  <span>Loading scan history...</span>
                </div>
              ) : (
                <ScanHistoryComponent
                  history={scanHistory.map((test) => {
                    // Extract URL from the first event's details or data
                    let url = "Unknown URL"

                    // Look for URL in event details
                    const urlEvent = test.events?.find(
                      (event: any) => event.event_type === "load" && event.details?.url,
                    )

                    if (urlEvent?.details?.url) {
                      url = urlEvent.details.url
                    } else {
                      // Fallback: look for URL in info event data
                      const infoEvent = test.events?.find(
                        (event: any) => event.event_type === "info" && event.details?.data?.url,
                      )
                      if (infoEvent?.details?.data?.url) {
                        url = infoEvent.details.data.url
                      }
                    }

                    // Get timestamp from first event
                    const timestamp = test.events?.[0]?.timestamp ? new Date(test.events[0].timestamp) : new Date()

                    // Count findings by severity from results array
                    const findings = {
                      high: test.results?.filter((r: any) => r.severity?.toLowerCase() === "high").length || 0,
                      medium: test.results?.filter((r: any) => r.severity?.toLowerCase() === "medium").length || 0,
                      low: test.results?.filter((r: any) => r.severity?.toLowerCase() === "low").length || 0,
                    }

                    return {
                      id: test.test_id,
                      url,
                      timestamp,
                      findings,
                    }
                  })}
                  onSelectScan={(scan) => {
                    const test = scanHistory.find((t) => t.test_id === scan.id)
                    if (test) {
                      // Extract URL using the same logic as above
                      let url = scan.url

                      const urlEvent = test.events?.find(
                        (event: any) => event.event_type === "load" && event.details?.url,
                      )

                      if (urlEvent?.details?.url) {
                        url = urlEvent.details.url
                      } else {
                        const infoEvent = test.events?.find(
                          (event: any) => event.event_type === "info" && event.details?.data?.url,
                        )
                        if (infoEvent?.details?.data?.url) {
                          url = infoEvent.details.data.url
                        }
                      }

                      handleScan(url, test.test_id)
                    }
                  }}
                />
              )}
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  )
}
