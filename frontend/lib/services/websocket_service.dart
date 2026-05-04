import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

const String cloudUrl = "wss://special-space-palm-tree-x5669qjw764626r57-40047.app.github.dev/ws";

class WebSocketService extends ChangeNotifier {
  WebSocketChannel? _channel;
  final List<String> logs = [];
  bool isScanning = false;
  String currentStatus = "Disconnected";

  void connect([String url = cloudUrl]) {
    try {
      _channel = WebSocketChannel.connect(Uri.parse(url));
      currentStatus = "Connected";
      
      _channel!.stream.listen(
        (message) {
          final data = jsonDecode(message);
          _handleMessage(data);
        },
        onDone: () => _handleDisconnect(),
        onError: (error) => _handleDisconnect(),
      );
    } catch (e) {
      _handleDisconnect();
    }
    notifyListeners();
  }

  void _handleMessage(Map<String, dynamic> data) {
    if (data['type'] == 'log') {
      logs.insert(0, data['message']); // Newest logs at top
    } else if (data['type'] == 'status') {
      isScanning = data['is_running'];
    }
    notifyListeners();
  }

  void sendCommand(String command) {
    _channel?.sink.add(jsonEncode({"command": command}));
  }

  void _handleDisconnect() {
    currentStatus = "Disconnected";
    isScanning = false;
    notifyListeners();
  }
}