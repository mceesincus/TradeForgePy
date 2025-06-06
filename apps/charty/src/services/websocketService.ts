// src/services/websocketService.ts

type MessageCallback = (data: any) => void;
type EventCallback = () => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private messageListeners: MessageCallback[] = [];
  private openListeners: EventCallback[] = [];
  private closeListeners: EventCallback[] = [];
  private errorListeners: EventCallback[] = [];

  public connect(url: string) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      console.log('WebSocket is already connected.');
      return;
    }

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
      this.errorListeners.forEach(cb => cb());
    };

    this.socket.onclose = () => {
      console.log('WebSocket connection closed.');
      this.closeListeners.forEach(cb => cb());
      this.socket = null;
    };
  }

  public sendMessage(data: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.error('WebSocket is not connected.');
    }
  }

  public onMessage(callback: MessageCallback) {
    this.messageListeners.push(callback);
  }

  public onOpen(callback: EventCallback) {
    this.openListeners.push(callback);
  }

  public onClose(callback: EventCallback) {
    this.closeListeners.push(callback);
  }

  public onError(callback: EventCallback) {
    this.errorListeners.push(callback);
  }

  public disconnect() {
    if (this.socket) {
      this.socket.close();
    }
  }
}

export const websocketService = new WebSocketService();