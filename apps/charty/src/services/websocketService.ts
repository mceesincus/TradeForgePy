// src/services/websocketService.ts
type MessageCallback = (data: any) => void;
type EventCallback = () => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private url: string = '';
  private messageListeners: Set<MessageCallback> = new Set();
  private openListeners: Set<EventCallback> = new Set();
  private closeListeners: Set<EventCallback> = new Set();

  public connect(url: string) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      if (this.url === url) {
        console.log('WebSocket is already connected to this URL.');
        return;
      }
      this.disconnect(); // Disconnect if URL is different
    }
    this.url = url;

    console.log(`Attempting to connect to WebSocket at ${url}...`);
    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      console.log('WebSocket connection established.');
      this.openListeners.forEach(cb => cb());
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.messageListeners.forEach(cb => cb(data));
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.socket.onclose = () => {
      console.log('WebSocket connection closed.');
      this.closeListeners.forEach(cb => cb());
      this.socket = null;
    };
  }

  public sendMessage(data: any) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.error('Cannot send message, WebSocket is not open.');
    }
  }

  // These methods now return an unsubscribe function
  public onMessage(callback: MessageCallback): () => void {
    this.messageListeners.add(callback);
    return () => this.messageListeners.delete(callback);
  }

  public onOpen(callback: EventCallback): () => void {
    this.openListeners.add(callback);
    return () => this.openListeners.delete(callback);
  }

  public onClose(callback: EventCallback): () => void {
    this.closeListeners.add(callback);
    return () => this.closeListeners.delete(callback);
  }

  public disconnect() {
    if (this.socket) {
      this.socket.close();
    }
  }
}

export const websocketService = new WebSocketService();