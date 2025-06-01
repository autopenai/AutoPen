"use client"

import type React from "react"
import { Terminal, AlertCircle, CheckCircle, AlertTriangle, Shield } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import type { LogEntry, SecurityFinding } from "@/types/pentest"

interface ScanLogProps {
  logs: LogEntry[]
  findings: SecurityFinding[]
  onFindingHover?: (finding: SecurityFinding | null) => void
  onLogClick?: (log: LogEntry | null) => void
  selectedLog?: LogEntry | null
}

const ScanLog: React.FC<ScanLogProps> = ({ logs, findings, onFindingHover, onLogClick, selectedLog }) => {
  const getLogIcon = (type: LogEntry["type"]) => {
    switch (type) {
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-400" />
      case "warning":
        return <AlertTriangle className="h-4 w-4 text-yellow-400" />
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-400" />
      case "info":
      default:
        return null // No icon for regular info logs
    }
  }

  const getSeverityIcon = (severity: SecurityFinding["severity"]) => {
    switch (severity) {
      case "high":
        return <AlertCircle className="h-4 w-4 text-red-500" />
      case "medium":
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />
      case "low":
        return <Shield className="h-4 w-4 text-blue-500" />
    }
  }

  const getSeverityColor = (severity: SecurityFinding["severity"]) => {
    switch (severity) {
      case "high":
        return "bg-red-500/10 text-red-400 border-red-500/20"
      case "medium":
        return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
      case "low":
        return "bg-blue-500/10 text-blue-400 border-blue-500/20"
    }
  }

  const groupedFindings = findings.reduce(
    (acc, finding) => {
      if (!acc[finding.severity]) {
        acc[finding.severity] = []
      }
      acc[finding.severity].push(finding)
      return acc
    },
    {} as Record<SecurityFinding["severity"], SecurityFinding[]>,
  )

  const mockCode = `<form action="/login" method="POST">
  <input type="text" name="username" />
  <input type="password" name="password" />
  <button type="submit">Login</button>
</form>`

  return (
    <div className="h-full flex flex-col">
      <Card className="h-full bg-transparent border-0 rounded-none flex-1">
        <CardContent className="p-0 h-full">
          <ScrollArea className="h-full">
            <div className="space-y-4">
              {/* Scan Log Accordion */}
              <Accordion type="single" collapsible defaultValue="scan-log">
                <AccordionItem value="scan-log" className="border-0">
                  <AccordionTrigger className="flex items-center justify-between w-full p-4 border-b border-border bg-card/50 hover:bg-card/70 transition-colors">
                    <div className="flex items-center space-x-2">
                      <Terminal className="h-5 w-5" />
                      <span className="text-lg font-semibold">Scan Log</span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="p-0">
                    <div className="p-4 space-y-2">
                      {logs.map((log, index) => {
                        const icon = getLogIcon(log.type)
                        return (
                          <div
                            key={log.id}
                            className="flex items-start space-x-3 p-2 rounded hover:bg-background/30 transition-colors cursor-pointer"
                            onClick={() => onLogClick?.(log)}
                            onMouseEnter={() => {
                              const associatedFinding = findings.find((f) => f.title === log.message)
                              if (associatedFinding) onFindingHover?.(associatedFinding)
                            }}
                            onMouseLeave={() => onFindingHover?.(null)}
                          >
                            {icon && <div className="flex-shrink-0 mt-0.5">{icon}</div>}
                            <div className="flex-1 min-w-0">
                              <p className="text-sm text-foreground leading-relaxed">{log.message}</p>
                              {log.details && (
                                <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{log.details}</p>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>

              {/* Security Findings Accordion */}
              <Accordion type="single" collapsible defaultValue="security-findings">
                <AccordionItem value="security-findings" className="border-0">
                  <AccordionTrigger className="flex items-center justify-between w-full p-4 border-b border-border bg-card/50 hover:bg-card/70 transition-colors">
                    <div className="flex items-center space-x-2">
                      <Shield className="h-5 w-5" />
                      <span className="text-lg font-semibold">Security Findings ({findings.length})</span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="p-0">
                    <div className="p-4 space-y-4">
                      {/* Summary Cards */}
                      <div className="grid grid-cols-3 gap-2">
                        {(["high", "medium", "low"] as const).map((severity) => (
                          <div key={severity} className="p-3 bg-background/30 rounded border border-border/30">
                            <div className="flex items-center space-x-2">
                              {getSeverityIcon(severity)}
                              <div>
                                <p className="text-xs font-medium capitalize">{severity}</p>
                                <p className="text-lg font-bold">{groupedFindings[severity]?.length || 0}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Individual Findings */}
                      <div className="space-y-3">
                        {findings.map((finding, index) => (
                          <Accordion key={finding.id} type="single" collapsible>
                            <AccordionItem value={finding.id} className="border border-border/50 rounded-lg">
                              <AccordionTrigger
                                onMouseEnter={() => onFindingHover?.(finding)}
                                onMouseLeave={() => onFindingHover?.(null)}
                                onClick={() =>
                                  onLogClick?.({
                                    id: finding.id,
                                    timestamp: finding.timestamp,
                                    type: "error",
                                    message: finding.title,
                                    details: finding.description,
                                  })
                                }
                                className="p-3 hover:bg-background/70 transition-colors"
                              >
                                <div className="flex items-start justify-between w-full">
                                  <div className="flex items-start space-x-2 flex-1">
                                    {getSeverityIcon(finding.severity)}
                                    <div className="text-left">
                                      <span className="text-sm font-medium">{finding.title}</span>
                                      <p className="text-xs text-muted-foreground mt-1">{finding.description}</p>
                                      <div className="flex items-center justify-between text-xs text-muted-foreground mt-2">
                                        <span>{finding.location}</span>
                                      </div>
                                    </div>
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    <Badge className={getSeverityColor(finding.severity)} variant="outline">
                                      {finding.severity.toUpperCase()}
                                    </Badge>
                                  </div>
                                </div>
                              </AccordionTrigger>
                              <AccordionContent className="p-3 pt-0">
                                <div className="bg-background/50 border border-border rounded-lg p-4">
                                  <pre className="text-xs text-foreground overflow-auto">
                                    <code>{mockCode}</code>
                                  </pre>
                                </div>
                              </AccordionContent>
                            </AccordionItem>
                          </Accordion>
                        ))}
                      </div>

                      {findings.length === 0 && (
                        <div className="text-center py-8">
                          <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                          <p className="text-muted-foreground">No security findings yet</p>
                          <p className="text-sm text-muted-foreground">Scan in progress...</p>
                        </div>
                      )}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}

export default ScanLog
