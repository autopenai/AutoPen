"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { ArrowLeft, Search, Shield, Activity, ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import ScanLog from "./ScanLog"
import type { SecurityFinding, LogEntry } from "@/types/pentest"

interface ScanInterfaceProps {
  initialUrl: string
  onBack: () => void
}

const ScanInterface: React.FC<ScanInterfaceProps> = ({ initialUrl, onBack }) => {
  const [currentUrl, setCurrentUrl] = useState(initialUrl)
  const [isLogOpen, setIsLogOpen] = useState(true)
  const [findings, setFindings] = useState<SecurityFinding[]>([])
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [isScanning, setIsScanning] = useState(false)
  const [hoveredFinding, setHoveredFinding] = useState<SecurityFinding | null>(null)
  const [scanningElements, setScanningElements] = useState<string[]>([])
  const [scanStatus, setScanStatus] = useState<string>("")
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null)

  const addLog = (type: LogEntry["type"], message: string, details?: string) => {
    const newLog: LogEntry = {
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
      type,
      message,
      details,
    }
    setLogs((prev) => [...prev, newLog])
  }

  const simulateElementScan = (element: string) => {
    setScanningElements((prev) => [...prev, element])
    setTimeout(() => {
      setScanningElements((prev) => prev.filter((e) => e !== element))
    }, 2000)
  }

  const simulateScan = async () => {
    setIsScanning(true)
    setFindings([])
    setLogs([])
    setScanningElements([])
    setScanStatus("Initializing scan...")

    addLog("info", `🎯 Target URL: ${currentUrl}`)
    addLog("info", "🚀 Starting vulnerability assessment...")
    addLog("info", "🌐 Initializing browser session...")
    await new Promise((resolve) => setTimeout(resolve, 1000))

    addLog("success", "✅ Browser session started successfully")
    addLog("info", "🤖 Creating LangChain agent...")
    addLog("info", "🔍 Running vulnerability assessment...")
    await new Promise((resolve) => setTimeout(resolve, 1500))

    setScanStatus("Analyzing page structure...")
    addLog(
      "info",
      "I need to understand the structure of the webpage first. I will use the scrape_page tool to get the current page content.",
    )
    addLog("info", "Action: scrape_page")
    simulateElementScan("ssl-config")
    await new Promise((resolve) => setTimeout(resolve, 2000))

    addLog("info", "Scraping page with query: scrape")
    addLog("info", "Getting text content...")
    addLog("info", "Retrieved 1030 characters of text")
    addLog("info", "Getting HTML content...")
    addLog("info", "Retrieved 28929 characters of HTML")
    addLog("info", "Found 1 forms, 2 inputs, 3 buttons")
    await new Promise((resolve) => setTimeout(resolve, 1500))

    setScanStatus("Testing for SQL injection...")
    addLog(
      "info",
      "The page has a login form with two input fields for username and password. Now, I will test for SQL injection vulnerability.",
    )
    addLog("info", "Action: input_textbox")
    addLog("info", "Inputting text with query: #username,admin")
    simulateElementScan("search-input")
    await new Promise((resolve) => setTimeout(resolve, 2000))

    addLog("info", "Successfully typed 'admin' into element with selector '#username'")
    addLog("info", "Now entering malicious password to test for SQL injection.")
    addLog("info", "Action: input_textbox")
    addLog("info", "Inputting text with query: #password,' OR 1=1--")
    await new Promise((resolve) => setTimeout(resolve, 1500))

    const xssFinding: SecurityFinding = {
      id: "2",
      title: "Potential XSS Vulnerability",
      severity: "high",
      description: "User input is not properly sanitized in search functionality.",
      location: "/search?q=",
      timestamp: new Date(),
      element: "search-input",
    }
    setFindings((prev) => [...prev, xssFinding])
    addLog("error", "🚨 XSS vulnerability detected in search functionality")

    await new Promise((resolve) => setTimeout(resolve, 1000))
    setScanStatus("Checking form security...")
    addLog("info", "Action: click_button")
    addLog("info", "Clicking button with query: button:has-text('Login')")
    addLog("info", "Successfully clicked element with selector 'button:has-text('Login')'")
    simulateElementScan("contact-form")
    await new Promise((resolve) => setTimeout(resolve, 2000))

    const csrfFinding: SecurityFinding = {
      id: "3",
      title: "Missing CSRF Protection",
      severity: "medium",
      description: "Forms do not include CSRF tokens for protection against cross-site request forgery.",
      location: "/contact-form",
      timestamp: new Date(),
      element: "contact-form",
    }
    setFindings((prev) => [...prev, csrfFinding])
    addLog("warning", "⚠️ Missing CSRF protection detected")

    await new Promise((resolve) => setTimeout(resolve, 1000))
    setScanStatus("Analyzing security headers...")
    addLog("info", "The form has been submitted. Now checking for signs of successful login.")
    addLog("info", "Action: scrape_page")
    addLog("info", "Scraping page with query: scrape")
    simulateElementScan("headers")
    await new Promise((resolve) => setTimeout(resolve, 1500))

    addLog("info", "Login Failed. Invalid credentials. Try admin/admin for demo access.")
    addLog("info", "The login was not successful, indicating the SQL injection attempt was not successful.")

    const headerFinding: SecurityFinding = {
      id: "4",
      title: "Missing Security Headers",
      severity: "low",
      description: "Important security headers like Content-Security-Policy are missing.",
      location: "HTTP Headers",
      timestamp: new Date(),
      element: "headers",
    }
    setFindings((prev) => [...prev, headerFinding])
    addLog("info", "📋 Security headers analysis complete")

    await new Promise((resolve) => setTimeout(resolve, 1000))
    setScanStatus("Finalizing assessment...")
    addLog("info", "============================================================")
    addLog("success", "🏁 FINAL ASSESSMENT RESULT:")
    addLog("info", "============================================================")
    addLog("info", `The login page at ${currentUrl} shows mixed security posture with ${3} vulnerabilities identified.`)
    addLog("info", "============================================================")
    addLog("success", "🧹 Browser session closed")

    setScanStatus("Scan completed")
    setIsScanning(false)
  }

  useEffect(() => {
    simulateScan()
  }, [])

  const handleNewScan = () => {
    if (currentUrl.trim()) {
      simulateScan()
    }
  }

  const getHighlightColor = (element: string) => {
    if (scanningElements.includes(element)) return "border-blue-500 bg-blue-500/20"
    if (hoveredFinding?.element === element) {
      switch (hoveredFinding.severity) {
        case "high":
          return "border-red-500 bg-red-500/20"
        case "medium":
          return "border-yellow-500 bg-yellow-500/20"
        case "low":
          return "border-blue-500 bg-blue-500/20"
        default:
          return ""
      }
    }
    return ""
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-border bg-card/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" onClick={onBack} className="flex items-center space-x-2">
                <ArrowLeft className="h-4 w-4" />
                <span>Back</span>
              </Button>
              <div className="h-6 w-px bg-border" />
              <h1 className="text-lg font-semibold">Security Scan</h1>
            </div>

            {/* Status Indicator */}
            <div className="flex items-center space-x-2">
              {isScanning && (
                <>
                  <Activity className="h-4 w-4 text-blue-500 animate-pulse" />
                  <span className="text-sm text-muted-foreground">{scanStatus}</span>
                </>
              )}
              {!isScanning && findings.length > 0 && (
                <span className="text-sm text-muted-foreground">Scan completed - {findings.length} findings</span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="flex h-[calc(100vh-73px)] relative">
        {/* Main Content - Website iframe */}
        <div className="flex-1 flex flex-col">
          <div className="p-4 border-b border-border bg-card/30">
            <div className="flex items-center space-x-2">
              <div className="flex items-center bg-background border border-border rounded-full px-4 py-2 flex-1 min-h-[44px]">
                <Shield className="h-4 w-4 text-muted-foreground mr-3" />
                <Input
                  type="text"
                  value={currentUrl}
                  onChange={(e) => setCurrentUrl(e.target.value)}
                  className="border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 text-sm flex-1"
                  placeholder="Enter website URL"
                />
                <Button size="sm" onClick={handleNewScan} disabled={isScanning} className="ml-2 rounded-full">
                  <Search className="h-3 w-3 mr-1" />
                  Scan
                </Button>
              </div>
            </div>
          </div>

          <div className="flex-1 bg-background/50 relative">
            <iframe
              src={currentUrl}
              className="w-full h-full border-0"
              title="Target Website"
              sandbox="allow-scripts allow-same-origin"
            />

            {/* Scanning overlays */}
            <div className="absolute inset-4 pointer-events-none">
              {/* SSL Config overlay */}
              <motion.div
                className={`absolute top-0 left-0 w-full h-16 border-2 rounded ${getHighlightColor("ssl-config")}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: getHighlightColor("ssl-config") ? 1 : 0 }}
                transition={{ duration: 0.3 }}
              />

              {/* Search input overlay */}
              <motion.div
                className={`absolute top-1/3 left-1/4 w-1/2 h-12 border-2 rounded ${getHighlightColor("search-input")}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: getHighlightColor("search-input") ? 1 : 0 }}
                transition={{ duration: 0.3 }}
              />

              {/* Contact form overlay */}
              <motion.div
                className={`absolute bottom-1/4 right-1/4 w-1/3 h-32 border-2 rounded ${getHighlightColor("contact-form")}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: getHighlightColor("contact-form") ? 1 : 0 }}
                transition={{ duration: 0.3 }}
              />

              {/* Headers overlay */}
              <motion.div
                className={`absolute top-0 right-0 w-1/4 h-8 border-2 rounded ${getHighlightColor("headers")}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: getHighlightColor("headers") ? 1 : 0 }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>
        </div>

        {/* Floating Toggle Button */}
        <motion.div
          className="absolute top-1/2 right-0 z-10 transform -translate-y-1/2"
          style={{ right: isLogOpen ? "384px" : "0px" }}
          animate={{ right: isLogOpen ? "384px" : "0px" }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
        >
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsLogOpen(!isLogOpen)}
            className="rounded-l-lg rounded-r-none border-r-0 bg-background/95 backdrop-blur shadow-lg hover:bg-background/100 h-12 px-2"
          >
            {isLogOpen ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </motion.div>

        {/* Analysis Panel - Slide in/out */}
        <motion.div
          className="w-96 border-l border-border bg-card/50 overflow-hidden"
          initial={{ width: isLogOpen ? "384px" : "0px" }}
          animate={{ width: isLogOpen ? "384px" : "0px" }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
        >
          {isLogOpen && (
            <ScanLog
              logs={logs}
              findings={findings}
              onFindingHover={setHoveredFinding}
              onLogClick={setSelectedLog}
              selectedLog={selectedLog}
            />
          )}
        </motion.div>
      </div>
    </motion.div>
  )
}

export default ScanInterface
