// Central place for host, port, scheme, paths ─ easier to tweak later.
library ws_constants;

import 'package:flutter/foundation.dart' show kIsWeb;
import 'dart:io' show Platform;

const String serverURL = 'wss://10.0.0.43:50213';

/// Set to `true` on prod; keep `false` when you’re still using a
/// self‑signed certificate on localhost.
const bool kAllowSelfSigned = true;

final String host =
    kIsWeb ? 'localhost' : (Platform.isAndroid ? '10.0.2.2' : 'localhost');

// A real cert usually listens on 443, but you can keep your dev port
// if you’ve terminated TLS with a reverse proxy (nginx, Caddy, …).
const int port = 50213;

/// We use `wss` (= WebSocket over TLS) everywhere.
/// If you really must fall back to plain WebSocket, change this to `"ws"`.
const String scheme = 'wss';

const String lobbyPath = '/ws'; // for WSRequest
const String gamePath = '/ws'; // for WSService; keep same here
