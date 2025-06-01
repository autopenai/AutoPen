"use client"

import type React from "react"
import { motion } from "framer-motion"
import { Clock, Shield, AlertTriangle, AlertCircle } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { ScanHistory } from "@/types/pentest"

interface ScanHistoryProps {
  history: ScanHistory[]
  onSelectScan?: (scan: ScanHistory) => void
}

const ScanHistoryComponent: React.FC<ScanHistoryProps> = ({ history, onSelectScan }) => {
  const getTotalFindings = (findings: ScanHistory["findings"]) => {
    return findings.high + findings.medium + findings.low
  }

  const getHighestSeverity = (findings: ScanHistory["findings"]) => {
    if (findings.high > 0) return "high"
    if (findings.medium > 0) return "medium"
    if (findings.low > 0) return "low"
    return "none"
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "high":
        return <AlertCircle className="h-4 w-4 text-orange-400" />
      case "medium":
        return <AlertTriangle className="h-4 w-4 text-yellow-400" />
      case "low":
        return <Shield className="h-4 w-4 text-blue-400" />
      default:
        return <Shield className="h-4 w-4 text-green-400" />
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2 mb-6">
        <Clock className="h-5 w-5 text-muted-foreground" />
        <h2 className="text-xl font-semibold">Scan History</h2>
      </div>

      <div className="grid gap-4">
        {history.map((scan, index) => {
          const totalFindings = getTotalFindings(scan.findings)
          const severity = getHighestSeverity(scan.findings)

          return (
            <motion.div
              key={scan.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.02 }}
              className="cursor-pointer"
              onClick={() => onSelectScan?.(scan)}
            >
              <Card className="bg-card/50 border-border hover:bg-card/80 transition-colors">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-base font-medium">{scan.url}</CardTitle>
                      <CardDescription className="text-muted-foreground">
                        {scan.timestamp.toLocaleDateString()} at {scan.timestamp.toLocaleTimeString()}
                      </CardDescription>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getSeverityIcon(severity)}
                      <Badge variant="outline" className="text-xs">
                        {totalFindings} findings
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center space-x-4 text-sm">
                    {scan.findings.high > 0 && (
                      <div className="flex items-center space-x-1">
                        <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                        <span className="text-orange-400">{scan.findings.high} High</span>
                      </div>
                    )}
                    {scan.findings.medium > 0 && (
                      <div className="flex items-center space-x-1">
                        <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                        <span className="text-yellow-400">{scan.findings.medium} Medium</span>
                      </div>
                    )}
                    {scan.findings.low > 0 && (
                      <div className="flex items-center space-x-1">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <span className="text-blue-400">{scan.findings.low} Low</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )
        })}

        {history.length === 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-12">
            <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">No scans performed yet</p>
            <p className="text-sm text-muted-foreground">Start your first security scan above</p>
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default ScanHistoryComponent
