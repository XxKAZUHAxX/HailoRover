/**
 * WebSocket client for receiving MJPEG frames and detection data.
 *
 * The server sends two frame types on a single WebSocket:
 *   - Binary frames: JPEG images
 *   - Text frames: JSON detection arrays
 *
 * Detection frames are correlated with the most recent image frame.
 */

import type { DetectionFrame } from "../types";

type ImageCallback = (blob: Blob) => void;
type DetectionCallback = (data: DetectionFrame) => void;
type StatusCallback = (connected: boolean) => void;

const RECONNECT_DELAY_MS = 2000;
const MAX_RECONNECT_DELAY_MS = 15000;

export class StreamClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = RECONNECT_DELAY_MS;
  private shouldReconnect = true;

  private onImage: ImageCallback | null = null;
  private onDetection: DetectionCallback | null = null;
  private onStatus: StatusCallback | null = null;

  constructor(url: string) {
    this.url = url;
  }

  connect(): void {
    this.shouldReconnect = true;
    this.reconnectDelay = RECONNECT_DELAY_MS;
    this._connect();
  }

  disconnect(): void {
    this.shouldReconnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  setOnImage(cb: ImageCallback): void {
    this.onImage = cb;
  }

  setOnDetection(cb: DetectionCallback): void {
    this.onDetection = cb;
  }

  setOnStatus(cb: StatusCallback): void {
    this.onStatus = cb;
  }

  private _connect(): void {
    try {
      this.ws = new WebSocket(this.url);
      this.ws.binaryType = "blob";

      this.ws.onopen = () => {
        this.reconnectDelay = RECONNECT_DELAY_MS;
        this.onStatus?.(true);
      };

      this.ws.onmessage = (event: MessageEvent) => {
        if (event.data instanceof Blob) {
          this.onImage?.(event.data);
        } else if (typeof event.data === "string") {
          try {
            const parsed = JSON.parse(event.data) as DetectionFrame;
            if (parsed.type === "detections") {
              this.onDetection?.(parsed);
            }
          } catch {
            // Ignore malformed JSON
          }
        }
      };

      this.ws.onclose = () => {
        this.onStatus?.(false);
        if (this.shouldReconnect) {
          this.reconnectTimer = setTimeout(() => {
            this._connect();
          }, this.reconnectDelay);
          this.reconnectDelay = Math.min(
            this.reconnectDelay * 1.5,
            MAX_RECONNECT_DELAY_MS
          );
        }
      };

      this.ws.onerror = () => {
        // onclose will fire after this — reconnect handled there
      };
    } catch {
      // Connection failed — schedule reconnect
      if (this.shouldReconnect) {
        this.reconnectTimer = setTimeout(() => {
          this._connect();
        }, this.reconnectDelay);
      }
    }
  }
}

/**
 * Build the WebSocket URL based on the current page location.
 * In development, Vite proxies /ws to the backend.
 * In production, same-origin — just swap protocol to ws/wss.
 */
export function getStreamUrl(): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/stream`;
}
