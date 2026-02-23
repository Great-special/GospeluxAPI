// Web App Integration Example (JavaScript/React)
// This file shows how to integrate FCM in a web application

/*
SETUP INSTRUCTIONS:

1. Install Firebase SDK:
   npm install firebase

2. Get your Firebase config from Firebase Console > Project Settings > Web App

3. Enable Firebase Cloud Messaging in Firebase Console

4. Generate VAPID key pair in Firebase Console > Project Settings > Cloud Messaging
*/

// firebase-config.js
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Cloud Messaging
const messaging = getMessaging(app);

export { messaging };

// ============================================
// FCM Service (fcm-service.js)
// ============================================

import { messaging } from './firebase-config';
import { getToken, onMessage } from 'firebase/messaging';

const API_BASE_URL = 'https://your-api.com/api/fcm';
const VAPID_KEY = 'YOUR_VAPID_PUBLIC_KEY'; // From Firebase Console

class FCMService {
  constructor() {
    this.currentToken = null;
    this.authToken = localStorage.getItem('authToken'); // Your auth token
  }

  /**
   * Request notification permission and get FCM token
   */
  async requestPermission() {
    try {
      const permission = await Notification.requestPermission();
      
      if (permission === 'granted') {
        console.log('Notification permission granted.');
        const token = await this.getToken();
        return token;
      } else {
        console.log('Notification permission denied.');
        return null;
      }
    } catch (error) {
      console.error('Error requesting permission:', error);
      return null;
    }
  }

  /**
   * Get FCM token
   */
  async getToken() {
    try {
      const token = await getToken(messaging, { 
        vapidKey: VAPID_KEY 
      });
      
      if (token) {
        console.log('FCM Token:', token);
        this.currentToken = token;
        
        // Register device with backend
        await this.registerDevice(token);
        
        return token;
      } else {
        console.log('No registration token available.');
        return null;
      }
    } catch (error) {
      console.error('Error getting token:', error);
      return null;
    }
  }

  /**
   * Register device token with Django backend
   */
  async registerDevice(token) {
    try {
      const response = await fetch(`${API_BASE_URL}/devices/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${this.authToken}`,
        },
        body: JSON.stringify({
          token: token,
          platform: 'web',
          device_id: this.getDeviceId(),
          device_name: this.getDeviceName(),
        }),
      });

      const data = await response.json();
      
      if (response.ok) {
        console.log('Device registered successfully:', data);
      } else {
        console.error('Failed to register device:', data);
      }
      
      return data;
    } catch (error) {
      console.error('Error registering device:', error);
      throw error;
    }
  }

  /**
   * Subscribe to a topic
   */
  async subscribeToTopic(topic) {
    try {
      const response = await fetch(`${API_BASE_URL}/topics/subscribe/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${this.authToken}`,
        },
        body: JSON.stringify({ topic }),
      });

      const data = await response.json();
      
      if (response.ok) {
        console.log(`Subscribed to topic: ${topic}`);
      } else {
        console.error('Failed to subscribe to topic:', data);
      }
      
      return data;
    } catch (error) {
      console.error('Error subscribing to topic:', error);
      throw error;
    }
  }

  /**
   * Unsubscribe from a topic
   */
  async unsubscribeFromTopic(topic) {
    try {
      const response = await fetch(`${API_BASE_URL}/topics/unsubscribe/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${this.authToken}`,
        },
        body: JSON.stringify({ topic }),
      });

      const data = await response.json();
      
      if (response.ok) {
        console.log(`Unsubscribed from topic: ${topic}`);
      } else {
        console.error('Failed to unsubscribe from topic:', data);
      }
      
      return data;
    } catch (error) {
      console.error('Error unsubscribing from topic:', error);
      throw error;
    }
  }

  /**
   * Listen for foreground messages
   */
  onMessageReceived(callback) {
    onMessage(messaging, (payload) => {
      console.log('Message received in foreground:', payload);
      
      const { notification, data } = payload;
      
      if (notification) {
        // Show notification using browser's notification API
        this.showNotification(notification, data);
      }
      
      // Call callback with payload
      if (callback) {
        callback(payload);
      }
    });
  }

  /**
   * Show browser notification
   */
  showNotification(notification, data) {
    const { title, body, icon, image } = notification;
    
    const options = {
      body: body,
      icon: icon || '/default-icon.png',
      image: image,
      data: data,
      badge: icon,
      tag: 'notification-tag',
      requireInteraction: false,
    };

    // Check if browser supports notifications
    if ('Notification' in window && Notification.permission === 'granted') {
      const notif = new Notification(title, options);
      
      notif.onclick = (event) => {
        event.preventDefault();
        
        // Handle notification click
        if (data?.click_action) {
          window.open(data.click_action, '_blank');
        }
        
        notif.close();
      };
    }
  }

  /**
   * Get unique device ID (generate or retrieve from storage)
   */
  getDeviceId() {
    let deviceId = localStorage.getItem('deviceId');
    
    if (!deviceId) {
      deviceId = this.generateDeviceId();
      localStorage.setItem('deviceId', deviceId);
    }
    
    return deviceId;
  }

  /**
   * Generate unique device ID
   */
  generateDeviceId() {
    return 'web-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
  }

  /**
   * Get device name
   */
  getDeviceName() {
    const ua = navigator.userAgent;
    let browser = 'Unknown';
    
    if (ua.includes('Chrome')) browser = 'Chrome';
    else if (ua.includes('Firefox')) browser = 'Firefox';
    else if (ua.includes('Safari')) browser = 'Safari';
    else if (ua.includes('Edge')) browser = 'Edge';
    
    return `Web - ${browser}`;
  }

  /**
   * Deactivate current device
   */
  async deactivateDevice() {
    try {
      // Get all devices for current user
      const response = await fetch(`${API_BASE_URL}/devices/my_devices/`, {
        headers: {
          'Authorization': `Token ${this.authToken}`,
        },
      });

      const result = await response.json();
      
      if (result.success && result.data.length > 0) {
        // Find current device and deactivate
        const currentDevice = result.data.find(
          device => device.token === this.currentToken
        );
        
        if (currentDevice) {
          await fetch(
            `${API_BASE_URL}/devices/${currentDevice.id}/deactivate/`,
            {
              method: 'POST',
              headers: {
                'Authorization': `Token ${this.authToken}`,
              },
            }
          );
          console.log('Device deactivated');
        }
      }
    } catch (error) {
      console.error('Error deactivating device:', error);
    }
  }
}

// Export singleton instance
const fcmService = new FCMService();
export default fcmService;

// ============================================
// React Component Example (App.js)
// ============================================

import React, { useEffect, useState } from 'react';
import fcmService from './fcm-service';

function App() {
  const [fcmToken, setFcmToken] = useState(null);
  const [lastMessage, setLastMessage] = useState(null);
  const [permissionStatus, setPermissionStatus] = useState('default');

  useEffect(() => {
    // Check current permission status
    setPermissionStatus(Notification.permission);

    // Request permission and initialize FCM
    initializeFCM();

    // Cleanup on unmount
    return () => {
      // Optional: deactivate device on unmount
      // fcmService.deactivateDevice();
    };
  }, []);

  const initializeFCM = async () => {
    // Request permission
    const token = await fcmService.requestPermission();
    
    if (token) {
      setFcmToken(token);
      setPermissionStatus('granted');
      
      // Listen for messages
      fcmService.onMessageReceived((payload) => {
        setLastMessage(payload);
        console.log('Received message:', payload);
      });
    } else {
      setPermissionStatus('denied');
    }
  };

  const handleRequestPermission = async () => {
    await initializeFCM();
  };

  const handleSubscribeTopic = async (topic) => {
    try {
      await fcmService.subscribeToTopic(topic);
      alert(`Subscribed to ${topic}`);
    } catch (error) {
      alert('Failed to subscribe to topic');
    }
  };

  const handleUnsubscribeTopic = async (topic) => {
    try {
      await fcmService.unsubscribeFromTopic(topic);
      alert(`Unsubscribed from ${topic}`);
    } catch (error) {
      alert('Failed to unsubscribe from topic');
    }
  };

  return (
    <div className="App" style={{ padding: '20px' }}>
      <h1>FCM Web Integration Demo</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <h2>Permission Status</h2>
        <p>
          <strong>Status:</strong> {permissionStatus}
        </p>
        {permissionStatus !== 'granted' && (
          <button onClick={handleRequestPermission}>
            Request Notification Permission
          </button>
        )}
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h2>FCM Token</h2>
        <textarea
          readOnly
          value={fcmToken || 'No token yet'}
          style={{ width: '100%', height: '80px' }}
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h2>Last Message</h2>
        <pre style={{ background: '#f5f5f5', padding: '10px' }}>
          {lastMessage 
            ? JSON.stringify(lastMessage, null, 2)
            : 'No messages received yet'
          }
        </pre>
      </div>

      <div>
        <h2>Topic Subscription</h2>
        <button onClick={() => handleSubscribeTopic('general')}>
          Subscribe to "general"
        </button>
        {' '}
        <button onClick={() => handleUnsubscribeTopic('general')}>
          Unsubscribe from "general"
        </button>
        <br /><br />
        <button onClick={() => handleSubscribeTopic('news')}>
          Subscribe to "news"
        </button>
        {' '}
        <button onClick={() => handleUnsubscribeTopic('news')}>
          Unsubscribe from "news"
        </button>
      </div>
    </div>
  );
}

export default App;

// ============================================
// Service Worker (firebase-messaging-sw.js)
// Place this in your public folder
// ============================================

/*
// public/firebase-messaging-sw.js

importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
});

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('Received background message:', payload);

  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: payload.notification.icon || '/firebase-logo.png',
    image: payload.notification.image,
    data: payload.data,
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);
  
  event.notification.close();
  
  const clickAction = event.notification.data?.click_action;
  
  if (clickAction) {
    event.waitUntil(
      clients.openWindow(clickAction)
    );
  }
});
*/
