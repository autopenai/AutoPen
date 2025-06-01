"use client";

import type React from "react";
import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Search,
  Shield,
  Activity,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import ScanLog from "./ScanLog";
import type { PentestEvent, TestResult, Test } from "@/types/pentest";
import { startNewTest, getTestById, subscribeToTestEvents } from "@/lib/api";

interface ScanInterfaceProps {
  initialUrl: string;
  testId?: string;
  onBack: () => void;
}

interface ApiResult {
  severity: string;
  type: string;
  title: string;
  description: string;
}

const ScanInterface: React.FC<ScanInterfaceProps> = ({
  initialUrl,
  testId,
  onBack,
}) => {
  const [currentUrl, setCurrentUrl] = useState(initialUrl);
  const [isLogOpen, setIsLogOpen] = useState(true);
  const [test, setTest] = useState<Test | null>(null);
  const [events, setEvents] = useState<PentestEvent[]>([]);
  const [results, setResults] = useState<TestResult[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [hoveredResult, setHoveredResult] = useState<TestResult | null>(null);
  const [scanningElements, setScanningElements] = useState<string[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<PentestEvent | null>(null);
  const [currentTestId, setCurrentTestId] = useState<string | undefined>(
    testId
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch test data
  const fetchTestData = useCallback(async (id: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const testData = await getTestById(id);

      if (testData) {
        setTest(testData);
        setEvents(testData.events || []);
        setResults(testData.results || []);
        setIsScanning(
          testData.status === "in_progress" ||
            testData.status === "running" ||
            testData.status === "active"
        );
      } else {
        setError("Test not found");
      }
    } catch (error) {
      console.error("Error fetching test data:", error);
      setError(
        error instanceof Error ? error.message : "Failed to fetch test data"
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Replace SSE subscription with polling
  useEffect(() => {
    if (!currentTestId) return;

    // Initial fetch
    fetchTestData(currentTestId);

    // Set up polling interval
    const pollInterval = setInterval(() => {
      fetchTestData(currentTestId);
    }, 2000); // Poll every 2 seconds

    // Cleanup interval on unmount or when testId changes
    return () => {
      clearInterval(pollInterval);
    };
  }, [currentTestId, fetchTestData]);

  // Stop polling when scan is completed
  useEffect(() => {
    if (test?.status === "completed" || test?.status === "failed") {
      setIsScanning(false);
    }
  }, [test?.status]);

  const handleNewScan = async () => {
    if (!currentUrl.trim() || isScanning) return;

    setEvents([]);
    setResults([]);
    setIsScanning(true);
    setIsLoading(true);
    setError(null);

    try {
      const response = await startNewTest(currentUrl);

      if (response && response.test_id) {
        setCurrentTestId(response.test_id);
        // The SSE subscription will be set up by the useEffect
      } else {
        setError("Failed to start scan - no test ID returned");
        setIsScanning(false);
      }
    } catch (error) {
      console.error("Error starting new test:", error);
      setError(error instanceof Error ? error.message : "Failed to start scan");
      setIsScanning(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleElementScan = useCallback((element: string) => {
    setScanningElements((prev) => [...prev, element]);
    setTimeout(() => {
      setScanningElements((prev) => prev.filter((e) => e !== element));
    }, 2000);
  }, []);

  useEffect(() => {
    if (hoveredResult?.element) {
      handleElementScan(hoveredResult.element);
    }
  }, [hoveredResult, handleElementScan]);

  const getHighlightColor = (element: string) => {
    if (scanningElements.includes(element))
      return "border-blue-500 bg-blue-500/20";
    if (hoveredResult?.element === element) {
      switch (hoveredResult.severity.toLowerCase()) {
        case "high":
          return "border-red-500 bg-red-500/20";
        case "medium":
          return "border-yellow-500 bg-yellow-500/20";
        case "low":
          return "border-blue-500 bg-blue-500/20";
        default:
          return "";
      }
    }
    return "";
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen bg-background"
    >
      {/* Header */}
      <div className="border-b border-border bg-card/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={onBack}
                className="flex items-center space-x-2"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Back</span>
              </Button>
              <div className="h-6 w-px bg-border" />
              <h1 className="text-lg font-semibold">Security Scan</h1>
              {currentTestId && (
                <span className="text-xs bg-blue-500/10 text-blue-400 px-2 py-1 rounded">
                  Test ID: {currentTestId}
                </span>
              )}
            </div>

            {/* Status Indicator */}
            <div className="flex items-center space-x-2">
              {error && (
                <div className="flex items-center space-x-1 text-red-400">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-sm">Error</span>
                </div>
              )}
              {isLoading && (
                <>
                  <Activity className="h-4 w-4 text-blue-500 animate-pulse" />
                  <span className="text-sm text-muted-foreground">
                    Loading...
                  </span>
                </>
              )}
              {!isLoading && isScanning && (
                <>
                  <Activity className="h-4 w-4 text-blue-500 animate-pulse" />
                  <span className="text-sm text-muted-foreground">
                    {test?.current_phase || "Scanning..."}
                    {test?.progress_percentage !== undefined &&
                      ` (${test.progress_percentage}%)`}
                  </span>
                </>
              )}
              {!isLoading && !isScanning && results.length > 0 && (
                <span className="text-sm text-muted-foreground">
                  Scan completed - {results.length} findings
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-500/10 border-b border-red-500/20 px-4 py-2">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 text-red-500" />
              <span className="text-sm text-red-500">{error}</span>
            </div>
          </div>
        </div>
      )}

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
                <Button
                  size="sm"
                  onClick={handleNewScan}
                  disabled={isScanning || isLoading}
                  className="ml-2 rounded-full"
                >
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
              sandbox="allow-forms allow-scripts allow-same-origin"
            />

            {/* Scanning Animation Overlay */}
            {isScanning && (
              <div className="absolute inset-0 pointer-events-none z-10">
                {/* Dimmed overlay */}
                <motion.div
                  className="absolute inset-0 bg-black/30 backdrop-blur-[1px]"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.5 }}
                />

                {/* Horizontal scanning line (white) - top to bottom and back */}
                <motion.div
                  className="absolute left-0 right-0 h-3 bg-gradient-to-r from-transparent via-white to-transparent shadow-lg shadow-white/50"
                  initial={{ top: "0%", opacity: 0 }}
                  animate={{
                    top: ["0%", "100%", "0%"],
                    opacity: [0, 1, 1, 0],
                  }}
                  transition={{
                    duration: 4,
                    repeat: Infinity,
                    ease: "easeInOut",
                    times: [0, 0.45, 0.55, 1],
                  }}
                />

                {/* Vertical scanning line (white) - left to right and back */}
                <motion.div
                  className="absolute top-0 bottom-0 w-3 bg-gradient-to-b from-transparent via-white to-transparent shadow-lg shadow-white/50"
                  initial={{ left: "0%", opacity: 0 }}
                  animate={{
                    left: ["0%", "100%", "0%"],
                    opacity: [0, 1, 1, 0],
                  }}
                  transition={{
                    duration: 4,
                    repeat: Infinity,
                    ease: "easeInOut",
                    times: [0, 0.45, 0.55, 1],
                    delay: 2, // Start after horizontal line completes first pass
                  }}
                />

                {/* Grid scanning effect */}
                <motion.div
                  className="absolute inset-0"
                  style={{
                    backgroundImage: `
                      linear-gradient(rgba(0, 255, 255, 0.1) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(0, 255, 255, 0.1) 1px, transparent 1px)
                    `,
                    backgroundSize: "50px 50px",
                  }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: [0, 0.3, 0] }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    repeatDelay: 2,
                  }}
                />

                {/* Scanning status indicator */}
                <motion.div
                  className="absolute top-4 left-4 bg-black/80 backdrop-blur text-cyan-400 px-3 py-2 rounded-lg text-sm font-mono flex items-center space-x-2"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
                  <span className="text-white">SCANNING IN PROGRESS</span>
                </motion.div>
              </div>
            )}

            {/* Existing scanning overlays for hover effects */}
            <div className="absolute inset-4 pointer-events-none">
              <motion.div
                className={`absolute top-0 left-0 w-full h-16 border-2 rounded ${getHighlightColor(
                  "ssl-config"
                )}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: getHighlightColor("ssl-config") ? 1 : 0 }}
                transition={{ duration: 0.3 }}
              />
              <motion.div
                className={`absolute top-1/3 left-1/4 w-1/2 h-12 border-2 rounded ${getHighlightColor(
                  "search-input"
                )}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: getHighlightColor("search-input") ? 1 : 0 }}
                transition={{ duration: 0.3 }}
              />
              <motion.div
                className={`absolute bottom-1/4 right-1/4 w-1/3 h-32 border-2 rounded ${getHighlightColor(
                  "contact-form"
                )}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: getHighlightColor("contact-form") ? 1 : 0 }}
                transition={{ duration: 0.3 }}
              />
              <motion.div
                className={`absolute top-0 right-0 w-1/4 h-8 border-2 rounded ${getHighlightColor(
                  "headers"
                )}`}
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
            {isLogOpen ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </motion.div>

        {/* Analysis Panel */}
        <motion.div
          className="w-96 border-l border-border bg-card/50 overflow-hidden"
          initial={{ width: isLogOpen ? "384px" : "0px" }}
          animate={{ width: isLogOpen ? "384px" : "0px" }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
        >
          {isLogOpen && (
            <ScanLog
              events={events}
              results={results}
              onResultHover={setHoveredResult}
              onEventClick={setSelectedEvent}
              selectedEvent={selectedEvent}
            />
          )}
        </motion.div>
      </div>
    </motion.div>
  );
};

export default ScanInterface;
