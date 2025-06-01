"use client"

import type React from "react"
import { useState } from "react"
import { motion } from "framer-motion"
import { Search, Shield, ChevronLeft, ChevronRight, RotateCcw, Lock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface AddressBarProps {
  onScan: (url: string) => void
  isScanning?: boolean
}

const AddressBar: React.FC<AddressBarProps> = ({ onScan, isScanning = false }) => {
  const [url, setUrl] = useState("")

  const handleScan = () => {
    if (url.trim()) {
      onScan(url.trim())
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-5xl mx-auto mb-12">
      <div className="bg-white rounded-t-lg shadow-2xl">
        {/* Browser Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-gray-100 rounded-t-lg border-b border-gray-200">
          {/* Window Controls */}
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          </div>
        </div>

        {/* Browser Toolbar */}
        <form
          onSubmit={e => {
            e.preventDefault();
            handleScan();
          }}
          className="flex items-center gap-3 px-4 py-3 bg-white border-b border-gray-200"
        >
          {/* Navigation Buttons */}
          <div className="flex items-center gap-1">
            <button className="p-2 hover:bg-gray-100 rounded-full disabled:opacity-50" disabled>
              <ChevronLeft className="w-4 h-4 text-gray-600" />
            </button>
            <button className="p-2 hover:bg-gray-100 rounded-full disabled:opacity-50" disabled>
              <ChevronRight className="w-4 h-4 text-gray-600" />
            </button>
            <button className="p-2 hover:bg-gray-100 rounded-full" type="button">
              <RotateCcw className="w-4 h-4 text-gray-600" />
            </button>
          </div>

          {/* Address Bar */}
          <div className="flex-1 relative">
            <div className="flex items-center bg-gray-50 hover:bg-white border border-gray-300 hover:border-gray-400 rounded-full px-4 py-2 focus-within:border-blue-500 focus-within:bg-white transition-all duration-200 shadow-sm">
              {/* Security Indicator */}
              <div className="flex items-center gap-2 mr-3">
                <Lock className="w-4 h-4 text-gray-600" />
              </div>

              {/* URL Input */}
              <Input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Enter or paste a website URL to scan (e.g., https://example.com)"
                className="flex-1 bg-transparent border-0 text-gray-900 placeholder:text-gray-500 focus-visible:ring-0 focus-visible:ring-offset-0 text-xs font-mono"
                disabled={isScanning}
              />

              {/* Clear Button */}
              {url && (
                <span
                  onClick={() => setUrl("")}
                  className="ml-2 p-1 hover:bg-gray-200 rounded-full text-gray-500 hover:text-gray-700 transition-colors cursor-pointer"
                >
                  ×
                </span>
              )}
            </div>
          </div>

          {/* Scan Button */}
          <Button
            type="submit"
            disabled={!url.trim() || isScanning}
            className="bg-black hover:bg-gray-800 text-white px-6 py-2 rounded-full text-sm font-medium transition-all duration-200 disabled:opacity-50"
          >
            {isScanning ? (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Scanning...
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Search className="w-4 h-4" />
                Scan
              </div>
            )}
          </Button>
        </form>

        {/* Browser Content Area (empty, for layout) */}
        <div className="bg-white p-8 rounded-b-lg min-h-[40px]" />
      </div>
    </motion.div>
  )
}

export default AddressBar
