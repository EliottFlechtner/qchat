import { WS_BASE_URL } from "./config";

export type WsCallbacks = {
  onNotification: (text: string) => void;
  onStatus?: (status: "connecting" | "open" | "closed" | "error") => void;
};

export class WebSocketClient {
  private username: string;
  private cb: WsCallbacks;
  private ws?: WebSocket;
  private retryMs = 1000;
  private stopped = false;
  private keepAliveTimer?: number;

  constructor(username: string, cb: WsCallbacks) {
    this.username = username;
    this.cb = cb;
  }

  start() {
    this.stopped = false;
    this.connect();
  }

  stop() {
    this.stopped = true;
    if (this.keepAliveTimer) window.clearInterval(this.keepAliveTimer);
    if (this.ws) this.ws.close();
  }

  private connect() {
    this.cb.onStatus?.("connecting");
    const url = `${WS_BASE_URL}/${encodeURIComponent(this.username)}`;
    const ws = new WebSocket(url);
    this.ws = ws;

    ws.onopen = () => {
      this.cb.onStatus?.("open");
      this.retryMs = 1000;
      // keep alive
      this.keepAliveTimer = window.setInterval(() => {
        try {
          ws.send("ping");
        } catch {}
      }, 25000);
    };

    ws.onmessage = (ev) => {
      const text = typeof ev.data === "string" ? ev.data : "";
      if (text) this.cb.onNotification(text);
    };

    ws.onerror = () => {
      this.cb.onStatus?.("error");
    };

    ws.onclose = () => {
      this.cb.onStatus?.("closed");
      if (this.keepAliveTimer) window.clearInterval(this.keepAliveTimer);
      if (this.stopped) return;
      // backoff
      const delay = this.retryMs;
      this.retryMs = Math.min(30000, this.retryMs * 2);
      setTimeout(() => this.connect(), delay);
    };
  }
}
