// Flutter Integration Example
// This file shows how to integrate FCM in a Flutter app

/*
SETUP INSTRUCTIONS:

1. Add dependencies to pubspec.yaml:
   dependencies:
     firebase_core: ^2.24.2
     firebase_messaging: ^14.7.9
     http: ^1.1.0

2. Initialize Firebase in your main.dart
*/

// main.dart
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:io';

// Background message handler
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  print("Handling a background message: ${message.messageId}");
  print("Title: ${message.notification?.title}");
  print("Body: ${message.notification?.body}");
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  
  // Set up background message handler
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FCM Demo',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: FCMDemoScreen(),
    );
  }
}

class FCMDemoScreen extends StatefulWidget {
  @override
  _FCMDemoScreenState createState() => _FCMDemoScreenState();
}

class _FCMDemoScreenState extends State<FCMDemoScreen> {
  final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;
  String? _fcmToken;
  String _lastMessage = 'No messages yet';
  
  // Your Django API base URL
  final String apiBaseUrl = 'https://gospelux.com/api/fcm';
  final String authToken = 'your-auth-token'; // Get from login
  
  @override
  void initState() {
    super.initState();
    _setupFCM();
  }
  
  Future<void> _setupFCM() async {
    // Request permission for iOS
    NotificationSettings settings = await _firebaseMessaging.requestPermission(
      alert: true,
      announcement: false,
      badge: true,
      carPlay: false,
      criticalAlert: false,
      provisional: false,
      sound: true,
    );
    
    print('User granted permission: ${settings.authorizationStatus}');
    
    // Get FCM token
    _fcmToken = await _firebaseMessaging.getToken();
    print('FCM Token: $_fcmToken');
    
    if (_fcmToken != null) {
      // Register device with your Django backend
      await _registerDevice(_fcmToken!);
    }
    
    // Handle foreground messages
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      print('Got a message whilst in the foreground!');
      print('Message data: ${message.data}');
      
      if (message.notification != null) {
        print('Message also contained a notification: ${message.notification}');
        setState(() {
          _lastMessage = '${message.notification!.title}: ${message.notification!.body}';
        });
        
        // Show dialog or snackbar
        _showNotificationDialog(message);
      }
    });
    
    // Handle when user taps on notification
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      print('A new onMessageOpenedApp event was published!');
      // Navigate to specific screen based on message data
      _handleNotificationTap(message);
    });
    
    // Check if app was opened from a notification
    RemoteMessage? initialMessage = await _firebaseMessaging.getInitialMessage();
    if (initialMessage != null) {
      _handleNotificationTap(initialMessage);
    }
    
    // Listen for token refresh
    _firebaseMessaging.onTokenRefresh.listen((newToken) {
      print('FCM Token refreshed: $newToken');
      _registerDevice(newToken);
    });
  }
  
  Future<void> _registerDevice(String token) async {
    try {
      final response = await http.post(
        Uri.parse('$apiBaseUrl/devices/register/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Token $authToken',
        },
        body: json.encode({
          'token': token,
          'platform': Platform.isAndroid ? 'android' : 'ios',
          'device_id': 'unique-device-id', // Generate or get device ID
          'device_name': Platform.isAndroid ? 'Android Device' : 'iOS Device',
        }),
      );
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        print('Device registered successfully');
        final data = json.decode(response.body);
        print('Response: $data');
      } else {
        print('Failed to register device: ${response.statusCode}');
        print('Response: ${response.body}');
      }
    } catch (e) {
      print('Error registering device: $e');
    }
  }
  
  Future<void> _subscribeToTopic(String topic) async {
    try {
      // Subscribe using FCM directly
      await _firebaseMessaging.subscribeToTopic(topic);
      
      // Also register with backend
      final response = await http.post(
        Uri.parse('$apiBaseUrl/topics/subscribe/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Token $authToken',
        },
        body: json.encode({
          'topic': topic,
        }),
      );
      
      if (response.statusCode == 200) {
        print('Subscribed to topic: $topic');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Subscribed to $topic')),
        );
      }
    } catch (e) {
      print('Error subscribing to topic: $e');
    }
  }
  
  Future<void> _unsubscribeFromTopic(String topic) async {
    try {
      // Unsubscribe using FCM directly
      await _firebaseMessaging.unsubscribeFromTopic(topic);
      
      // Also unregister with backend
      final response = await http.post(
        Uri.parse('$apiBaseUrl/topics/unsubscribe/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Token $authToken',
        },
        body: json.encode({
          'topic': topic,
        }),
      );
      
      if (response.statusCode == 200) {
        print('Unsubscribed from topic: $topic');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Unsubscribed from $topic')),
        );
      }
    } catch (e) {
      print('Error unsubscribing from topic: $e');
    }
  }
  
  void _showNotificationDialog(RemoteMessage message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(message.notification?.title ?? 'Notification'),
        content: Text(message.notification?.body ?? 'No content'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('OK'),
          ),
        ],
      ),
    );
  }
  
  void _handleNotificationTap(RemoteMessage message) {
    print('Notification tapped with data: ${message.data}');
    
    // Navigate based on data
    if (message.data.containsKey('screen')) {
      // Navigate to specific screen
      String screen = message.data['screen'];
      print('Navigate to: $screen');
      // Navigator.pushNamed(context, screen);
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('FCM Integration Demo'),
      ),
      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'FCM Token:',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            SizedBox(height: 8),
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey[200],
                borderRadius: BorderRadius.circular(8),
              ),
              child: SelectableText(
                _fcmToken ?? 'Loading...',
                style: TextStyle(fontSize: 12),
              ),
            ),
            SizedBox(height: 24),
            Text(
              'Last Message:',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            SizedBox(height: 8),
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue[50],
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(_lastMessage),
            ),
            SizedBox(height: 24),
            Text(
              'Topic Subscription:',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: () => _subscribeToTopic('general'),
                    child: Text('Subscribe to "general"'),
                  ),
                ),
                SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () => _unsubscribeFromTopic('general'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                    ),
                    child: Text('Unsubscribe'),
                  ),
                ),
              ],
            ),
            SizedBox(height: 12),
            ElevatedButton(
              onPressed: () => _subscribeToTopic('news'),
              child: Text('Subscribe to "news"'),
              style: ElevatedButton.styleFrom(
                minimumSize: Size(double.infinity, 48),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/*
ADDITIONAL SETUP:

1. Android (android/app/build.gradle):
   - Add: apply plugin: 'com.google.gms.google-services'
   - Download google-services.json from Firebase Console
   - Place in android/app/

2. iOS (ios/Runner/Info.plist):
   - Download GoogleService-Info.plist from Firebase Console
   - Add to ios/Runner/
   - Enable push notifications in Xcode

3. Permissions:
   Android (AndroidManifest.xml):
   <uses-permission android:name="android.permission.INTERNET"/>
   <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>

4. Test:
   - Run the app
   - Copy the FCM token
   - Use Django admin or API to send a test notification
*/
