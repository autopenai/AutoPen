"use client";

import type React from "react";
import { useEffect, useRef } from "react";
import { Terminal, AlertCircle, AlertTriangle, Shield } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import type { PentestEvent, TestResult, EventType } from "@/types/pentest";

interface ScanLogProps {
  events: PentestEvent[];
  results: TestResult[];
  onResultHover?: (result: TestResult | null) => void;
  onEventClick?: (event: PentestEvent | null) => void;
  selectedEvent?: PentestEvent | null;
}

const ScanLog: React.FC<ScanLogProps> = ({
  events,
  results,
  onResultHover,
  onEventClick,
  selectedEvent,
}) => {
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const eventsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new events are added
  useEffect(() => {
    if (eventsEndRef.current) {
      eventsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [events]);

  const getEventIcon = (eventType: EventType) => {
    switch (eventType) {
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-400" />;
      case "vulnerability":
        return <AlertTriangle className="h-4 w-4 text-yellow-400" />;
      case "load":
      case "click":
      case "input":
      case "info":
      default:
        return null; // No icon for regular info logs
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "high":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case "medium":
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case "low":
        return <Shield className="h-4 w-4 text-blue-500" />;
      default:
        return <Shield className="h-4 w-4 text-blue-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "high":
        return "bg-red-500/10 text-red-400 border-red-500/20";
      case "medium":
        return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
      case "low":
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      default:
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
    }
  };

  const groupedResults = results.reduce((acc, result) => {
    const severity = result.severity.toLowerCase();
    if (!acc[severity]) {
      acc[severity] = [];
    }
    acc[severity].push(result);
    return acc;
  }, {} as Record<string, TestResult[]>);

  const formatEventDetails = (event: PentestEvent) => {
    if (!event.details) return null;

    // Handle the API schema structure: details: { message: string | null, data: object | null }
    const { message, data } = event.details as {
      message?: string | null;
      data?: any | null;
    };

    const formattedDetails: string[] = [];

    // Add message if it exists
    if (message) {
      formattedDetails.push(`Message: ${message}`);
    }

    // Handle data object based on event type
    if (data) {
      if (event.event_type === "load" && data.url) {
        formattedDetails.push(`URL: ${data.url}`);
      } else if (event.event_type === "input" && data.field) {
        formattedDetails.push(`Field: ${data.field}`);
        if (data.test_value) {
          formattedDetails.push(`Test Value: ${data.test_value}`);
        }
      } else if (event.event_type === "info" && data.url) {
        formattedDetails.push(`Target URL: ${data.url}`);
      } else if (
        event.event_type === "info" &&
        data.vulnerabilities_found !== undefined
      ) {
        formattedDetails.push(
          `Vulnerabilities Found: ${data.vulnerabilities_found}`
        );
      } else {
        // For any other data, show as JSON
        formattedDetails.push(`Data: ${JSON.stringify(data, null, 2)}`);
      }
    }

    return formattedDetails.length > 0 ? formattedDetails.join("\n") : null;
  };

  return (
    <div className="h-full flex flex-col">
      <Card className="h-full bg-transparent border-0 rounded-none flex-1">
        <CardContent className="p-0 h-full">
          <ScrollArea className="h-full" ref={scrollAreaRef}>
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
                      {events.map((event, index) => {
                        const icon = getEventIcon(event.event_type);
                        const details = formatEventDetails(event);
                        const timestamp = new Date(
                          event.timestamp
                        ).toLocaleTimeString();

                        return (
                          <div
                            key={`${event.event_type}-${index}`}
                            className="flex items-start space-x-3 p-2 rounded hover:bg-background/30 transition-colors cursor-pointer"
                            onClick={() => onEventClick?.(event)}
                            onMouseEnter={() => {
                              // Handle vulnerability events that might have vulnerability data in details.data
                              if (
                                event.event_type === "vulnerability" &&
                                event.details?.data
                              ) {
                                const vulnData = event.details.data;
                                if (vulnData.title) {
                                  const matchingResult = results.find(
                                    (r) => r.title === vulnData.title
                                  );
                                  if (matchingResult)
                                    onResultHover?.(matchingResult);
                                }
                              }
                            }}
                            onMouseLeave={() => onResultHover?.(null)}
                          >
                            <div className="flex-shrink-0 mt-0.5 w-4 h-4 flex items-center justify-center">
                              {icon}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between">
                                <p className="text-sm text-foreground leading-relaxed">
                                  {event.message}
                                </p>
                                <span className="text-xs text-muted-foreground ml-2">
                                  {timestamp}
                                </span>
                              </div>
                              {details && (
                                <pre className="text-xs text-muted-foreground mt-1 leading-relaxed font-mono whitespace-pre-wrap">
                                  {details}
                                </pre>
                              )}
                            </div>
                          </div>
                        );
                      })}
                      {/* Invisible element to scroll to */}
                      <div ref={eventsEndRef} />
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>

              {/* Security Findings Accordion */}
              <Accordion
                type="single"
                collapsible
                defaultValue="security-findings"
              >
                <AccordionItem value="security-findings" className="border-0">
                  <AccordionTrigger className="flex items-center justify-between w-full p-4 border-b border-border bg-card/50 hover:bg-card/70 transition-colors">
                    <div className="flex items-center space-x-2">
                      <Shield className="h-5 w-5" />
                      <span className="text-lg font-semibold">
                        Security Findings ({results.length})
                      </span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="p-0">
                    <div className="p-4 space-y-4">
                      {/* Summary Cards */}
                      <div className="grid grid-cols-3 gap-2">
                        {(["high", "medium", "low"] as const).map(
                          (severity) => (
                            <div
                              key={severity}
                              className="p-3 bg-background/30 rounded border border-border/30"
                            >
                              <div className="flex items-center space-x-2">
                                {getSeverityIcon(severity)}
                                <div>
                                  <p className="text-xs font-medium capitalize">
                                    {severity}
                                  </p>
                                  <p className="text-lg font-bold">
                                    {groupedResults[severity]?.length || 0}
                                  </p>
                                </div>
                              </div>
                            </div>
                          )
                        )}
                      </div>

                      {/* Individual Findings */}
                      <div className="space-y-3">
                        {results.map((result, index) => (
                          <Accordion
                            key={`result-${index}`}
                            type="single"
                            collapsible
                          >
                            <AccordionItem
                              value={`result-${index}`}
                              className="border border-border/50 rounded-lg"
                            >
                              <AccordionTrigger
                                onMouseEnter={() => onResultHover?.(result)}
                                onMouseLeave={() => onResultHover?.(null)}
                                className="p-3 hover:bg-background/70 transition-colors"
                              >
                                <div className="flex items-start justify-between w-full">
                                  <div className="flex items-start space-x-2 flex-1">
                                    {getSeverityIcon(result.severity)}
                                    <div className="text-left">
                                      <span className="text-sm font-medium">
                                        {result.title}
                                      </span>
                                      <p className="text-xs text-muted-foreground mt-1">
                                        {result.description.substring(0, 100)}
                                        ...
                                      </p>
                                      <div className="flex items-center justify-between text-xs text-muted-foreground mt-2">
                                        <span>{result.vulnerability_type}</span>
                                      </div>
                                    </div>
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    <Badge
                                      className={getSeverityColor(
                                        result.severity
                                      )}
                                      variant="outline"
                                    >
                                      {result.severity.toUpperCase()}
                                    </Badge>
                                  </div>
                                </div>
                              </AccordionTrigger>
                              <AccordionContent className="p-3 pt-0">
                                <div className="space-y-3">
                                  <div className="text-sm">
                                    <p className="font-medium mb-2">
                                      Full Description:
                                    </p>
                                    <p className="text-muted-foreground leading-relaxed">
                                      {result.description}
                                    </p>
                                  </div>
                                </div>
                              </AccordionContent>
                            </AccordionItem>
                          </Accordion>
                        ))}
                      </div>

                      {results.length === 0 && (
                        <div className="text-center py-8">
                          <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                          <p className="text-muted-foreground">
                            No security findings yet
                          </p>
                          <p className="text-sm text-muted-foreground">
                            Scan in progress...
                          </p>
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
  );
};

export default ScanLog;
