"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Shield } from "lucide-react"
import AddressBar from "@/components/AddressBar"
import ScanHistoryComponent from "@/components/ScanHistory"
import ScanInterface from "@/components/ScanInterface"
import type { ScanHistory } from "@/types/pentest"

export default function HomePage() {
  const [currentView, setCurrentView] = useState<"home" | "scanning">("home")
  const [targetUrl, setTargetUrl] = useState("")
  const [scanHistory] = useState<ScanHistory[]>([
    {
      id: "1",
      url: "example.com",
      timestamp: new Date(Date.now() - 86400000), // 1 day ago
      findings: { high: 2, medium: 3, low: 1 },
    },
    {
      id: "2",
      url: "testsite.org",
      timestamp: new Date(Date.now() - 172800000), // 2 days ago
      findings: { high: 0, medium: 2, low: 4 },
    },
    {
      id: "3",
      url: "demo.com",
      timestamp: new Date(Date.now() - 259200000), // 3 days ago
      findings: { high: 1, medium: 1, low: 2 },
    },
  ])

  const handleScan = (url: string) => {
    setTargetUrl(url)
    setCurrentView("scanning")
  }

  const handleBack = () => {
    setCurrentView("home")
    setTargetUrl("")
  }

  if (currentView === "scanning") {
    return <ScanInterface initialUrl={targetUrl} onBack={handleBack} />
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
                  PenTest Agent
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
              <AddressBar onScan={handleScan} />
            </motion.div>
          </div>
        </div>
      </div>

      {/* Scan History Section */}
      <div className="border-t border-border bg-card/20 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.7 }}
          >
            <ScanHistoryComponent history={scanHistory} onSelectScan={(scan) => handleScan(scan.url)} />
          </motion.div>
        </div>
      </div>
    </div>
  )
}
