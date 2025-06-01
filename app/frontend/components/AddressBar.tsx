"use client"

import type React from "react"
import { useState } from "react"
import { motion } from "framer-motion"
import { Search, Shield } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface AddressBarProps {
  onScan: (url: string) => void
  isScanning?: boolean
}

const AddressBar: React.FC<AddressBarProps> = ({ onScan, isScanning = false }) => {
  const [url, setUrl] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (url.trim()) {
      onScan(url.trim())
    }
  }

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center bg-background border border-border rounded-full overflow-hidden min-h-[56px]">
          <div className="flex items-center pl-6 pr-3">
            <Shield className="h-5 w-5 text-muted-foreground" />
          </div>

          <Input
            type="text"
            placeholder="Enter website URL to scan (e.g., example.com)"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="flex-1 border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 text-foreground placeholder:text-muted-foreground text-base"
            disabled={isScanning}
          />

          <Button
            type="submit"
            disabled={!url.trim() || isScanning}
            className="m-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded-full px-6"
          >
            <Search className="h-4 w-4 mr-2" />
            {isScanning ? "Scanning..." : "Scan"}
          </Button>
        </div>
      </form>
    </motion.div>
  )
}

export default AddressBar
