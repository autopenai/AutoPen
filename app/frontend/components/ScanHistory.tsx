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
      <div className="flex items-center space-x-2 mb-4">
        <Clock className="h-5 w-5 text-muted-foreground" />
        <h2 className="text-xl font-semibold">Recent Scans</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
              <Card className="bg-card/50 border-border hover:bg-card/80 transition-colors h-full">
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between space-x-4">
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-sm font-medium truncate max-w-full">{scan.url}</CardTitle>
                      <CardDescription className="text-xs text-muted-foreground truncate">
                        {scan.timestamp.toLocaleDateString()}
                      </CardDescription>
                    </div>
                    <div className="flex items-center space-x-2 flex-shrink-0">
                      {getSeverityIcon(severity)}
                      <Badge variant="outline" className="text-xs whitespace-nowrap">
                        {totalFindings} findings
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0 pb-3">
                  <div className="flex items-center space-x-2 text-xs">
                    {scan.findings.high > 0 && (
                      <div className="flex items-center space-x-1">
                        <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                        <span className="text-orange-400">{scan.findings.high}</span>
                      </div>
                    )}
                    {scan.findings.medium > 0 && (
                      <div className="flex items-center space-x-1">
                        <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                        <span className="text-yellow-400">{scan.findings.medium}</span>
                      </div>
                    )}
                    {scan.findings.low > 0 && (
                      <div className="flex items-center space-x-1">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <span className="text-blue-400">{scan.findings.low}</span>
                      </div>
                    )}
                  </div>
                  {/* Security Findings Tab */}
                  {scan.results && scan.results.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {scan.results.map((finding: any, idx: number) => (
                        <div key={idx} className="p-2 rounded bg-muted/30 border text-xs">
                          <div>
                            <span className="font-semibold">{finding.title}</span>
                            <span className={`ml-2 px-2 py-0.5 rounded text-white ${finding.severity === "HIGH" ? "bg-red-500" : finding.severity === "MEDIUM" ? "bg-yellow-500" : "bg-blue-500"}`}>
                              {finding.severity}
                            </span>
                          </div>
                          <div className="italic">{finding.type}</div>
                          <div>{finding.description}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )
        })}

        {history.length === 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-8 col-span-3">
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
