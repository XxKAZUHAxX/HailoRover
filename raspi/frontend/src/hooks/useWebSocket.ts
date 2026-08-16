import { useEffect, useRef, useState, useCallback } from "react";
import { StreamClient, getStreamUrl } from "../lib/ws-client";
import { renderDetections } from "../lib/bbox-renderer";
import type { Detection, SystemHealth } from "../types";

interface UseWebSocketReturn {
  videoRef: React.RefObject<HTMLImageElement>;
  canvasRef: React.RefObject<HTMLCanvasElement>;
  connected: boolean;
  detections: Detection[];
  fps: number;
  inferenceMs: number;
  systemHealth: SystemHealth | null;
  fetchHealth: () => Promise<void>;
}

export function useWebSocket(): UseWebSocketReturn {
  const videoRef = useRef<HTMLImageElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [connected, setConnected] = useState(false);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [fps, setFps] = useState(0);
  const [inferenceMs, setInferenceMs] = useState(0);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);

  const clientRef = useRef<StreamClient | null>(null);

  useEffect(() => {
    const url = getStreamUrl();
    const client = new StreamClient(url);
    clientRef.current = client;

    client.setOnImage((blob: Blob) => {
      const url = URL.createObjectURL(blob);
      if (videoRef.current) {
        // Revoke previous blob to prevent memory leak
        const prev = videoRef.current.src;
        videoRef.current.src = url;
        if (prev && prev.startsWith("blob:")) {
          URL.revokeObjectURL(prev);
        }
      }
    });

    client.setOnDetection((frame) => {
      setDetections(frame.objects);
      setFps(frame.fps);
      setInferenceMs(frame.inference_ms ?? 0);

      // Draw bboxes on canvas overlay
      if (canvasRef.current && videoRef.current) {
        const canvas = canvasRef.current;
        const video = videoRef.current;
        canvas.width = video.naturalWidth || video.clientWidth;
        canvas.height = video.naturalHeight || video.clientHeight;
        const ctx = canvas.getContext("2d");
        if (ctx) {
          renderDetections(ctx, frame.objects, canvas.width, canvas.height);
        }
      }
    });

    client.setOnStatus(setConnected);
    client.connect();

    return () => {
      client.disconnect();
    };
  }, []);

  const fetchHealth = useCallback(async () => {
    try {
      const res = await fetch("/api/system/health");
      if (res.ok) {
        const data: SystemHealth = await res.json();
        setSystemHealth(data);
      }
    } catch {
      // Server may be unavailable
    }
  }, []);

  // Poll health every 5s
  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 5000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  return {
    videoRef,
    canvasRef,
    connected,
    detections,
    fps,
    inferenceMs,
    systemHealth,
    fetchHealth,
  };
}
