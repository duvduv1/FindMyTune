// lib/services/secure_ws.dart

import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

/// SecureWS handles a WebSocket connection, sending and receiving JSON messages.
class SecureWS {
  final String url;
  WebSocketChannel? _channel;
  bool _connected = false;

  // We keep a single controller for the app lifetime so subscribers don't get
  // closed out when we disconnect/reconnect.
  final _messageController = StreamController<Map<String, dynamic>>.broadcast();

  SecureWS(this.url);

  /// Connects to the WebSocket server at [url], if not already connected.
  Future<void> connect() async {
    if (_connected) return;
    _channel = WebSocketChannel.connect(Uri.parse(url));
    _connected = true;

    // Listen once per connection; push raw JSON into our broadcast controller.
    _channel!.stream.listen((data) {
      try {
        final msg = json.decode(data as String) as Map<String, dynamic>;
        _messageController.add(msg);
      } catch (e, st) {
        _messageController.addError(e, st);
      }
    }, onDone: () {
      // mark disconnected but do NOT close the controller
      _connected = false;
    }, onError: (err, st) {
      _connected = false;
      _messageController.addError(err, st);
    });
  }

  /// Stream of decoded JSON messages from the server.
  Stream<Map<String, dynamic>> get messages => _messageController.stream;

  /// Sends a JSON-serializable [message] to the server, reconnecting if needed.
  Future<void> send(Map<String, dynamic> message) async {
    if (!_connected) {
      await connect();
    }
    _channel!.sink.add(json.encode(message));
  }

  /// Closes the WebSocket connection (but keeps the message stream open).
  Future<void> close() async {
    if (!_connected || _channel == null) return;
    await _channel!.sink.close();
    _connected = false;
    _channel = null;
    // Do not close _messageController: subscribers stay alive for next connect()
  }
}
