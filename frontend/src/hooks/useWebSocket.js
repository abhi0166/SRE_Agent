import { useState, useEffect, useRef, useCallback } from 'react';

export const useWebSocket = (url, options = {}) => {
  const [connected, setConnected] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const websocket = useRef(null);
  const reconnectTimer = useRef(null);

  const {
    reconnectInterval = 5000,
    maxReconnectAttempts = 5,
    onOpen,
    onClose,
    onError,
    onMessage
  } = options;

  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const connect = useCallback(() => {
    try {
      websocket.current = new WebSocket(url);

      websocket.current.onopen = (event) => {
        setConnected(true);
        setError(null);
        setReconnectAttempts(0);
        onOpen?.(event);
      };

      websocket.current.onclose = (event) => {
        setConnected(false);
        onClose?.(event);

        // Attempt reconnection if not manually closed
        if (!event.wasClean && reconnectAttempts < maxReconnectAttempts) {
          reconnectTimer.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1);
            connect();
          }, reconnectInterval);
        }
      };

      websocket.current.onerror = (event) => {
        setError(event);
        onError?.(event);
      };

      websocket.current.onmessage = (event) => {
        try {
          const parsedData = JSON.parse(event.data);
          setData(parsedData);
          onMessage?.(parsedData);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };
    } catch (err) {
      setError(err);
      console.error('WebSocket connection failed:', err);
    }
  }, [url, reconnectAttempts, maxReconnectAttempts, reconnectInterval, onOpen, onClose, onError, onMessage]);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
    }
    if (websocket.current) {
      websocket.current.close();
    }
  }, []);

  const sendMessage = useCallback((message) => {
    if (websocket.current && connected) {
      websocket.current.send(JSON.stringify(message));
    }
  }, [connected]);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return {
    connected,
    data,
    error,
    sendMessage,
    disconnect,
    reconnectAttempts
  };
};